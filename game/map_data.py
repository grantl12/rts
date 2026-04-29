"""
Kirk Assassination scene — The Quad at UVU.
Terrain codes: 0=void 1=ground 2=path 3=plaza 4=grass
"""

W, H = 28, 24

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

    # Campus ground footprint
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            m[y][x] = GROUND

    # Central quad / plaza
    for y in range(7, 17):
        for x in range(8, 20):
            m[y][x] = PLAZA

    # Grass patches inside quad (four corners)
    for y in range(8, 10):
        for x in range(9, 12):
            m[y][x] = GRASS
    for y in range(14, 16):
        for x in range(16, 19):
            m[y][x] = GRASS
    for y in range(8, 10):
        for x in range(16, 19):
            m[y][x] = GRASS
    for y in range(14, 16):
        for x in range(9, 12):
            m[y][x] = GRASS

    # N-S main walkway (cols 13-14)
    for y in range(1, H - 1):
        m[y][13] = PATH
        m[y][14] = PATH

    # E-W main walkway (rows 11-12)
    for x in range(1, W - 1):
        m[11][x] = PATH
        m[12][x] = PATH

    # Diagonal paths through quad
    for i in range(6):
        if 0 <= 7 + i < H and 0 <= 8 + i < W:
            m[7 + i][8 + i] = PATH
        if 0 <= 7 + i < H and 0 <= 19 - i < W:
            m[7 + i][19 - i] = PATH

    return m


TERRAIN = build_terrain()

# -------------------------------------------------------------------
# Buildings  (x, y = top-left tile, w/h in tiles, floors, type, name)
# -------------------------------------------------------------------
BUILDINGS = [
    # id, name, sub, x, y, w, h, floors, type, hp, max_hp
    ("library",    "FULTON LIBRARY",      "INTEL HQ",       2,  1, 5, 3, 4, "intel",    940, 1000),
    ("engineering","ENGINEERING CENTER",  "TECH FACILITY",  19, 2, 4, 3, 5, "tech",     750,  800),
    ("sorensen",   "SORENSEN CENTER",     "COMMAND HQ",     2,  9, 3, 5, 3, "command", 1500, 1500),
    ("business",   "WOODBURY BUSINESS",   "ECON HUB",       22, 9, 3, 5, 3, "resource", 580,  600),
    ("losee",      "LOSEE CENTER",        "BARRACKS",       8, 18, 6, 3, 2, "barracks", 700,  700),
    ("admin",      "ADMINISTRATION",      "CMD ANNEX",      15,18, 5, 3, 3, "command",  820,  900),
    ("clock",      "CLOCK TOWER",         "SENSOR ARRAY",   13,11, 2, 2, 9, "sensor",   380,  400),
    ("parking_n",  "NORTH PARKING",       "VEHICLE DEPOT",  8,  1, 4, 2, 1, "depot",    200,  200),
]

# Kirk's rally point — center of the quad, where the assassination happens
KIRK_RALLY = (13.5, 12.0)

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
