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
DASHA_YEAR_DAYS = 365.242199


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
class PratyantardashaPeriod:
    mahadasha: str
    antardasha: str
    pratyantardasha: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class DashaBundle:
    public: dict
    major_periods: list[DashaPeriod]
    antardasha_periods: list[AntardashaPeriod]
    pratyantardasha_periods: list[PratyantardashaPeriod]


def build_vimshottari_dasha(
    moon_longitude: float,
    birth_dt: datetime,
    reference_dt: datetime | None = None,
    year_length: float | None = None,
) -> DashaBundle:
    year_days = year_length if year_length is not None else DASHA_YEAR_DAYS
    reference_dt = reference_dt or datetime.now(tz=timezone.utc)
    nakshatra_index = int(moon_longitude / NAKSHATRA_SPAN)
    mahadasha_lord = DASHA_ORDER[nakshatra_index % len(DASHA_ORDER)]
    degrees_into_nakshatra = moon_longitude % NAKSHATRA_SPAN
    remaining_fraction = (NAKSHATRA_SPAN - degrees_into_nakshatra) / NAKSHATRA_SPAN
    total_major_days = DASHA_YEARS[mahadasha_lord] * year_days
    elapsed_major_days = total_major_days * (1 - remaining_fraction)
    cycle_start = birth_dt - timedelta(days=elapsed_major_days)
 
    major_periods: list[DashaPeriod] = []
    current_start = cycle_start
    start_index = DASHA_ORDER.index(mahadasha_lord)
    for offset in range(len(DASHA_ORDER)):
        lord = DASHA_ORDER[(start_index + offset) % len(DASHA_ORDER)]
        duration = timedelta(days=DASHA_YEARS[lord] * year_days)
        end = current_start + duration
        major_periods.append(DashaPeriod(planet=lord, start=current_start, end=end))
        current_start = end
 
    antardasha_periods: list[AntardashaPeriod] = []
    for major in major_periods:
        major_index = DASHA_ORDER.index(major.planet)
        current_sub_start = major.start
        for offset in range(len(DASHA_ORDER)):
            sub_lord = DASHA_ORDER[(major_index + offset) % len(DASHA_ORDER)]
            duration_days = DASHA_YEARS[major.planet] * DASHA_YEARS[sub_lord] * year_days / 120
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
 
    # --- Pratyantardasha (3rd level) ---
    pratyantardasha_periods: list[PratyantardashaPeriod] = []
    for ad in antardasha_periods:
        ad_index = DASHA_ORDER.index(ad.antardasha)
        pd_start = ad.start
        for offset in range(len(DASHA_ORDER)):
            pd_lord = DASHA_ORDER[(ad_index + offset) % len(DASHA_ORDER)]
            # PD duration = (MD years × AD years × PD years / 120²) × year_days
            pd_days = (
                DASHA_YEARS[ad.mahadasha]
                * DASHA_YEARS[ad.antardasha]
                * DASHA_YEARS[pd_lord]
                * year_days
                / 14400  # 120 * 120
            )
            pd_end = pd_start + timedelta(days=pd_days)
            pratyantardasha_periods.append(
                PratyantardashaPeriod(
                    mahadasha=ad.mahadasha,
                    antardasha=ad.antardasha,
                    pratyantardasha=pd_lord,
                    start=pd_start,
                    end=pd_end,
                )
            )
            pd_start = pd_end

    current_major = _find_current_major(major_periods, reference_dt)
    current_antardasha = _find_current_antardasha(antardasha_periods, reference_dt)
    current_pratyantardasha = _find_current_pratyantardasha(pratyantardasha_periods, reference_dt)

    public = {
        "current": {
            "mahadasha": current_major.planet,
            "antardasha": current_antardasha.antardasha,
            "pratyantardasha": current_pratyantardasha.pratyantardasha,
            "start": current_antardasha.start.date().isoformat(),
            "end": current_antardasha.end.date().isoformat(),
            "pd_start": current_pratyantardasha.start.date().isoformat(),
            "pd_end": current_pratyantardasha.end.date().isoformat(),
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

    return DashaBundle(
        public=public,
        major_periods=major_periods,
        antardasha_periods=antardasha_periods,
        pratyantardasha_periods=pratyantardasha_periods,
    )


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


def _find_current_pratyantardasha(
    periods: list[PratyantardashaPeriod], moment: datetime
) -> PratyantardashaPeriod:
    for period in periods:
        if period.start <= moment < period.end:
            return period
    return periods[-1]
