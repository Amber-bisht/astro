from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
import os
from typing import Any
from zoneinfo import ZoneInfo

import requests


class LocationResolutionError(ValueError):
    """Raised when place or timezone data cannot be resolved."""


class ProviderConfigurationError(LocationResolutionError):
    """Raised when geocoding providers are not configured."""


@dataclass(frozen=True)
class ResolvedPlace:
    label: str
    lat: float
    lon: float
    timezone: str


@dataclass(frozen=True)
class ResolvedBirthData:
    name: str | None
    dob: date
    birth_time: time
    time_accuracy: str
    place: ResolvedPlace
    local_datetime: datetime
    utc_datetime: datetime


class GeocodingService:
    def __init__(self) -> None:
        self.opencage_key = os.getenv("OPENCAGE_API_KEY")
        self.google_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_GEOCODING_API_KEY")

    @property
    def provider_name(self) -> str | None:
        if self.opencage_key:
            return "opencage"
        if self.google_key:
            return "google"
        return None

    def require_provider(self) -> str:
        provider = self.provider_name
        if not provider:
            raise ProviderConfigurationError(
                "Configure OPENCAGE_API_KEY or GOOGLE_MAPS_API_KEY for place lookup."
            )
        return provider

    def autocomplete(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query = query.strip()
        if len(query) < 2:
            return []
        provider = self.require_provider()
        if provider == "opencage":
            return self._opencage_search(query, limit)
        return self._google_search(query, limit)

    def resolve_place(self, place_input: str | dict[str, Any]) -> ResolvedPlace:
        if isinstance(place_input, str):
            query = place_input.strip()
            if not query:
                raise LocationResolutionError("Place of birth is required.")
            candidates = self.autocomplete(query, limit=1)
            if not candidates:
                raise LocationResolutionError(f"Could not resolve place '{query}'.")
            top = candidates[0]
            return ResolvedPlace(
                label=top["label"],
                lat=float(top["lat"]),
                lon=float(top["lon"]),
                timezone=top["timezone"],
            )

        label = (place_input.get("label") or place_input.get("query") or "").strip()
        lat = place_input.get("lat")
        lon = place_input.get("lon")
        timezone_name = place_input.get("timezone")

        if lat is not None and lon is not None and timezone_name:
            self._validate_timezone(timezone_name)
            return ResolvedPlace(
                label=label or f"{lat:.4f}, {lon:.4f}",
                lat=float(lat),
                lon=float(lon),
                timezone=timezone_name,
            )

        query = (place_input.get("query") or label).strip()
        if not query:
            raise LocationResolutionError("Place of birth must include a query or resolved coordinates.")
        return self.resolve_place(query)

    def resolve_birth_details(
        self,
        *,
        name: str | None,
        dob: date,
        time_value: str | None,
        time_accuracy: str | None,
        place_input: str | dict[str, Any],
    ) -> ResolvedBirthData:
        accuracy = self._normalize_time_accuracy(time_value, time_accuracy)
        birth_time = self._parse_birth_time(time_value, accuracy)
        place = self.resolve_place(place_input)
        local_tz = ZoneInfo(place.timezone)
        local_datetime = datetime.combine(dob, birth_time, tzinfo=local_tz)
        utc_datetime = local_datetime.astimezone(timezone.utc)
        return ResolvedBirthData(
            name=(name or "").strip() or None,
            dob=dob,
            birth_time=birth_time,
            time_accuracy=accuracy,
            place=place,
            local_datetime=local_datetime,
            utc_datetime=utc_datetime,
        )

    def _normalize_time_accuracy(self, time_value: str | None, time_accuracy: str | None) -> str:
        normalized_time = (time_value or "").strip().lower()
        normalized_accuracy = (time_accuracy or "").strip().lower()
        if normalized_accuracy and normalized_accuracy not in {"exact", "approx"}:
            raise LocationResolutionError("time_accuracy must be exact or approx.")
        if not normalized_time:
            raise LocationResolutionError("Birth time is required.")
        return normalized_accuracy or "exact"

    def _parse_birth_time(self, time_value: str | None, time_accuracy: str) -> time:
        normalized_time = (time_value or "").strip().lower()
        if not normalized_time:
            raise LocationResolutionError("Birth time is required.")

        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(normalized_time, fmt).time()
            except ValueError:
                continue
        raise LocationResolutionError("Birth time must be in HH:MM or HH:MM:SS format.")

    def _opencage_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            "https://api.opencagedata.com/geocode/v1/json",
            params={
                "q": query,
                "key": self.opencage_key,
                "limit": limit,
                "language": "en",
                "no_annotations": 0,
                "pretty": 0,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("results", []):
            timezone_name = item.get("annotations", {}).get("timezone", {}).get("name")
            lat = item.get("geometry", {}).get("lat")
            lon = item.get("geometry", {}).get("lng")
            if timezone_name and lat is not None and lon is not None:
                results.append(
                    {
                        "label": item.get("formatted") or query,
                        "lat": float(lat),
                        "lon": float(lon),
                        "timezone": timezone_name,
                    }
                )
        return results

    def _google_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": self.google_key},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status")
        if status != "OK":
            raise LocationResolutionError(payload.get("error_message") or f"Google geocoding failed with {status}.")

        results = []
        for item in payload.get("results", [])[:limit]:
            location = item.get("geometry", {}).get("location", {})
            lat = location.get("lat")
            lon = location.get("lng")
            if lat is None or lon is None:
                continue
            timezone_name = self._google_timezone(float(lat), float(lon))
            results.append(
                {
                    "label": item.get("formatted_address") or query,
                    "lat": float(lat),
                    "lon": float(lon),
                    "timezone": timezone_name,
                }
            )
        return results

    def _google_timezone(self, lat: float, lon: float) -> str:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/timezone/json",
            params={
                "location": f"{lat},{lon}",
                "timestamp": int(datetime.now(tz=timezone.utc).timestamp()),
                "key": self.google_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status")
        if status != "OK":
            raise LocationResolutionError(payload.get("errorMessage") or f"Google timezone failed with {status}.")
        timezone_name = payload.get("timeZoneId")
        if not timezone_name:
            raise LocationResolutionError("Google timezone lookup returned no timeZoneId.")
        self._validate_timezone(timezone_name)
        return timezone_name

    @staticmethod
    def _validate_timezone(timezone_name: str) -> None:
        try:
            ZoneInfo(timezone_name)
        except Exception as exc:  # pragma: no cover - defensive path
            raise LocationResolutionError(f"Invalid timezone '{timezone_name}'.") from exc
