from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
import os
from typing import Any
from zoneinfo import ZoneInfo

import requests


class LocalMeanTime(tzinfo):
    """Custom Timezone object to handle Local Mean Time (LMT) based on longitude."""

    def __init__(self, longitude: float, label: str = "LMT") -> None:
        self.longitude = longitude
        self.label = label
        # Longitude 1 degree = 4 minutes of time (360 degrees = 1440 minutes)
        self.offset_seconds = int(round(longitude * 240))
        self._utcoffset = timedelta(seconds=self.offset_seconds)

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return self._utcoffset

    def tzname(self, dt: datetime | None) -> str:
        return self.label

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)


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
    is_lmt: bool = False


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

    def autocomplete(self, query: str, limit: int = 5, birth_timestamp: int | None = None) -> list[dict[str, Any]]:
        query = query.strip()
        if len(query) < 2:
            return []
        provider = self.require_provider()
        if provider == "opencage":
            return self._opencage_search(query, limit)
        return self._google_search(query, limit, birth_timestamp=birth_timestamp)

    def resolve_place(self, place_input: str | dict[str, Any], birth_timestamp: int | None = None) -> ResolvedPlace:
        if isinstance(place_input, str):
            query = place_input.strip()
            if not query:
                raise LocationResolutionError("Place of birth is required.")
            candidates = self.autocomplete(query, limit=1, birth_timestamp=birth_timestamp)
            top = candidates[0]
            final_timezone = top["timezone"]
            return ResolvedPlace(
                label=top["label"],
                lat=float(top["lat"]),
                lon=float(top["lon"]),
                timezone=final_timezone,
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
        
        # Determine birth timestamp for timezone lookup
        # We use a naive UTC timestamp first to get the correct historical ID
        provisional_utc = datetime.combine(dob, birth_time, tzinfo=timezone.utc)
        birth_timestamp = int(provisional_utc.timestamp())

        place = self.resolve_place(place_input, birth_timestamp=birth_timestamp)

        # --- Professional Grade Historical Override Logic ---
        # We check for regions where IANA (Asia/Kolkata) is generalized
        # Specifically pre-1955 India and pre-standardization Global periods.
        
        target_tz: tzinfo = ZoneInfo(place.timezone)
        is_lmt = False
        
        # India logic
        is_india = "india" in place.label.lower()
        if is_india:
            # 1. Pre-1906: No national standard; force Pure Longitudinal LMT
            if dob.year < 1906:
                target_tz = LocalMeanTime(place.lon, label="LMT")
                is_lmt = True
            # 2. Mumbai (Bombay) Municipal Time (+4:51) used until 1955
            elif dob.year < 1955 and ("mumbai" in place.label.lower() or "bombay" in place.label.lower()):
                target_tz = LocalMeanTime(72.8777, label="Bombay Time")
                is_lmt = True
            # 3. Kolkata (Calcutta) Municipal Time (+5:54) used until 1948
            elif dob.year < 1948 and ("kolkata" in place.label.lower() or "calcutta" in place.label.lower()):
                target_tz = LocalMeanTime(88.3639, label="Calcutta Time")
                is_lmt = True

        # combine() doesn't take fold in Python 3.9; use replace() instead.
        # This handles the second occurrence of a repeated hour (switch-backs).
        local_datetime = datetime.combine(dob, birth_time, tzinfo=target_tz).replace(fold=1)
        utc_datetime = local_datetime.astimezone(timezone.utc)

        return ResolvedBirthData(
            name=(name or "").strip() or None,
            dob=dob,
            birth_time=birth_time,
            time_accuracy=accuracy,
            place=place,
            local_datetime=local_datetime,
            utc_datetime=utc_datetime,
            is_lmt=is_lmt,
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

    def _google_search(self, query: str, limit: int, birth_timestamp: int | None = None) -> list[dict[str, Any]]:
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
            timezone_name = self._google_timezone(float(lat), float(lon), timestamp=birth_timestamp)
            results.append(
                {
                    "label": item.get("formatted_address") or query,
                    "lat": float(lat),
                    "lon": float(lon),
                    "timezone": timezone_name,
                }
            )
        return results

    def _google_timezone(self, lat: float, lon: float, timestamp: int | None = None) -> str:
        if timestamp is None:
            timestamp = int(datetime.now(tz=timezone.utc).timestamp())
            
        response = requests.get(
            "https://maps.googleapis.com/maps/api/timezone/json",
            params={
                "location": f"{lat},{lon}",
                "timestamp": timestamp,
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
