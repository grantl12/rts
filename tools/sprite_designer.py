"""
Sprite Designer — Deep State RTS
Procedural unit sprite viewer/exporter.
Run directly: python tools/sprite_designer.py

Controls:
  LEFT/RIGHT arrows — cycle unit
  UP/DOWN arrows    — cycle facing direction (SW / SE / NE / NW)
  S                 — save current facing as PNG to assets/sprites/
  A                 — save all 4 directions as PNG strip
"""
import os, sys, math
import pygame

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Palette ───────────────────────────────────────────────────────────────────
class Pal:
    # Shared
    SKIN      = (200, 160,  96)
    DARK      = (  6,  13,  10)
    NEON_TEAL = (  0, 255, 204)
    NEON_ORG  = (255, 102,   0)
    BLACK     = ( 20,  18,  16)

    # Gravy Seal (camo/MAGA militia)
    GS_HELM_HI  = (122,  96,  64)
    GS_HELM_MID = ( 90,  72,  48)
    GS_HELM_SHD = ( 60,  48,  32)
    GS_VISOR    = (  0,  26,  20)
    GS_ARMOR_HI = (106,  80,  48)
    GS_ARMOR_MID= ( 74,  56,  32)
    GS_ARMOR_SHD= ( 46,  34,  18)
    GS_PANTS_HI = ( 74,  64,  48)
    GS_PANTS_MID= ( 52,  48,  40)
    GS_BOOT     = ( 24,  20,  16)
    GS_WEAPON   = ( 37,  37,  32)

    # ICE Agent (all-white tactical, face hidden)
    ICE_SUIT_HI  = (230, 230, 225)
    ICE_SUIT_MID = (200, 200, 195)
    ICE_SUIT_SHD = (155, 155, 150)
    ICE_VISOR    = ( 18,  18,  16)   # dark face shield
    ICE_BOOT     = (120, 120, 115)
    ICE_BADGE    = (220, 180,  20)   # gold ICE patch
    ICE_WEAPON   = ( 50,  50,  48)

    # Protester
    PR_HOODIE_HI = (106, 128, 112)
    PR_HOODIE_MID= ( 80,  96,  84)
    PR_HOODIE_SHD= ( 56,  72,  60)
    PR_JEANS     = ( 58,  88, 138)
    PR_SHOE      = (200, 190, 175)
    PR_SIGN_BG   = (208, 180, 110)
    PR_SIGN_INK  = ( 88,  48,  16)
    PR_BEANIE    = (192,  48,  48)
    PR_HAIR      = ( 58,  40,  16)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def rr(surf, x, y, w, h, col, radius=2):
    """Filled rounded rect."""
    pygame.draw.rect(surf, col, (x, y, w, h), border_radius=radius)

def circle(surf, cx, cy, r, col):
    pygame.draw.circle(surf, col, (int(cx), int(cy)), int(r))

def line(surf, x1, y1, x2, y2, col, w=1):
    pygame.draw.line(surf, col, (int(x1), int(y1)), (int(x2), int(y2)), w)


# ── Unit draw functions (48×56 native, scale= pixel multiplier) ──────────────

