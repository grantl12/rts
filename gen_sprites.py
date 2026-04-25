#!/usr/bin/env python3
"""
Generate pixel art unit sprite sheets for THE DEEP STATE RTS.
Spec: 32x32 per frame, horizontal atlas, nearest-neighbour / 1-bit alpha.
Atlas order per unit: IDLE(4) | MOVE(6) | ATTACK(4) | PANIC(2)
Civilian adds:        RECORDING(2)  → 18 total frames
"""

from PIL import Image
import os

OUT = r"D:\Users\grant\Documents\RTS\client\assets\sprites\units"
SZ = 32
T = (0, 0, 0, 0)

# ── palettes ─────────────────────────────────────────────────────────────────
SKIN = (224, 172, 120, 255)
EYE  = (38,  38,  38,  255)
BROW = (100, 70,  45,  255)

# Regency – Blues · Tans · Greys
RB  = (72,  108, 160, 255)   # uniform blue
RBD = (45,  65,  105, 255)   # dark blue (boots, detail)
RT  = (188, 158, 108, 255)   # hat tan
RTD = (148, 118, 72,  255)   # dark tan (brim shadow)
RG  = (148, 152, 158, 255)   # grey pants
RGL = (190, 195, 200, 255)   # light grey accent
WND = (140, 200, 255, 255)   # audit-wand glow

# MAGA – Red · White · Blue · Camo
MR  = (195, 30,  30,  255)   # red cap
MRD = (140, 18,  18,  255)   # shadow
MC1 = (100, 110, 80,  255)   # camo light
MC2 = (68,  78,  52,  255)   # camo mid
MC3 = (55,  50,  40,  255)   # camo dark
MJ  = (55,  85,  150, 255)   # jeans
MJD = (35,  60,  110, 255)   # dark jeans
MFG = (240, 210, 55,  255)   # flare glow
MFR = (220, 80,  30,  255)   # flare body

# Sovereign – Purples · Dark Greys · Neon
SH  = (55,  35,  80,  255)   # hood
SHD = (30,  15,  50,  255)   # hood shadow
SG  = (52,  52,  62,  255)   # body grey
SGD = (32,  32,  42,  255)   # dark grey
SN  = (185, 80,  255, 255)   # neon
SNL = (220, 155, 255, 255)   # neon light

# Oligarchy – Reds · Blacks · Gold
OB  = (28,  22,  22,  255)   # black armor
OBD = (12,  8,   8,   255)   # very dark
OR  = (178, 28,  28,  255)   # red trim
OG  = (205, 168, 38,  255)   # gold
OGL = (238, 208, 88,  255)   # light gold

# Civilian – Greys · Muted Browns
CG  = (128, 122, 116, 255)   # grey shirt
CGL = (175, 170, 162, 255)   # light grey
CB  = (148, 102, 68,  255)   # brown pants
CBL = (188, 145, 102, 255)   # light brown
CP  = (48,  48,  72,  255)   # phone body
CS  = (80,  215, 100, 255)   # screen green
CRD = (225, 48,  48,  255)   # recording red

# ── primitives ────────────────────────────────────────────────────────────────
def new():
    return Image.new("RGBA", (SZ, SZ), T)

def r(img, x, y, w, h, c):
    px = img.load()
    for dy in range(h):
        for dx in range(w):
            nx, ny = x + dx, y + dy
            if 0 <= nx < SZ and 0 <= ny < SZ:
                px[nx, ny] = c

def p(img, x, y, c):
    if 0 <= x < SZ and 0 <= y < SZ:
        img.putpixel((x, y), c)

def sheet(frames):
    s = Image.new("RGBA", (SZ * len(frames), SZ), T)
    for i, f in enumerate(frames):
        s.paste(f, (i * SZ, 0))
    return s

# ── shared body parts ─────────────────────────────────────────────────────────
# Standard layout (neutral/idle):
#   Headgear   y=4-8
#   Head       y=9-13  x=12-19
#   Torso      y=14-20 x=11-20
#   Arms       y=14-19 x=8-10 (L)  x=21-23 (R)
#   Legs       y=21-26 x=11-14(L)  x=16-19(R)
#   Feet       y=26-28 x=10-14(L)  x=15-19(R)

def base_head(img, skin=SKIN, eye=EYE, ey=11):
    r(img, 12, 9,  8, 5, skin)
    p(img, 14, ey, eye)
    p(img, 17, ey, eye)

