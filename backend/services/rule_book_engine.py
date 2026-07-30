from __future__ import annotations

from typing import Any
from backend.services.ephemeris import SIGN_LORDS, SIGNS, NAKSHATRAS

# Dignity/Friendship mappings for Phaladeepika
SIGN_LORDS_LOWER = {k: v.lower() for k, v in SIGN_LORDS.items()}

LIVELIHOOD_DESCRIPTIONS = {
    "Sun": (
        "Livelihood will be derived through the Sun's qualities: dealing with state/government authority, "
        "administration, medicine, pharmaceutical formulations, gold/copper metalwork, forest/mountain lands, "
        "or prestigious public counseling under the patronage of respectable persons (Phaladeepika Ch. 5, Verse 2)."
    ),
    "Moon": (
        "Livelihood will be derived through the Moon's qualities: agricultural products, milk and dairy products, "
        "shells, pearls, fish, marine work, women's apparel/cosmetics, water-related activities, trade of soft materials, "
        "music, arts, or counseling (Phaladeepika Ch. 5, Verse 3)."
    ),
    "Mars": (
        "Livelihood will be derived through Mars's qualities: metallurgy, gold work, weapons, engineering, fire, "
        "policing, military service, surgery, physical labor, theft/fraud/cunningness, chemistry, or dealing with "
        "land and real estate (Phaladeepika Ch. 5, Verse 4)."
    ),
    "Mercury": (
        "Livelihood will be derived through Mercury's qualities: writing, literature, accounting, mathematics, "
        "printing, publishing, astrology, poetry, grammar, painting, craftwork, teaching, communication, "
        "and business negotiation (Phaladeepika Ch. 5, Verse 5)."
    ),
    "Jupiter": (
        "Livelihood will be derived through Jupiter's qualities: teaching, spiritual initiation, priesthood, "
        "consulting, judiciary/law, religious duties, charitable institutions, research, advisory roles to leaders, "
        "and intellectual pursuits (Phaladeepika Ch. 5, Verse 6)."
    ),
    "Venus": (
        "Livelihood will be derived through Venus's qualities: trade of gems, jewelry, silver, silk and fine clothing, "
        "perfumes, flowers, cattle, dairy, arts, cinema, drama, poetry, and luxury items or counseling (Phaladeepika Ch. 5, Verse 7)."
    ),
    "Saturn": (
        "Livelihood will be derived through Saturn's qualities: labor, bricklaying, pottery, dealing with wood/timber, "
        "stones, iron, petroleum, execution, masonry, service under others, low-level trades, or working in "
        "remote lands/forests (Phaladeepika Ch. 5, Verse 8)."
    )
}

