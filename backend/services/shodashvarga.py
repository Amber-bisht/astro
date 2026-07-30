from __future__ import annotations

from math import floor
from typing import Any
from backend.services.ephemeris import SIGNS, SIGN_LORDS, PLANET_ORDER, PLANET_LABELS, classify_planet_strength, degree_in_sign, sign_index_from_longitude, whole_sign_house

# Elemental grouping
SIGN_ELEMENTS = {
    "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air", "Cancer": "Water",
    "Leo": "Fire", "Virgo": "Earth", "Libra": "Air", "Scorpio": "Water",
    "Sagittarius": "Fire", "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water"
}

def sign_type(sign_name: str) -> str:
    """Return Movable (Chara), Fixed (Sthira), or Dual (Dvisvabhava)."""
    idx = SIGNS.index(sign_name)
    mod = idx % 3
    if mod == 0:
        return "Movable"
    elif mod == 1:
        return "Fixed"
    return "Dual"

# --- DIVISION ALGORITHMS ---

def compute_d2_sign(longitude: float) -> int:
    """D2 (Hora): 15 degree halves."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    is_odd = (sign_idx % 2) == 0  # Aries=0, Gemini=2, etc. (even indexes are odd signs in astrology)
    
    if is_odd:
        # First half goes to Leo (Sun), second half to Cancer (Moon)
        return 4 if deg < 15.0 else 3
    else:
        # First half goes to Cancer (Moon), second half to Leo (Sun)
        return 3 if deg < 15.0 else 4

def compute_d3_sign(longitude: float) -> int:
    """D3 (Drekkana): 10 degree decanates."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 10.0)  # 0, 1, 2
    
    # 1st part same sign, 2nd part 5th sign, 3rd part 9th sign
    return (sign_idx + (part * 4)) % 12

def compute_d4_sign(longitude: float) -> int:
    """D4 (Chaturthamsa): 7.5 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 7.5)  # 0, 1, 2, 3
    
    # Parts go to 1, 4, 7, 10 signs
    return (sign_idx + (part * 3)) % 12

def compute_d7_sign(longitude: float) -> int:
    """D7 (Saptamsa): 7 equal parts (4°17'08" each)."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / (30.0 / 7.0))  # 0-6
    is_odd = (sign_idx % 2) == 0
    
    if is_odd:
        return (sign_idx + part) % 12
    else:
        # Starts from 7th sign
        return (sign_idx + 6 + part) % 12

def compute_d9_sign(longitude: float) -> int:
    """D9 (Navamsa): 9 equal parts (3°20' each)."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / (30.0 / 9.0))  # 0-8
    elem = SIGN_ELEMENTS[SIGNS[sign_idx]]
    
    start_map = {"Fire": 0, "Earth": 9, "Air": 6, "Water": 3}
    start = start_map[elem]
    return (start + part) % 12

def compute_d10_sign(longitude: float) -> int:
    """D10 (Dasamsa): 10 equal parts (3° each)."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 3.0)  # 0-9
    is_odd = (sign_idx % 2) == 0
    
    if is_odd:
        return (sign_idx + part) % 12
    else:
        # Starts from 9th sign
        return (sign_idx + 8 + part) % 12

def compute_d12_sign(longitude: float) -> int:
    """D12 (Dwadashamsa): 2.5 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 2.5)  # 0-11
    
    # Starts from same sign
    return (sign_idx + part) % 12

def compute_d16_sign(longitude: float) -> int:
    """D16 (Shodashamsa): 1.875 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 1.875)  # 0-15
    stype = sign_type(SIGNS[sign_idx])
    
    # Movable starts from Aries (0), Fixed from Leo (4), Dual from Sag (8)
    start = 0 if stype == "Movable" else 4 if stype == "Fixed" else 8
    return (start + part) % 12

def compute_d20_sign(longitude: float) -> int:
    """D20 (Vimsamsa): 1.5 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 1.5)  # 0-19
    stype = sign_type(SIGNS[sign_idx])
    
    # Movable starts from Aries (0), Fixed from Sagittarius (8), Dual from Leo (4)
    start = 0 if stype == "Movable" else 8 if stype == "Fixed" else 4
    return (start + part) % 12

def compute_d24_sign(longitude: float) -> int:
    """D24 (Chaturvimsamsa): 1.25 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 1.25)  # 0-23
    is_odd = (sign_idx % 2) == 0
    
    # Odd signs start from Leo (4), Even signs from Cancer (3)
    start = 4 if is_odd else 3
    return (start + part) % 12