def base_torso(img, col, arm_col=None):
    ac = arm_col if arm_col else col
    r(img, 11, 14, 10, 7, col)
    r(img, 8,  14, 3,  6, ac)  # L arm
    r(img, 21, 14, 3,  6, ac)  # R arm

def base_legs(img, leg, boot, lo=0, ro=0):
    """lo/ro = y-offset for left/right foot (walk cycle)."""
    r(img, 11, 21, 4, 6, leg)
    r(img, 16, 21, 4, 6, leg)
    r(img, 10, 26 + lo, 5, 2, boot)
    r(img, 15, 26 + ro, 5, 2, boot)

def wide_brim_hat(img, crown, brim, hy=0):
    r(img, 13, 4+hy, 6, 5, crown)
    r(img,  8, 8+hy, 16, 2, brim)

def cap(img, col, shadow, hy=0):
    r(img, 12, 5+hy, 8, 4, col)
    r(img, 19, 8+hy, 4, 1, shadow)  # visor underside
    r(img, 18, 7+hy, 6, 2, shadow)  # visor

def hood(img, col, shadow, hy=0):
    r(img, 10, 5+hy, 12, 9, col)  # hood volume
    r(img, 13, 9+hy, 6,  5, SKIN) # face aperture
    r(img, 10, 12+hy, 3, 2, shadow) # shadow under chin L
    r(img, 19, 12+hy, 3, 2, shadow) # shadow under chin R

def armor_helm(img, col, shadow, visor, hy=0):
    r(img, 11, 5+hy, 10, 7, col)   # helmet shell
    r(img, 12, 10+hy, 8, 2, visor)  # visor slit
    p(img, 20, 8+hy, OG)            # monocle-HUD dot
    p(img, 20, 9+hy, OG)
    r(img, 11, 5+hy, 2,  7, shadow) # left edge shadow

# ── PARK RANGER ───────────────────────────────────────────────────────────────
def ranger_base(img, hy=0, ey=11, lo=0, ro=0, arm_dy=0, panic_dx=0):
    ox = panic_dx
    wide_brim_hat(img, RT, RTD, hy)
    base_head(img, SKIN, EYE, ey)
    # uniform
    base_torso(img, RB)
    # badge on chest
    p(img, 13, 16, RGL)
    p(img, 14, 16, RGL)
    # clipboard in R hand
    r(img, 21+ox, 13+arm_dy, 4, 6, RT)
    p(img, 22+ox, 12+arm_dy, RG)
    p(img, 23+ox, 12+arm_dy, RG)
    r(img, 22+ox, 15+arm_dy, 2, 1, RTD)
    r(img, 22+ox, 17+arm_dy, 2, 1, RTD)
    # audit wand in L hand
    r(img, 6+ox, 12+arm_dy, 2, 8, RBD)
    p(img, 7+ox, 11+arm_dy, WND)
    p(img, 6+ox, 11+arm_dy, WND)
    # legs + boots
    base_legs(img, RG, RBD, lo, ro)

def make_ranger():
    frames = []
    # IDLE (4): head bob
    for hd in [0, 1, 0, -1]:
        f = new()
        ranger_base(f, hy=hd, ey=11+hd)
        frames.append(f)
    # MOVE (6): leg cycle
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new()
        ranger_base(f, lo=lo, ro=ro)
        frames.append(f)
    # ATTACK (4): clipboard raised
    for ad in [-3, -4, -3, -1]:
        f = new()
        ranger_base(f, arm_dy=ad)
        frames.append(f)
    # PANIC (2): shake
    for dx in [-1, 1]:
        f = new()
        ranger_base(f, panic_dx=dx)
        frames.append(f)
    return sheet(frames)

