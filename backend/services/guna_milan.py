from __future__ import annotations

from typing import Any

from backend.services.ephemeris import (
    ChartBundle,
    NAKSHATRA_GANA,
    NAKSHATRA_NADI,
    NAKSHATRA_YONI,
    NATURAL_RELATIONSHIPS,
    PLANET_LABELS,
    SIGNS,
    degree_in_sign,
    relationship_between,
)


VARNA_RANKS = {"Shudra": 1, "Vaishya": 2, "Kshatriya": 3, "Brahmin": 4}
VARNA_BY_SIGN = {
    "Aries": "Kshatriya",
    "Taurus": "Vaishya",
    "Gemini": "Shudra",
    "Cancer": "Brahmin",
    "Leo": "Kshatriya",
    "Virgo": "Vaishya",
    "Libra": "Shudra",
    "Scorpio": "Brahmin",
    "Sagittarius": "Kshatriya",
    "Capricorn": "Vaishya",
    "Aquarius": "Shudra",
    "Pisces": "Brahmin",
}

VASHYA_MATRIX = {
    "Chatushpada": {"Chatushpada": 2.0, "Manava": 1.0, "Jalachara": 1.0, "Vanachara": 1.5, "Keeta": 1.0},
    "Manava": {"Chatushpada": 1.0, "Manava": 2.0, "Jalachara": 1.5, "Vanachara": 0.0, "Keeta": 1.0},
    "Jalachara": {"Chatushpada": 1.0, "Manava": 1.5, "Jalachara": 2.0, "Vanachara": 1.0, "Keeta": 1.0},
    "Vanachara": {"Chatushpada": 0.0, "Manava": 0.0, "Jalachara": 0.0, "Vanachara": 2.0, "Keeta": 0.0},
    "Keeta": {"Chatushpada": 1.0, "Manava": 1.0, "Jalachara": 1.0, "Vanachara": 0.0, "Keeta": 2.0},
}

YONI_SCORE_MATRIX = {
    "Horse": {"Horse": 4, "Elephant": 2, "Sheep": 2, "Serpent": 3, "Dog": 2, "Cat": 2, "Rat": 2, "Cow": 1, "Buffalo": 0, "Tiger": 1, "Deer": 3, "Monkey": 3, "Mongoose": 2, "Lion": 1},
    "Elephant": {"Horse": 2, "Elephant": 4, "Sheep": 3, "Serpent": 3, "Dog": 2, "Cat": 2, "Rat": 2, "Cow": 2, "Buffalo": 3, "Tiger": 1, "Deer": 2, "Monkey": 3, "Mongoose": 2, "Lion": 0},
    "Sheep": {"Horse": 2, "Elephant": 3, "Sheep": 4, "Serpent": 2, "Dog": 1, "Cat": 2, "Rat": 1, "Cow": 3, "Buffalo": 3, "Tiger": 1, "Deer": 2, "Monkey": 0, "Mongoose": 2, "Lion": 1},
    "Serpent": {"Horse": 3, "Elephant": 3, "Sheep": 2, "Serpent": 4, "Dog": 2, "Cat": 1, "Rat": 1, "Cow": 1, "Buffalo": 1, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 0, "Lion": 2},
    "Dog": {"Horse": 2, "Elephant": 2, "Sheep": 1, "Serpent": 2, "Dog": 4, "Cat": 2, "Rat": 1, "Cow": 2, "Buffalo": 2, "Tiger": 1, "Deer": 0, "Monkey": 2, "Mongoose": 1, "Lion": 1},
    "Cat": {"Horse": 2, "Elephant": 2, "Sheep": 2, "Serpent": 1, "Dog": 2, "Cat": 4, "Rat": 0, "Cow": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 3, "Mongoose": 3, "Lion": 2},
    "Rat": {"Horse": 2, "Elephant": 2, "Sheep": 1, "Serpent": 1, "Dog": 1, "Cat": 0, "Rat": 4, "Cow": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 1, "Lion": 2},
    "Cow": {"Horse": 1, "Elephant": 2, "Sheep": 3, "Serpent": 1, "Dog": 2, "Cat": 2, "Rat": 2, "Cow": 4, "Buffalo": 3, "Tiger": 0, "Deer": 3, "Monkey": 2, "Mongoose": 2, "Lion": 1},
    "Buffalo": {"Horse": 0, "Elephant": 3, "Sheep": 3, "Serpent": 1, "Dog": 2, "Cat": 2, "Rat": 2, "Cow": 3, "Buffalo": 4, "Tiger": 1, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 1},
    "Tiger": {"Horse": 1, "Elephant": 1, "Sheep": 1, "Serpent": 2, "Dog": 1, "Cat": 2, "Rat": 2, "Cow": 0, "Buffalo": 1, "Tiger": 4, "Deer": 1, "Monkey": 1, "Mongoose": 2, "Lion": 1},
    "Deer": {"Horse": 3, "Elephant": 2, "Sheep": 2, "Serpent": 2, "Dog": 0, "Cat": 2, "Rat": 2, "Cow": 3, "Buffalo": 2, "Tiger": 1, "Deer": 4, "Monkey": 2, "Mongoose": 2, "Lion": 2},
    "Monkey": {"Horse": 3, "Elephant": 3, "Sheep": 0, "Serpent": 2, "Dog": 2, "Cat": 3, "Rat": 2, "Cow": 2, "Buffalo": 2, "Tiger": 1, "Deer": 2, "Monkey": 4, "Mongoose": 3, "Lion": 2},
    "Mongoose": {"Horse": 2, "Elephant": 2, "Sheep": 2, "Serpent": 0, "Dog": 1, "Cat": 3, "Rat": 1, "Cow": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 3, "Mongoose": 4, "Lion": 2},
    "Lion": {"Horse": 1, "Elephant": 0, "Sheep": 1, "Serpent": 2, "Dog": 1, "Cat": 2, "Rat": 2, "Cow": 1, "Buffalo": 1, "Tiger": 1, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 4},
}

