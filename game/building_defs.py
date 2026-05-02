"""
Building catalog — single source of truth for all structure types.

Categories:
  "base"         — player-built, faction-specific
  "civilian"     — neutral capturable objectives
  "garrisonable" — infantry can enter and fire from windows

Each entry is a dict; the designer and game both read from here.
"""

# ── Palette helpers ────────────────────────────────────────────────────────────
def _pal(top, wall_l, wall_r, accent=None, window=None):
    return {
        "top":    top,
        "wall_l": wall_l,
        "wall_r": wall_r,
        "accent": accent or top,
        "window": window or (0, 60, 80),
    }

# Shared tones
_CONCRETE   = _pal((80,80,75),   (55,55,50),   (68,68,62),   accent=(100,100,95))
_BRICK      = _pal((120,70,50),  (88,50,35),   (105,62,44),  accent=(160,90,60))
_GLASS_BLUE = _pal((40,70,100),  (28,50,75),   (35,62,90),   window=(80,160,220))
_BRUTALIST  = _pal((90,88,82),   (62,60,56),   (76,74,70),   accent=(110,108,100))

# Regency base palette (dark navy + gold)
_REG_BASE   = _pal((28,40,80),   (18,28,58),   (24,36,70),   accent=(200,160,20), window=(0,80,200))
# Regency fortification (dark concrete + red)
_REG_FORT   = _pal((40,32,28),   (28,22,18),   (35,28,22),   accent=(180,30,20))

# Frontline palette (olive drab + orange)
_FRONT_BASE = _pal((55,65,38),   (38,46,26),   (48,57,33),   accent=(220,120,30), window=(80,140,60))

# Sovereign palette (dark purple + neon)
_SOV_BASE   = _pal((38,24,58),   (26,16,42),   (33,20,50),   accent=(160,60,220))

# Oligarchy palette (black + gold)
_OLIG_BASE  = _pal((22,18,14),   (14,10,8),    (18,14,10),   accent=(200,160,30), window=(60,40,10))

# Civilian tones
_CAMPUS     = _pal((105,95,82),  (72,65,56),   (88,80,68),   accent=(140,120,90), window=(120,180,200))
_CAMPUS_RED = _pal((130,55,45),  (92,38,30),   (112,48,38),  accent=(180,80,55),  window=(180,140,100))
_GLASS_GRN  = _pal((35,75,60),   (24,54,44),   (30,65,52),   window=(80,200,160))


# Regency palette (dark teal + neon cyan + red accents)
_REG_PATRIOT = _pal((15,50,50),  (10,35,35),   (13,42,42),   accent=(220,30,20), window=(0,255,200))

# Sovereign palette (darkest teal + shadow)
_SOV_SHADOW  = _pal((10,25,25),  (5,15,15),    (8,20,20),    accent=(0,255,180))

# ── CATALOG ───────────────────────────────────────────────────────────────────

