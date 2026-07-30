from __future__ import annotations

from math import floor
from typing import Any
from backend.services.ephemeris import SIGNS, SIGN_LORDS, PLANET_LABELS, whole_sign_house, classify_planet_strength

class VedicEvidenceEngine:
    def __init__(self, chart_data: dict[str, Any]):
        self.chart_data = chart_data
        
        # Determine D60 Lagna index for D60 Dusthana checking
        # Ascendant longitude reconstruction
        lagna_sign = chart_data["core_identity"]["lagna"]
        lagna_deg = chart_data["core_identity"]["lagna_degree"]
        lagna_sign_idx = SIGNS.index(lagna_sign)
        asc_longitude = lagna_sign_idx * 30 + lagna_deg
        
        # D60 division
        d60_span = 30.0 / 60.0  # 0.5 degrees
        d60_pada = int(floor((asc_longitude % 30.0) / d60_span))
        self.d60_lagna_idx = (lagna_sign_idx + d60_pada) % 12

    def get_planet_strength_coefficient(self, planet_key: str) -> float:
        """Calculate a net algebraic strength coefficient for a planet."""
        d1_str = self.chart_data["planet_strength"].get(planet_key, "neutral")
        d9_planets = self.chart_data.get("navamsa", {}).get("planets", {})
        d9_str = d9_planets.get(planet_key, {}).get("strength", "neutral")
        d9_house = d9_planets.get(planet_key, {}).get("navamsa_house", 1)
        
        # 1. Base Dignity weights
        dignity_weights = {
            "exalted": 2.5, "own": 1.5, "friendly": 0.75, "neutral": 0.0,
            "enemy": -0.75, "debilitated": -2.5
        }
        
        coeff = dignity_weights.get(d1_str, 0.0)
        coeff += dignity_weights.get(d9_str, 0.0) * 0.8
        
        # 2. Neechabhanga Check (exaltation override)
        for yoga in self.chart_data.get("yogas", []):
            if "Neechabhanga" in yoga.get("name", "") and planet_key.capitalize() in yoga.get("description", ""):
                coeff += 3.0
                
        # 3. D9 Navamsa Dusthana (-1.5 except Mars in 6th Navamsa)
        if d9_house in {3, 6, 8, 12}:
            if planet_key == "mars" and d9_house == 6:
                coeff += 1.0
            else:
                coeff -= 1.5
                
        # 4. D60 Shashtiamsa Dusthana
        d60_sign = self.chart_data.get("shodashvarga", {}).get("charts", {}).get("D60", {}).get(planet_key)
        if d60_sign and d60_sign in SIGNS:
            d60_sign_idx = SIGNS.index(d60_sign)
            d60_house = whole_sign_house(d60_sign_idx, self.d60_lagna_idx)
            if d60_house in {6, 8, 12}:
                coeff -= 1.0
                
        # 5. Shadbala Shashtiamsa Strength modifier
        total_shashtiamsa = self.chart_data.get("shadbala", {}).get(planet_key, {}).get("total_shashtiamsa", 200.0)
        coeff += (total_shashtiamsa - 200.0) / 100.0
        
        return round(coeff, 2)

    def score_house_advanced(self, house_number: int) -> dict[str, Any]:
        """Refactored house scoring algorithm incorporating BAV/SAV and Shadbala weights."""
        base_score = 5.0
        
        # Lord key
        lord_name = self.chart_data["lords_mapping"][str(house_number)]
        lord_key = lord_name.lower()
        
        # Lord strength coefficient
        lord_coeff = self.get_planet_strength_coefficient(lord_key)
        base_score += lord_coeff * 0.8
        
        # Lord placement in D1
        planets_data = self.chart_data.get("planets", {})
        lord_house = planets_data.get(lord_key, {}).get("house", 1)
        if lord_house in {1, 4, 7, 10}:
            base_score += 1.2
        elif lord_house in {6, 8, 12}:
            base_score -= 1.2
            
        # Occupants
        occupants = self.chart_data["houses"][str(house_number)].get("occupants", [])
        for occupant in occupants:
            occ_key = occupant.lower()
            occ_coeff = self.get_planet_strength_coefficient(occ_key)
            base_score += 0.5 if occ_coeff > 0 else -0.5
            
        # Ashtakavarga SAV points modifier
        sav_points = self.chart_data.get("ashtakvarga", {}).get("sav", [28]*12)[house_number - 1]
        base_score += (sav_points - 28) * 0.1
        
        # BAV Lord points in this house
        bav_points = self.chart_data.get("ashtakvarga", {}).get("bav", {}).get(lord_key, [4]*12)[house_number - 1]
        base_score += (bav_points - 4) * 0.25
        
        lord_strength = self.chart_data.get("planet_strength", {}).get(lord_key, "neutral")
        lord_sign = planets_data.get(lord_key, {}).get("sign", "Aries")
        
        # Aspects received
        aspects_list = self.chart_data.get("aspects", {}).get("aspects_received", {}).get(str(house_number), [])
        aspected_by = [asp["planet"] for asp in aspects_list]
        
        final_score = min(10.0, max(0.0, base_score))
        return {
            "score": round(final_score, 2),
            "lord": lord_name,
            "lord_house": lord_house,
            "lord_strength": lord_strength,
            "lord_sign": lord_sign,
            "occupants": occupants,
            "aspected_by": aspected_by,
            "sav_points": sav_points,
            "bav_points": bav_points,
            "lord_coefficient": lord_coeff
        }

    def get_confidence_interval(self, planet_key: str) -> float:
        """Calculate the percentage confidence of predictions involving this planet."""
        d1_str = self.chart_data["planet_strength"].get(planet_key, "neutral")
        d9_planets = self.chart_data.get("navamsa", {}).get("planets", {})
        d9_str = d9_planets.get(planet_key, {}).get("strength", "neutral")
        d9_house = d9_planets.get(planet_key, {}).get("navamsa_house", 1)
        
        shadbala_strength = self.chart_data.get("shadbala", {}).get(planet_key, {}).get("total_shashtiamsa", 200.0)
        
        # Check alignment of D1 strength, D9 strength, and Shadbala
        d1_is_strong = d1_str in {"exalted", "own", "friendly"}
        d9_is_strong = d9_str in {"exalted", "own", "friendly"}
        shadbala_is_strong = shadbala_strength >= 250.0
        d9_is_dusthana = d9_house in {3, 6, 8, 12}
        
        score = 70.0  # base confidence
        
        # Positive consensus
        if d1_is_strong and d9_is_strong and shadbala_is_strong and not d9_is_dusthana:
            score = 95.0
        elif d1_is_strong and d9_is_strong:
            score = 85.0
        # Conflicting/unstable
        elif d1_is_strong and d9_is_dusthana:
            score = 55.0  # Seshadri Iyer dreamy effect drops confidence in D1 outcomes
        elif not d1_is_strong and d9_is_strong:
            score = 65.0  # Neechabhanga / late rise
            
        return score

    def compile_evidence_chains(self) -> dict[str, Any]:
        """Compile unified evidence chains resolving classical contradictions for key life themes."""
        evidence_chains = {}
        
        # 1. Career (10th Lord & Placements)
        lord_10 = self.chart_data["lords_mapping"]["10"]
        lord_key = lord_10.lower()
        d1_sign = self.chart_data["planets"][lord_key]["sign"]
        d9_sign = self.chart_data.get("navamsa", {}).get("planets", {}).get(lord_key, {}).get("sign", "Unknown")
        d10_sign = self.chart_data.get("shodashvarga", {}).get("charts", {}).get("D10", {}).get(lord_key, "Unknown")
        
        d1_dignity = self.chart_data["planet_strength"].get(lord_key, "neutral")
        d9_dignity = self.chart_data.get("navamsa", {}).get("planets", {}).get(lord_key, {}).get("strength", "neutral")
        
        chain = f"D1 10th Lord ({lord_10}) {d1_dignity} in {d1_sign} ➔ D9 Navamsa {d9_dignity} in {d9_sign} ➔ D10 Dasamsa in {d10_sign}"
        
        # Contradiction Resolution
        if d1_dignity == "exalted" and d9_dignity == "debilitated":
            resolution = f"CRITICAL CONTRADICTION: {lord_10} is exalted in D1 but debilitated in D9. Its external promise of initial grand success will face deep internal struggles and eventual deflation during its dasha."
        elif d1_dignity == "debilitated" and d9_dignity == "exalted":
            resolution = f"ULTRA RAJA YOGA (Neechabhanga): {lord_10} is debilitated in D1 but rises to exaltation in D9. Severe early career struggles or low status will mathematically transform into grand success and public honor."
        else:
            resolution = f"Consistent career path guided by {lord_10}'s placements. Placed favorably in divisional charts."
            
        evidence_chains["career"] = {
            "chain": chain,
            "resolution": resolution,
            "confidence": self.get_confidence_interval(lord_key)
        }
        
        # 2. Mind & Personality (Moon)
        moon_d1_dignity = self.chart_data["planet_strength"].get("moon", "neutral")
        moon_d9_house = self.chart_data.get("navamsa", {}).get("planets", {}).get("moon", {}).get("navamsa_house", 1)
        
        moon_chain = f"Moon {moon_d1_dignity} in D1 ➔ placed in D9 House {moon_d9_house}"
        if moon_d1_dignity == "exalted" and moon_d9_house in {3, 6, 8, 12}:
            moon_resolution = f"SESHADRI IYER DREAMY EFFECT: Moon is exalted but falls in D9 Dusthana (House {moon_d9_house}). While the native exhibits strong mental stamina externally, they experience deep internal anxiety or emotional distance."
        else:
            moon_resolution = "Emotional nature is balanced and consistent across D1 and D9 charts."
            
        evidence_chains["personality"] = {
            "chain": moon_chain,
            "resolution": moon_resolution,
            "confidence": self.get_confidence_interval("moon")
        }
        
        return evidence_chains
