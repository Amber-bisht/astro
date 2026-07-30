from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from backend.services.aspects import compute_aspects
from backend.services.ashtakvarga import compute_ashtakvarga, get_transit_bindu
from backend.services.dasha import DashaBundle, build_vimshottari_dasha
from backend.services.ephemeris import (
    ChartBundle,
    COMPOUND_STRENGTH_WEIGHTS,
    DISPLAY_TO_KEY,
    PLANET_LABELS,
    PLANET_ORDER,
    SIGNS,
    build_chart_bundle,
    compute_transit_snapshot,
    sign_index_from_longitude,
    is_planet_benefic,
    is_planet_malefic,
)
from backend.services.geocoding import ResolvedBirthData
from backend.services.guna_milan import bhakoot_compatible, bhakoot_distance, get_nadi_type
from backend.services.navamsa import compute_navamsa
from backend.services.validation import validate_full_chart_object
from backend.services.yogas import detect_yogas


STRENGTH_WEIGHTS = COMPOUND_STRENGTH_WEIGHTS


def build_pair_charts(boy_birth: ResolvedBirthData, girl_birth: ResolvedBirthData) -> dict[str, dict[str, Any]]:
    boy_bundle = build_chart_bundle(boy_birth)
    girl_bundle = build_chart_bundle(girl_birth)

    _enrich_chart(boy_bundle)
    _enrich_chart(girl_bundle)

    _apply_pairwise_doshas(boy_bundle, girl_bundle)

    validate_full_chart_object(boy_bundle.data)
    validate_full_chart_object(girl_bundle.data)
    return {"boy": boy_bundle.data, "girl": girl_bundle.data}


def build_single_chart(birth: ResolvedBirthData) -> dict[str, Any]:
    """Build a fully enriched chart for a single person (no pairwise doshas)."""
    bundle = build_chart_bundle(birth)
    _enrich_chart(bundle)
    # Remove bhakoot from doshas since there is no partner to compare
    bundle.data["doshas"].pop("bhakoot", None)
    validate_full_chart_object(bundle.data)
    return bundle.data