# ── MAGA PATRIOT ──────────────────────────────────────────────────────────────
def maga_base(img, hy=0, ey=11, lo=0, ro=0, arm_dy=0, panic_dx=0):
    ox = panic_dx
    cap(img, MR, MRD, hy)
    base_head(img, SKIN, EYE, ey)
    # camo tactical vest over torso
    r(img, 11, 14, 10, 7, MC1)
    # camo splotch pattern
    r(img, 11, 14, 3, 3, MC2)
    r(img, 17, 15, 4, 2, MC3)
    r(img, 13, 18, 3, 3, MC2)
    r(img, 18, 18, 3, 3, MC3)
    # arms (sleeves, camo)
    r(img, 8,  14, 3, 6, MC2)
    r(img, 21, 14, 3, 6, MC2)
    # flare in R hand
    r(img, 21+ox, 15+arm_dy, 2, 6, MFR)
    p(img, 21+ox, 14+arm_dy, MFG)
    p(img, 22+ox, 14+arm_dy, MFG)
    p(img, 21+ox, 13+arm_dy, (255, 240, 180, 180))  # glow aura
    # jeans
    r(img, 11, 21, 4, 6, MJ)
    r(img, 16, 21, 4, 6, MJ)
    # denim shadow on inner leg
    p(img, 14, 22, MJD)
    p(img, 14, 23, MJD)
    p(img, 16, 22, MJD)
    p(img, 16, 23, MJD)
    # boots
    r(img, 10, 26+lo, 5, 2, MC3)
    r(img, 15, 26+ro, 5, 2, MC3)

def make_maga():
    frames = []
    for hd in [0, 1, 0, -1]:
        f = new(); maga_base(f, hy=hd, ey=11+hd); frames.append(f)
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new(); maga_base(f, lo=lo, ro=ro); frames.append(f)
    for ad in [-3, -5, -3, -1]:
        f = new(); maga_base(f, arm_dy=ad); frames.append(f)
    for dx in [-1, 1]:
        f = new(); maga_base(f, panic_dx=dx); frames.append(f)
    return sheet(frames)

# ── PROXY ─────────────────────────────────────────────────────────────────────
def proxy_base(img, hy=0, lo=0, ro=0, arm_dy=0, panic_dx=0):
    ox = panic_dx
    hood(img, SH, SHD, hy)
    # goggles over face aperture
    r(img, 13, 9+hy, 3, 2, SN)
    r(img, 17, 9+hy, 3, 2, SN)
    p(img, 14, 9+hy, SNL)  # goggle lens bright
    p(img, 18, 9+hy, SNL)
    # body
    r(img, 11, 14, 10, 7, SG)
    # neon trim lines
    r(img, 11, 14, 1, 7, SN)
    r(img, 20, 14, 1, 7, SN)
    # arms
    r(img, 8,  14, 3, 6, SGD)
    r(img, 21, 14, 3, 6, SGD)
    # neon arm trim
    p(img, 8,  14, SN); p(img, 8, 15, SN)
    p(img, 23, 14, SN); p(img, 23, 15, SN)
    # sabotage kit in R hand (glowing device)
    r(img, 21+ox, 14+arm_dy, 4, 5, SGD)
    p(img, 21+ox, 14+arm_dy, SN)
    p(img, 24+ox, 14+arm_dy, SN)
    p(img, 24+ox, 18+arm_dy, SNL)
    p(img, 21+ox, 18+arm_dy, SNL)
    p(img, 22+ox, 16+arm_dy, SN)  # blinking indicator
    # dark pants
    r(img, 11, 21, 4, 6, SGD)
    r(img, 16, 21, 4, 6, SGD)
    # neon piping on legs
    p(img, 11, 21, SN); p(img, 11, 22, SN)
    p(img, 19, 21, SN); p(img, 19, 22, SN)
    # boots
    r(img, 10, 26+lo, 5, 2, SHD)
    r(img, 15, 26+ro, 5, 2, SHD)

def make_proxy():
    frames = []
    for hd in [0, 1, 0, -1]:
        f = new(); proxy_base(f, hy=hd); frames.append(f)
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new(); proxy_base(f, lo=lo, ro=ro); frames.append(f)
    for ad in [-3, -5, -3, -1]:
        f = new(); proxy_base(f, arm_dy=ad); frames.append(f)
    for dx in [-1, 1]:
        f = new(); proxy_base(f, panic_dx=dx); frames.append(f)
    return sheet(frames)