def draw_gravy_seal(surf, x0, y0, sc=1, facing=0, t=0):
    """
    Gravy Seal — camo tactical operator, glowing teal visor.
    facing: 0=SW 1=SE 2=NE 3=NW
    """
    bob = int(math.sin(t * 0.05) * 1.2 * sc)
    flip = facing in (1, 2)

    s = lambda v: int(v * sc)

    # Work on a temp surface, flip if needed
    tmp = pygame.Surface((s(48), s(56)), pygame.SRCALPHA)

    def Y(v): return s(v) + bob

    # Shadow
    circle(tmp, s(24), Y(54), s(10), (0, 0, 0, 90))

    # Back boot
    rr(tmp, s(26), Y(45), s(10), s(6), Pal.GS_BOOT)

    # Back leg
    rr(tmp, s(25), Y(35), s(9), s(12), Pal.GS_PANTS_SHD if hasattr(Pal,'GS_PANTS_SHD') else Pal.GS_PANTS_MID)

    # Back arm
    rr(tmp, s(34), Y(24), s(7), s(13), Pal.GS_ARMOR_SHD)

    # Torso
    pts = [(s(11),Y(24)),(s(37),Y(23)),(s(38),Y(39)),(s(10),Y(40))]
    pygame.draw.polygon(tmp, Pal.GS_ARMOR_MID, pts)
    pts2 = [(s(14),Y(26)),(s(34),Y(25)),(s(34),Y(37)),(s(14),Y(38))]
    pygame.draw.polygon(tmp, Pal.GS_ARMOR_HI, pts2)

    # Chest neon edge
    line(tmp, s(14),Y(26), s(34),Y(25), Pal.NEON_TEAL, max(1,s(1)))
    line(tmp, s(11),Y(24), s(11),Y(36), Pal.NEON_TEAL, max(1,s(1)))
    # Belt
    rr(tmp, s(10),Y(37), s(28),s(3), Pal.GS_ARMOR_SHD)
    rr(tmp, s(21),Y(37), s(6), s(2),  Pal.GS_WEAPON, 1)
    pygame.draw.rect(tmp, Pal.NEON_TEAL, (s(21),Y(37),s(6),s(2)), 1)

    # Front arm
    rr(tmp, s(5), Y(22), s(7), s(14), Pal.GS_ARMOR_MID)
    rr(tmp, s(5), Y(22), s(3), s(14), Pal.GS_ARMOR_HI)
    rr(tmp, s(4), Y(30), s(9), s(4),  Pal.GS_ARMOR_HI)

    # Weapon (SMG)
    rr(tmp, s(-2),Y(28), s(18),s(5), Pal.GS_WEAPON, 1)
    rr(tmp, s(-2),Y(28), s(14),s(2), (55,55,50), 1)
    rr(tmp, s(5), Y(33), s(4), s(6),  Pal.GS_WEAPON, 1)
    pygame.draw.rect(tmp, (48,48,44), (s(-6),Y(30),s(6),s(2)))
    # Muzzle flash
    circle(tmp, s(-7), Y(31), s(3), (*Pal.NEON_ORG, 200))
    # Scope
    pygame.draw.rect(tmp, Pal.NEON_TEAL, (s(3),Y(28),s(5),s(2)))

    # Front boot + leg
    rr(tmp, s(13),Y(47), s(11),s(7), (32,26,20), 2)
    rr(tmp, s(14),Y(37), s(9), s(12), Pal.GS_PANTS_MID)
    rr(tmp, s(13),Y(43), s(10),s(5),  Pal.GS_PANTS_HI)
    pygame.draw.rect(tmp, (*Pal.NEON_TEAL, 100), (s(13),Y(43),s(10),s(1)))

    # Neck
    pygame.draw.rect(tmp, Pal.SKIN, (s(20),Y(16),s(7),s(7)))

    # Helmet dome
    pygame.draw.ellipse(tmp, Pal.GS_HELM_MID,
        (s(11), Y(4), s(26), s(14)))
    pygame.draw.ellipse(tmp, Pal.GS_HELM_HI,
        (s(14), Y(4), s(16), s(9)))
    # Helm brim
    rr(tmp, s(11),Y(16), s(26),s(5), Pal.GS_HELM_SHD, 2)
    # Visor
    rr(tmp, s(12),Y(16), s(23),s(6), Pal.GS_VISOR, 2)
    # Visor glow
    scan_y = Y(17) + int((t * 2) % (s(4)))
    pygame.draw.rect(tmp, (*Pal.NEON_TEAL, 200), (s(13),Y(17),s(21),s(4)))
    pygame.draw.rect(tmp, (*Pal.NEON_TEAL, 255), (s(13), scan_y, s(21), max(1,s(1))))
    # Neon helm band
    line(tmp, s(12),Y(15), s(35),Y(15), (*Pal.NEON_TEAL, 180), max(1,s(1)))
    # Antenna
    line(tmp, s(33),Y(8), s(36),Y(1), (*Pal.NEON_TEAL, 180), max(1,s(1)))
    circle(tmp, s(36), Y(1), s(2), Pal.NEON_ORG)

    if flip:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (x0, y0))