def _enrich_chart(bundle: ChartBundle) -> None:
    # 1. Base calculations first (aspects, navamsa, transits, yogas, ashtakvarga)
    bundle.data["aspects"] = compute_aspects(bundle)
    bundle.data["navamsa"] = compute_navamsa(bundle)
    bundle.data["transits"] = compute_transit_snapshot(bundle.lagna_sign_index)
    bundle.data["yogas"] = detect_yogas(bundle)

    ashtakvarga = compute_ashtakvarga(bundle)
    bundle.data["ashtakvarga"] = ashtakvarga

    # 2. Heavy-duty Vedic engine computations (Shadbala, Shodashvarga, Graph Yogas, Chandra States, Vedhas)
    from backend.services.shadbala import compute_shadbala
    from backend.services.shodashvarga import compute_shodashvarga
    from backend.services.yoga_compiler import compile_and_detect_yogas
    from backend.services.vedha_engine import check_saptashalaka_vedha, check_sarvatobhadra_vedha
    from backend.services.chandra_states import compute_chandra_states
    from backend.services.evidence_engine import VedicEvidenceEngine

    bundle.data["shadbala"] = compute_shadbala(bundle)
    bundle.data["shodashvarga"] = compute_shodashvarga(bundle)
    bundle.data["graph_yogas"] = compile_and_detect_yogas(bundle)
    bundle.data["chandra_states"] = compute_chandra_states(bundle.moon_longitude)
    
    natal_nak = bundle.data["core_identity"]["nakshatra"]
    bundle.data["vedhas"] = {
        "saptashalaka": check_saptashalaka_vedha(natal_nak, bundle.data["transits"]),
        "sarvatobhadra": check_sarvatobhadra_vedha(natal_nak, bundle.data["transits"])
    }

    # 3. Deterministic Evidence Synthesis & Advanced House Scoring
    engine = VedicEvidenceEngine(bundle.data)
    bundle.data["house_scores"] = {
        "wealth_2nd": engine.score_house_advanced(2),
        "marriage_7th": engine.score_house_advanced(7),
        "career_10th": engine.score_house_advanced(10),
        "gains_11th": engine.score_house_advanced(11)
    }
    bundle.data["evidence_chains"] = engine.compile_evidence_chains()

    # 4. Dasha, Windows, and Doshas (which depend on house_scores)
    dasha_bundle = build_vimshottari_dasha(
        bundle.moon_longitude,
        bundle.resolved_birth.utc_datetime,
        year_length=bundle.resolved_birth.year_length,
    )
    bundle.data["dasha"] = dasha_bundle.public
    bundle.data["derived_windows"] = derive_windows(bundle, dasha_bundle)
    bundle.data["doshas"] = {
        "manglik": compute_manglik(bundle, partner=None),
        "nadi": {"type": get_nadi_type(bundle)},
        "bhakoot": {"rashi_distance": 1, "compatible": True},
    }

    # 5. Rule Book Interpretations
    from backend.services.rule_book_engine import (
        translate_seshadri_iyer_d9,
        translate_phaladeepika_livelihood,
        translate_birth_panchanga,
    )
    bundle.data["rule_book_interpretations"] = {
        "seshadri_iyer_d9": translate_seshadri_iyer_d9(bundle.data),
        "phaladeepika_livelihood": translate_phaladeepika_livelihood(bundle.data),
        "birth_panchanga": translate_birth_panchanga(bundle.data),
    }

    # 6. Enrich transit data with BAV bindus for transit assessment
    for t_key in ("jupiter", "saturn"):
        transit_info = bundle.data["transits"].get(t_key, {})
        t_sign = transit_info.get("sign")
        if t_sign and t_sign in SIGNS:
            t_sign_idx = SIGNS.index(t_sign)
            bindu = get_transit_bindu(ashtakvarga, t_key, t_sign_idx)
            transit_info["bav_bindus"] = bindu
            if bindu is not None:
                transit_info["transit_quality"] = (
                    "favorable" if bindu >= 5
                    else "neutral" if bindu == 4
                    else "challenging"
                )


def _apply_pairwise_doshas(boy: ChartBundle, girl: ChartBundle) -> None:
    boy_manglik = compute_manglik(boy, partner=girl)
    girl_manglik = compute_manglik(girl, partner=boy)
    boy.data["doshas"]["manglik"] = boy_manglik
    girl.data["doshas"]["manglik"] = girl_manglik

    compatibility = bhakoot_compatible(boy, girl)
    boy.data["doshas"]["bhakoot"] = {"rashi_distance": bhakoot_distance(boy, girl), "compatible": compatibility}
    girl.data["doshas"]["bhakoot"] = {"rashi_distance": bhakoot_distance(girl, boy), "compatible": compatibility}


def compute_house_scores(bundle: ChartBundle) -> dict[str, dict[str, Any]]:
    return {
        "wealth_2nd": score_house(bundle, 2),
        "marriage_7th": score_house(bundle, 7),
        "career_10th": score_house(bundle, 10),
        "gains_11th": score_house(bundle, 11),
    }


