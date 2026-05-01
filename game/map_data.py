"""
Kirk Assassination scene — The Quad at UVU.
Terrain codes: 0=void 1=ground 2=path 3=plaza 4=grass
"""

W, H = 56, 44

# Terrain types
VOID   = 0
GROUND = 1
PATH   = 2
PLAZA  = 3
GRASS  = 4

# Tile colors (teal terminal aesthetic)
TILE_COLORS = {
    VOID:   (6,  13, 10),
    GROUND: (14, 28, 23),
    PATH:   (21, 43, 35),
    PLAZA:  (18, 34, 32),
    GRASS:  (12, 31, 20),
}


def build_terrain():
    m = [[VOID] * W for _ in range(H)]

    # Interior ground footprint (1-tile void border)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            m[y][x] = GROUND

    # --- Grass zones ---

    # North fields: y=6-14, x=12-41
    for y in range(6, 15):
        for x in range(12, 42):
            m[y][x] = GRASS

    # NE corner fields: y=1-14, x=42-54
    for y in range(1, 15):
        for x in range(42, 55):
            m[y][x] = GRASS

    # Western fields: y=15-32, x=6-14
    for y in range(15, 33):
        for x in range(6, 15):
            m[y][x] = GRASS

    # Southern approach: y=36-42, x=8-29
    for y in range(36, 43):
        for x in range(8, 30):
            m[y][x] = GRASS

    # --- THE QUAD plaza: x=21-33, y=16-27 ---
    for y in range(16, 28):
        for x in range(21, 34):
            m[y][x] = PLAZA

    # Quad grass corners (2x2 patches at each inside corner)
    # Top-left
    for y in range(16, 18):
        for x in range(21, 23):
            m[y][x] = GRASS
    # Top-right
    for y in range(16, 18):
        for x in range(32, 34):
            m[y][x] = GRASS
    # Bottom-left
    for y in range(26, 28):
        for x in range(21, 23):
            m[y][x] = GRASS
    # Bottom-right
    for y in range(26, 28):
        for x in range(32, 34):
            m[y][x] = GRASS

    # --- Roads (PATH) ---

    # Main E-W approach road: y=33-34, x=8-53
    for y in range(33, 35):
        for x in range(8, 54):
            m[y][x] = PATH

    # Central N-S spine: x=25-26, y=5-33
    for y in range(5, 34):
        for x in range(25, 27):
            m[y][x] = PATH

    # Top E-W road: y=5-6, x=5-52
    for y in range(5, 7):
        for x in range(5, 53):
            m[y][x] = PATH

    # Left N-S road: x=5-6, y=6-43
    for y in range(6, 44):
        for x in range(5, 7):
            m[y][x] = PATH

    # Quad E-W walkway: y=20-21, x=14-40
    for y in range(20, 22):
        for x in range(14, 41):
            m[y][x] = PATH

    # Player staging connector: x=46-47, y=34-43
    for y in range(34, 44):
        for x in range(46, 48):
            m[y][x] = PATH

    # South-of-quad E-W: y=27-28, x=15-46
    for y in range(27, 29):
        for x in range(15, 47):
            m[y][x] = PATH

    # R1 approach N-S: x=50-51, y=6-15
    for y in range(6, 16):
        for x in range(50, 52):
            m[y][x] = PATH

    return m


TERRAIN = build_terrain()

# -------------------------------------------------------------------
# Buildings  (id, name, sub, x, y, w, h, floors, type, hp, max_hp)
# -------------------------------------------------------------------
BUILDINGS = [
    ("library",        "FULTON LIBRARY",        "INTEL HQ",       19, 13, 4, 3, 4, "intel",    940, 1000),
    ("engineering",    "ENGINEERING CENTER",     "TECH FACILITY",  29, 13, 4, 3, 5, "tech",     750,  800),
    ("sorensen",       "SORENSEN CENTER",        "CMD ANNEX",      16, 18, 3, 5, 3, "command", 1500, 1500),
    ("business",       "WOODBURY BUSINESS",      "ECON HUB",       34, 18, 3, 5, 3, "resource", 580,  600),
    ("clock",          "CLOCK TOWER",            "SENSOR ARRAY",   25, 20, 2, 2, 9, "sensor",   380,  400),
    ("losee",          "LOSEE CENTER",           "BARRACKS",       21, 28, 6, 3, 2, "barracks", 700,  700),
    ("admin",          "ADMINISTRATION BLDG",    "CMD ANNEX",      29, 28, 5, 3, 3, "command",  820,  900),
    ("north_parking",  "NORTH PARKING",          "VEHICLE DEPOT",  11,  4, 4, 2, 1, "depot",    200,  200),
    ("cafe",           "CAMPUS CAFE",            "RESOURCE NODE",  38, 29, 3, 2, 2, "resource", 300,  300),
    ("medical",        "MEDICAL CENTER",         "HEAL AURA",      40, 22, 3, 3, 3, "resource", 400,  400),
    ("student_housing","STUDENT HOUSING",        "GARRISON PT",    44, 16, 4, 3, 2, "barracks", 350,  350),
    ("delta_house",    "DELTA HOUSE",            "GARRISON PT",    44, 26, 3, 3, 2, "barracks", 280,  280),
    ("audit_point",    "AUDIT CHECKPOINT",       "SENSOR NODE",    36, 33, 2, 2, 2, "sensor",   250,  250),
    ("comms_tower",    "COMMS TOWER",            "INTEL RELAY",    12, 21, 2, 2, 4, "intel",    300,  300),
]

# Kirk's rally point — center of the quad plaza
KIRK_RALLY = (26.5, 21.0)

# Building color palettes by type
BTYPE_COLORS = {
    "intel":    {"top": (26, 56, 48),  "wall_l": (13, 36, 25),  "wall_r": (18, 46, 34)},
    "tech":     {"top": (46, 42, 16),  "wall_l": (28, 26, 13),  "wall_r": (34, 32, 15)},
    "command":  {"top": (46, 26, 10),  "wall_l": (28, 16,  8),  "wall_r": (34, 20, 10)},
    "resource": {"top": (26, 48, 24),  "wall_l": (14, 34, 12),  "wall_r": (18, 42, 16)},
    "barracks": {"top": (22, 32, 48),  "wall_l": (12, 20, 32),  "wall_r": (16, 24, 40)},
    "sensor":   {"top": (32, 56, 48),  "wall_l": (15, 34, 25),  "wall_r": (20, 44, 32)},
    "depot":    {"top": (24, 24, 24),  "wall_l": (14, 14, 14),  "wall_r": (18, 18, 18)},
}
