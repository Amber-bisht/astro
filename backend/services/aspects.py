"""Vedic planetary aspects (Drishti) computation.

Standard Vedic aspects:
- Every planet casts a full aspect on the 7th house from itself.
- Mars additionally aspects the 4th and 8th houses.
- Jupiter additionally aspects the 5th and 9th houses.
- Saturn additionally aspects the 3rd and 10th houses.
- Rahu and Ketu are treated like Jupiter (5th, 7th, 9th aspects).
"""

from __future__ import annotations

from typing import Any

from backend.services.ephemeris import (
    BENEFIC_PLANETS,
    ChartBundle,
    MALEFIC_PLANETS,
    PLANET_LABELS,
    PLANET_ORDER,
)

# Offsets from the planet's house (planet house + offset = aspected house).
# All planets have the 7th aspect; special planets add extra offsets.
SPECIAL_ASPECT_OFFSETS: dict[str, list[int]] = {
    "mars": [3, 7],       # 4th and 8th house from Mars
    "jupiter": [4, 8],    # 5th and 9th house from Jupiter
    "saturn": [2, 9],     # 3rd and 10th house from Saturn
    "rahu": [4, 8],       # treated like Jupiter
    "ketu": [4, 8],       # treated like Jupiter
}

# Common 7th-house aspect offset applied to every planet.
UNIVERSAL_ASPECT_OFFSET = 6  # 7th house = current + 6 (0-indexed)


def compute_aspects(bundle: ChartBundle) -> dict[str, Any]:
    """Compute the full Drishti matrix for a chart.

    Returns:
        {
            "aspects_given": {
                "sun": [7],           # house numbers aspected
                "mars": [4, 7, 8],
                ...
            },
            "aspects_received": {
                "1": [{"planet": "Saturn", "type": "malefic"}],
                "2": [],
                ...
            }
        }
    """
    aspects_given: dict[str, list[int]] = {}
    # Initialise every house with an empty list.
    aspects_received: dict[str, list[dict[str, str]]] = {str(h): [] for h in range(1, 13)}

    for planet_key in PLANET_ORDER:
        planet_house = bundle.planet_houses[planet_key]
        label = PLANET_LABELS[planet_key]
        planet_type = "benefic" if label in BENEFIC_PLANETS else "malefic"

        # Collect all offset values for this planet.
        offsets = [UNIVERSAL_ASPECT_OFFSET]  # 7th aspect
        if planet_key in SPECIAL_ASPECT_OFFSETS:
            offsets.extend(SPECIAL_ASPECT_OFFSETS[planet_key])

        aspected_houses: list[int] = []
        for offset in sorted(offsets):
            target_house = ((planet_house - 1 + offset) % 12) + 1
            aspected_houses.append(target_house)
            aspects_received[str(target_house)].append({
                "planet": label,
                "type": planet_type,
            })

        aspects_given[planet_key] = sorted(aspected_houses)

    return {
        "aspects_given": aspects_given,
        "aspects_received": aspects_received,
    }
