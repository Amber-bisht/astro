# 🕉️ Kundali Compatibility Engine

A **Vedic astrology marriage compatibility engine** that generates astronomically accurate birth charts and AI-ready structured data for two individuals. Built with Swiss Ephemeris for precision and designed so AI (ChatGPT, etc.) can provide deep astrological analysis from the output.

## ✨ Features

### Core Astrology Engine
- **Lahiri Ayanamsa** + **Whole Sign** house system (standard Vedic setup)
- Sidereal planetary positions via [Swiss Ephemeris](https://www.astro.com/swisseph/)
- 9 planets (Sun through Ketu) with sign, house, degree, nakshatra, pada, retrograde flag, and speed
- 12-house chart with lords and occupants
- Planet dignity classification (exalted / own / friendly / neutral / enemy / debilitated)

### Compatibility Analysis
- **Ashtakoota Guna Milan** (8-point matching system, scored out of 36)
  - Varna, Vasya, Tara, Yoni, Maitri, Gana, Bhakoot, Nadi
- **Dosha detection**: Manglik (with cancellation logic), Nadi, Bhakoot
- **House scoring** with full AI-explainable breakdown (lord, dignity, occupants, aspects)
- **Vimshottari Dasha** timeline with current period and antardasha
- **Derived timing windows** for marriage and career

### Advanced Data Layers
- **Planetary Aspects (Drishti)** — full aspect matrix with benefic/malefic classification
- **Navamsa (D9)** — divisional chart for marriage depth analysis
- **Transit Snapshot** — current Jupiter & Saturn positions relative to natal lagna
- **House Strength Breakdown** — lord, dignity, occupants, benefics/malefics, aspecting planets

### AI Prompt Generator
- **6 ready-to-paste ChatGPT prompts** covering:
  - 💍 Marriage Compatibility
  - 💰 Wealth & Finance
  - 💪 Health & Longevity
  - 👶 Children & Family
  - 💼 Career & Growth
  - ⚡ Overall Verdict (all-in-one)
- Each prompt includes a **system prompt** (expert Vedic astrologer role with tier-based verdict rules) and **focused data extraction** (only relevant chart data, not raw JSON dumps)
- Click-to-preview and one-click clipboard copy

### Other Features
- Place autocomplete via geocoding (Nominatim / Google Places)
- MongoDB profile persistence (optional — auto-saves entered profiles)
- Strict validation on all chart output (no partial data ever returned)

---

## 🏗️ Architecture

```
kundali/
├── backend/
│   ├── main.py                  # FastAPI app, endpoints, CORS
│   └── services/
│       ├── ephemeris.py          # Swiss Ephemeris wrapper, chart computation
│       ├── chart_builder.py      # Chart enrichment, house scoring, doshas
│       ├── guna_milan.py         # Ashtakoota scoring (8 gunas)
│       ├── dasha.py              # Vimshottari Dasha computation
│       ├── aspects.py            # Planetary aspects (Drishti) matrix
│       ├── navamsa.py            # D9 divisional chart
│       ├── geocoding.py          # Place resolution + timezone
│       └── validation.py         # Strict chart completeness checks
├── frontend/
│   ├── index.html               # Single-page app
│   ├── app.js                   # UI logic + AI prompt generators
│   └── style.css                # Design system
├── requirements.txt
└── .env                         # MONGODB_URI, GOOGLE_PLACES_KEY (optional)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- [Swiss Ephemeris](https://pypi.org/project/pyswisseph/) (`pyswisseph`)

### Install

```bash
cd kundali
pip install -r requirements.txt
```

### Configure (Optional)

Create a `.env` file:

```env
# Optional — enables profile persistence
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/kundali

# Optional — enables Google Places autocomplete (falls back to Nominatim)
GOOGLE_PLACES_KEY=your_key_here
```

### Run

```bash
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serve frontend |
| `GET` | `/health` | Server health + geocoding provider status |
| `GET` | `/places/autocomplete?q=...` | Place search for autocomplete |
| `POST` | `/guna-milan` | Ashtakoota compatibility score (36-point) |
| `POST` | `/full-data` | Complete validated charts + Guna Milan + all layers |
| `GET` | `/profiles` | List saved profiles (requires MongoDB) |
| `POST` | `/profiles` | Save a profile (requires MongoDB) |

### Request Format (`/full-data` and `/guna-milan`)

```json
{
  "boy": {
    "name": "Mayank",
    "dob": "1996-06-04",
    "time": "18:34",
    "time_accuracy": "exact",
    "place": "Rudrapur"
  },
  "girl": {
    "name": "Tanya",
    "dob": "1999-10-31",
    "time": "00:49",
    "place": "Saharanpur"
  }
}
```

Place can also be an object with pre-resolved coordinates:

```json
"place": {
  "label": "New Delhi, India",
  "lat": 28.6139,
  "lon": 77.209,
  "timezone": "Asia/Kolkata"
}
```

---

## 📊 Response Structure (`/full-data`)

```
{
  "boy": { <chart> },
  "girl": { <chart> },
  "guna_milan": { score, max_score, verdict, breakdown }
}
```

Each `<chart>` contains:

| Key | Content |
|-----|---------|
| `meta` | Ayanamsa, house system, coordinates, timezone, timestamps |
| `core_identity` | Lagna, moon sign, sun sign, nakshatra, tithi, yoga, karana |
| `planets` | 9 planets with sign, house, degree, longitude, nakshatra, pada, retro, speed |
| `houses` | 12 houses with sign, lord, occupants |
| `lords_mapping` | House → lord planet mapping |
| `planet_strength` | Dignity for each planet (exalted/own/friendly/neutral/enemy/debilitated) |
| `doshas` | Manglik (with severity + cancellation), Nadi, Bhakoot |
| `house_scores` | Wealth/Marriage/Career/Gains with full breakdown (lord, occupants, aspects) |
| `aspects` | `aspects_given` (planet → houses) + `aspects_received` (house → planets) |
| `navamsa` | D9 ascendant + all 9 planets with sign, house, strength |
| `transits` | Current Jupiter & Saturn with sign, degree, nakshatra, transit house |
| `dasha` | Current mahadasha/antardasha + full Vimshottari timeline |
| `derived_windows` | AI-computed marriage window and career peak years |

---

## 🤖 AI Prompt System

The app generates **6 specialized ChatGPT prompts** from the chart data. Each prompt:

1. **System prompt** — Sets ChatGPT as an expert Vedic astrologer with rules for using only provided data, considering both D1/D9, factoring aspects, and giving clear tier ratings
2. **Focused data** — Extracts only the relevant subset (e.g., marriage prompt only sends 7th house, Venus, D9, doshas — not the entire JSON)
3. **Analysis questions** — Specific questions for the topic area
4. **Verdict requirement** — Forces a clear 🟢/🟡/🟠/🔴/⛔ rating

### Verdict Tiers

| Tier | Meaning |
|------|---------|
| 🟢 **BEST MATCH** | Rare celestial alignment, highly favorable |
| 🟡 **GOOD MATCH** | Solid foundation, minor issues manageable |
| 🟠 **AVERAGE** | Proceed with awareness, some areas need work |
| 🔴 **CHALLENGING** | Serious remedies needed before proceeding |
| ⛔ **AVOID** | Major fundamental incompatibility |

---

## 🔧 Technical Notes

- **Swiss Ephemeris** provides sub-arcsecond precision for planetary positions
- **Whole Sign houses** — each house = one full sign, starting from the ascendant sign
- **Lahiri Ayanamsa** — the most widely used ayanamsa in Indian Vedic astrology
- **Vimshottari Dasha** — 120-year cycle based on Moon's nakshatra at birth
- **Navamsa (D9)** — each sign divided into 9 parts (3°20' each), mapped by element cycle
- **Drishti aspects** — all planets aspect 7th; Mars +4th/8th; Jupiter +5th/9th; Saturn +3rd/10th

---

## 📋 Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `pyswisseph` | Swiss Ephemeris Python bindings |
| `requests` | Geocoding HTTP calls |
| `motor` | Async MongoDB driver (optional) |
| `pymongo` | MongoDB (optional) |
| `python-dotenv` | Environment variables |

---

## 📄 License

Internal use only.
