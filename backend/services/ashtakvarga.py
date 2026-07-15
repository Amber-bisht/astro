"""Ashtakvarga (8-fold strength) system for Vedic astrology.

Computes Bhinnashtakvarga (BAV) per planet and Sarvashtakvarga (SAV)
aggregate. The BAV tables follow the standard Parashari rules from
Brihat Parashara Hora Shastra.

Each planet's BAV indicates how many benefic contributions (Bindus)
it receives in each of the 12 signs from the 7 planets + Lagna.
SAV is the sum of all BAV tables per sign (max 56, grand total = 337).
"""

from __future__ import annotations

from typing import Any

from backend.services.ephemeris import (
    ChartBundle,
    PLANET_LABELS,
    SIGNS,
    sign_index_from_longitude,
)


# ────────────────────────────────────────────────────────────
# BAV Rules: For each planet, from each reference point, which
# house-offsets (1-indexed from the reference) award a bindu.
# Source: BPHS Chapter 66-73
# ────────────────────────────────────────────────────────────

# Keys: (planet_receiving, reference_point) → set of offsets that give bindus
# Reference points: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Lagna

_BAV_RULES: dict[str, dict[str, set[int]]] = {
    "sun": {
        "Sun":     {1, 2, 4, 7, 8, 9, 10, 11},
        "Moon":    {3, 6, 10, 11},
        "Mars":    {1, 2, 4, 7, 8, 9, 10, 11},
        "Mercury": {3, 5, 6, 9, 10, 11, 12},
        "Jupiter": {5, 6, 9, 11},
        "Venus":   {6, 7, 12},
        "Saturn":  {1, 2, 4, 7, 8, 9, 10, 11},
        "Lagna":   {3, 4, 6, 10, 11, 12},
    },
    "moon": {
        "Sun":     {3, 6, 7, 8, 10, 11},
        "Moon":    {1, 3, 6, 7, 10, 11},
        "Mars":    {2, 3, 5, 6, 9, 10, 11},
        "Mercury": {1, 3, 4, 5, 7, 8, 10, 11},
        "Jupiter": {1, 4, 7, 8, 10, 11, 12},
        "Venus":   {3, 4, 5, 7, 9, 10, 11},
        "Saturn":  {3, 5, 6, 11},
        "Lagna":   {3, 6, 10, 11},
    },
    "mars": {
        "Sun":     {3, 5, 6, 10, 11},
        "Moon":    {3, 6, 11},
        "Mars":    {1, 2, 4, 7, 8, 10, 11},
        "Mercury": {3, 5, 6, 11},
        "Jupiter": {6, 10, 11, 12},
        "Venus":   {6, 8, 11, 12},
        "Saturn":  {1, 4, 7, 8, 9, 10, 11},
        "Lagna":   {1, 3, 6, 10, 11},
    },
    "mercury": {
        "Sun":     {5, 6, 9, 11, 12},
        "Moon":    {2, 4, 6, 8, 10, 11},
        "Mars":    {1, 2, 4, 7, 8, 9, 10, 11},
        "Mercury": {1, 3, 5, 6, 9, 10, 11, 12},
        "Jupiter": {6, 8, 11, 12},
        "Venus":   {1, 2, 3, 4, 5, 8, 9, 11},
        "Saturn":  {1, 2, 4, 7, 8, 9, 10, 11},
        "Lagna":   {1, 2, 4, 6, 8, 10, 11},
    },
    "jupiter": {
        "Sun":     {1, 2, 3, 4, 7, 8, 9, 10, 11},
        "Moon":    {2, 5, 7, 9, 11},
        "Mars":    {1, 2, 4, 7, 8, 10, 11},
        "Mercury": {1, 2, 4, 5, 6, 9, 10, 11},
        "Jupiter": {1, 2, 3, 4, 7, 8, 10, 11},
        "Venus":   {2, 5, 6, 9, 10, 11},
        "Saturn":  {3, 5, 6, 12},
        "Lagna":   {1, 2, 4, 5, 6, 7, 9, 10, 11},
    },
    "venus": {
        "Sun":     {8, 11, 12},
        "Moon":    {1, 2, 3, 4, 5, 8, 9, 11, 12},
        "Mars":    {3, 4, 6, 8, 11, 12},
        "Mercury": {3, 5, 6, 9, 11},
        "Jupiter": {5, 8, 9, 10, 11},
        "Venus":   {1, 2, 3, 4, 5, 8, 9, 10, 11},
        "Saturn":  {3, 4, 5, 8, 9, 10, 11},
        "Lagna":   {1, 2, 3, 4, 5, 8, 9, 11},
    },
    "saturn": {
        "Sun":     {1, 2, 4, 7, 8, 10, 11},
        "Moon":    {3, 6, 11},
        "Mars":    {3, 5, 6, 10, 11, 12},
        "Mercury": {6, 8, 9, 10, 11, 12},
        "Jupiter": {5, 6, 11, 12},
        "Venus":   {6, 11, 12},
        "Saturn":  {3, 5, 6, 11},
        "Lagna":   {1, 3, 4, 6, 10, 11},
    },
}

# Planets that contribute to BAV (7 true planets, no Rahu/Ketu)
BAV_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def compute_ashtakvarga(bundle: ChartBundle) -> dict[str, Any]:
    """Compute full Ashtakvarga tables.

    Returns:
        {
            "bav": {
                "sun":  [4, 3, 5, ...],   # 12 bindu counts per sign
                "moon": [3, 5, 4, ...],
                ...
            },
            "sav": [28, 31, 25, ...],   # 12 sign totals (sum of all BAV)
            "grand_total": 337
        }
    """
    # Get sign indices for all reference points
    reference_signs: dict[str, int] = {}
    for planet_key in BAV_PLANETS:
        label = PLANET_LABELS[planet_key]
        reference_signs[label] = bundle.planet_sign_indices[planet_key]
    reference_signs["Lagna"] = bundle.lagna_sign_index

    bav: dict[str, list[int]] = {}
    sav = [0] * 12

    for planet_key in BAV_PLANETS:
        rules = _BAV_RULES[planet_key]
        bindus = [0] * 12

        for ref_label, offsets in rules.items():
            ref_sign = reference_signs[ref_label]
            for offset in offsets:
                # offset is 1-indexed from the reference sign
                target_sign = (ref_sign + offset - 1) % 12
                bindus[target_sign] += 1

        bav[planet_key] = bindus
        for i in range(12):
            sav[i] += bindus[i]

    grand_total = sum(sav)

    return {
        "bav": bav,
        "sav": sav,
        "sav_signs": {SIGNS[i]: sav[i] for i in range(12)},
        "grand_total": grand_total,
    }


def get_transit_bindu(
    ashtakvarga: dict[str, Any],
    planet_key: str,
    transit_sign_index: int,
) -> int | None:
    """Get the BAV bindu count for a transiting planet in a given sign.

    Returns None if the planet has no BAV (e.g. Rahu/Ketu).
    """
    bav = ashtakvarga.get("bav", {}).get(planet_key)
    if bav is None:
        return None
    return bav[transit_sign_index]