# ── CONTRACTOR ────────────────────────────────────────────────────────────────
def contractor_base(img, hy=0, lo=0, ro=0, arm_dy=0, panic_dx=0):
    ox = panic_dx
    armor_helm(img, OB, OBD, OBD, hy)
    # armor shoulder pads
    r(img, 8,  13, 4, 3, OB)
    r(img, 20, 13, 4, 3, OB)
    p(img, 8,  13, OR); p(img, 11, 13, OR)  # red trim
    p(img, 20, 13, OR); p(img, 23, 13, OR)
    # torso armor
    r(img, 11, 14, 10, 7, OB)
    # red chest stripe
    r(img, 15, 14, 2, 7, OR)
    # gold detail
    p(img, 15, 14, OG); p(img, 16, 14, OG)
    p(img, 15, 20, OG); p(img, 16, 20, OG)
    # arms (thick armor)
    r(img, 8,  14, 3, 6, OBD)
    r(img, 21, 14, 3, 6, OBD)
    p(img, 8,  16, OR); p(img, 23, 16, OR)  # arm stripe
    # heavy rifle: stock behind body L, barrel extends R
    r(img, 5+ox, 16+arm_dy, 6, 2, OB)    # stock/body
    r(img, 21+ox, 15+arm_dy, 6, 2, OBD)  # barrel
    p(img, 26+ox, 14+arm_dy, OBD)         # scope
    p(img, 26+ox, 15+arm_dy, OBD)
    p(img, 21+ox, 16+arm_dy, OG)          # gold grip accent
    # armored pants
    r(img, 11, 21, 4, 6, OB)
    r(img, 16, 21, 4, 6, OB)
    p(img, 12, 21, OR); p(img, 13, 21, OR)
    p(img, 17, 21, OR); p(img, 18, 21, OR)
    # boots
    r(img, 10, 26+lo, 5, 2, OBD)
    r(img, 15, 26+ro, 5, 2, OBD)

def make_contractor():
    frames = []
    for hd in [0, 0, 1, 0]:
        f = new(); contractor_base(f, hy=hd); frames.append(f)
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new(); contractor_base(f, lo=lo, ro=ro); frames.append(f)
    for ad in [-2, -4, -2, 0]:
        f = new(); contractor_base(f, arm_dy=ad); frames.append(f)
    for dx in [-1, 1]:
        f = new(); contractor_base(f, panic_dx=dx); frames.append(f)
    return sheet(frames)

# ── CIVILIAN ──────────────────────────────────────────────────────────────────
def civilian_base(img, hy=0, ey=11, lo=0, ro=0, phone=False, recording=False, panic_dx=0):
    ox = panic_dx
    # no headgear – just messy hair
    r(img, 12, 6+hy, 8, 4, BROW)      # hair
    p(img, 11, 7+hy, BROW)
    p(img, 20, 7+hy, BROW)
    r(img, 11, 8+hy, 2, 2, BROW)      # sideburn L
    r(img, 19, 8+hy, 2, 2, BROW)      # sideburn R
    base_head(img, SKIN, EYE, ey)
    # casual shirt (grey)
    r(img, 11, 14, 10, 7, CG)
    # collar detail
    p(img, 15, 14, CGL); p(img, 16, 14, CGL)
    # arms
    r(img, 8,  14, 3, 6, CG)
    r(img, 21, 14, 3, 6, CG)
    if phone:
        sc = CRD if recording else CS
        r(img, 21+ox, 12, 3, 6, CP)   # phone body
        r(img, 21+ox, 13, 3, 4, sc)   # screen
        if recording:
            p(img, 22+ox, 13, (255, 100, 100, 255))  # rec dot
    # brown pants
    r(img, 11, 21, 4, 6, CB)
    r(img, 16, 21, 4, 6, CB)
    p(img, 14, 21, CBL); p(img, 14, 22, CBL)
    p(img, 16, 21, CBL); p(img, 16, 22, CBL)
    # shoes
    r(img, 10, 26+lo, 5, 2, (70, 55, 40, 255))
    r(img, 15, 26+ro, 5, 2, (70, 55, 40, 255))

def make_civilian():
    frames = []
    # IDLE
    for hd in [0, 1, 0, -1]:
        f = new(); civilian_base(f, hy=hd, ey=11+hd); frames.append(f)
    # MOVE
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new(); civilian_base(f, lo=lo, ro=ro); frames.append(f)
    # ATTACK – raise phone (citizen journalism moment)
    for ph_raise in [True, True, True, True]:
        f = new(); civilian_base(f, phone=ph_raise); frames.append(f)
    # PANIC
    for dx in [-1, 1]:
        f = new(); civilian_base(f, panic_dx=dx); frames.append(f)
    # RECORDING (2 extra)
    for blink in [False, True]:
        f = new(); civilian_base(f, phone=True, recording=not blink); frames.append(f)
    return sheet(frames)