BUILDINGS = {

    # ══════════════════════════════════════════════════════════════════
    #  REGENCY — Base Buildings
    # ══════════════════════════════════════════════════════════════════

    "reg_hq": {
        "name":        "ADMINISTRATIVE HQ",
        "sub":         "COMMAND CENTER",
        "category":    "base",
        "faction":     "regency",
        "w": 4, "h": 4, "floors": 4,
        "cost":        0,
        "hp":          2000,
        "power_draw":  -40,
        "garrison":    0,
        "produces":    [],
        "description": "The nexus for all local narrative budgeting and population auditing. Loss = mission failure.",
        "palette":     _REG_BASE,
        "flags":       ["command", "required"],
        "roof_style":  "antenna",
    },

    "reg_barracks": {
        "name":        "COMPLIANCE BARRACKS",
        "sub":         "INFANTRY PRODUCTION",
        "category":    "base",
        "faction":     "regency",
        "w": 3, "h": 3, "floors": 2,
        "cost":        500,
        "hp":          800,
        "power_draw":  -12,
        "garrison":    0,
        "produces":    ["gravy_seal", "ice_agent", "ice_agent_tac", "proud_perimeter", "donor", "patriot_lawyer"],
        "description": "Orientation facility for citizens awaiting successful personality optimization.",
        "palette":     _REG_BASE,
        "flags":       ["production"],
        "roof_style":  "flat",
    },

    "reg_pen": {
        "name":        "COMPLIANCE PEN",
        "sub":         "CIVILIAN HOLDING",
        "category":    "base",
        "faction":     "regency",
        "w": 3, "h": 3, "floors": 1,
        "cost":        400,
        "hp":          600,
        "power_draw":  -5,
        "garrison":    12,
        "produces":    [],
        "passive_income": 0,
        "description": "Secured orientation facility for citizens awaiting successful personality optimization.",
        "palette":     _REG_FORT,
        "flags":       ["holding_pen"],
        "roof_style":  "flat",
    },

    "reg_power": {
        "name":        "POWER SUBSTATION",
        "sub":         "GRID NODE",
        "category":    "base",
        "faction":     "regency",
        "w": 2, "h": 2, "floors": 2,
        "cost":        300,
        "hp":          500,
        "power_draw":  +60,   # positive = generates
        "garrison":    0,
        "produces":    [],
        "description": "Generates +60 power. All production stops at 0 power.",
        "palette":     _pal((60,55,20),(42,38,14),(52,48,18),accent=(220,200,30)),
        "flags":       ["power"],
        "roof_style":  "tower",
    },

    "reg_depot": {
        "name":        "VEHICLE DEPOT",
        "sub":         "MOTORPOOL",
        "category":    "base",
        "faction":     "regency",
        "w": 4, "h": 3, "floors": 1,
        "cost":        800,
        "hp":          700,
        "power_draw":  -20,
        "garrison":    0,
        "produces":    ["unmarked_van", "mrap", "compliance_bus"],
        "description": "Storage for community outreach vehicles designed for heavy urban stabilization.",
        "palette":     _REG_FORT,
        "flags":       ["production", "vehicle"],
        "roof_style":  "hangar",
    },

    "reg_detention": {
        "name":        "COMPLIANCE CENTER",
        "sub":         "DETENTION FACILITY",
        "category":    "base",
        "faction":     "regency",
        "w": 3, "h": 2, "floors": 1,
        "cost":        300,
        "hp":          400,
        "power_draw":  -8,
        "garrison":    0,
        "produces":    [],
        "description": "Holds detained civilians. +§5/sec per occupant. Bust costs +15 Infamy.",
        "palette":     _REG_FORT,
        "flags":       ["detention", "income"],
        "roof_style":  "flat",
    },

    "reg_tower": {
        "name":        "SURVEILLANCE TOWER",
        "sub":         "SENSOR ARRAY",
        "category":    "base",
        "faction":     "regency",
        "w": 1, "h": 1, "floors": 6,
        "cost":        250,
        "hp":          300,
        "power_draw":  -6,
        "garrison":    0,
        "produces":    [],
        "description": "Clears 48-tile fog radius. Shares vision with all Regency units.",
        "palette":     _REG_BASE,
        "flags":       ["vision"],
        "roof_style":  "antenna",
    },

    "reg_wall": {
        "name":        "SECURITY BARRIER",
        "sub":         "FORTIFICATION",
        "category":    "base",
        "faction":     "regency",
        "w": 1, "h": 1, "floors": 1,
        "cost":        50,
        "hp":          600,
        "power_draw":  0,
        "garrison":    0,
        "produces":    [],
        "description": "Blocks movement. Infantry can fire over. Vehicles destroy on contact.",
        "palette":     _REG_FORT,
        "flags":       ["wall", "impassable"],
        "roof_style":  "flat",
    },

    "reg_propaganda": {
        "name":        "PROPAGANDA TOWER",
        "sub":         "INFORMATION OPS",
        "category":    "base",
        "faction":     "regency",
        "w": 2, "h": 2, "floors": 3,
        "cost":        400,
        "hp":          350,
        "power_draw":  -15,
        "garrison":    0,
        "produces":    [],
        "description": "High-fidelity signal broadcast system for synchronizing the public perspective.",
        "palette":     _pal((60,28,20),(42,18,14),(52,24,18),accent=(220,50,30)),
        "flags":       ["aura", "infamy_reduce"],
        "roof_style":  "dish",
    },

    "reg_relay": {
        "name":        "RELAY STATION",
        "sub":         "COMMS NODE",
        "category":    "base",
        "faction":     "regency",
        "w": 2, "h": 2, "floors": 2,
        "cost":        350,
        "hp":          300,
        "power_draw":  -10,
        "garrison":    0,
        "produces":    [],
        "description": "Extends ability radius. Each station adds +8 to Fact Check AoE.",
        "palette":     _REG_BASE,
        "flags":       ["relay"],
        "roof_style":  "dish",
    },

    "reg_patriot_hq": {
        "name":        "PATRIOT TRAINING CENTER",
        "sub":         "ELITE INFANTRY PRODUCTION",
        "category":    "base",
        "faction":     "regency",
        "w": 4, "h": 3, "floors": 2,
        "cost":        750,
        "hp":          1200,
        "power_draw":  -25,
        "garrison":    0,
        "produces":    ["gravy_seal"],
        "description": "Trains elite Gravy Seal squads. Features a red-hat roof and neon 'AMERICA FIRST' signage.",
        "palette":     _REG_PATRIOT,
        "flags":       ["production", "elite"],
        "roof_style":  "hat",
    },

    "reg_alpr_tower": {
        "name":        "ALPR SCANNER ARRAY",
        "sub":         "BOLO SENSOR NODE",
        "category":    "base",
        "faction":     "regency",
        "w": 1, "h": 1, "floors": 5,
        "cost":        300,
        "hp":          400,
        "power_draw":  -10,
        "garrison":    0,
        "produces":    [],
        "description": "Automatically scans passing civilian vehicles. Identifies BOLO targets for +50§ bounty.",
        "palette":     _REG_PATRIOT,
        "flags":       ["vision", "scanner"],
        "roof_style":  "antenna",
    },

    # ══════════════════════════════════════════════════════════════════
    #  FRONTLINE — Base Buildings
    # ══════════════════════════════════════════════════════════════════

    "fl_hq": {
        "name":        "FIELD COMMAND POST",
        "sub":         "FRONTLINE HQ",
        "category":    "base",
        "faction":     "frontline",
        "w": 3, "h": 3, "floors": 2,
        "cost":        0,
        "hp":          1200,
        "power_draw":  -20,
        "garrison":    0,
        "produces":    [],
        "description": "Frontline command tent. Ruggedised, deployable anywhere.",
        "palette":     _FRONT_BASE,
        "flags":       ["command", "required"],
        "roof_style":  "tent",
    },

    "fl_drone": {
        "name":        "DRONE RELAY HUB",
        "sub":         "ISR PLATFORM",
        "category":    "base",
        "faction":     "frontline",
        "w": 2, "h": 2, "floors": 1,
        "cost":        450,
        "hp":          300,
        "power_draw":  -18,
        "garrison":    0,
        "produces":    ["drone_scout", "drone_assault", "drone_operator"],
        "description": "Produces recon and assault drones. Grants map vision on launch.",
        "palette":     _FRONT_BASE,
        "flags":       ["production", "vehicle"],
        "roof_style":  "dish",
    },

    "fl_hacktivist": {
        "name":        "HACKTIVIST CELL",
        "sub":         "DIGITAL OPERATIONS",
        "category":    "base",
        "faction":     "frontline",
        "w": 2, "h": 2, "floors": 1,
        "cost":        300,
        "hp":          300,
        "power_draw":  -10,
        "garrison":    0,
        "produces":    [],
        "description": "DDoS pulse every 45s — disables nearest enemy scanner/command building for 30s.",
        "palette":     _FRONT_BASE,
        "flags":       ["ddos"],
        "roof_style":  "flat",
    },

    "fl_press": {
        "name":        "PRESS BUREAU",
        "sub":         "MEDIA OPS",
        "category":    "base",
        "faction":     "frontline",
        "w": 2, "h": 2, "floors": 2,
        "cost":        350,
        "hp":          250,
        "power_draw":  -12,
        "garrison":    0,
        "produces":    ["proxy", "news_van", "journalist", "agitator"],
        "description": "Generates Infamy for Regency on kills (+5 per). Funds Frontline via viral windows.",
        "palette":     _FRONT_BASE,
        "flags":       ["income", "infamy_amplify"],
        "roof_style":  "flat",
    },

    # ══════════════════════════════════════════════════════════════════
    #  SOVEREIGN — Base Buildings
    # ══════════════════════════════════════════════════════════════════

    "sov_safehouse": {
        "name":        "REVOLUTIONARY SAFEHOUSE",
        "sub":         "SOVEREIGN HQ",
        "category":    "base",
        "faction":     "sovereign",
        "w": 3, "h": 3, "floors": 2,
        "cost":        0,
        "hp":          900,
        "power_draw":  0,
        "garrison":    8,
        "produces":    ["proxy"],
        "description": "Hidden command post. Blends with civilian structures. 8 garrison slots.",
        "palette":     _SOV_BASE,
        "flags":       ["command", "required", "garrisonable"],
        "roof_style":  "flat",
    },

    "sov_cache": {
        "name":        "WEAPONS CACHE",
        "sub":         "ARMAMENT DEPOT",
        "category":    "base",
        "faction":     "sovereign",
        "w": 2, "h": 2, "floors": 1,
        "cost":        300,
        "hp":          200,
        "power_draw":  0,
        "garrison":    0,
        "produces":    ["proxy", "vbied"],
        "description": "Trains Proxies and prepares VBIEDs. Explodes dramatically when destroyed.",
        "palette":     _SOV_BASE,
        "flags":       ["production", "volatile"],
        "roof_style":  "flat",
    },

    "sov_shadow_lab": {
        "name":        "SHADOW LAB",
        "sub":         "SOVEREIGN R&D",
        "category":    "base",
        "faction":     "sovereign",
        "w": 3, "h": 2, "floors": 1,
        "cost":        600,
        "hp":          450,
        "power_draw":  0,
        "garrison":    4,
        "produces":    [],
        "description": "Unlocks advanced Sovereign abilities. Features hidden antennas and dark teal 'shadow' palette.",
        "palette":     _SOV_SHADOW,
        "flags":       ["tech", "garrisonable"],
        "roof_style":  "dish",
    },

    # ══════════════════════════════════════════════════════════════════
    #  OLIGARCHY — Base Buildings
    # ══════════════════════════════════════════════════════════════════

    "olig_hq": {
        "name":        "STAFFING AGENCY",
        "sub":         "OLIGARCHY HQ",
        "category":    "base",
        "faction":     "oligarchy",
        "w": 4, "h": 3, "floors": 3,
        "cost":        0,
        "hp":          1800,
        "power_draw":  -30,
        "garrison":    0,
        "produces":    ["contractor", "gravy_seal", "wagner"],
        "description": "Legitimate-looking corporate office. Produces all Oligarchy units.",
        "palette":     _OLIG_BASE,
        "flags":       ["command", "required"],
        "roof_style":  "flat",
    },

    "olig_salvage": {
        "name":        "SALVAGE YARD",
        "sub":         "RESOURCE EXTRACTION",
        "category":    "base",
        "faction":     "oligarchy",
        "w": 4, "h": 3, "floors": 1,
        "cost":        500,
        "hp":          600,
        "power_draw":  -10,
        "garrison":    0,
        "produces":    [],
        "description": "Converts wrecks into §400 credits each. Removes wreck cover in radius.",
        "palette":     _OLIG_BASE,
        "flags":       ["income", "salvage"],
        "roof_style":  "crane",
    },

    "olig_troll": {
        "name":        "TROLL FARM",
        "sub":         "NARRATIVE OPERATIONS",
        "category":    "base",
        "faction":     "oligarchy",
        "w": 2, "h": 2, "floors": 1,
        "cost":        400,
        "hp":          400,
        "power_draw":  -8,
        "garrison":    0,
        "produces":    [],
        "description": "Passively erodes enemy capture progress on nearby objectives. Most annoying building in the game.",
        "palette":     _OLIG_BASE,
        "flags":       ["troll"],
        "roof_style":  "flat",
    },

    # ══════════════════════════════════════════════════════════════════
    #  CIVILIAN / NEUTRAL — Capturable Objectives
    # ══════════════════════════════════════════════════════════════════

    "civ_cafe": {
        "name":        "CAMPUS CAFÉ",
        "sub":         "INCOME NODE  +§12/SEC",
        "category":    "civilian",
        "faction":     None,
        "w": 2, "h": 2, "floors": 1,
        "cost":        0,
        "hp":          250,
        "power_draw":  0,
        "garrison":    4,
        "produces":    [],
        "description": "Neutral income building. Capture for passive credits. 4 garrison slots.",
        "palette":     _CAMPUS,
        "flags":       ["capturable", "income", "garrisonable"],
        "roof_style":  "awning",
    },

    "civ_library": {
        "name":        "STUDENT LIBRARY",
        "sub":         "XP AMPLIFIER",
        "category":    "civilian",
        "faction":     None,
        "w": 4, "h": 3, "floors": 3,
        "cost":        0,
        "hp":          300,
        "power_draw":  0,
        "garrison":    8,
        "produces":    [],
        "description": "Centralized repository for the permanent redaction of unauthorized historical data.",
        "palette":     _BRUTALIST,
        "flags":       ["capturable", "xp_boost", "garrisonable"],
        "roof_style":  "flat",
    },

    "civ_medical": {
        "name":        "MEDICAL CENTER",
        "sub":         "SUPPLY NODE",
        "category":    "civilian",
        "faction":     None,
        "w": 3, "h": 2, "floors": 2,
        "cost":        0,
        "hp":          250,
        "power_draw":  0,
        "garrison":    6,
        "produces":    [],
        "description": "Facility dedicated to biological maintenance and experimental revenue extraction.",
        "palette":     _pal((200,200,200),(155,155,155),(178,178,178),accent=(200,30,30),window=(180,220,255)),
        "flags":       ["capturable", "heal_aura", "garrisonable"],
        "roof_style":  "cross",
    },

    "civ_dispensary": {
        "name":        "CAMPUS DISPENSARY",
        "sub":         "MORALE + INCOME NODE",
        "category":    "civilian",
        "faction":     None,
        "w": 2, "h": 1, "floors": 1,
        "cost":        0,
        "hp":          150,
        "power_draw":  0,
        "garrison":    2,
        "produces":    [],
        "description": "Neutral building. Provides §8/sec and slow Morale regen in radius. 2 garrison.",
        "palette":     _GLASS_GRN,
        "flags":       ["capturable", "income", "morale_aura", "garrisonable"],
        "roof_style":  "flat",
    },

    "civ_dorm_delta": {
        "name":        "DELTA HOUSE",
        "sub":         "GREEK ROW — MORALE",
        "category":    "civilian",
        "faction":     None,
        "w": 3, "h": 2, "floors": 2,
        "cost":        0,
        "hp":          300,
        "power_draw":  0,
        "garrison":    10,
        "produces":    [],
        "description": "Greek house. Morale aura: friendly units in range never retreat. 10 garrison.",
        "palette":     _CAMPUS_RED,
        "flags":       ["capturable", "morale_aura", "garrisonable"],
        "roof_style":  "gable",
    },

    "civ_dorm_sigma": {
        "name":        "SIGMA HOUSE",
        "sub":         "GREEK ROW — SUPPLY",
        "category":    "civilian",
        "faction":     None,
        "w": 3, "h": 2, "floors": 2,
        "cost":        0,
        "hp":          300,
        "power_draw":  0,
        "garrison":    10,
        "produces":    [],
        "description": "Greek house. Supply aura: +1 ammo regen/sec for garrisoned units.",
        "palette":     _CAMPUS_RED,
        "flags":       ["capturable", "supply_aura", "garrisonable"],
        "roof_style":  "gable",
    },

    "civ_clock_tower": {
        "name":        "CLOCK TOWER",
        "sub":         "VISION ANCHOR",
        "category":    "civilian",
        "faction":     None,
        "w": 2, "h": 2, "floors": 8,
        "cost":        0,
        "hp":          400,
        "power_draw":  0,
        "garrison":    2,
        "produces":    [],
        "description": "Reminder of the finite duration of your current employment contract.",
        "palette":     _CAMPUS,
        "flags":       ["capturable", "vision", "landmark"],
        "roof_style":  "spire",
    },

    "audit_point": {
        "name":        "AUDIT POINT",
        "sub":         "NARRATIVE CONTROL",
        "category":    "civilian",
        "faction":     None,
        "w": 1, "h": 1, "floors": 1,
        "cost":        0,
        "hp":          1000,
        "power_draw":  0,
        "garrison":    0,
        "passive_income": 10,
        "description": "Critical map objective. Capture to gain Narrative Control (+10 credits/tick).",
        "palette":     _pal((200,200,0), (150,150,0), (180,180,0), accent=(255,255,255)),
        "flags":       ["capturable", "objective"],
        "roof_style":  "antenna",
    },

    # ══════════════════════════════════════════════════════════════════
    #  GARRISONABLE — Generic civilian structures on map
    # ══════════════════════════════════════════════════════════════════

    "garr_house": {
        "name":        "RESIDENTIAL HOUSE",
        "sub":         "GARRISON — 4 INFANTRY",
        "category":    "garrisonable",
        "faction":     None,
        "w": 2, "h": 2, "floors": 1,
        "cost":        0,
        "hp":          200,
        "power_draw":  0,
        "garrison":    4,
        "produces":    [],
        "description": "Small house. Infantry fire from windows at -15% accuracy penalty.",
        "palette":     _pal((160,120,80),(115,85,55),(138,104,68),window=(200,220,180)),
        "flags":       ["garrisonable", "destructible"],
        "roof_style":  "gable",
    },

    "garr_office": {
        "name":        "OFFICE BLOCK",
        "sub":         "GARRISON — 8 INFANTRY",
        "category":    "garrisonable",
        "faction":     None,
        "w": 3, "h": 2, "floors": 4,
        "cost":        0,
        "hp":          350,
        "power_draw":  0,
        "garrison":    8,
        "produces":    [],
        "description": "Multi-storey office. Each floor is a firing tier. Artillery destroys in 1 volley.",
        "palette":     _GLASS_BLUE,
        "flags":       ["garrisonable", "destructible", "multi_floor_garrison"],
        "roof_style":  "flat",
    },

    "garr_shop": {
        "name":        "STRIP MALL UNIT",
        "sub":         "GARRISON — 3 INFANTRY",
        "category":    "garrisonable",
        "faction":     None,
        "w": 3, "h": 1, "floors": 1,
        "cost":        0,
        "hp":          180,
        "power_draw":  0,
        "garrison":    3,
        "produces":    [],
        "description": "Low storefront. Good cover, poor sightlines. Cheap to clear.",
        "palette":     _pal((140,120,90),(100,85,62),(120,104,76),window=(180,200,160)),
        "flags":       ["garrisonable", "destructible"],
        "roof_style":  "awning",
    },

    "garr_parking": {
        "name":        "PARKING STRUCTURE",
        "sub":         "GARRISON — VEHICLES + 6 INF",
        "category":    "garrisonable",
        "faction":     None,
        "w": 4, "h": 3, "floors": 3,
        "cost":        0,
        "hp":          500,
        "power_draw":  0,
        "garrison":    6,
        "produces":    [],
        "description": "Open-sided. Vehicles can park inside for cover. Infantry on top floor.",
        "palette":     _CONCRETE,
        "flags":       ["garrisonable", "vehicle_cover", "destructible"],
        "roof_style":  "flat",
    },
}


def get_by_category(cat: str):
    return {k: v for k, v in BUILDINGS.items() if v["category"] == cat}


def get_by_faction(faction: str):
    return {k: v for k, v in BUILDINGS.items() if v.get("faction") == faction}