NAKSHATRA_CLASSES = {
    # Dhruva (Fixed)
    "Rohini": ("Dhruva (Fixed)", "Represents stability, long-term focus, and permanence. Excellent for career paths in agriculture, construction, or administration."),
    "Uttara Phalguni": ("Dhruva (Fixed)", "Represents stability, long-term focus, and permanence. Excellent for career paths in agriculture, construction, or administration."),
    "Uttara Ashadha": ("Dhruva (Fixed)", "Represents stability, long-term focus, and permanence. Excellent for career paths in agriculture, construction, or administration."),
    "Uttara Bhadrapada": ("Dhruva (Fixed)", "Represents stability, long-term focus, and permanence. Excellent for career paths in agriculture, construction, or administration."),
    # Mridu (Soft)
    "Mrigashira": ("Mridu (Soft/Sweet)", "Represents friendship, artistic talent, and pleasant nature. Excellent for creative roles, arts, partnership business, and public relations."),
    "Chitra": ("Mridu (Soft/Sweet)", "Represents friendship, artistic talent, and pleasant nature. Excellent for creative roles, arts, partnership business, and public relations."),
    "Anuradha": ("Mridu (Soft/Sweet)", "Represents friendship, artistic talent, and pleasant nature. Excellent for creative roles, arts, partnership business, and public relations."),
    "Revati": ("Mridu (Soft/Sweet)", "Represents friendship, artistic talent, and pleasant nature. Excellent for creative roles, arts, partnership business, and public relations."),
    # Kshipra (Swift)
    "Ashwini": ("Kshipra (Swift/Light)", "Represents speed, quick learning, and dynamism. Excellent for technology, medicine, sports, and fast-paced environments."),
    "Pushya": ("Kshipra (Swift/Light)", "Represents speed, quick learning, and dynamism. Excellent for technology, medicine, sports, and fast-paced environments."),
    "Hasta": ("Kshipra (Swift/Light)", "Represents speed, quick learning, and dynamism. Excellent for technology, medicine, sports, and fast-paced environments."),
    # Ugra (Fierce)
    "Bharani": ("Ugra (Fierce/Severe)", "Represents power, force, and directness. Gives a highly ambitious and competitive drive. Excellent for positions of leadership, security, or legal dispute resolution."),
    "Magha": ("Ugra (Fierce/Severe)", "Represents power, force, and directness. Gives a highly ambitious and competitive drive. Excellent for positions of leadership, security, or legal dispute resolution."),
    "Purva Phalguni": ("Ugra (Fierce/Severe)", "Represents power, force, and directness. Gives a highly ambitious and competitive drive. Excellent for positions of leadership, security, or legal dispute resolution."),
    "Purva Ashadha": ("Ugra (Fierce/Severe)", "Represents power, force, and directness. Gives a highly ambitious and competitive drive. Excellent for positions of leadership, security, or legal dispute resolution."),
    "Purva Bhadrapada": ("Ugra (Fierce/Severe)", "Represents power, force, and directness. Gives a highly ambitious and competitive drive. Excellent for positions of leadership, security, or legal dispute resolution."),
    # Tikshna (Sharp)
    "Ardra": ("Tikshna (Sharp/Dreadful)", "Represents analytical power, research capability, and sharpness. Gives a highly critical and investigative intellect. Excellent for research, science, surgery, and auditing."),
    "Ashlesha": ("Tikshna (Sharp/Dreadful)", "Represents analytical power, research capability, and sharpness. Gives a highly critical and investigative intellect. Excellent for research, science, surgery, and auditing."),
    "Jyeshtha": ("Tikshna (Sharp/Dreadful)", "Represents analytical power, research capability, and sharpness. Gives a highly critical and investigative intellect. Excellent for research, science, surgery, and auditing."),
    "Mula": ("Tikshna (Sharp/Dreadful)", "Represents analytical power, research capability, and sharpness. Gives a highly critical and investigative intellect. Excellent for research, science, surgery, and auditing."),
    # Chara (Movable)
    "Punarvasu": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    "Swati": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    "Vishakha": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    "Shravana": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    "Dhanishta": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    "Shatabhisha": ("Chara (Movable)", "Represents travel, motion, and change. Excellent for careers in marketing, trade, aviation, tourism, and consulting."),
    # Misra (Mixed)
    "Krittika": ("Misra (Mixed/Sharp-Soft)", "Represents dual talents. Good for creative design, culinary arts, or specialized crafts.")
}

