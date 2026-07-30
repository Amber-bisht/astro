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


RASI_MULTIPLIERS = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]
GRAHA_MULTIPLIERS = {
    "sun": 10,
    "moon": 3,
    "mars": 8,
    "mercury": 5,
    "jupiter": 10,
    "venus": 3,
    "saturn": 5
}

def trikona_shodhana(bav: list[int]) -> list[int]:
    """Trikona Shodhana (Triangular Reductions) grouping signs into elemental trines."""
    reduced = list(bav)
    trines = [
        [0, 4, 8],   # Aries, Leo, Sagittarius
        [1, 5, 9],   # Taurus, Virgo, Capricorn
        [2, 6, 10],  # Gemini, Libra, Aquarius
        [3, 7, 11]   # Cancer, Scorpio, Pisces
    ]
    for trine in trines:
        vals = [reduced[i] for i in trine]
        if 0 in vals:
            continue
        min_val = min(vals)
        for i in trine:
            reduced[i] -= min_val
    return reduced

def ekadhipatya_shodhana(bav: list[int], occupied_signs: set[int]) -> list[int]:
    """Ekadhipatya Shodhana (Dual Lordship Reductions) for Mars, Venus, Mercury, Jupiter, Saturn."""
    reduced = list(bav)
    pairs = [
        (0, 7),  # Mars: Aries & Scorpio
        (1, 6),  # Venus: Taurus & Libra
        (2, 5),  # Mercury: Gemini & Virgo
        (8, 11), # Jupiter: Sagittarius & Pisces
        (9, 10)  # Saturn: Capricorn & Aquarius
    ]
    for s1, s2 in pairs:
        b1 = reduced[s1]
        b2 = reduced[s2]
        if b1 == 0 or b2 == 0:
            continue
        
        occ1 = s1 in occupied_signs
        occ2 = s2 in occupied_signs
        
        if not occ1 and not occ2:
            # Both vacant
            if b1 == b2:
                reduced[s1] = 0
                reduced[s2] = 0
            else:
                min_val = min(b1, b2)
                reduced[s1] = min_val
                reduced[s2] = min_val
        elif occ1 != occ2:
            # One occupied, one vacant
            s_vac = s2 if occ1 else s1
            s_occ = s1 if occ1 else s2
            if reduced[s_vac] > reduced[s_occ]:
                reduced[s_vac] = reduced[s_occ]
        else:
            # Both occupied
            continue
            
    return reduced

def calculate_sodhyapinda(reduced_bav: list[int], planet_sign_indices: dict[str, int]) -> int:
    """Calculate the Sodhyapinda (Shodhita Pinda) summing Rasi Pinda and Graha Pinda."""
    rasi_pinda = sum(reduced_bav[i] * RASI_MULTIPLIERS[i] for i in range(12))
    graha_pinda = 0
    for p_key, mult in GRAHA_MULTIPLIERS.items():
        if p_key in planet_sign_indices:
            occ_sign = planet_sign_indices[p_key]
            graha_pinda += reduced_bav[occ_sign] * mult
    return rasi_pinda + graha_pinda


def compute_ashtakvarga(bundle: ChartBundle) -> dict[str, Any]:
    """Compute full Ashtakvarga tables, reductions, and Sodhyapinda.

    Returns:
        {
            "bav": {
                "sun":  [4, 3, 5, ...],   # 12 bindu counts per sign
                ...
            },
            "bav_reductions": {
                "sun": {
                    "trikona_reduced": [...],
                    "ekadhipatya_reduced": [...],
                    "sodhyapinda": 120
                },
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

    # Occupied signs by physical 7 planets
    occupied_signs = set(bundle.planet_sign_indices[p] for p in BAV_PLANETS)

    bav: dict[str, list[int]] = {}
    bav_reductions: dict[str, dict[str, Any]] = {}
    sav = [0] * 12

    for planet_key in BAV_PLANETS:
        rules = _BAV_RULES[planet_key]
        bindus = [0] * 12

        for ref_label, offsets in rules.items():
            ref_sign = reference_signs[ref_label]
            for offset in offsets:
                target_sign = (ref_sign + offset - 1) % 12
                bindus[target_sign] += 1

        bav[planet_key] = bindus
        
        # Reductions
        trikona_reduced = trikona_shodhana(bindus)
        ekadhipatya_reduced = ekadhipatya_shodhana(trikona_reduced, occupied_signs)
        sodhyapinda = calculate_sodhyapinda(ekadhipatya_reduced, bundle.planet_sign_indices)
        
        bav_reductions[planet_key] = {
            "trikona_reduced": trikona_reduced,
            "ekadhipatya_reduced": ekadhipatya_reduced,
            "sodhyapinda": sodhyapinda
        }
        
        for i in range(12):
            sav[i] += bindus[i]

    grand_total = sum(sav)

    return {
        "bav": bav,
        "bav_reductions": bav_reductions,
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
