from __future__ import annotations

from typing import Any

# Ordering of 28 Nakshatras including Abhijit
NAKSHATRAS_28 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Abhijit", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# 1-indexed pairing for Saptashalaka (Ashwini is 1, Revati is 28)
SAPTASHALAKA_PAIRS = {
    1: 26, 2: 25, 3: 24, 4: 23, 5: 22, 6: 21, 7: 20, 8: 19, 9: 18, 10: 17, 11: 16, 12: 15, 13: 14,
    26: 1, 25: 2, 24: 3, 23: 4, 22: 5, 21: 6, 20: 7, 19: 8, 18: 9, 17: 10, 16: 11, 15: 12, 14: 13,
    28: 27, 27: 28
}

# Coordinate mapping for Sarvatobhadra 9x9 Grid (row, col) from 0 to 8
SARVATOBHADRA_GRID = {
    "Krittika": (0, 1), "Rohini": (0, 2), "Mrigashira": (0, 3), "Ardra": (0, 4), "Punarvasu": (0, 5), "Pushya": (0, 6), "Ashlesha": (0, 7),
    "Magha": (1, 8), "Purva Phalguni": (2, 8), "Uttara Phalguni": (3, 8), "Hasta": (4, 8), "Chitra": (5, 8), "Swati": (6, 8), "Vishakha": (7, 8),
    "Anuradha": (8, 7), "Jyeshtha": (8, 6), "Mula": (8, 5), "Purva Ashadha": (8, 4), "Uttara Ashadha": (8, 3), "Abhijit": (8, 2), "Shravana": (8, 1),
    "Dhanishta": (7, 0), "Shatabhisha": (6, 0), "Purva Bhadrapada": (5, 0), "Uttara Bhadrapada": (4, 0), "Revati": (3, 0), "Ashwini": (2, 0), "Bharani": (1, 0)
}

MALEFIC_PLANETS = {"sun", "mars", "saturn", "rahu", "ketu"}

def get_nakshatra_28_index(nak_name: str) -> int:
    """Helper to find the index (0-27) of a nakshatra, matching substring."""
    clean_name = nak_name.split(" ")[0].lower()
    for idx, name in enumerate(NAKSHATRAS_28):
        if name.lower() in clean_name or clean_name in name.lower():
            return idx
    return 0

def check_saptashalaka_vedha(natal_nak: str, transits: dict[str, Any]) -> list[dict[str, Any]]:
    """Verify if any transiting malefic is casting Saptashalaka Vedha on native's Janma Nakshatra."""
    natal_idx_1 = get_nakshatra_28_index(natal_nak) + 1  # 1-indexed
    paired_idx_1 = SAPTASHALAKA_PAIRS.get(natal_idx_1)
    if not paired_idx_1:
        return []
    
    paired_name = NAKSHATRAS_28[paired_idx_1 - 1]
    active_vedhas = []
    
    for p_key, info in transits.items():
        if p_key in MALEFIC_PLANETS:
            t_nak = info.get("nakshatra", "")
            t_idx_1 = get_nakshatra_28_index(t_nak) + 1
            if t_idx_1 == paired_idx_1:
                active_vedhas.append({
                    "planet": p_key.capitalize(),
                    "transit_nakshatra": t_nak,
                    "target_nakshatra": paired_name,
                    "type": "Saptashalaka Vedha",
                    "description": f"Transiting malefic {p_key.capitalize()} in {t_nak} casts a direct Saptashalaka Vedha on your Janma Nakshatra ({natal_nak})."
                })
    return active_vedhas

def check_sarvatobhadra_vedha(natal_nak: str, transits: dict[str, Any]) -> list[dict[str, Any]]:
    """Calculate Sarvatobhadra Vedhas (Puro, Vama, Prishta) on native's Janma Nakshatra."""
    natal_clean = ""
    natal_nak_lower = natal_nak.split(" ")[0].lower()
    for name in SARVATOBHADRA_GRID:
        if name.lower() in natal_nak_lower or natal_nak_lower in name.lower():
            natal_clean = name
            break
            
    if not natal_clean:
        return []
        
    r_n, c_n = SARVATOBHADRA_GRID[natal_clean]
    active_vedhas = []
    
    for p_key, info in transits.items():
        t_nak = info.get("nakshatra", "")
        t_clean = ""
        t_nak_lower = t_nak.split(" ")[0].lower()
        for name in SARVATOBHADRA_GRID:
            if name.lower() in t_nak_lower or t_nak_lower in name.lower():
                t_clean = name
                break
                
        if not t_clean or t_clean == natal_clean:
            continue
            
        r_t, c_t = SARVATOBHADRA_GRID[t_clean]
        
        # Check alignment lines
        is_puro = (r_t == r_n) or (c_t == c_n)
        is_diagonal = abs(r_t - r_n) == abs(c_t - c_n)
        
        if is_puro or is_diagonal:
            # Determine Vedha Type based on speed and retro
            speed = info.get("speed", 1.0)
            retro = info.get("retro", False)
            
            # Simple heuristic matching the Chakra rules:
            if retro:
                v_type = "Vama Vedha (Left/Diagonal)"
            elif speed > 1.2:  # fast-moving
                v_type = "Puro Vedha (Front/Straight)"
            elif speed < 0.2:  # slow-moving/stationary
                v_type = "Prishta Vedha (Rear/Diagonal)"
            else:
                v_type = "Standard Vedha"
                
            active_vedhas.append({
                "planet": p_key.capitalize(),
                "transit_nakshatra": t_nak,
                "target_nakshatra": natal_clean,
                "type": v_type,
                "description": f"Transiting {p_key.capitalize()} in {t_nak} casts a {v_type} on your Janma Nakshatra ({natal_nak})."
            })
            
    return active_vedhas