def draw_ice_agent(surf, x0, y0, sc=1, facing=0, t=0):
    """
    ICE Agent — all-white tactical suit, dark face shield (face fully hidden).
    """
    bob = int(math.sin(t * 0.05 + 1) * sc)
    flip = facing in (1, 2)
    s = lambda v: int(v * sc)
    tmp = pygame.Surface((s(48), s(56)), pygame.SRCALPHA)
    def Y(v): return s(v) + bob

    # Shadow
    circle(tmp, s(24), Y(54), s(9), (0,0,0,80))

    # Boots (grey-white)
    rr(tmp, s(27),Y(46), s(9),s(6), Pal.ICE_BOOT)
    rr(tmp, s(15),Y(47), s(9),s(6), Pal.ICE_BOOT)
    # Boot laces
    for i in range(3):
        line(tmp, s(16),Y(47.5+i*1.5), s(23),Y(47.5+i*1.5), (180,180,170), 1)

    # Pants
    rr(tmp, s(26),Y(34), s(9),s(14), Pal.ICE_SUIT_SHD)
    rr(tmp, s(15),Y(34), s(9),s(15), Pal.ICE_SUIT_MID)
    # Knee pads
    rr(tmp, s(26),Y(42), s(9),s(5), Pal.ICE_SUIT_SHD, 1)
    rr(tmp, s(15),Y(42), s(9),s(5), Pal.ICE_SUIT_SHD, 1)

    # Body armor
    rr(tmp, s(11),Y(20), s(27),s(16), Pal.ICE_SUIT_MID, 3)
    rr(tmp, s(10),Y(20), s(28),s(14), Pal.ICE_SUIT_SHD, 2)
    # Front plate
    rr(tmp, s(13),Y(22), s(22),s(12), Pal.ICE_SUIT_MID, 2)
    # ICE badge (gold)
    pygame.draw.rect(tmp, Pal.ICE_BADGE, (s(17),Y(25),s(14),s(5)))
    f = pygame.font.SysFont("couriernew", max(6, s(5)), bold=True)
    lbl = f.render("ICE", True, (30, 30, 30))
    tmp.blit(lbl, (s(20), Y(25)))
    # Belt + zip-ties
    pygame.draw.rect(tmp, Pal.ICE_SUIT_SHD, (s(10),Y(33),s(28),s(3)))
    for i in range(3):
        line(tmp, s(16+i*4),Y(36), s(16+i*4),Y(40), (220,220,180,180), max(1,s(1)))
        rr(tmp, s(15+i*4),Y(39), s(2),s(2), (220,220,180))

    # Arms
    rr(tmp, s(35),Y(22), s(6),s(13), Pal.ICE_SUIT_SHD)
    rr(tmp, s(7), Y(22), s(6),s(13), Pal.ICE_SUIT_MID)
    # Gloves (dark)
    rr(tmp, s(35),Y(32), s(6),s(5), (50,50,48), 2)
    rr(tmp, s(7), Y(32), s(6),s(5), (50,50,48), 2)

    # Baton
    rr(tmp, s(2), Y(30), s(8),s(3), (42,42,40), 1)
    rr(tmp, s(-1),Y(30), s(3),s(3), (26,26,24), 1)
    # Electric tip
    circle(tmp, s(-1), Y(31), s(2), (80,120,255,230))
    circle(tmp, s(-1), Y(31), s(4), (80,120,255,60))

    # Neck
    pygame.draw.rect(tmp, Pal.ICE_SUIT_SHD, (s(21),Y(16),s(7),s(6)))

    # Helmet (white)
    pygame.draw.ellipse(tmp, Pal.ICE_SUIT_MID, (s(11),Y(6),s(26),s(14)))
    pygame.draw.ellipse(tmp, Pal.ICE_SUIT_HI,  (s(14),Y(6),s(16),s(9)))
    # Balaclava face — FULLY HIDDEN, no skin visible
    rr(tmp, s(15),Y(12), s(18),s(8), (26,26,24), 3)
    # Dark face shield
    rr(tmp, s(14),Y(12), s(20),s(7), Pal.ICE_VISOR, 2)
    # NVG mount
    rr(tmp, s(22),Y(5), s(8),s(4), (38,38,36), 1)
    circle(tmp, s(26), Y(7), s(3), (200,220,80,200))
    circle(tmp, s(26), Y(7), s(5), (200,220,80,50))
    # Helm strap
    line(tmp, s(15),Y(12), s(17),Y(17), Pal.ICE_SUIT_SHD, max(1,s(1)))

    if flip:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (x0, y0))


