> **Reference:** Updated "Find Your Nearest Nagar Van Park" feature prompt for AI agents. Last updated: 2025-06-13.

## UPDATED DETAILED PROMPT: "Find Your Nearest Nagar Van Park" Feature

### Project Overview
Build an interactive "Locate Your Nearest NVY Park" web page/tab for urbanforestpark.com that allows users to input their location (address or GPS coordinates) and discover nearby Nagar Van Yojana sites within their state, displaying distance, driving directions, and comprehensive site details.

### Scope & States (8 States — 235 Total Sites)
Focus on 8 states with active NVY implementation:

#### 1. Madhya Pradesh (108 sites)
Largest concentration across Ujjain, Indore, Bhopal, Gwalior, Khargone, Seoni, Chhindwara, Balaghat, Burhanpur, Satna, Sagar, Singrauli, Narmadapuram, and other districts.

#### 2. Andhra Pradesh (61 sites)
Southern presence across Nellore, Chittoor, Tirupati, Kurnool, Guntur, Vizianagaram, Kadapa, and others.

#### 3. Jharkhand (30 sites)
Eastern cluster in Ranchi, Saraikela, Bokaro, Hazaribagh, Deoghar, Medininagar, Giridih, Jamshedpur.

#### 4. Gujarat (11 sites)
Western anchor: Surat (Dumas Forest Area, 40 Ha), Gandhinagar (Aranya Udhyan, Indroda Nature Park, 50 Ha), Ahmedabad, Rajkot, Panchmahl.

#### 5. Uttar Pradesh (12 sites)
Northern expansion across multiple divisions:

**Amroha Division (5 sites):**
- Daulatipur Nagar Van (50 Ha, >50 species)
- Dhanaura Nagar Van (10 Ha, >50 species)
- Ishwardeva Nagar Van (25 Ha, >50 species)
- Sihali Nagar Van / Gajraula (25 Ha, >70 species)
- Jati Nagar Van (50 Ha, >100 species)

**Additional UP Sites (7 sites):**
- Agra — Kakretha (50 Ha)
- Gorakhpur — Gorakhpur I, II, Nagar Van Ramlakhna (50+50+15 Ha)
- Raebareli — Merui Lalganj, Rajapur, Gangapur Kamva (50+50+50 Ha)

#### 6. Rajasthan (10 sites — NEW)
- Jodhpur (North) — Kaylana (50 Ha)
- Udaipur — Machla Magra (50 Ha)
- Rajsamand — Dayalshah killa (20 Ha)
- Kota (North) — Devli Areb (32 Ha)
- Ajmer — Van devi vrikshkunj (5 Ha)
- Kota (South) — Awali Rojhadi (50 Ha)
- Alwar — Bhugor (15 Ha)
- Churu (A) — Depalsar (50 Ha)
- Churu (C) — Buntiya (40 Ha)
- Jaipur — Muhana (26 Ha)

#### 7. Punjab (3 sites — NEW)
- SAS Nagar — Mullanpur FDA (15 Ha)
- Patiala — Bir Kheri Gujjran Park (16.9 Ha)
- Pathankot — Rakh Nehar Ki Bir Reserve Forest (50 Ha)

### Data Source
NVY sites data with all 8 states is in `public/assets/data/nvy-sites.json` (235 total sites). The UP Amroha sites (IDs 6000-6004) include supplementary fields: `saplingPlanted`, `speciesCount`, `topSpecies`, `forestDivision`, `managingAuthority`.

### UX/UI Considerations
- **State selector** dropdown: All States / MP / AP / Jharkhand / Gujarat / Uttar Pradesh / Rajasthan / Punjab
- **Color-coded markers**: UP = blue, MP = green, AP = orange, JH = red, GJ = yellow, RJ = purple, PB = teal
- **State-level stats**: "12 parks in Uttar Pradesh | 108 in MP | 61 in AP | 30 in JH | 11 in GJ | 10 in RJ | 3 in PB"
- **Forest Division filter**: e.g., "Amroha Forest Division"
- **Fallback message**: *"This location is outside our current coverage. Try searching within Madhya Pradesh, Andhra Pradesh, Jharkhand, Gujarat, Uttar Pradesh, Rajasthan, or Punjab."*
- **Geocoding priority**: Google Geocoding API / Nominatim for all listed cities and districts