def compute_d27_sign(longitude: float) -> int:
    """D27 (Saptavimsamsa): 1.111... degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / (30.0 / 27.0))  # 0-26
    elem = SIGN_ELEMENTS[SIGNS[sign_idx]]
    
    # Fire starting from Aries (0), Earth from Cancer (3), Air from Libra (6), Water from Capricorn (9)
    start = 0 if elem == "Fire" else 3 if elem == "Earth" else 6 if elem == "Air" else 9
    return (start + part) % 12

def compute_d30_sign(longitude: float) -> int:
    """D30 (Trimsamsa): Uneven degrees mapped to planetary domains."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    is_odd = (sign_idx % 2) == 0
    
    # Trimsamsa doesn't use signs directly but planetary domains.
    # Map odd sign ranges: Mars (0-5, Aries=0), Saturn (5-10, Aquarius=10), Jupiter (10-18, Sag=8), Mercury (18-25, Gemini=2), Venus (25-30, Taurus=1)
    if is_odd:
        if deg < 5.0: return 0    # Aries (Mars)
        if deg < 10.0: return 10  # Aquarius (Saturn)
        if deg < 18.0: return 8   # Sagittarius (Jupiter)
        if deg < 25.0: return 2   # Gemini (Mercury)
        return 1                  # Taurus (Venus)
    else:
        # Even sign ranges: Venus (0-5, Taurus=1), Mercury (5-12, Gemini=2), Jupiter (12-20, Sag=8), Saturn (20-25, Aquarius=10), Mars (25-30, Aries=0)
        if deg < 5.0: return 1    # Taurus (Venus)
        if deg < 12.0: return 2   # Gemini (Mercury)
        if deg < 20.0: return 8   # Sagittarius (Jupiter)
        if deg < 25.0: return 10  # Aquarius (Saturn)
        return 0                  # Aries (Mars)

def compute_d40_sign(longitude: float) -> int:
    """D40 (Khavedamsa): 0.75 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 0.75)  # 0-39
    is_odd = (sign_idx % 2) == 0
    
    # Odd signs start from Aries (0), Even from Libra (6)
    start = 0 if is_odd else 6
    return (start + part) % 12

def compute_d45_sign(longitude: float) -> int:
    """D45 (Akshavedamsa): 0.666... degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / (30.0 / 45.0))  # 0-44
    stype = sign_type(SIGNS[sign_idx])
    
    # Movable starts Aries (0), Fixed starts Leo (4), Dual starts Sagittarius (8)
    start = 0 if stype == "Movable" else 4 if stype == "Fixed" else 8
    return (start + part) % 12

def compute_d60_sign(longitude: float) -> int:
    """D60 (Shashtiamsa): 0.5 degree parts."""
    sign_idx = sign_index_from_longitude(longitude)
    deg = degree_in_sign(longitude)
    part = int(deg / 0.5)  # 0-59
    
    # Starts from same sign
    return (sign_idx + part) % 12

# --- VAISESHIKAMSA CALCULATOR ---

VAISESHIKAMSA_NAMES = {
    2: "Parijata",
    3: "Uttama",
    4: "Gopura",
    5: "Simhasana",
    6: "Paravata",
    7: "Devaloka",
    8: "Brahmaloka",
    9: "Sakra",
    10: "Airavata"
}

def calculate_vaiseshikamsa_status(dignity_count: int) -> str:
    for count in sorted(VAISESHIKAMSA_NAMES.keys(), reverse=True):
        if dignity_count >= count:
            return VAISESHIKAMSA_NAMES[count]
    return "Ordinary"

def compute_shodashvarga(bundle: ChartBundle) -> dict[str, Any]:
    """Compute the 16 divisional charts (Shodashvarga) and Vaiseshikamsa status for all planets."""
    divisional_charts = {
        "D1": lambda l: sign_index_from_longitude(l),
        "D2": compute_d2_sign,
        "D3": compute_d3_sign,
        "D4": compute_d4_sign,
        "D7": compute_d7_sign,
        "D9": compute_d9_sign,
        "D10": compute_d10_sign,
        "D12": compute_d12_sign,
        "D16": compute_d16_sign,
        "D20": compute_d20_sign,
        "D24": compute_d24_sign,
        "D27": compute_d27_sign,
        "D30": compute_d30_sign,
        "D40": compute_d40_sign,
        "D45": compute_d45_sign,
        "D60": compute_d60_sign
    }
    
    shodashvarga_data: dict[str, dict[str, str]] = {v: {} for v in divisional_charts}
    vaiseshikamsa_dignities: dict[str, int] = {p: 0 for p in PLANET_ORDER}
    
    for p_key in PLANET_ORDER:
        longitude = bundle.planet_longitudes[p_key]
        label = PLANET_LABELS[p_key]
        
        for v_name, func in divisional_charts.items():
            sign_idx = func(longitude)
            sign_name = SIGNS[sign_idx]
            shodashvarga_data[v_name][p_key] = sign_name
            
            # Evaluate dignity
            strength = classify_planet_strength(label, sign_name)
            if strength in {"exalted", "own", "friendly"}:
                # Count major 10 vargas for Vaiseshikamsa (D1, D2, D3, D7, D9, D10, D12, D16, D30, D60)
                if v_name in {"D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16", "D30", "D60"}:
                    vaiseshikamsa_dignities[p_key] += 1
                    
    vaiseshikamsa_status = {
        p: {
            "dignity_count": vaiseshikamsa_dignities[p],
            "status": calculate_vaiseshikamsa_status(vaiseshikamsa_dignities[p])
        }
        for p in PLANET_ORDER
    }
    
    return {
        "charts": shodashvarga_data,
        "vaiseshikamsa": vaiseshikamsa_status
    }