SIGN_TEXTS = [
    ["THEY LIVE", "WE SLEEP"],
    ["NO KINGS", "NO MASTERS"],
    ["AUDIT THIS"],
    ["§ = COMPLIANCE"],
    ["KIRK WAS", "RIGHT"],
    ["DEFUND THE", "DEEP STATE"],
]


def draw_protester(surf, x0, y0, sc=1, facing=0, t=0, sign_idx=0):
    """
    Protester — hoodie, raised sign. sign_idx cycles sign text.
    """
    bob  = int(math.sin(t * 0.05 + 2) * 0.7 * sc)
    wave = int(math.sin(t * 0.08) * 1.5 * sc)
    flip = facing in (1, 2)
    s = lambda v: int(v * sc)
    tmp = pygame.Surface((s(48), s(56)), pygame.SRCALPHA)
    def Y(v): return s(v) + bob

    # Shadow
    circle(tmp, s(24), Y(54), s(8), (0,0,0,80))

    # Shoes
    rr(tmp, s(26),Y(47), s(9),s(6), Pal.PR_SHOE)
    rr(tmp, s(14),Y(48), s(9),s(6), Pal.PR_SHOE)
    pygame.draw.rect(tmp, (120,115,105), (s(26),Y(51),s(9),s(2)))
    pygame.draw.rect(tmp, (120,115,105), (s(14),Y(52),s(9),s(2)))

    # Jeans
    rr(tmp, s(25),Y(34), s(9),s(15), Pal.PR_JEANS)
    rr(tmp, s(14),Y(34), s(9),s(16), (74,110,158))

    # Hoodie body
    rr(tmp, s(10),Y(19), s(28),s(17), Pal.PR_HOODIE_MID, 3)
    rr(tmp, s(16),Y(28), s(16),s(6),  Pal.PR_HOODIE_SHD, 2)  # pocket
    # Belt/waist
    pygame.draw.rect(tmp, (42,40,32), (s(10),Y(33),s(28),s(2)))

    # Sign arm (raised, left side)
    rr(tmp, s(6), Y(18)+wave, s(6),s(14), Pal.PR_HOODIE_MID, 2)
    rr(tmp, s(6), Y(16)+wave, s(6),s(5),  Pal.SKIN, 2)

    # Sign stick
    line(tmp, s(9),Y(3)+wave, s(9),Y(18)+wave, (138,104,64), max(2,s(2)))

    # Sign board
    sign_w, sign_h = s(30), s(14)
    sign_x, sign_y = s(-6), Y(1)+wave
    rr(tmp, sign_x, sign_y, sign_w, sign_h, Pal.PR_SIGN_BG, 1)
    pygame.draw.rect(tmp, (160,130,70), (sign_x,sign_y,sign_w,sign_h), 1)

    lines = SIGN_TEXTS[sign_idx % len(SIGN_TEXTS)]
    sf = pygame.font.SysFont("impact", max(7, s(5)), bold=True)
    for li, txt in enumerate(lines):
        lbl = sf.render(txt, True, Pal.PR_SIGN_INK)
        tmp.blit(lbl, (sign_x + (sign_w - lbl.get_width())//2,
                       sign_y + 2 + li * (sign_h // max(1,len(lines)))))

    # Back arm
    rr(tmp, s(35),Y(21), s(6),s(14), Pal.PR_HOODIE_SHD)
    rr(tmp, s(35),Y(32), s(6),s(5),  Pal.SKIN, 2)

    # Head
    rr(tmp, s(16),Y(9), s(17),s(13), Pal.SKIN, 5)
    # Hair
    rr(tmp, s(17),Y(12), s(5),s(3), Pal.PR_HAIR, 2)

    # Beanie
    pts = [(s(14),Y(13)),(s(34),Y(11)),(s(30),Y(3)),(s(20),Y(1))]
    pygame.draw.polygon(tmp, Pal.PR_BEANIE, pts)
    # Pom pom
    circle(tmp, s(24), Y(2), s(3), (232,64,64))
    # Face
    pygame.draw.ellipse(tmp, (58,40,16), (s(19),Y(13),s(4),s(3)))   # L eye
    pygame.draw.ellipse(tmp, (58,40,16), (s(26),Y(12),s(4),s(3)))   # R eye
    line(tmp, s(20),Y(18), s(27),Y(17), (160,120,80), max(1,s(1)))  # mouth

    # Mask on chin
    rr(tmp, s(18),Y(18), s(13),s(3), (80,80,80,100), 1)

    if flip:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (x0, y0))


# ── Unit registry ──────────────────────────────────────────────────────────────

UNITS = [
    {
        "id":    "gravy_seal",
        "name":  "GRAVY SEAL",
        "class": "MILITIA IRREGULARS",
        "draw":  draw_gravy_seal,
        "native_w": 48, "native_h": 56,
    },
    {
        "id":    "ice_agent",
        "name":  "ICE AGENT",
        "class": "REGENCY ENFORCEMENT",
        "draw":  draw_ice_agent,
        "native_w": 48, "native_h": 56,
    },
    {
        "id":    "protester",
        "name":  "PROTESTER",
        "class": "CIVILIAN RESISTANCE",
        "draw":  draw_protester,
        "native_w": 48, "native_h": 56,
    },
]

DIRS = ["SW", "SE", "NE", "NW"]

# ── Main designer UI ───────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((1100, 720))
    pygame.display.set_caption("SPRITE DESIGNER — DEEP STATE RTS")
    clock  = pygame.time.Clock()

    font_big = pygame.font.SysFont("couriernew", 22, bold=True)
    font_med = pygame.font.SysFont("couriernew", 13, bold=True)
    font_sm  = pygame.font.SysFont("couriernew", 10)

    TEAL  = (0, 255, 204)
    ORANGE= (255, 102, 0)
    DARK  = (6, 13, 10)
    PANEL = (10, 20, 16)
    GREY  = (0, 60, 45)

    unit_idx  = 0
    facing    = 0
    sign_idx  = 0
    t         = 0

    PREVIEW_SCALE = 8   # 48×56 → 384×448

    while True:
        dt = clock.tick(60)
        t += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                elif event.key == pygame.K_LEFT:
                    unit_idx = (unit_idx - 1) % len(UNITS)
                elif event.key == pygame.K_RIGHT:
                    unit_idx = (unit_idx + 1) % len(UNITS)
                elif event.key == pygame.K_UP:
                    facing = (facing - 1) % 4
                elif event.key == pygame.K_DOWN:
                    facing = (facing + 1) % 4
                elif event.key == pygame.K_SPACE:
                    sign_idx = (sign_idx + 1) % len(SIGN_TEXTS)
                elif event.key == pygame.K_s:
                    _save_single(unit_idx, facing, sign_idx, font_sm)
                elif event.key == pygame.K_a:
                    _save_all_dirs(unit_idx, sign_idx)

        screen.fill(DARK)

        u = UNITS[unit_idx]
        pw = u["native_w"] * PREVIEW_SCALE
        ph = u["native_h"] * PREVIEW_SCALE
        px = (screen.get_width() - 540) // 2
        py = (screen.get_height() - ph) // 2 + 20

        # Checker background
        checker = pygame.Surface((pw, ph))
        checker.fill((18, 18, 18))
        for cy in range(0, ph, 14):
            for cx in range(0, pw, 14):
                if (cx // 14 + cy // 14) % 2:
                    pygame.draw.rect(checker, (22, 22, 22), (cx, cy, 14, 14))
        screen.blit(checker, (px, py))

        # Draw unit
        kwargs = {"facing": facing, "t": t}
        if u["id"] == "protester":
            kwargs["sign_idx"] = sign_idx
        u["draw"](screen, px, py, sc=PREVIEW_SCALE, **kwargs)

        # Border
        pygame.draw.rect(screen, GREY, (px - 1, py - 1, pw + 2, ph + 2), 1)

        # Direction grid (4 small previews)
        sm = 3
        grid_x = px + pw + 30
        grid_y = py
        for di, dlbl in enumerate(DIRS):
            gx = grid_x + (di % 2) * (u["native_w"] * sm + 20)
            gy = grid_y + (di // 2) * (u["native_h"] * sm + 30)
            bg = pygame.Surface((u["native_w"]*sm, u["native_h"]*sm))
            bg.fill((16,16,16))
            screen.blit(bg, (gx, gy))
            kw2 = {"facing": di, "t": t}
            if u["id"] == "protester":
                kw2["sign_idx"] = sign_idx
            u["draw"](screen, gx, gy, sc=sm, **kw2)
            border_col = TEAL if di == facing else GREY
            pygame.draw.rect(screen, border_col, (gx-1, gy-1, u["native_w"]*sm+2, u["native_h"]*sm+2), 1)
            dl = font_sm.render(dlbl, True, TEAL if di == facing else (0,60,45))
            screen.blit(dl, (gx + 2, gy + u["native_h"]*sm + 4))

        # Labels
        nl = font_big.render(u["name"],  True, ORANGE)
        cl = font_med.render(u["class"], True, (0, 120, 90))
        screen.blit(nl, (px, py - 40))
        screen.blit(cl, (px, py - 20))

        # Controls hint
        hints = [
            "← → : CYCLE UNIT",
            "↑ ↓ : FACING DIR",
            "SPACE: CYCLE SIGN" if u["id"] == "protester" else "",
            "S : SAVE PNG",
            "A : SAVE ALL DIRS",
        ]
        for hi, ht in enumerate(hints):
            if not ht: continue
            hl = font_sm.render(ht, True, (0, 60, 45))
            screen.blit(hl, (12, 12 + hi * 14))

        # Native size label
        ns = font_sm.render(f"NATIVE {u['native_w']}×{u['native_h']}px · {PREVIEW_SCALE}× PREVIEW", True, (0,60,45))
        screen.blit(ns, (px, py + ph + 8))

        pygame.display.flip()


def _save_single(unit_idx, facing, sign_idx, font=None):
    u = UNITS[unit_idx]
    w, h = u["native_w"], u["native_h"]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    kwargs = {"facing": facing}
    if u["id"] == "protester":
        kwargs["sign_idx"] = sign_idx
    u["draw"](surf, 0, 0, sc=1, **kwargs)
    path = os.path.join(OUT_DIR, f"{u['id']}_{DIRS[facing].lower()}.png")
    pygame.image.save(surf, path)
    print(f"Saved → {path}")


def _save_all_dirs(unit_idx, sign_idx):
    u = UNITS[unit_idx]
    w, h = u["native_w"], u["native_h"]
    strip = pygame.Surface((w * 4, h), pygame.SRCALPHA)
    for di in range(4):
        kwargs = {"facing": di}
        if u["id"] == "protester":
            kwargs["sign_idx"] = sign_idx
        u["draw"](strip, di * w, 0, sc=1, **kwargs)
    path = os.path.join(OUT_DIR, f"{u['id']}_strip.png")
    pygame.image.save(strip, path)
    print(f"Saved strip → {path}")


if __name__ == "__main__":
    main()
