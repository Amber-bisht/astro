from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
import jwt
import requests
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
db_client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI else None
db = db_client.get_default_database() if db_client else None

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "kundali-default-secret-change-me")
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

from backend.services.chart_builder import build_pair_charts, build_single_chart
from backend.services.geocoding import (
    GeocodingService,
    LocationResolutionError,
    ProviderConfigurationError,
)
from backend.services.guna_milan import calculate_guna_milan
from backend.services.ephemeris import build_chart_bundle
from backend.services.validation import IncompleteChartDataError


class PlaceInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: Optional[str] = None
    label: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    timezone: Optional[str] = None


class PersonInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    gender: Optional[str] = None
    dob: str
    time: str
    time_accuracy: Optional[Literal["exact", "approx"]] = "exact"
    place: Union[str, PlaceInput]


class CompatibilityRequest(BaseModel):
    boy: PersonInput
    girl: PersonInput


BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Kundali Compatibility Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")

geocoding_service = GeocodingService()


@app.exception_handler(IncompleteChartDataError)
async def incomplete_chart_handler(_, __):
    return JSONResponse(status_code=500, content={"error": "incomplete_chart_data"})


@app.exception_handler(LocationResolutionError)
async def location_error_handler(_, exc: LocationResolutionError):
    status_code = 503 if isinstance(exc, ProviderConfigurationError) else 422
    return JSONResponse(status_code=status_code, content={"error": "invalid_birth_details", "detail": str(exc)})


@app.exception_handler(requests.RequestException)
async def request_error_handler(_, exc: requests.RequestException):
    return JSONResponse(status_code=502, content={"error": "geocoding_provider_error", "detail": str(exc)})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/matching")
async def matching_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "matching.html")


@app.get("/kundli")
async def kundli_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "single.html")


@app.get("/daily")
async def daily_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "daily.html")


@app.get("/monthly")
async def monthly_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "monthly.html")


@app.get("/yearly")
async def yearly_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "yearly.html")


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "geocoding_provider": geocoding_service.provider_name,
        "autocomplete_configured": geocoding_service.provider_name is not None,
    }


# ============================================================
# AUTH — JWT + httpOnly cookies
# ============================================================


