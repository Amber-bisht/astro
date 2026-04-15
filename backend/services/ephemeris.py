from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import floor
from typing import Any

import swisseph as swe

from backend.services.geocoding import ResolvedBirthData


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

PLANET_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
PLANET_LABELS = {
    "sun": "Sun",
    "moon": "Moon",
    "mars": "Mars",
    "mercury": "Mercury",
    "jupiter": "Jupiter",
    "venus": "Venus",
    "saturn": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}
DISPLAY_TO_KEY = {value: key for key, value in PLANET_LABELS.items()}
SWISS_PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mars": swe.MARS,
    "mercury": swe.MERCURY,
    "jupiter": swe.JUPITER,
    "venus": swe.VENUS,
    "saturn": swe.SATURN,
    "rahu": swe.TRUE_NODE,
}

SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

NAKSHATRA_GANA = {
    "Ashwini": "Deva",
    "Bharani": "Manushya",
    "Krittika": "Rakshasa",
    "Rohini": "Manushya",
    "Mrigashira": "Deva",
    "Ardra": "Manushya",
    "Punarvasu": "Deva",
    "Pushya": "Deva",
    "Ashlesha": "Rakshasa",
    "Magha": "Rakshasa",
    "Purva Phalguni": "Manushya",
    "Uttara Phalguni": "Manushya",
    "Hasta": "Deva",
    "Chitra": "Rakshasa",
    "Swati": "Deva",
    "Vishakha": "Rakshasa",
    "Anuradha": "Deva",
    "Jyeshtha": "Rakshasa",
    "Mula": "Rakshasa",
    "Purva Ashadha": "Manushya",
    "Uttara Ashadha": "Manushya",
    "Shravana": "Deva",
    "Dhanishta": "Rakshasa",
    "Shatabhisha": "Rakshasa",
    "Purva Bhadrapada": "Manushya",
    "Uttara Bhadrapada": "Manushya",
    "Revati": "Deva",
}

NAKSHATRA_NADI = {
    "Ashwini": "Adi",
    "Bharani": "Madhya",
    "Krittika": "Antya",
    "Rohini": "Antya",
    "Mrigashira": "Madhya",
    "Ardra": "Adi",
    "Punarvasu": "Adi",
    "Pushya": "Madhya",
    "Ashlesha": "Antya",
    "Magha": "Antya",
    "Purva Phalguni": "Madhya",
    "Uttara Phalguni": "Adi",
    "Hasta": "Adi",
    "Chitra": "Madhya",
    "Swati": "Antya",
    "Vishakha": "Antya",
    "Anuradha": "Madhya",
    "Jyeshtha": "Adi",
    "Mula": "Adi",
    "Purva Ashadha": "Madhya",
    "Uttara Ashadha": "Antya",
    "Shravana": "Antya",
    "Dhanishta": "Madhya",
    "Shatabhisha": "Adi",
    "Purva Bhadrapada": "Adi",
    "Uttara Bhadrapada": "Madhya",
    "Revati": "Antya",
}

NAKSHATRA_YONI = {
    "Ashwini": "Horse",
    "Bharani": "Elephant",
    "Krittika": "Sheep",
    "Rohini": "Serpent",
    "Mrigashira": "Serpent",
    "Ardra": "Dog",
    "Punarvasu": "Cat",
    "Pushya": "Sheep",
    "Ashlesha": "Cat",
    "Magha": "Rat",
    "Purva Phalguni": "Rat",
    "Uttara Phalguni": "Cow",
    "Hasta": "Buffalo",
    "Chitra": "Tiger",
    "Swati": "Buffalo",
    "Vishakha": "Tiger",
    "Anuradha": "Deer",
    "Jyeshtha": "Deer",
    "Mula": "Dog",
    "Purva Ashadha": "Monkey",
    "Uttara Ashadha": "Mongoose",
    "Shravana": "Monkey",
    "Dhanishta": "Lion",
    "Shatabhisha": "Horse",
    "Purva Bhadrapada": "Lion",
    "Uttara Bhadrapada": "Cow",
    "Revati": "Elephant",
}

TITHIS = [
    "Shukla Pratipada",
    "Shukla Dwitiya",
    "Shukla Tritiya",
    "Shukla Chaturthi",
    "Shukla Panchami",
    "Shukla Shashthi",
    "Shukla Saptami",
    "Shukla Ashtami",
    "Shukla Navami",
    "Shukla Dashami",
    "Shukla Ekadashi",
    "Shukla Dwadashi",
    "Shukla Trayodashi",
    "Shukla Chaturdashi",
    "Purnima",
    "Krishna Pratipada",
    "Krishna Dwitiya",
    "Krishna Tritiya",
    "Krishna Chaturthi",
    "Krishna Panchami",
    "Krishna Shashthi",
    "Krishna Saptami",
    "Krishna Ashtami",
    "Krishna Navami",
    "Krishna Dashami",
    "Krishna Ekadashi",
    "Krishna Dwadashi",
    "Krishna Trayodashi",
    "Krishna Chaturdashi",
    "Amavasya",
]

