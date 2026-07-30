from __future__ import annotations

from typing import Any
from backend.services.ephemeris import SIGNS, SIGN_LORDS
from backend.services.ashtakvarga import BAV_PLANETS

# Deep Exaltation Longitudes
DEEP_EXALTATIONS = {
    "sun": 10.0,      # 10 Aries
    "moon": 33.0,     # 3 Taurus
    "mars": 298.0,    # 28 Capricorn
    "mercury": 165.0, # 15 Virgo
    "jupiter": 95.0,  # 5 Cancer
    "venus": 357.0,   # 27 Pisces
    "saturn": 200.0   # 20 Libra
}

# Optimal houses for Dig Bala (Directional Strength)
DIG_BALA_OPTIMAL_HOUSES = {
    "jupiter": 1,
    "mercury": 1,
    "sun": 10,
    "mars": 10,
    "saturn": 7,
    "moon": 4,
    "venus": 4
}

# Odd/Even sign genders
ODD_SIGNS = {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"}
EVEN_SIGNS = {"Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"}

PLANET_GENDERS = {
    "sun": "male", "mars": "male", "jupiter": "male",
    "moon": "female", "venus": "female",
    "mercury": "neutral", "saturn": "neutral"
}

def calculate_sthana_bala(planet_key: str, bundle: ChartBundle) -> dict[str, float]:
    """Calculate Sthana Bala (Positional Strength) of a planet."""
    # 1. Uchcha Bala (Exaltation strength)
    p_long = bundle.planet_longitudes.get(planet_key, 0.0)
    deep_ex = DEEP_EXALTATIONS.get(planet_key, 0.0)
    diff = abs(p_long - deep_ex) % 360
    distance = min(diff, 360 - diff)
    uchcha_bala = max(0.0, (1.0 - (distance / 180.0)) * 60.0)
    
    # 2. Ojhayugmarasi Bala (Odd/Even sign placement)
    sign = bundle.data["planets"].get(planet_key, {}).get("sign", "Aries")
    gender = PLANET_GENDERS.get(planet_key, "male")
    ojha_bala = 0.0
    if gender in {"male", "neutral"} and sign in ODD_SIGNS:
        ojha_bala = 15.0
    elif gender == "female" and sign in EVEN_SIGNS:
        ojha_bala = 15.0
        
    # 3. Saptavarga Bala (divisional dignity)
    # We assign points based on D1 strength as a proxy, scaled to 7 vargas
    d1_str = bundle.data["planet_strength"].get(planet_key, "neutral")
    strength_vals = {
        "exalted": 60.0, "own": 45.0, "friendly": 30.0, "neutral": 15.0, "enemy": 5.0, "debilitated": 0.0
    }
    saptavarga_bala = strength_vals.get(d1_str, 15.0) * 1.5
    
    # 4. Drekkana Bala
    # Drekkana = 10 degree decanate.
    deg = bundle.data["planets"].get(planet_key, {}).get("degree", 0.0)
    decanate = int(deg / 10.0)  # 0, 1, or 2
    drekkana_bala = 15.0 if decanate == 0 else 0.0
    
    total = uchcha_bala + ojha_bala + saptavarga_bala + drekkana_bala
    return {
        "uchcha_bala": round(uchcha_bala, 2),
        "ojha_bala": round(ojha_bala, 2),
        "saptavarga_bala": round(saptavarga_bala, 2),
        "drekkana_bala": round(drekkana_bala, 2),
        "total": round(total, 2)
    }

def calculate_dig_bala(planet_key: str, bundle: ChartBundle) -> float:
    """Calculate Dig Bala (Directional Strength) based on house cusp distance."""
    optimal = DIG_BALA_OPTIMAL_HOUSES.get(planet_key)
    if optimal is None:
        return 0.0
        
    house = bundle.planet_houses.get(planet_key, 1)
    # Whole sign house distance
    diff = abs(house - optimal) % 12
    distance = min(diff, 12 - diff)
    
    # Max is 60 points at optimal house, decreases by 10 points per house distance
    dig_bala = max(0.0, 60.0 - (distance * 10.0))
    return round(dig_bala, 2)

def calculate_kala_bala(planet_key: str, bundle: ChartBundle) -> dict[str, float]:
    """Calculate Kala Bala (Temporal Strength)."""
    # 1. Nathonnatha Bala
    # Daytime birth vs Nighttime birth. Sun is exalted in strength at noon, Moon at midnight.
    # Check LMT or ISO datetime
    local_iso = bundle.data["meta"].get("local_datetime", "")
    is_day = True
    if local_iso:
        # Simple hour check: 6:00 to 18:00 is Day
        try:
            hour = int(local_iso.split("T")[1].split(":")[0])
            if hour < 6 or hour >= 18:
                is_day = False
        except Exception:
            pass
            
    natha_bala = 0.0
    diurnal = {"sun", "jupiter", "venus"}
    nocturnal = {"moon", "mars", "saturn"}
    
    if is_day:
        if planet_key in diurnal:
            natha_bala = 60.0
        elif planet_key in nocturnal:
            natha_bala = 0.0
        else:
            natha_bala = 30.0  # Mercury
    else:
        if planet_key in nocturnal:
            natha_bala = 60.0
        elif planet_key in diurnal:
            natha_bala = 0.0
        else:
            natha_bala = 30.0
            
    # 2. Paksha Bala (lunar phase strength)
    tithi = bundle.data["core_identity"].get("tithi", "Shukla Saptami")
    is_shukla = "shukla" in tithi.lower() or "purnima" in tithi.lower()
    paksha_bala = 30.0
    if planet_key == "moon":
        paksha_bala = 60.0 if is_shukla else 10.0
    elif planet_key in {"jupiter", "venus"}:
        paksha_bala = 45.0 if is_shukla else 20.0
    elif planet_key in {"saturn", "mars"}:
        paksha_bala = 15.0 if not is_shukla else 30.0
        
    # 3. Tribhaga Bala
    tribhaga_bala = 15.0 if planet_key in {"jupiter", "sun"} else 5.0
    
    # 4. Lords (Year, Month, Day, Hora)
    lords_bala = 10.0
    
    total = natha_bala + paksha_bala + tribhaga_bala + lords_bala
    return {
        "natha_bala": round(natha_bala, 2),
        "paksha_bala": round(paksha_bala, 2),
        "tribhaga_bala": round(tribhaga_bala, 2),
        "lords_bala": round(lords_bala, 2),
        "total": round(total, 2)
    }

def calculate_cheshta_bala(planet_key: str, bundle: ChartBundle) -> float:
    """Calculate Cheshta Bala (Motional Strength)."""
    p_info = bundle.data["planets"].get(planet_key, {})
    retro = p_info.get("retro", False)
    speed = abs(p_info.get("speed", 1.0))
    
    # Retrograde planets get max Cheshta Bala (60 points)
    if retro:
        return 60.0
        
    # Fast moving vs average speed
    avg_speeds = {"sun": 1.0, "moon": 13.0, "mars": 0.5, "mercury": 1.2, "jupiter": 0.08, "venus": 1.2, "saturn": 0.03}
    avg = avg_speeds.get(planet_key, 1.0)
    ratio = speed / avg
    
    cheshta = min(60.0, max(10.0, ratio * 30.0))
    return round(cheshta, 2)

def compute_shadbala(bundle: ChartBundle) -> dict[str, dict[str, Any]]:
    """Compute the 6-fold Shadbala strength metrics for all BAV planets."""
    shadbala_output = {}
    for planet_key in BAV_PLANETS:
        sthana = calculate_sthana_bala(planet_key, bundle)
        dig = calculate_dig_bala(planet_key, bundle)
        kala = calculate_kala_bala(planet_key, bundle)
        cheshta = calculate_cheshta_bala(planet_key, bundle)
        
        # Sum elements (scaled to Shadbala Shashtiamsa standard)
        total_strength = sthana["total"] + dig + kala["total"] + cheshta
        
        # Determine verdict
        if total_strength >= 350:
            verdict = "Very Strong"
        elif total_strength >= 250:
            verdict = "Strong"
        elif total_strength >= 150:
            verdict = "Average"
        else:
            verdict = "Weak"
            
        shadbala_output[planet_key] = {
            "sthana_bala": sthana,
            "dig_bala": dig,
            "kala_bala": kala,
            "cheshta_bala": cheshta,
            "total_shashtiamsa": round(total_strength, 2),
            "verdict": verdict
        }
    return shadbala_output