KARANA_DEITIES = {
    "Bava": ("Movable", "Lord Indra", "Born under Bava Karana. This movable and active Karana ruled by Lord Indra grants dynamism, adaptability, and successful execution of projects."),
    "Balava": ("Movable", "Lord Brahma", "Born under Balava Karana. This movable and active Karana ruled by Lord Brahma grants high intelligence, creative capabilities, and educational success."),
    "Kaulava": ("Movable", "Lord Mitra", "Born under Kaulava Karana. This movable and active Karana ruled by Lord Mitra (Sun) grants strong friendships, social popularity, and diplomatic skills."),
    "Taitila": ("Movable", "Lord Aryaman", "Born under Taitila Karana. This movable and active Karana ruled by Lord Aryaman grants nobility, courage, and leadership potential."),
    "Gara": ("Movable", "Lord Bhumi", "Born under Gara Karana. This movable and active Karana ruled by Lord Bhumi (Earth) grants stability, patience, and excellent agricultural/grounded skills."),
    "Vanija": ("Movable", "Lord Manibhadra", "Born under Vanija Karana. This movable and active Karana ruled by Lord Manibhadra (Kubera) grants business intellect, trading success, and wealth accumulation."),
    "Vishti": ("Movable", "Lord Yama", "Born under Vishti (Bhadra) Karana. This is a severe declination alignment associated with Lord Yama. It indicates that the native may face initial delays or public friction in their endeavors, and they must avoid starting auspicious works during Bhadra. Spiritual remedies include reciting Bhadra Mantras or worshipping Lord Shiva."),
    "Shakuni": ("Fixed", "Lord Garuda", "Born under Shakuni Karana. This fixed Karana ruled by Lord Garuda grants keen eyesight/insight, research skills, and capability to cure or heal."),
    "Chatushpada": ("Fixed", "Lord Vrishabha", "Born under Chatushpada Karana. This fixed Karana ruled by Lord Vrishabha (Shiva's Bull) grants stable foundations, animal welfare skills, and professional dedication."),
    "Naga": ("Fixed", "Lord Ananta", "Born under Naga Karana. This fixed Karana ruled by Lord Ananta (Serpents) grants deep mystical knowledge, hidden strength, and strategic defense skills."),
    "Kimstughna": ("Fixed", "Lord Vayu", "Born under Kimstughna Karana. This fixed Karana ruled by Lord Vayu (Wind) grants rapid communication skills, versatile talents, and joyful character.")
}


def translate_seshadri_iyer_d9(json_payload: dict[str, Any]) -> dict[str, Any]:
    """Seshadri Iyer's Shodashvarga Rules applied to the D9 Navamsa Chart."""
    d9_data = json_payload.get("navamsa")
    if not d9_data or "ascendant" not in d9_data:
        return {}
    
    d9_planets = d9_data.get("planets", {})
    d1_strengths = json_payload.get("planet_strength", {})
    d1_planets = json_payload.get("planets", {})
    
    d9_lagna = d9_data["ascendant"]["sign"]
    d9_lagna_lord = SIGN_LORDS.get(d9_lagna, "Sun")
    d9_lagna_lord_key = d9_lagna_lord.lower()
    
    # Get D9 Lagna Lord house
    d9_lagna_lord_house = d9_planets.get(d9_lagna_lord_key, {}).get("navamsa_house", 1)
    
    dusthanas = {3, 6, 8, 12}
    rulings = {}
    
    for planet_key, p_info in d9_planets.items():
        house = p_info["navamsa_house"]
        p_label = planet_key.capitalize()
        d1_sign = d1_planets.get(planet_key, {}).get("sign", "Unknown")
        d1_str = d1_strengths.get(planet_key, "neutral")
        d9_str = p_info.get("strength", "neutral")
        
        # Check for Dusthana placements
        if house in dusthanas:
            # Check for classical Seshadri exceptions
            if planet_key == "mars" and house == 6:
                ruling = "Mars in 6th Navamsa is a powerful exception (Seshadri Iyer Rule 1a). It casts its full aspect on the D9 Lagna, protecting and strengthening marital dynamics."
            elif planet_key == "moon" and d1_str == "exalted":
                ruling = (f"CRITICAL WARNING (Seshadri Iyer Rule 2 & 14): {p_label} is EXALTED in D1 ({d1_sign}) "
                          f"but falls into the {house}th house (Dusthana) in D9 Navamsa. Under Shodashvarga rules, "
                          f"this severely damages its auspiciousness. Its high status in D1 is a 'dreamy effect' and will "
                          f"result in unexpected setbacks, hidden blockages, or emotional distance during its dasha periods.")
            else:
                ruling = f"Seshadri Iyer Warning: {p_label} is in the {house}th house (Dusthana) of D9 Navamsa. It will cause delays, obstacles, and muted results for its D9 marriage and relationship portfolios."
        else:
            # Favorable placements & Neechabhanga checking
            if d1_str == "debilitated" and d9_str == "exalted":
                ruling = (f"ULTRA RAJA YOGA (Seshadri Iyer Rule 5 - Neechabhanga): {p_label} is debilitated in D1 ({d1_sign}) "
                          f"but is EXALTED in the D9 {house}th house ({p_info['sign']}). This denotes massive initial struggles, "
                          f"humiliation, and delays, followed by a monumental rise, extraordinary status, and prosperity in its portfolio.")
            elif planet_key == "venus" and house == 10:
                ruling = f"Superb Placement: {p_label} is exalted in the 10th house (Kendra) of D9, representing public dignity and excellent status through marital alliance."
            else:
                ruling = f"Favorable Placement: {p_label} is in the {house}th house (Non-Dusthana) of D9 Navamsa with '{d9_str}' dignity."
                
        # Seshadri Rule 3: Conjunction with D9 Lagna Lord
        if planet_key != d9_lagna_lord_key and house == d9_lagna_lord_house:
            ruling += f" Also, {p_label} is conjunct the D9 Lagna Lord ({d9_lagna_lord}) in House {house} (Seshadri Iyer Rule 3), which significantly boosts its expression and provides protective guidance for its portfolios."
            
        # Seshadri Rule 4: Placed in D9 1st House
        if house == 1:
            ruling += f" Placed in the 1st house (Lagna Kendra) of D9 Navamsa (Seshadri Iyer Rule 4), granting it direct prominence and shaping the native's core approach to Navamsa activities."

        rulings[planet_key] = {
            "d9_house": house,
            "d9_sign": p_info["sign"],
            "translation": ruling
        }
    return rulings