def score_house(bundle: ChartBundle, house_number: int) -> dict[str, Any]:
    """Score a house and return a full breakdown for AI explainability."""
    score = 5.0
    lord_label = bundle.data["lords_mapping"][str(house_number)]
    lord_key = DISPLAY_TO_KEY[lord_label]
    lord_house = bundle.planet_houses[lord_key]
    lord_strength = bundle.data["planet_strength"][lord_key]
    lord_sign = bundle.data["planets"][lord_key]["sign"]
    score += STRENGTH_WEIGHTS[lord_strength]

    if lord_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 1.5
    elif lord_house in {2, 3}:
        score += 0.5
    elif lord_house in {6, 8, 12}:
        score -= 1.5

    occupants = bundle.data["houses"][str(house_number)].get("occupants", [])
    benefic_occupants: list[str] = []
    malefic_occupants: list[str] = []
    for occupant in occupants:
        occupant_key = DISPLAY_TO_KEY[occupant]
        if is_planet_benefic(occupant, bundle.planet_longitudes):
            score += 0.6
            benefic_occupants.append(occupant)
        elif is_planet_malefic(occupant, bundle.planet_longitudes):
            score -= 0.6
            malefic_occupants.append(occupant)
        if occupant_key == lord_key:
            score += 0.5

    # Gather aspect data (computed before house_scores).
    aspects_received = bundle.data.get("aspects", {}).get("aspects_received", {})
    house_aspects = aspects_received.get(str(house_number), [])
    aspected_by = [entry["planet"] for entry in house_aspects]

    return {
        "score": round(max(0.0, min(10.0, score)), 2),
        "lord": lord_label,
        "lord_sign": lord_sign,
        "lord_house": lord_house,
        "lord_strength": lord_strength,
        "occupants": occupants,
        "benefic_occupants": benefic_occupants,
        "malefic_occupants": malefic_occupants,
        "aspected_by": aspected_by,
    }


def compute_manglik(bundle: ChartBundle, partner: ChartBundle | None) -> dict[str, Any]:
    mars_house = bundle.planet_houses["mars"]
    
    mars_sign_index = bundle.planet_sign_indices["mars"]
    moon_sign_index = bundle.planet_sign_indices["moon"]
    venus_sign_index = bundle.planet_sign_indices["venus"]
    
    mars_house_moon = ((mars_sign_index - moon_sign_index) % 12) + 1
    mars_house_venus = ((mars_sign_index - venus_sign_index) % 12) + 1
    
    lagna_manglik = mars_house in {1, 2, 4, 7, 8, 12}
    moon_manglik = mars_house_moon in {1, 2, 4, 7, 8, 12}
    venus_manglik = mars_house_venus in {1, 2, 4, 7, 8, 12}
    
    present = lagna_manglik or moon_manglik or venus_manglik
    strength = bundle.data["planet_strength"]["mars"]
    
    # 1. Own sign or exalted cancellation
    cancellation = present and strength in {"exalted", "own"}
    
    # 2. Conjunction/Aspect of Jupiter (Jupiter is in same sign as Mars or aspects Mars)
    if present and not cancellation:
        jupiter_house = bundle.planet_houses["jupiter"]
        jupiter_aspects = bundle.data.get("aspects", {}).get("aspects_given", {}).get("jupiter", [])
        if jupiter_house == mars_house or mars_house in jupiter_aspects:
            cancellation = True
            
    # 3. Partner is also Manglik (mutual cancellation)
    if partner is not None and present:
        p_mars_house = partner.planet_houses["mars"]
        p_mars_sign = partner.planet_sign_indices["mars"]
        p_moon_sign = partner.planet_sign_indices["moon"]
        p_venus_sign = partner.planet_sign_indices["venus"]
        
        p_mars_house_moon = ((p_mars_sign - p_moon_sign) % 12) + 1
        p_mars_house_venus = ((p_mars_sign - p_venus_sign) % 12) + 1
        
        partner_manglik = (
            p_mars_house in {1, 2, 4, 7, 8, 12} or
            p_mars_house_moon in {1, 2, 4, 7, 8, 12} or
            p_mars_house_venus in {1, 2, 4, 7, 8, 12}
        )
        if partner_manglik:
            cancellation = True

    severity = "low"
    if present:
        placements = []
        if lagna_manglik:
            placements.append(mars_house)
        if moon_manglik:
            placements.append(mars_house_moon)
        if venus_manglik:
            placements.append(mars_house_venus)
            
        if any(h in {7, 8} for h in placements):
            severity = "high"
        elif all(h == 2 for h in placements):
            severity = "mild"
        else:
            severity = "medium"
            
        if strength in {"exalted", "own"} and severity == "high":
            severity = "medium"
        if cancellation:
            severity = "low"

    return {
        "present": present,
        "mars_house": mars_house,
        "mars_house_moon": mars_house_moon,
        "mars_house_venus": mars_house_venus,
        "lagna_manglik": lagna_manglik,
        "moon_manglik": moon_manglik,
        "venus_manglik": venus_manglik,
        "severity": severity,
        "cancellation": cancellation,
    }