GANA_SCORES = {
    frozenset({"Deva"}): 6.0,
    frozenset({"Manushya"}): 6.0,
    frozenset({"Rakshasa"}): 6.0,
    frozenset({"Deva", "Manushya"}): 5.0,
    frozenset({"Manushya", "Rakshasa"}): 1.0,
    frozenset({"Deva", "Rakshasa"}): 0.0,
}


def calculate_guna_milan(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    breakdown = {
        "varna": varna_score(boy, girl),
        "vasya": vasya_score(boy, girl),
        "tara": tara_score(boy, girl),
        "yoni": yoni_score(boy, girl),
        "maitri": maitri_score(boy, girl),
        "gana": gana_score(boy, girl),
        "bhakoot": bhakoot_score(boy, girl),
        "nadi": nadi_score(boy, girl),
    }
    total = round(sum(g["obtained"] for g in breakdown.values()), 2)
    return {
        "score": total,
        "max_score": 36,
        "breakdown": breakdown,
        "verdict": compatibility_verdict(total),
    }


def compatibility_verdict(score: float) -> str:
    if score >= 30:
        return "Excellent"
    if score >= 24:
        return "Good"
    if score >= 18:
        return "Average"
    return "Challenging"


def varna_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_varna = VARNA_BY_SIGN[boy.data["core_identity"]["moon_sign"]]
    girl_varna = VARNA_BY_SIGN[girl.data["core_identity"]["moon_sign"]]
    score = 1.0 if VARNA_RANKS[boy_varna] >= VARNA_RANKS[girl_varna] else 0.0
    return {
        "boy": boy_varna,
        "girl": girl_varna,
        "max": 1,
        "obtained": score,
        "area": "Work",
    }


def vasya_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_vasya = get_vashya_type(boy)
    girl_vasya = get_vashya_type(girl)
    score = VASHYA_MATRIX[girl_vasya][boy_vasya]
    return {
        "boy": boy_vasya,
        "girl": girl_vasya,
        "max": 2,
        "obtained": score,
        "area": "Dominance",
    }


def tara_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_to_girl = tara_is_favorable(boy.moon_nakshatra_index, girl.moon_nakshatra_index)
    girl_to_boy = tara_is_favorable(girl.moon_nakshatra_index, boy.moon_nakshatra_index)
    score = 3.0 if boy_to_girl and girl_to_boy else 1.5 if boy_to_girl or girl_to_boy else 0.0

    # Get labels for the report
    boy_label = "Favorable" if boy_to_girl else "Unfavorable"
    girl_label = "Favorable" if girl_to_boy else "Unfavorable"

    return {
        "boy": boy_label,
        "girl": girl_label,
        "max": 3,
        "obtained": score,
        "area": "Destiny",
    }


def yoni_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_yoni = get_yoni_type(boy)
    girl_yoni = get_yoni_type(girl)
    score = float(YONI_SCORE_MATRIX[boy_yoni][girl_yoni])
    return {
        "boy": boy_yoni,
        "girl": girl_yoni,
        "max": 4,
        "obtained": score,
        "area": "Mentality",
    }


def maitri_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_lord = boy.data["lords_mapping"][str(whole_moon_house(boy))]
    girl_lord = girl.data["lords_mapping"][str(whole_moon_house(girl))]
    relationship_a = relationship_between(boy_lord, girl_lord)
    relationship_b = relationship_between(girl_lord, boy_lord)
    pair = {relationship_a, relationship_b}
    if relationship_a == "same" or relationship_b == "same" or pair == {"friend"}:
        score = 5.0
    elif pair == {"friend", "neutral"}:
        score = 4.0
    elif pair == {"neutral"}:
        score = 3.0
    elif pair == {"enemy"}:
        score = 0.0
    elif "enemy" in pair and "friend" in pair:
        score = 1.0
    elif "enemy" in pair and "neutral" in pair:
        score = 0.5
    else:
        score = 3.0

    return {
        "boy": boy_lord,
        "girl": girl_lord,
        "max": 5,
        "obtained": score,
        "area": "Compatibility",
    }


def gana_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_gana = get_gana_type(boy)
    girl_gana = get_gana_type(girl)
    score = GANA_SCORES[frozenset({boy_gana, girl_gana})]
    return {
        "boy": boy_gana,
        "girl": girl_gana,
        "max": 6,
        "obtained": score,
        "area": "Guna Level",
    }


def bhakoot_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    compatible = bhakoot_compatible(boy, girl)
    score = 7.0 if compatible else 0.0
    return {
        "boy": boy.data["core_identity"]["moon_sign"],
        "girl": girl.data["core_identity"]["moon_sign"],
        "max": 7,
        "obtained": score,
        "area": "Love",
    }


def nadi_score(boy: ChartBundle, girl: ChartBundle) -> dict[str, Any]:
    boy_nadi = get_nadi_type(boy)
    girl_nadi = get_nadi_type(girl)
    score = 8.0 if boy_nadi != girl_nadi else 0.0
    return {
        "boy": boy_nadi,
        "girl": girl_nadi,
        "max": 8,
        "obtained": score,
        "area": "Health",
    }


def get_nadi_type(bundle: ChartBundle) -> str:
    return NAKSHATRA_NADI[bundle.data["core_identity"]["nakshatra"]]


def get_gana_type(bundle: ChartBundle) -> str:
    return NAKSHATRA_GANA[bundle.data["core_identity"]["nakshatra"]]


def get_yoni_type(bundle: ChartBundle) -> str:
    return NAKSHATRA_YONI[bundle.data["core_identity"]["nakshatra"]]


def get_vashya_type(bundle: ChartBundle) -> str:
    moon_sign = bundle.data["core_identity"]["moon_sign"]
    moon_degree = bundle.data["planets"]["moon"]["degree"]
    if moon_sign in {"Aries", "Taurus"}:
        return "Chatushpada"
    if moon_sign in {"Gemini", "Virgo", "Libra", "Aquarius"}:
        return "Manava"
    if moon_sign in {"Cancer", "Pisces"}:
        return "Jalachara"
    if moon_sign == "Leo":
        return "Vanachara"
    if moon_sign == "Scorpio":
        return "Keeta"
    if moon_sign == "Sagittarius":
        return "Manava" if moon_degree < 15 else "Chatushpada"
    if moon_sign == "Capricorn":
        return "Chatushpada" if moon_degree < 15 else "Jalachara"
    return "Manava"


def bhakoot_distance(bundle: ChartBundle, partner: ChartBundle) -> int:
    return ((partner.moon_sign_index - bundle.moon_sign_index) % 12) + 1


def bhakoot_compatible(boy: ChartBundle, girl: ChartBundle) -> bool:
    bad_distances = {2, 5, 6, 8, 9, 12}
    return bhakoot_distance(boy, girl) not in bad_distances


def tara_is_favorable(start_index: int, end_index: int) -> bool:
    distance = ((end_index - start_index) % 27) + 1
    remainder = distance % 9
    return remainder not in {3, 5, 7}


def whole_moon_house(bundle: ChartBundle) -> int:
    return bundle.planet_houses["moon"]