def translate_phaladeepika_livelihood(json_payload: dict[str, Any]) -> dict[str, Any]:
    """Phaladeepika Chapter 5 Career & Livelihood Calculation."""
    try:
        d1_strengths = json_payload.get("planet_strength", {})
        planets_data = json_payload.get("planets", {})
        
        # Lagna Lord Details
        lagna_sign = json_payload["core_identity"]["lagna"]
        lagna_lord = SIGN_LORDS[lagna_sign]
        lagna_lord_key = lagna_lord.lower()
        lagna_lord_strength = d1_strengths.get(lagna_lord_key, "neutral")
        
        strength_rank = {"exalted": 4, "own": 3, "friendly": 2, "neutral": 1, "enemy": 0, "debilitated": -2}
        
        # Calculate weighted scores
        def score_point(key, strength):
            base = strength_rank.get(strength, 1)
            p_house = planets_data.get(key, {}).get("house", 1) if key in planets_data else 1
            if p_house in {1, 4, 7, 10}:
                base += 1.5
            elif p_house in {6, 8, 12}:
                base -= 1.5
            return base
            
        sun_score = score_point("sun", d1_strengths.get("sun", "neutral"))
        moon_score = score_point("moon", d1_strengths.get("moon", "neutral"))
        lagna_lord_score = score_point(lagna_lord_key, lagna_lord_strength)
        
        # Choose the strongest point
        if moon_score > sun_score and moon_score > lagna_lord_score:
            strongest = "moon"
            ref_sign = json_payload["core_identity"]["moon_sign"]
        elif sun_score > moon_score and sun_score > lagna_lord_score:
            strongest = "sun"
            ref_sign = json_payload["core_identity"]["sun_sign"]
        else:
            strongest = "lagna"
            ref_sign = lagna_sign
            
        # 2. 10th sign from reference
        ref_idx = SIGNS.index(ref_sign)
        tenth_idx = (ref_idx + 9) % 12
        tenth_sign = SIGNS[tenth_idx]
        
        # 3. 10th Lord
        tenth_lord = SIGN_LORDS[tenth_sign]
        tenth_lord_key = tenth_lord.lower()
        
        # 4. Navamsa sign occupied by 10th Lord
        d9_planets = json_payload.get("navamsa", {}).get("planets", {})
        if tenth_lord_key not in d9_planets:
            tenth_lord_key = "sun"
            
        navamsa_occupied_by_lord = d9_planets[tenth_lord_key]["sign"]
        
        # 5. Navamsa Lord
        navamsa_lord = SIGN_LORDS[navamsa_occupied_by_lord]
        
        # 6. Description
        shloka_text = LIVELIHOOD_DESCRIPTIONS.get(navamsa_lord, LIVELIHOOD_DESCRIPTIONS["Sun"])
        
        return {
            "strongest_reference": strongest,
            "tenth_sign_from_ref": tenth_sign,
            "tenth_lord_from_ref": tenth_lord,
            "lord_navamsa_sign": navamsa_occupied_by_lord,
            "ultimate_livelihood_planet": navamsa_lord,
            "classical_authority": "Phaladeepika Ch. 5, Verse 1-8",
            "scriptural_translation": shloka_text,
            "debug_scores": {
                "sun": sun_score,
                "moon": moon_score,
                "lagna_lord": lagna_lord_score
            }
        }
    except Exception as e:
        return {
            "strongest_reference": "lagna",
            "tenth_sign_from_ref": "Unknown",
            "tenth_lord_from_ref": "Sun",
            "lord_navamsa_sign": "Unknown",
            "ultimate_livelihood_planet": "Sun",
            "classical_authority": "Phaladeepika Ch. 5, Verse 1-8",
            "scriptural_translation": LIVELIHOOD_DESCRIPTIONS["Sun"],
            "error": str(e)
        }

