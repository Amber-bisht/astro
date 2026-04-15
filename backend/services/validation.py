from __future__ import annotations

from typing import Any


class IncompleteChartDataError(ValueError):
    """Raised when a chart response fails the strict completeness contract."""


REQUIRED_PLANETS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
REQUIRED_HOUSES = {str(index) for index in range(1, 13)}
REQUIRED_HOUSE_SCORES = {"wealth_2nd", "marriage_7th", "career_10th", "gains_11th"}


def validate_full_chart_object(chart: dict[str, Any]) -> None:
    _require_keys(chart, {"meta", "core_identity", "planets", "houses", "lords_mapping", "planet_strength", "doshas", "house_scores", "dasha", "derived_windows", "aspects", "navamsa", "transits"})

    _require_non_empty(chart["meta"], {"ayanamsa", "house_system", "lat", "lon", "timezone", "time_accuracy"})
    _require_non_empty(chart["core_identity"], {"lagna", "moon_sign", "sun_sign", "nakshatra", "nakshatra_pada", "tithi", "yoga", "karana"})

    planets = chart["planets"]
    if set(planets) != REQUIRED_PLANETS:
        raise IncompleteChartDataError("Any planet missing")
    for payload in planets.values():
        _require_non_empty(payload, {"sign", "house", "degree", "nakshatra", "pada", "retro"})

    houses = chart["houses"]
    if set(houses) != REQUIRED_HOUSES:
        raise IncompleteChartDataError("Houses not 1-12")
    for payload in houses.values():
        _require_non_empty(payload, {"sign", "lord"})

    lords_mapping = chart["lords_mapping"]
    if set(lords_mapping) != REQUIRED_HOUSES:
        raise IncompleteChartDataError("Lords mapping incomplete")

    planet_strength = chart["planet_strength"]
    if set(planet_strength) != REQUIRED_PLANETS:
        raise IncompleteChartDataError("Planet strength incomplete")

    doshas = chart["doshas"]
    _require_keys(doshas, {"manglik", "nadi", "bhakoot"})
    _require_non_empty(doshas["manglik"], {"present", "mars_house", "severity", "cancellation"})
    _require_non_empty(doshas["nadi"], {"type"})
    _require_non_empty(doshas["bhakoot"], {"rashi_distance", "compatible"})

    house_scores = chart["house_scores"]
    _require_non_empty(house_scores, REQUIRED_HOUSE_SCORES)
    for hs_key in REQUIRED_HOUSE_SCORES:
        if not isinstance(house_scores[hs_key], dict) or "score" not in house_scores[hs_key]:
            raise IncompleteChartDataError(f"{hs_key} must be a dict with 'score' key")

    dasha = chart["dasha"]
    _require_keys(dasha, {"current", "timeline"})
    _require_non_empty(dasha["current"], {"mahadasha", "antardasha", "start", "end"})
    if not dasha["timeline"]:
        raise IncompleteChartDataError("Dasha missing")

    derived_windows = chart["derived_windows"]
    _require_non_empty(derived_windows, {"marriage_window", "career_peak"})
    for key in ("marriage_window", "career_peak"):
        value = derived_windows[key]
        if not isinstance(value, list) or len(value) != 2 or any(item in (None, "") for item in value):
            raise IncompleteChartDataError(f"{key} incomplete")

    # --- Aspects ---
    aspects = chart["aspects"]
    _require_keys(aspects, {"aspects_given", "aspects_received"})
    if set(aspects["aspects_given"]) != REQUIRED_PLANETS:
        raise IncompleteChartDataError("aspects_given incomplete")
    if set(aspects["aspects_received"]) != REQUIRED_HOUSES:
        raise IncompleteChartDataError("aspects_received incomplete")

    # --- Navamsa (D9) ---
    navamsa = chart["navamsa"]
    _require_keys(navamsa, {"ascendant", "planets"})
    _require_non_empty(navamsa["ascendant"], {"sign", "degree"})
    if set(navamsa["planets"]) != REQUIRED_PLANETS:
        raise IncompleteChartDataError("Navamsa planets incomplete")
    for payload in navamsa["planets"].values():
        _require_non_empty(payload, {"sign", "navamsa_house", "strength"})

    # --- Transit snapshot ---
    transits = chart["transits"]
    _require_non_empty(transits, {"jupiter", "saturn"})
    for t_key in ("jupiter", "saturn"):
        _require_non_empty(transits[t_key], {"sign", "degree", "nakshatra", "pada", "transit_house"})


def _require_keys(payload: dict[str, Any], keys: set[str]) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise IncompleteChartDataError(", ".join(missing))


def _require_non_empty(payload: dict[str, Any], keys: set[str]) -> None:
    for key in keys:
        if key not in payload:
            raise IncompleteChartDataError(key)
        value = payload[key]
        if value is None or value == "" or value == [] or value == {}:
            raise IncompleteChartDataError(key)
