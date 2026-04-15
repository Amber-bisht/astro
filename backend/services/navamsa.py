"""Navamsa (D9) divisional chart computation.

The Navamsa divides each sign into 9 equal parts (3°20' each).
The starting sign of the navamsa cycle depends on the element of the
natal sign:
  - Fire  (Aries, Leo, Sagittarius)  → cycle starts from Aries (index 0)
  - Earth (Taurus, Virgo, Capricorn) → cycle starts from Capricorn (index 9)
  - Air   (Gemini, Libra, Aquarius)  → cycle starts from Libra (index 6)
  - Water (Cancer, Scorpio, Pisces)  → cycle starts from Cancer (index 3)
"""

from __future__ import annotations

from math import floor
from typing import Any

from backend.services.ephemeris import (
    ChartBundle,
    PLANET_LABELS,
    PLANET_ORDER,
    SIGNS,
    classify_planet_strength,
    degree_in_sign,
    normalize_longitude,
    sign_index_from_longitude,
    whole_sign_house,
)

NAVAMSA_SPAN = 30.0 / 9  # 3.3333… degrees per navamsa pada

# Starting sign index of navamsa cycle, keyed by element.
ELEMENT_START: dict[str, int] = {
    "Fire": 0,   # Aries
    "Earth": 9,  # Capricorn
    "Air": 6,    # Libra
    "Water": 3,  # Cancer
}

SIGN_ELEMENT: dict[str, str] = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}


def navamsa_sign_index(longitude: float) -> int:
    """Compute the Navamsa sign index for a given sidereal longitude."""
    natal_sign_index = sign_index_from_longitude(longitude)
    natal_sign = SIGNS[natal_sign_index]
    element = SIGN_ELEMENT[natal_sign]
    start = ELEMENT_START[element]
    deg = degree_in_sign(longitude)
    pada = min(int(deg / NAVAMSA_SPAN), 8)  # 0-8
    return (start + pada) % 12


def compute_navamsa(bundle: ChartBundle) -> dict[str, Any]:
    """Build a complete Navamsa (D9) chart payload.

    Returns:
        {
            "ascendant": {"sign": "Libra", "degree": 12.34},
            "planets": {
                "sun":  {"sign": "Gemini", "navamsa_house": 9, "strength": "friendly"},
                ...
            }
        }
    """
    # Navamsa lagna: use the natal ascendant longitude.
    lagna_longitude = bundle.data["planets"]["sun"]["longitude"]  # fallback
    # Reconstruct ascendant longitude from sign + degree.
    lagna_sign = bundle.data["core_identity"]["lagna"]
    lagna_deg = bundle.data["core_identity"]["lagna_degree"]
    lagna_sign_idx = SIGNS.index(lagna_sign)
    asc_longitude = lagna_sign_idx * 30 + lagna_deg

    navamsa_lagna_index = navamsa_sign_index(asc_longitude)
    navamsa_lagna_degree = round(degree_in_sign(asc_longitude) % NAVAMSA_SPAN * (30.0 / NAVAMSA_SPAN), 4)

    planets_payload: dict[str, dict[str, Any]] = {}
    for planet_key in PLANET_ORDER:
        longitude = bundle.planet_longitudes[planet_key]
        d9_sign_idx = navamsa_sign_index(longitude)
        d9_sign = SIGNS[d9_sign_idx]
        d9_house = whole_sign_house(d9_sign_idx, navamsa_lagna_index)
        label = PLANET_LABELS[planet_key]
        strength = classify_planet_strength(label, d9_sign)

        planets_payload[planet_key] = {
            "sign": d9_sign,
            "navamsa_house": d9_house,
            "strength": strength,
        }

    return {
        "ascendant": {
            "sign": SIGNS[navamsa_lagna_index],
            "degree": navamsa_lagna_degree,
        },
        "planets": planets_payload,
    }