def derive_windows(bundle: ChartBundle, dasha_bundle: DashaBundle) -> dict[str, list[str]]:
    marriage_window = choose_window(
        bundle,
        dasha_bundle,
        primary_lord=bundle.data["lords_mapping"]["7"],
        secondary_lords={bundle.data["lords_mapping"]["2"], "Venus", "Jupiter"},
        relevant_score=bundle.data["house_scores"]["marriage_7th"]["score"],
        future_years=15,
        age_range=(18, 45),
    )
    career_window = choose_window(
        bundle,
        dasha_bundle,
        primary_lord=bundle.data["lords_mapping"]["10"],
        secondary_lords={bundle.data["lords_mapping"]["11"], "Sun", "Saturn", "Mercury"},
        relevant_score=bundle.data["house_scores"]["career_10th"]["score"],
        future_years=18,
        age_range=(21, 60),
    )
    return {"marriage_window": marriage_window, "career_peak": career_window}


def choose_window(
    bundle: ChartBundle,
    dasha_bundle: DashaBundle,
    *,
    primary_lord: str,
    secondary_lords: set[str],
    relevant_score: float,
    future_years: int,
    age_range: tuple[int, int],
) -> list[str]:
    now = datetime.now(tz=timezone.utc)
    future_end = now + timedelta(days=365 * future_years)
    future_candidates = score_periods(
        bundle,
        dasha_bundle.antardasha_periods,
        primary_lord=primary_lord,
        secondary_lords=secondary_lords,
        relevant_score=relevant_score,
        start_limit=now,
        end_limit=future_end,
    )
    if future_candidates:
        return to_year_window(future_candidates[0])

    adulthood_start = bundle.resolved_birth.utc_datetime + timedelta(days=365 * age_range[0])
    adulthood_end = bundle.resolved_birth.utc_datetime + timedelta(days=365 * age_range[1])
    fallback_candidates = score_periods(
        bundle,
        dasha_bundle.antardasha_periods,
        primary_lord=primary_lord,
        secondary_lords=secondary_lords,
        relevant_score=relevant_score,
        start_limit=adulthood_start,
        end_limit=adulthood_end,
    )
    if fallback_candidates:
        return to_year_window(fallback_candidates[0])

    timeline = dasha_bundle.public["timeline"][0]
    return [timeline["start"][:4], timeline["end"][:4]]


def score_periods(
    bundle: ChartBundle,
    periods: list,
    *,
    primary_lord: str,
    secondary_lords: set[str],
    relevant_score: float,
    start_limit: datetime,
    end_limit: datetime,
) -> list:
    scored = []
    target_lords = set(secondary_lords) | {primary_lord}
    for period in periods:
        if period.end < start_limit or period.start > end_limit:
            continue
        score = relevant_score / 5
        if period.mahadasha == primary_lord:
            score += 2.0
        elif period.mahadasha in target_lords:
            score += 1.25
        if period.antardasha == primary_lord:
            score += 2.5
        elif period.antardasha in target_lords:
            score += 1.5
        if score > 2.0:
            scored.append((score, period.start, period.end))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored


def to_year_window(scored_period: tuple[float, datetime, datetime]) -> list[str]:
    _, start, end = scored_period
    return [str(start.year), str(end.year)]
