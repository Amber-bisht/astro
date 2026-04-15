from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.services.ephemeris import NAKSHATRA_SPAN


DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}
DASHA_YEAR_DAYS = 365.25636


@dataclass(frozen=True)
class DashaPeriod:
    planet: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class AntardashaPeriod:
    mahadasha: str
    antardasha: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class DashaBundle:
    public: dict
    major_periods: list[DashaPeriod]
    antardasha_periods: list[AntardashaPeriod]


def build_vimshottari_dasha(moon_longitude: float, birth_dt: datetime, reference_dt: datetime | None = None) -> DashaBundle:
    reference_dt = reference_dt or datetime.now(tz=timezone.utc)
    nakshatra_index = int(moon_longitude / NAKSHATRA_SPAN)
    mahadasha_lord = DASHA_ORDER[nakshatra_index % len(DASHA_ORDER)]
    degrees_into_nakshatra = moon_longitude % NAKSHATRA_SPAN
    remaining_fraction = (NAKSHATRA_SPAN - degrees_into_nakshatra) / NAKSHATRA_SPAN
    total_major_days = DASHA_YEARS[mahadasha_lord] * DASHA_YEAR_DAYS
    elapsed_major_days = total_major_days * (1 - remaining_fraction)
    cycle_start = birth_dt - timedelta(days=elapsed_major_days)

    major_periods: list[DashaPeriod] = []
    current_start = cycle_start
    start_index = DASHA_ORDER.index(mahadasha_lord)
    for offset in range(len(DASHA_ORDER)):
        lord = DASHA_ORDER[(start_index + offset) % len(DASHA_ORDER)]
        duration = timedelta(days=DASHA_YEARS[lord] * DASHA_YEAR_DAYS)
        end = current_start + duration
        major_periods.append(DashaPeriod(planet=lord, start=current_start, end=end))
        current_start = end

    antardasha_periods: list[AntardashaPeriod] = []
    for major in major_periods:
        major_index = DASHA_ORDER.index(major.planet)
        current_sub_start = major.start
        for offset in range(len(DASHA_ORDER)):
            sub_lord = DASHA_ORDER[(major_index + offset) % len(DASHA_ORDER)]
            duration_days = DASHA_YEARS[major.planet] * DASHA_YEARS[sub_lord] * DASHA_YEAR_DAYS / 120
            current_sub_end = current_sub_start + timedelta(days=duration_days)
            antardasha_periods.append(
                AntardashaPeriod(
                    mahadasha=major.planet,
                    antardasha=sub_lord,
                    start=current_sub_start,
                    end=current_sub_end,
                )
            )
            current_sub_start = current_sub_end

    current_major = _find_current_major(major_periods, reference_dt)
    current_antardasha = _find_current_antardasha(antardasha_periods, reference_dt)

    public = {
        "current": {
            "mahadasha": current_major.planet,
            "antardasha": current_antardasha.antardasha,
            "start": current_antardasha.start.date().isoformat(),
            "end": current_antardasha.end.date().isoformat(),
        },
        "timeline": [
            {
                "planet": period.planet,
                "start": max(period.start, birth_dt).date().isoformat(),
                "end": period.end.date().isoformat(),
            }
            for period in major_periods
            if period.end > birth_dt
        ],
    }

    return DashaBundle(public=public, major_periods=major_periods, antardasha_periods=antardasha_periods)


def _find_current_major(periods: list[DashaPeriod], moment: datetime) -> DashaPeriod:
    for period in periods:
        if period.start <= moment < period.end:
            return period
    return periods[-1]


def _find_current_antardasha(periods: list[AntardashaPeriod], moment: datetime) -> AntardashaPeriod:
    for period in periods:
        if period.start <= moment < period.end:
            return period
    return periods[-1]