YOGAS = [
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarman",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]

CHARA_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
FIXED_KARANAS = {1: "Kimstughna", 58: "Shakuni", 59: "Chatushpada", 60: "Naga"}

EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
    "Rahu": "Taurus",
    "Ketu": "Scorpio",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
    "Rahu": "Scorpio",
    "Ketu": "Taurus",
}

OWN_SIGNS = {
    "Sun": {"Leo"},
    "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

NATURAL_RELATIONSHIPS = {
    "Sun": {"friends": {"Moon", "Mars", "Jupiter"}, "neutral": {"Mercury"}, "enemies": {"Venus", "Saturn"}},
    "Moon": {"friends": {"Sun", "Mercury"}, "neutral": {"Mars", "Jupiter", "Venus", "Saturn"}, "enemies": set()},
    "Mars": {"friends": {"Sun", "Moon", "Jupiter"}, "neutral": {"Venus", "Saturn"}, "enemies": {"Mercury"}},
    "Mercury": {"friends": {"Sun", "Venus"}, "neutral": {"Mars", "Jupiter", "Saturn"}, "enemies": {"Moon"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"}, "neutral": {"Saturn"}, "enemies": {"Mercury", "Venus"}},
    "Venus": {"friends": {"Mercury", "Saturn"}, "neutral": {"Mars", "Jupiter"}, "enemies": {"Sun", "Moon"}},
    "Saturn": {"friends": {"Mercury", "Venus"}, "neutral": {"Jupiter"}, "enemies": {"Sun", "Moon", "Mars"}},
    "Rahu": {"friends": {"Mercury", "Venus", "Saturn"}, "neutral": {"Jupiter"}, "enemies": {"Sun", "Moon", "Mars"}},
    "Ketu": {"friends": {"Mars", "Venus", "Saturn"}, "neutral": {"Mercury", "Jupiter"}, "enemies": {"Sun", "Moon"}},
}

BENEFIC_PLANETS = {"Moon", "Mercury", "Jupiter", "Venus"}
MALEFIC_PLANETS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

SIDEREAL_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
NAKSHATRA_SPAN = 360 / 27


@dataclass
class ChartBundle:
    data: dict[str, Any]
    resolved_birth: ResolvedBirthData
    julian_day_ut: float
    moon_longitude: float
    moon_sign_index: int
    moon_nakshatra_index: int
    lagna_sign_index: int
    planet_longitudes: dict[str, float]
    planet_sign_indices: dict[str, int]
    planet_houses: dict[str, int]
    planet_strengths: dict[str, str]


def build_chart_bundle(resolved_birth: ResolvedBirthData) -> ChartBundle:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    utc_dt = resolved_birth.utc_datetime
    _, julian_day_ut = swe.utc_to_jd(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour,
        utc_dt.minute,
        utc_dt.second + utc_dt.microsecond / 1_000_000,
        swe.GREG_CAL,
    )

    cusps, ascmc = swe.houses_ex(
        julian_day_ut,
        resolved_birth.place.lat,
        resolved_birth.place.lon,
        b"W",
        SIDEREAL_FLAGS,
    )
    ascendant_longitude = normalize_longitude(ascmc[0])
    lagna_sign_index = sign_index_from_longitude(ascendant_longitude)

    planet_longitudes: dict[str, float] = {}
    planet_sign_indices: dict[str, int] = {}
    planet_houses: dict[str, int] = {}
    planet_payload: dict[str, dict[str, Any]] = {}

    for planet_key, swiss_id in SWISS_PLANETS.items():
        values, _ = swe.calc_ut(julian_day_ut, swiss_id, SIDEREAL_FLAGS)
        longitude = normalize_longitude(values[0])
        speed = round(values[3], 6)
        sign_index = sign_index_from_longitude(longitude)
        house = whole_sign_house(sign_index, lagna_sign_index)
        nakshatra_name, nakshatra_index, pada = get_nakshatra(longitude)
        planet_longitudes[planet_key] = longitude
        planet_sign_indices[planet_key] = sign_index
        planet_houses[planet_key] = house
        planet_payload[planet_key] = {
            "sign": SIGNS[sign_index],
            "house": house,
            "degree": round(degree_in_sign(longitude), 4),
            "longitude": round(longitude, 4),
            "nakshatra": nakshatra_name,
            "pada": pada,
            "retro": speed < 0,
            "speed": speed,
        }

    rahu_longitude = planet_longitudes["rahu"]
    ketu_longitude = normalize_longitude(rahu_longitude + 180)
    ketu_sign_index = sign_index_from_longitude(ketu_longitude)
    ketu_house = whole_sign_house(ketu_sign_index, lagna_sign_index)
    ketu_nakshatra, _, ketu_pada = get_nakshatra(ketu_longitude)
    planet_longitudes["ketu"] = ketu_longitude
    planet_sign_indices["ketu"] = ketu_sign_index
    planet_houses["ketu"] = ketu_house
    planet_payload["ketu"] = {
        "sign": SIGNS[ketu_sign_index],
        "house": ketu_house,
        "degree": round(degree_in_sign(ketu_longitude), 4),
        "longitude": round(ketu_longitude, 4),
        "nakshatra": ketu_nakshatra,
        "pada": ketu_pada,
        "retro": planet_payload["rahu"]["retro"],
        "speed": planet_payload["rahu"]["speed"],
    }

    house_payload: dict[str, dict[str, Any]] = {}
    lords_mapping: dict[str, str] = {}
    for house_number in range(1, 13):
        sign_index = (lagna_sign_index + house_number - 1) % 12
        sign_name = SIGNS[sign_index]
        lord_name = SIGN_LORDS[sign_name]
        occupants = [
            PLANET_LABELS[planet]
            for planet in PLANET_ORDER
            if planet_houses[planet] == house_number
        ]
        house_payload[str(house_number)] = {"sign": sign_name, "lord": lord_name, "occupants": occupants}
        lords_mapping[str(house_number)] = lord_name

    planet_strengths = {
        planet: classify_planet_strength(PLANET_LABELS[planet], planet_payload[planet]["sign"])
        for planet in PLANET_ORDER
    }

    moon_longitude = planet_longitudes["moon"]
    moon_sign_index = planet_sign_indices["moon"]
    moon_nakshatra_name, moon_nakshatra_index, moon_pada = get_nakshatra(moon_longitude)

    tithi_name = get_tithi_name(planet_longitudes["sun"], moon_longitude)
    yoga_name = get_yoga_name(planet_longitudes["sun"], moon_longitude)
    karana_name = get_karana_name(planet_longitudes["sun"], moon_longitude)

    warnings: list[str] = []
    if resolved_birth.time_accuracy != "exact":
        warnings.append(
            "Birth time is not exact; chart uses 12:00 local time when time is unknown and may shift house-dependent data."
        )

    chart_data = {
        "meta": {
            "ayanamsa": "Lahiri",
            "house_system": "WholeSign",
            "lat": round(resolved_birth.place.lat, 6),
            "lon": round(resolved_birth.place.lon, 6),
            "timezone": resolved_birth.place.timezone,
            "time_accuracy": resolved_birth.time_accuracy,
            "place_name": resolved_birth.place.label,
            "local_datetime": resolved_birth.local_datetime.isoformat(),
            "utc_datetime": resolved_birth.utc_datetime.isoformat(),
            "is_lmt": resolved_birth.is_lmt,
            "warnings": warnings,
        },
        "core_identity": {
            "lagna": SIGNS[lagna_sign_index],
            "lagna_degree": round(degree_in_sign(ascendant_longitude), 4),
            "moon_sign": SIGNS[moon_sign_index],
            "sun_sign": planet_payload["sun"]["sign"],
            "nakshatra": moon_nakshatra_name,
            "nakshatra_pada": moon_pada,
            "tithi": tithi_name,
            "yoga": yoga_name,
            "karana": karana_name,
        },
        "planets": {planet: planet_payload[planet] for planet in PLANET_ORDER},
        "houses": house_payload,
        "lords_mapping": lords_mapping,
        "planet_strength": {planet: planet_strengths[planet] for planet in PLANET_ORDER},
        "doshas": {},
        "house_scores": {},
        "dasha": {},
        "derived_windows": {},
    }

    return ChartBundle(
        data=chart_data,
        resolved_birth=resolved_birth,
        julian_day_ut=julian_day_ut,
        moon_longitude=moon_longitude,
        moon_sign_index=moon_sign_index,
        moon_nakshatra_index=moon_nakshatra_index,
        lagna_sign_index=lagna_sign_index,
        planet_longitudes=planet_longitudes,
        planet_sign_indices=planet_sign_indices,
        planet_houses=planet_houses,
        planet_strengths=planet_strengths,
    )


def normalize_longitude(value: float) -> float:
    return value % 360


def sign_index_from_longitude(longitude: float) -> int:
    return int(floor(normalize_longitude(longitude) / 30))


def degree_in_sign(longitude: float) -> float:
    return normalize_longitude(longitude) % 30


def get_sign(longitude: float) -> str:
    return SIGNS[sign_index_from_longitude(longitude)]


def whole_sign_house(planet_sign_index: int, lagna_sign_index: int) -> int:
    return ((planet_sign_index - lagna_sign_index) % 12) + 1


def get_nakshatra(longitude: float) -> tuple[str, int, int]:
    normalized = normalize_longitude(longitude)
    index = int(normalized / NAKSHATRA_SPAN)
    offset = normalized - (index * NAKSHATRA_SPAN)
    pada = int(offset / (NAKSHATRA_SPAN / 4)) + 1
    return NAKSHATRAS[index], index, pada


def classify_planet_strength(planet_label: str, sign_name: str) -> str:
    if EXALTATION_SIGNS.get(planet_label) == sign_name:
        return "exalted"
    if DEBILITATION_SIGNS.get(planet_label) == sign_name:
        return "debilitated"
    if sign_name in OWN_SIGNS.get(planet_label, set()):
        return "own"

    sign_lord = SIGN_LORDS[sign_name]
    relationship = NATURAL_RELATIONSHIPS[planet_label]
    if sign_lord in relationship["friends"]:
        return "friendly"
    if sign_lord in relationship["enemies"]:
        return "enemy"
    return "neutral"


def relationship_between(planeta: str, planetb: str) -> str:
    if planeta == planetb:
        return "same"
    relations = NATURAL_RELATIONSHIPS[planeta]
    if planetb in relations["friends"]:
        return "friend"
    if planetb in relations["enemies"]:
        return "enemy"
    return "neutral"


def get_tithi_name(sun_longitude: float, moon_longitude: float) -> str:
    elongation = normalize_longitude(moon_longitude - sun_longitude)
    index = int(elongation / 12) % 30
    return TITHIS[index]


def get_yoga_name(sun_longitude: float, moon_longitude: float) -> str:
    total = normalize_longitude(sun_longitude + moon_longitude)
    index = int(total / NAKSHATRA_SPAN) % 27
    return YOGAS[index]


def get_karana_name(sun_longitude: float, moon_longitude: float) -> str:
    elongation = normalize_longitude(moon_longitude - sun_longitude)
    karana_index = int(elongation / 6) + 1
    if karana_index in FIXED_KARANAS:
        return FIXED_KARANAS[karana_index]
    return CHARA_KARANAS[(karana_index - 2) % len(CHARA_KARANAS)]


def compute_transit_snapshot(lagna_sign_index: int) -> dict[str, dict[str, Any]]:
    """Current sidereal positions of Jupiter and Saturn.

    Args:
        lagna_sign_index: The natal lagna sign index so we can report
            which house each transiting planet currently occupies
            relative to the native's ascendant.

    Returns:
        {
            "jupiter": {
                "sign": "Taurus",
                "degree": 12.3456,
                "nakshatra": "Rohini",
                "pada": 2,
                "retro": false,
                "transit_house": 3
            },
            "saturn": { ... }
        }
    """
    from datetime import datetime, timezone as _tz

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now = datetime.now(tz=_tz.utc)
    _, jd_ut = swe.utc_to_jd(
        now.year, now.month, now.day,
        now.hour, now.minute,
        now.second + now.microsecond / 1_000_000,
        swe.GREG_CAL,
    )

    transit_planets = {"jupiter": swe.JUPITER, "saturn": swe.SATURN}
    snapshot: dict[str, dict[str, Any]] = {}

    for key, swiss_id in transit_planets.items():
        values, _ = swe.calc_ut(jd_ut, swiss_id, SIDEREAL_FLAGS)
        longitude = normalize_longitude(values[0])
        speed = round(values[3], 6)
        sign_idx = sign_index_from_longitude(longitude)
        nak_name, _, nak_pada = get_nakshatra(longitude)
        house = whole_sign_house(sign_idx, lagna_sign_index)

        snapshot[key] = {
            "sign": SIGNS[sign_idx],
            "degree": round(degree_in_sign(longitude), 4),
            "nakshatra": nak_name,
            "pada": nak_pada,
            "retro": speed < 0,
            "transit_house": house,
        }

    return snapshot


def iso_date(value: date) -> str:
    return value.isoformat()
