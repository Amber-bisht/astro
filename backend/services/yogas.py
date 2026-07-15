"""Yoga (planetary combination) detection for Vedic astrology.

Detects major yogas from the Brihat Parashara Hora Shastra and
other classical texts.  Each yoga has:
- name: classical Sanskrit name
- type: category (raj, dhan, pancha_mahapurusha, special)
- strength: strong | moderate | mild
- description: one-line human-readable explanation
- planets: list of planets forming the yoga
"""

from __future__ import annotations

from typing import Any

from backend.services.ephemeris import (
    ChartBundle,
    PLANET_LABELS,
    PLANET_ORDER,
    SIGN_LORDS,
    SIGNS,
)

# Houses classified by Parashara
KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}

# Planet keys for the 5 true planets that form Pancha Mahapurusha
MAHAPURUSHA_PLANETS = {"mars", "mercury", "jupiter", "venus", "saturn"}


def detect_yogas(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Run all yoga detectors and return a list of detected yogas."""
    yogas: list[dict[str, Any]] = []

    yogas.extend(_detect_raj_yogas(bundle))
    yogas.extend(_detect_dhan_yogas(bundle))
    yogas.extend(_detect_gajakesari(bundle))
    yogas.extend(_detect_pancha_mahapurusha(bundle))
    yogas.extend(_detect_neechabhanga(bundle))
    yogas.extend(_detect_viparita_raj(bundle))
    yogas.extend(_detect_kaal_sarpa(bundle))

    return yogas


# ────────────────────────────────────────────────────────────
# Individual Yoga Detectors
# ────────────────────────────────────────────────────────────


def _detect_raj_yogas(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Raj Yoga: Lord of a Kendra conjunct or exchanging with lord of a Trikona."""
    yogas: list[dict[str, Any]] = []
    lords = bundle.data["lords_mapping"]
    houses = bundle.planet_houses

    kendra_lords: dict[str, str] = {}  # lord_label -> house_number
    trikona_lords: dict[str, str] = {}

    for h in KENDRA_HOUSES:
        lord = lords[str(h)]
        kendra_lords[lord] = str(h)
    for h in TRIKONA_HOUSES:
        lord = lords[str(h)]
        trikona_lords[lord] = str(h)

    # Check for conjunction (same house) or mutual aspect
    from backend.services.ephemeris import DISPLAY_TO_KEY

    for k_lord, k_house_str in kendra_lords.items():
        for t_lord, t_house_str in trikona_lords.items():
            if k_lord == t_lord:
                # Same planet is lord of both kendra and trikona → automatic Raj Yoga
                yogas.append({
                    "name": "Raj Yoga",
                    "type": "raj",
                    "strength": "strong",
                    "description": (
                        f"{k_lord} is lord of Kendra (H{k_house_str}) and "
                        f"Trikona (H{t_house_str})"
                    ),
                    "planets": [k_lord],
                })
                continue

            k_key = DISPLAY_TO_KEY.get(k_lord)
            t_key = DISPLAY_TO_KEY.get(t_lord)
            if k_key is None or t_key is None:
                continue

            k_planet_house = houses.get(k_key)
            t_planet_house = houses.get(t_key)
            if k_planet_house is None or t_planet_house is None:
                continue

            # Conjunction: both lords in same house
            if k_planet_house == t_planet_house:
                yogas.append({
                    "name": "Raj Yoga",
                    "type": "raj",
                    "strength": "strong",
                    "description": (
                        f"{k_lord} (lord of H{k_house_str}) and "
                        f"{t_lord} (lord of H{t_house_str}) conjunct in H{k_planet_house}"
                    ),
                    "planets": [k_lord, t_lord],
                })

            # Exchange: kendra lord in trikona house, trikona lord in kendra house
            elif k_planet_house in TRIKONA_HOUSES and t_planet_house in KENDRA_HOUSES:
                yogas.append({
                    "name": "Raj Yoga (Exchange)",
                    "type": "raj",
                    "strength": "moderate",
                    "description": (
                        f"{k_lord} (H{k_house_str} lord) in Trikona H{k_planet_house}, "
                        f"{t_lord} (H{t_house_str} lord) in Kendra H{t_planet_house}"
                    ),
                    "planets": [k_lord, t_lord],
                })

    # Deduplicate (same pair can appear via multiple house combos)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for y in yogas:
        key = frozenset(y["planets"])
        desc_key = f"{key}|{y['name']}"
        if desc_key not in seen:
            seen.add(desc_key)
            unique.append(y)
    return unique


def _detect_dhan_yogas(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Dhan Yoga: Lords of 2nd, 5th, 9th, or 11th houses conjunct."""
    yogas: list[dict[str, Any]] = []
    lords = bundle.data["lords_mapping"]
    houses = bundle.planet_houses

    dhan_houses = [2, 5, 9, 11]
    dhan_lord_info: list[tuple[str, int, int]] = []  # (lord_label, source_house, current_house)

    from backend.services.ephemeris import DISPLAY_TO_KEY

    for h in dhan_houses:
        lord = lords[str(h)]
        key = DISPLAY_TO_KEY.get(lord)
        if key and key in houses:
            dhan_lord_info.append((lord, h, houses[key]))

    # Check for pairs conjunct in same house
    for i in range(len(dhan_lord_info)):
        for j in range(i + 1, len(dhan_lord_info)):
            lord_a, src_a, house_a = dhan_lord_info[i]
            lord_b, src_b, house_b = dhan_lord_info[j]
            if lord_a == lord_b:
                continue  # Same planet rules both houses
            if house_a == house_b:
                yogas.append({
                    "name": "Dhan Yoga",
                    "type": "dhan",
                    "strength": "strong" if {src_a, src_b} & {9, 11} else "moderate",
                    "description": (
                        f"{lord_a} (H{src_a} lord) and {lord_b} (H{src_b} lord) "
                        f"conjunct in H{house_a}"
                    ),
                    "planets": [lord_a, lord_b],
                })
    return yogas


def _detect_gajakesari(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Gajakesari Yoga: Jupiter in Kendra from Moon."""
    jupiter_house = bundle.planet_houses.get("jupiter")
    moon_house = bundle.planet_houses.get("moon")
    if jupiter_house is None or moon_house is None:
        return []

    distance = ((jupiter_house - moon_house) % 12) + 1
    if distance in KENDRA_HOUSES:
        strength = bundle.data["planet_strength"].get("jupiter", "neutral")
        return [{
            "name": "Gajakesari Yoga",
            "type": "special",
            "strength": "strong" if strength in {"exalted", "own", "adhi_mitra"} else "moderate",
            "description": f"Jupiter in H{jupiter_house} (Kendra from Moon in H{moon_house})",
            "planets": ["Jupiter", "Moon"],
        }]
    return []


def _detect_pancha_mahapurusha(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Pancha Mahapurusha Yogas: Mars/Mercury/Jupiter/Venus/Saturn in
    Kendra in own or exaltation sign.
    """
    YOGA_NAMES = {
        "mars": "Ruchaka",
        "mercury": "Bhadra",
        "jupiter": "Hamsa",
        "venus": "Malavya",
        "saturn": "Shasha",
    }
    yogas: list[dict[str, Any]] = []
    for planet_key in MAHAPURUSHA_PLANETS:
        house = bundle.planet_houses.get(planet_key)
        strength = bundle.data["planet_strength"].get(planet_key, "")
        if house in KENDRA_HOUSES and strength in {"exalted", "own"}:
            label = PLANET_LABELS[planet_key]
            yogas.append({
                "name": f"{YOGA_NAMES[planet_key]} Yoga",
                "type": "pancha_mahapurusha",
                "strength": "strong",
                "description": f"{label} ({strength}) in Kendra H{house}",
                "planets": [label],
            })
    return yogas


def _detect_neechabhanga(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Neechabhanga Raj Yoga: Debilitated planet with cancellation.

    A debilitated planet's dosha is cancelled if:
    1. Lord of the debilitation sign is in a Kendra from Lagna or Moon.
    2. Lord of the exaltation sign is in a Kendra from Lagna or Moon.
    3. The debilitated planet itself is in a Kendra.
    """
    from backend.services.ephemeris import DEBILITATION_SIGNS, EXALTATION_SIGNS, DISPLAY_TO_KEY

    yogas: list[dict[str, Any]] = []
    for planet_key in PLANET_ORDER:
        strength = bundle.data["planet_strength"].get(planet_key, "")
        if strength != "debilitated":
            continue

        label = PLANET_LABELS[planet_key]
        house = bundle.planet_houses[planet_key]
        sign = bundle.data["planets"][planet_key]["sign"]
        sign_lord = SIGN_LORDS[sign]

        # Check cancellation conditions
        cancellation_reason = None

        # Condition 1: Debilitation sign lord in Kendra from Lagna
        lord_key = DISPLAY_TO_KEY.get(sign_lord)
        if lord_key and lord_key in bundle.planet_houses:
            lord_house = bundle.planet_houses[lord_key]
            if lord_house in KENDRA_HOUSES:
                cancellation_reason = f"{sign_lord} (lord of {sign}) in Kendra H{lord_house}"

        # Condition 2: Planet itself in Kendra
        if cancellation_reason is None and house in KENDRA_HOUSES:
            cancellation_reason = f"{label} in Kendra H{house}"

        if cancellation_reason:
            yogas.append({
                "name": "Neechabhanga Raj Yoga",
                "type": "special",
                "strength": "moderate",
                "description": f"{label} debilitated in {sign}, cancelled: {cancellation_reason}",
                "planets": [label],
            })
    return yogas


def _detect_viparita_raj(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Viparita Raj Yoga: Lords of 6th, 8th, 12th in each other's houses."""
    lords = bundle.data["lords_mapping"]
    houses = bundle.planet_houses

    from backend.services.ephemeris import DISPLAY_TO_KEY

    dusthana_lord_info: dict[int, tuple[str, int | None]] = {}
    for h in DUSTHANA_HOUSES:
        lord = lords[str(h)]
        key = DISPLAY_TO_KEY.get(lord)
        current_house = houses.get(key) if key else None
        dusthana_lord_info[h] = (lord, current_house)

    yogas: list[dict[str, Any]] = []
    dusthana_list = sorted(DUSTHANA_HOUSES)
    for i in range(len(dusthana_list)):
        for j in range(i + 1, len(dusthana_list)):
            h1, h2 = dusthana_list[i], dusthana_list[j]
            lord1, house1 = dusthana_lord_info[h1]
            lord2, house2 = dusthana_lord_info[h2]
            if lord1 == lord2:
                continue
            # Lord of one dusthana in another dusthana
            if house1 is not None and house1 in DUSTHANA_HOUSES:
                if house2 is not None and house2 in DUSTHANA_HOUSES:
                    yogas.append({
                        "name": "Viparita Raj Yoga",
                        "type": "special",
                        "strength": "moderate",
                        "description": (
                            f"{lord1} (H{h1} lord) in H{house1}, "
                            f"{lord2} (H{h2} lord) in H{house2}"
                        ),
                        "planets": [lord1, lord2],
                    })
    return yogas


def _detect_kaal_sarpa(bundle: ChartBundle) -> list[dict[str, Any]]:
    """Kaal Sarpa Yoga: All 7 planets between Rahu-Ketu axis (on either side)."""
    rahu_long = bundle.planet_longitudes.get("rahu")
    ketu_long = bundle.planet_longitudes.get("ketu")
    if rahu_long is None or ketu_long is None:
        return []

    check_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
    
    all_in_sec1 = True  # Rahu -> Ketu
    all_in_sec2 = True  # Ketu -> Rahu

    for p_key in check_planets:
        p_long = bundle.planet_longitudes.get(p_key)
        if p_long is None:
            all_in_sec1 = False
            all_in_sec2 = False
            break

        # Sector 1: Rahu -> Ketu
        if rahu_long < ketu_long:
            in_sec1 = rahu_long <= p_long <= ketu_long
        else:
            in_sec1 = p_long >= rahu_long or p_long <= ketu_long

        # Sector 2: Ketu -> Rahu
        if ketu_long < rahu_long:
            in_sec2 = ketu_long <= p_long <= rahu_long
        else:
            in_sec2 = p_long >= ketu_long or p_long <= rahu_long

        if not in_sec1:
            all_in_sec1 = False
        if not in_sec2:
            all_in_sec2 = False

    if all_in_sec1 or all_in_sec2:
        return [{
            "name": "Kaal Sarpa Yoga",
            "type": "special",
            "strength": "strong",
            "description": "All planets hemmed between Rahu-Ketu axis",
            "planets": ["Rahu", "Ketu"],
        }]
    return []