def translate_birth_panchanga(json_payload: dict[str, Any]) -> dict[str, Any]:
    """Muhurta Chintamani Chapter 1 & Phaladeepika Ch. 4 Birth Panchanga Engine."""
    core = json_payload.get("core_identity", {})
    tithi = core.get("tithi", "Unknown")
    yoga = core.get("yoga", "Unknown")
    karana = core.get("karana", "Unknown")
    nakshatra = core.get("nakshatra", "Unknown")
    
    panchanga_ruling: dict[str, Any] = {}
    
    # 1. Yoga Translation
    malefic_yogas = {
        "Vishkambha": "May bring obstacles in early life, requiring patience and discipline.",
        "Atiganda": "Highly emotional, can cause sudden changes or obstacles in relationships.",
        "Shula": "Sharp-tongued, analytical, can face financial or health conflicts.",
        "Ganda": "Sudden blockages or accidents, but grants intense resilience.",
        "Vyaghata": "Prone to sudden aggressive bursts, but makes an excellent competitor.",
        "Vajra": "Hard, unyielding nature; may face physical strain or career battles.",
        "Vyatipata": "Vyatipata is a highly intense 'Mahapaata' declination alignment. It represents sudden emotional sensitivity, mental confusion, and early life blockages, but also makes the native highly intuitive and spiritually gifted.",
        "Parigha": "Feels blocked or hemmed in initially, but gains immense power in later life.",
        "Vaidhriti": "Vaidhriti is a highly intense 'Mahapaata' declination alignment. It represents erratic fortunes, deep spiritual capability, but initial struggles in family/home life."
    }
    
    if yoga in malefic_yogas:
        yoga_interpretation = f"Born under {yoga} Yoga. {malefic_yogas[yoga]}"
        remedy = "Worship Lord Shiva, recite Purusha Sukta, and observe fasts/give alms on birth tithis to neutralize the declination alignment."
        yoga_fav = False
    else:
        yoga_interpretation = f"Born under the highly auspicious {yoga} Yoga, which grants smooth accomplishments, noble character, and positive relationships."
        remedy = "Maintain righteousness (Dharma) and perform acts of charity to sustain the positive yoga effects."
        yoga_fav = True
        
    panchanga_ruling["yoga_ruling"] = {
        "name": yoga,
        "source": "Muhurta Chintamani Ch. 1, Verse 8 & Ch. 11",
        "is_favorable": yoga_fav,
        "interpretation": yoga_interpretation,
        "remedial_shastra": remedy
    }
    
    # 2. Tithi Translation
    if tithi != "Unknown":
        if tithi == "Purnima":
            num = 15
            paksha = "Shukla"
        elif tithi == "Amavasya":
            num = 15
            paksha = "Krishna"
        else:
            parts = tithi.split(" ")
            if len(parts) >= 2:
                paksha = parts[0]
                name_map = {
                    "Pratipada": 1, "Dwitiya": 2, "Tritiya": 3, "Chaturthi": 4, "Panchami": 5,
                    "Shashthi": 6, "Saptami": 7, "Ashtami": 8, "Navami": 9, "Dashami": 10,
                    "Ekadashi": 11, "Dwadashi": 12, "Trayodashi": 13, "Chaturdashi": 14
                }
                num = name_map.get(parts[1], 1)
            else:
                paksha = "Shukla"
                num = 1
                
        group_idx = (num - 1) % 5
        groups = ["Nanda", "Bhadra", "Jaya", "Rikta", "Poorna"]
        classification = groups[group_idx]
        
        deities = {
            "Nanda": "Lord Agni (The Fire God)",
            "Bhadra": "Lord Brahma (The Creator)",
            "Jaya": "Lord Ganesha / Shiva (The Auspicious)",
            "Rikta": "Lord Yama / Goddess Kali (The Transformative)",
            "Poorna": "Lord Shiva / Moon / Vishwadevas (The Completer)"
        }
        deity = deities[classification]
        
        if classification == "Rikta":
            tithi_interpretation = (
                f"Born on a Rikta (Empty) Tithi ({tithi}), which is historically challenging for starting new material projects, "
                f"but grants the native a sharp, combative, and highly spiritual intellect capable of cutting through obstacles."
            )
        else:
            tithi_interpretation = (
                f"Born on a {classification} (Auspicious/Fruitful) Tithi ({tithi}) governed by {deity}. "
                f"This bestows excellent creative energy, social success, and fulfillment of desires."
            )
            
        # Paksha Bala assessment
        if (paksha == "Shukla" and num >= 7) or (paksha == "Krishna" and num <= 10):
            tithi_interpretation += (
                f" Born under high Paksha Bala (bright phase of Moon). According to Phaladeepika Ch. 4, "
                f"this grants immense psychological strength, mental clarity, and public reputation, "
                f"acting as a natural shield against any inauspicious yogas."
            )
        else:
            tithi_interpretation += (
                f" Born under low Paksha Bala (waning/dark phase of Moon). According to Phaladeepika Ch. 4, "
                f"the native is advised to practice mindfulness and meditation to build emotional resilience and "
                f"gain deep intuitive power."
            )
            
        panchanga_ruling["tithi_ruling"] = {
            "name": tithi,
            "source": "Muhurta Chintamani Ch. 1, Verse 3 & Phaladeepika Ch. 4",
            "governing_deity": deity,
            "classification": classification,
            "interpretation": tithi_interpretation
        }
        
    # 3. Karana Translation
    if karana != "Unknown" and karana in KARANA_DEITIES:
        k_type, k_deity, k_desc = KARANA_DEITIES[karana]
        panchanga_ruling["karana_ruling"] = {
            "name": karana,
            "source": "Muhurta Chintamani Ch. 1",
            "classification": k_type,
            "governing_deity": k_deity,
            "interpretation": k_desc
        }
        
    # 4. Nakshatra Translation
    if nakshatra != "Unknown":
        nak_name = nakshatra.split(" ")[0]  # clean Abhijit or extra words
        matched = False
        for k, v in NAKSHATRA_CLASSES.items():
            if k in nak_name:
                panchanga_ruling["nakshatra_ruling"] = {
                    "name": nakshatra,
                    "source": "Muhurta Chintamani Ch. 2",
                    "classification": v[0],
                    "interpretation": v[1]
                }
                matched = True
                break
        if not matched:
            panchanga_ruling["nakshatra_ruling"] = {
                "name": nakshatra,
                "source": "Muhurta Chintamani Ch. 2",
                "classification": "General",
                "interpretation": "A stable lunar alignment directing the native's core instincts and focus."
            }
        
    return panchanga_ruling
