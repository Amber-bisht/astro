from __future__ import annotations

from math import floor
from typing import Any

# Complete 60 Chandra Kriya descriptions
CHANDRA_KRIYAS = {
    1: "Loss of position/status", 2: "Afflicted with grief", 3: "Wicked intentions", 4: "Loss of wealth", 5: "Prone to disputes",
    6: "Fear of enemies", 7: "Doubtful mind", 8: "Anger/rage", 9: "Vain efforts", 10: "Happiness through study",
    11: "Spiritual initiation", 12: "Perform holy deeds", 13: "Purity of mind", 14: "Dignity", 15: "Sensual pleasure",
    16: "Acquire wealth", 17: "Fame and recognition", 18: "Kingly honors", 19: "Wealth through business", 20: "Courage/valor",
    21: "Victory over foes", 22: "Inquisitiveness", 23: "Sensual indulgence", 24: "Sorrow/grief", 25: "Anguish",
    26: "Purity of thought", 27: "Religious deeds", 28: "Highly religious", 29: "Wealthy", 30: "Fame",
    31: "Loss of memory", 32: "Anger", 33: "Sorrow", 34: "Detachment", 35: "Unstable mind",
    36: "Restlessness", 37: "Creative tension", 38: "Happiness through children", 39: "Pleasant speech", 40: "Intellectual success",
    41: "Joy and prosperity", 42: "Kingly status", 43: "Administrative power", 44: "Victory", 45: "Command over others",
    46: "Kingly status", 47: "High honor", 48: "Leadership", 49: "Wealth", 50: "Kingly status",
    51: "Spiritual peace", 52: "Service to humanity", 53: "Self-realization", 54: "Contentment", 55: "Renunciation",
    56: "Cosmic union", 57: "Absolute wisdom", 58: "Deep meditation", 59: "Devotion", 60: "Auspicious end"
}

# Complete 12 Chandra Avastha descriptions
CHANDRA_AVASTHAS = {
    1: "Physical ailments/headaches", 2: "Fever and restlessness", 3: "Fear and insecurity", 4: "Happiness and peace",
    5: "Acquiring wisdom/study", 6: "Wealth and prosperity", 7: "Dignity and honor", 8: "Command and authority",
    9: "Victory and success", 10: "Joy and celebrations", 11: "Spiritual peace", 12: "Renunciation and high bliss"
}

# Complete 36 Chandra Vela descriptions
CHANDRA_VELAS = {
    1: "Headache/Physical pain", 2: "Restlessness", 3: "Sorrow", 4: "Anger", 5: "Dispute",
    6: "Fear", 7: "Wandering", 8: "Loss of wealth", 9: "Vain efforts", 10: "Study/Learning",
    11: "Religious initiation", 12: "Holy deeds", 13: "Purity of mind", 14: "Joy", 15: "Pleasure",
    16: "Acquire wealth", 17: "Fame", 18: "Kingly honors", 19: "Business success", 20: "Courage",
    21: "Victory", 22: "Inquisitiveness", 23: "Indulgence", 24: "Sorrow", 25: "Anguish",
    26: "Purity", 27: "Devotion", 28: "Highly religious", 29: "Wealthy", 30: "Fame",
    31: "Loss of memory", 32: "Anger", 33: "Sorrow", 34: "Detachment", 35: "Unstable", 36: "Deep Sleep / Bliss"
}

def compute_chandra_states(moon_longitude: float) -> dict[str, Any]:
    """Calculate Chandra Kriya, Avastha, and Vela based on the Moon's progress in its Nakshatra."""
    nak_span = 360.0 / 27.0  # 13°20' = 13.3333... degrees
    nak_idx = int(moon_longitude / nak_span)
    progress_deg = moon_longitude - (nak_idx * nak_span)
    progress_minutes = progress_deg * 60.0
    progress_minutes = min(800.0, max(0.0, progress_minutes))
    
    # 1. Chandra Kriya (60 divisions of 800 minutes = 13.333 minutes each)
    kriya_idx = int(floor(progress_minutes / (800.0 / 60.0))) + 1
    kriya_idx = min(60, max(1, kriya_idx))
    kriya_desc = CHANDRA_KRIYAS[kriya_idx]
    
    # 2. Chandra Avastha (12 divisions of 800 minutes = 66.666 minutes each)
    avastha_idx = int(floor(progress_minutes / (800.0 / 12.0))) + 1
    avastha_idx = min(12, max(1, avastha_idx))
    avastha_desc = CHANDRA_AVASTHAS[avastha_idx]
    
    # 3. Chandra Vela (36 divisions of 800 minutes = 22.222 minutes each)
    vela_idx = int(floor(progress_minutes / (800.0 / 36.0))) + 1
    vela_idx = min(36, max(1, vela_idx))
    vela_desc = CHANDRA_VELAS[vela_idx]
    
    return {
        "kriya": {
            "index": kriya_idx,
            "description": kriya_desc
        },
        "avastha": {
            "index": avastha_idx,
            "description": avastha_desc
        },
        "vela": {
            "index": vela_idx,
            "description": vela_desc
        }
    }
