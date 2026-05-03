"""
The Whipple District — Government Quarter, Twin Cities Metro.
Terrain: dense urban road grid, government plaza, residential blocks.
Catalyst: ICE compliance check → Aurora Ave. SUV crash. Narrative containment begins.
"""

W, H = 56, 44

VOID   = 0
GROUND = 1
PATH   = 2
PLAZA  = 3
GRASS  = 4

TILE_COLORS = {
    VOID:   (6,  13, 10),
    GROUND: (18, 22, 20),   # darker concrete — more urban than campus
    PATH:   (28, 34, 30),   # road asphalt
    PLAZA:  (22, 30, 36),   # government stone
    GRASS:  (12, 28, 18),
}


def build_terrain():
    m = [[VOID] * W for _ in range(H)]

    # Interior fill — all ground
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            m[y][x] = GROUND

    # ── E-W roads ─────────────────────────────────────────────────────
    for x in range(1, W - 1):
        m[8][x]  = PATH;  m[9][x]  = PATH   # Government Row (Ford Pkwy)
        m[19][x] = PATH;  m[20][x] = PATH   # Aurora Ave — incident street
        m[30][x] = PATH;  m[31][x] = PATH   # 46th Street

    # ── N-S roads ─────────────────────────────────────────────────────
    for y in range(1, H - 1):
        m[y][12] = PATH;  m[y][13] = PATH   # Cedar Ave
        m[y][24] = PATH;  m[y][25] = PATH   # Summit Ave
        m[y][37] = PATH;  m[y][38] = PATH   # Airport Blvd

    # ── Government Plaza (NE quadrant) ────────────────────────────────
    for y in range(1, 8):
        for x in range(39, W - 1):
            m[y][x] = PLAZA

    # ── Courthouse / Civic Plaza ──────────────────────────────────────
    for y in range(1, 8):
        for x in range(26, 38):
            m[y][x] = PLAZA

    # ── Riverside Park ────────────────────────────────────────────────
    for y in range(21, 30):
        for x in range(14, 24):
            m[y][x] = GRASS

    # ── Enemy staging — protest camp (NW) ────────────────────────────
    for y in range(1, 8):
        for x in range(1, 12):
            m[y][x] = GRASS

    # ── South green ───────────────────────────────────────────────────
    for y in range(32, 43):
        for x in range(26, 37):
            m[y][x] = GRASS

    # ── Median strips on long roads ───────────────────────────────────
    # Central median on Aurora Ave
    for x in range(14, 24):
        m[19][x] = GROUND

    return m


TERRAIN = build_terrain()

# ── Pre-placed neutral / faction buildings ─────────────────────────────────
# Format: (key, display_name, sub, x, y, w, h, floors, btype, hp, max_hp)

BUILDINGS = [
    # Government complex (NE)
    ("whipple",      "WHIPPLE FEDERAL BLDG",   "HHS / ICE ANNEX",   40, 1, 4, 4, 5, "command",  2000, 2000),
    ("ice_office",   "ICE FIELD OFFICE",        "ENFORCEMENT OPS",   47, 1, 3, 3, 3, "barracks",  800,  800),
    ("ng_armory",    "NATIONAL GUARD ARMORY",   "RESERVE BASE",      40, 10, 4, 3, 2, "depot",    1000, 1000),

    # Civic corridor (middle-top)
    ("courthouse",   "FEDERAL COURTHOUSE",      "JUSTICE ANNEX",     27, 1, 4, 4, 6, "command",  1500, 1500),
    ("city_hall",    "CITY HALL",               "MUNICIPAL HQ",      15, 1, 4, 3, 4, "command",  1200, 1200),
    ("archives",     "STATE ARCHIVES",          "INTEL VAULT",        1, 1, 3, 3, 3, "intel",     600,  600),

    # Mid-tier captures
    ("kare11",       "KARE-11 STUDIOS",         "MEDIA OPS",          1, 10, 3, 3, 4, "sensor",   400,  400),
    ("precinct",     "5TH PRECINCT",            "ENFORCEMENT HUB",   14, 10, 3, 3, 3, "barracks", 700,  700),
    ("transit",      "METRO TRANSIT HUB",       "INFRASTRUCTURE",    26, 10, 4, 2, 3, "resource", 500,  500),

    # Aurora Ave zone (incident area)
    ("checkpoint_a", "CHECKPOINT AURORA",       "SENSOR NODE",       35, 14, 2, 2, 2, "sensor",   300,  300),
    ("checkpoint_c", "CHECKPOINT CEDAR",        "SENSOR NODE",        1, 22, 2, 2, 2, "sensor",   300,  300),
    ("gas_station",  "VANTAGE GAS & GO",        "RESOURCE NODE",     39, 22, 2, 2, 1, "resource", 200,  200),
    ("community_ctr","COMMUNITY CENTER",        "CIVILIAN HOLD",     15, 22, 3, 3, 2, "barracks", 450,  450),
    ("river_apts",   "RIVERSIDE APTS",          "GARRISON PT",       26, 22, 4, 3, 4, "barracks", 600,  600),

    # South residential
    ("veterans",     "VETERANS HOME",           "GARRISON PT",       39, 32, 4, 3, 3, "barracks", 500,  500),
    ("cathedral",    "CATHEDRAL OF ST. PAUL",   "CIVILIAN REFUGE",   15, 32, 3, 3, 5, "command",  600,  600),
    ("postal",       "POSTAL ANNEX",            "CIVILIAN NODE",      1, 32, 3, 2, 2, "resource", 250,  250),
]

# Incident point — Aurora Ave compliance check (replaces KIRK_RALLY role)
KIRK_RALLY = (29.0, 16.5)

INCIDENT_LABEL = "AURORA AVE"
INCIDENT_SUV_CRASH_TARGET = (29.0, 13.0)   # SUV lurches north into the plaza

# Runner escape routes — edges of the district map
RUNNER_DESTINATIONS = [(52, 2), (2, 42), (52, 40)]

# Map identity
MAP_ID    = "district"
MAP_TITLE = "WHIPPLE DISTRICT"

# Building color palettes (same keys as map_data.py)
BTYPE_COLORS = {
    "intel":    {"top": (30, 40, 55),  "wall_l": (18, 25, 36),  "wall_r": (24, 32, 45)},
    "tech":     {"top": (46, 42, 16),  "wall_l": (28, 26, 13),  "wall_r": (34, 32, 15)},
    "command":  {"top": (50, 34, 18),  "wall_l": (32, 20, 10),  "wall_r": (40, 26, 14)},
    "resource": {"top": (30, 50, 28),  "wall_l": (18, 34, 16),  "wall_r": (24, 42, 20)},
    "barracks": {"top": (30, 36, 52),  "wall_l": (18, 22, 36),  "wall_r": (24, 28, 44)},
    "sensor":   {"top": (28, 52, 44),  "wall_l": (16, 34, 28),  "wall_r": (22, 42, 36)},
    "depot":    {"top": (32, 30, 24),  "wall_l": (20, 18, 14),  "wall_r": (26, 24, 18)},
}