# ── ICE AGENT ─────────────────────────────────────────────────────────────────
# Dark navy tactical uniform, ballistic cap w/ visor, ICE chest patch,
# flex-cuffs / tether device in R hand.  Shares Regency blue/grey palette
# but pushed darker – deliberate contrast against the Ranger's tan hat.
IN  = (32,  52,  88,  255)   # ICE navy
IND = (18,  30,  58,  255)   # dark navy (shadow, boots)
ING = (55,  72,  100, 255)   # mid navy (vest highlight)
IW  = (235, 235, 235, 255)   # ICE white lettering
ICF = (200, 195, 190, 255)   # flex-cuff silver
ICFD= (150, 145, 140, 255)   # cuff shadow

def ice_cap(img, hy=0):
    r(img, 12, 5+hy, 8, 4, IN)          # cap body
    r(img, 18, 7+hy, 6, 2, IND)         # visor
    p(img, 19, 8+hy, ING)               # visor highlight

def ice_base(img, hy=0, ey=11, lo=0, ro=0, arm_dy=0, panic_dx=0):
    ox = panic_dx
    ice_cap(img, hy)
    # head
    r(img, 12, 9+hy, 8, 5, SKIN)
    p(img, 14, 11+hy, EYE)
    p(img, 17, 11+hy, EYE)
    # balaclava / neck cover (dark)
    r(img, 12, 13+hy, 8, 1, IND)
    # tactical vest over torso
    r(img, 11, 14, 10, 7, IN)
    r(img, 11, 14, 10, 2, ING)          # vest shoulder yoke highlight
    # ICE chest patch: 3×2 white pixels
    r(img, 14, 16, 4, 2, IW)
    p(img, 14, 16, IND); p(img, 17, 16, IND)  # "I·C·E" pixel letters
    p(img, 15, 16, IW);  p(img, 16, 16, IW)
    # utility belt
    r(img, 11, 20, 10, 1, IND)
    p(img, 12, 20, ICF); p(img, 14, 20, ICF); p(img, 17, 20, ICF)
    # arms (heavy sleeves)
    r(img, 8,  14, 3, 6, IN)
    r(img, 21, 14, 3, 6, IN)
    p(img, 8,  14, ING); p(img, 8, 15, ING)   # shoulder seam
    p(img, 23, 14, ING); p(img, 23, 15, ING)
    # flex-cuffs in R hand
    r(img, 21+ox, 14+arm_dy, 4, 3, ICF)
    r(img, 22+ox, 15+arm_dy, 2, 2, ICFD)      # cuff loop shadow
    p(img, 21+ox, 16+arm_dy, ICF)
    p(img, 24+ox, 16+arm_dy, ICF)
    # dark tactical pants
    r(img, 11, 21, 4, 6, IND)
    r(img, 16, 21, 4, 6, IND)
    p(img, 11, 21, IN); p(img, 19, 21, IN)    # seam highlight
    # boots
    r(img, 10, 26+lo, 5, 2, IND)
    r(img, 15, 26+ro, 5, 2, IND)

def make_ice_agent():
    frames = []
    for hd in [0, 1, 0, -1]:
        f = new(); ice_base(f, hy=hd, ey=11+hd); frames.append(f)
    leg_cycle = [(0,2),(1,2),(2,0),(2,0),(2,1),(2,0)]
    for lo, ro in leg_cycle:
        f = new(); ice_base(f, lo=lo, ro=ro); frames.append(f)
    for ad in [-3, -5, -3, -1]:
        f = new(); ice_base(f, arm_dy=ad); frames.append(f)
    for dx in [-1, 1]:
        f = new(); ice_base(f, panic_dx=dx); frames.append(f)
    return sheet(frames)

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    units = {
        "park_ranger":  make_ranger,
        "ice_agent":    make_ice_agent,
        "maga_patriot": make_maga,
        "proxy":        make_proxy,
        "contractor":   make_contractor,
        "civilian":     make_civilian,
    }

    for name, fn in units.items():
        img = fn()
        path = os.path.join(OUT, f"{name}.png")
        img.save(path)
        frames = img.width // SZ
        print(f"  OK  {name}.png  {img.width}x{img.height}  ({frames} frames)")

    print(f"\nAll sprites saved to {OUT}")