def _get_user(request: Request) -> Optional[dict]:
    """Decode JWT from the session cookie. Returns {email, name, picture} or None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def _set_session_cookie(response: Response, user: dict) -> None:
    """Sign a JWT with user info and set it as an httpOnly cookie."""
    token = jwt.encode(
        {"email": user["email"], "name": user["name"], "picture": user["picture"]},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@app.get("/auth/config")
async def auth_config() -> dict:
    return {"google_client_id": GOOGLE_CLIENT_ID}


class GoogleAuthRequest(BaseModel):
    credential: str


@app.post("/auth/google")
async def google_auth(payload: GoogleAuthRequest, response: Response) -> dict:
    """Verify Google ID token, create/find user, set JWT cookie."""
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
            timeout=5,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        token_data = resp.json()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not verify token with Google")

    if GOOGLE_CLIENT_ID and token_data.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Token audience mismatch")

    email = token_data.get("email")
    name = token_data.get("name", email)
    picture = token_data.get("picture", "")

    if not email:
        raise HTTPException(status_code=401, detail="No email in token")

    # Save/update user in DB
    if db is not None:
        await db.users.update_one(
            {"email": email},
            {"$set": {"email": email, "name": name, "picture": picture}},
            upsert=True,
        )

    user = {"email": email, "name": name, "picture": picture}
    _set_session_cookie(response, user)

    return user


@app.get("/auth/me")
async def auth_me(request: Request) -> dict:
    user = _get_user(request)
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, **user}


@app.post("/auth/logout")
async def auth_logout(response: Response) -> dict:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}


# ============================================================
# PROFILES (bound to logged-in user via cookie)
# ============================================================


@app.get("/profiles")
async def get_profiles(
    request: Request,
    gender: Optional[str] = Query(None),
) -> dict:
    if db is None:
        return {"profiles": []}

    user = _get_user(request)
    if not user:
        return {"profiles": []}

    query: dict = {"user_email": user["email"]}
    if gender:
        query["gender"] = gender

    cursor = db.profiles.find(query, {"_id": 0, "user_email": 0}).sort("name", 1)
    profiles = await cursor.to_list(length=1000)
    return {"profiles": profiles}


@app.post("/profiles")
async def save_profile(
    profile: PersonInput,
    request: Request,
) -> dict:
    if db is None:
        return {"status": "error", "message": "DB not configured"}
    if not profile.name:
        raise HTTPException(status_code=422, detail="Name is required to save a profile.")

    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required to save profiles.")

    data = profile.model_dump(exclude_none=True)
    data["user_email"] = user["email"]
    await db.profiles.update_one(
        {"name": profile.name, "user_email": user["email"]},
        {"$set": data},
        upsert=True,
    )
    return {"status": "ok", "message": f"Profile '{profile.name}' saved."}


@app.get("/places/autocomplete")
def autocomplete(q: str = Query(..., min_length=2, max_length=120)) -> dict[str, object]:
    results = geocoding_service.autocomplete(q)
    return {"results": results, "provider": geocoding_service.provider_name}


@app.post("/guna-milan")
def guna_milan(payload: CompatibilityRequest) -> dict:
    boy_resolved, girl_resolved = _resolve_people(payload)
    boy_chart = build_chart_bundle(boy_resolved)
    girl_chart = build_chart_bundle(girl_resolved)

    # Auto-save profiles if names are present and user is logged in
    # Note: guna_milan doesn't receive auth header, so skip auto-save here

    response = calculate_guna_milan(boy_chart, girl_chart)
    response["boy_meta"] = {
        "lat": boy_resolved.place.lat,
        "lon": boy_resolved.place.lon,
        "timezone": boy_resolved.local_datetime.tzname(),
        "label": boy_resolved.place.label,
        "is_lmt": boy_resolved.is_lmt,
    }
    response["girl_meta"] = {
        "lat": girl_resolved.place.lat,
        "lon": girl_resolved.place.lon,
        "timezone": girl_resolved.local_datetime.tzname(),
        "label": girl_resolved.place.label,
        "is_lmt": girl_resolved.is_lmt,
    }

    warnings = _warnings_for_people(boy_chart, girl_chart)
    if warnings:
        response["warnings"] = warnings
    return response


@app.post("/full-data")
def full_data(payload: CompatibilityRequest) -> dict:
    boy_resolved, girl_resolved = _resolve_people(payload)
    
    # Auto-save profiles if names are present and user is logged in
    # Note: full-data doesn't receive auth header, so skip auto-save here

    charts = build_pair_charts(boy_resolved, girl_resolved)

    # Include Guna Milan so AI prompts have everything in one response
    boy_chart = build_chart_bundle(boy_resolved)
    girl_chart = build_chart_bundle(girl_resolved)
    guna_milan_result = calculate_guna_milan(boy_chart, girl_chart)
    charts["guna_milan"] = guna_milan_result

    return charts


@app.post("/single-chart")
def single_chart(payload: PersonInput) -> dict:
    resolved = geocoding_service.resolve_birth_details(
        name=payload.name,
        dob=_parse_date(payload.dob),
        time_value=payload.time,
        time_accuracy=payload.time_accuracy,
        place_input=_serialize_place(payload.place),
    )

    # Auto-save profile if name is present and user is logged in
    # Note: single-chart doesn't receive auth header, so skip auto-save here

    chart_data = build_single_chart(resolved)

    return {
        "chart": chart_data,
        "meta": {
            "lat": resolved.place.lat,
            "lon": resolved.place.lon,
            "timezone": resolved.local_datetime.tzname(),
            "label": resolved.place.label,
            "is_lmt": resolved.is_lmt,
        },
    }


def _resolve_people(payload: CompatibilityRequest):
    return (
        geocoding_service.resolve_birth_details(
            name=payload.boy.name,
            dob=_parse_date(payload.boy.dob),
            time_value=payload.boy.time,
            time_accuracy=payload.boy.time_accuracy,
            place_input=_serialize_place(payload.boy.place),
        ),
        geocoding_service.resolve_birth_details(
            name=payload.girl.name,
            dob=_parse_date(payload.girl.dob),
            time_value=payload.girl.time,
            time_accuracy=payload.girl.time_accuracy,
            place_input=_serialize_place(payload.girl.place),
        ),
    )


def _serialize_place(place: Union[str, PlaceInput]):
    if isinstance(place, PlaceInput):
        return place.model_dump(exclude_none=True)
    return place


def _parse_date(value: str):
    from datetime import datetime

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="dob must be in YYYY-MM-DD format") from exc


def _warnings_for_people(*bundles) -> list[str]:
    warnings: list[str] = []
    for role, bundle in zip(("Boy", "Girl"), bundles):
        if bundle.data["meta"]["time_accuracy"] != "exact":
            warnings.append(f"{role}: birth time marked {bundle.data['meta']['time_accuracy']}.")
    return warnings
