"""
Building Designer — Deep State RTS
Isometric building viewer for all structure types.

Controls:
  LEFT / RIGHT     — cycle buildings within category
  TAB              — cycle category (base / civilian / garrisonable)
  F                — flip view (SW ↔ SE facing)
  S                — export current building as PNG
  A                — export ALL buildings as PNGs
  Mouse wheel      — zoom preview
"""
import os, sys, math, pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from game.building_defs import BUILDINGS, get_by_category

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "buildings")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Colours ────────────────────────────────────────────────────────────────────
TEAL      = (0, 255, 204)
TEAL_DIM  = (0, 80, 60)
ORANGE    = (255, 102, 0)
DARK      = (6, 13, 10)
PANEL     = (10, 20, 16)
BORDER    = (0, 50, 38)
WHITE     = (230, 230, 225)
RED       = (200, 40, 40)
GOLD      = (200, 160, 20)

CATEGORIES = ["base", "civilian", "garrisonable"]
CAT_LABELS = {
    "base":         "BASE BUILDINGS",
    "civilian":     "CIVILIAN / NEUTRAL",
    "garrisonable": "GARRISONABLE STRUCTURES",
}

# ── Isometric drawing engine ───────────────────────────────────────────────────

class IsoBuilder:
    """Renders a single building definition to a pygame Surface."""

    def __init__(self, tile_w=72, tile_h=36, wall_h=22):
        self.TW = tile_w
        self.TH = tile_h
        self.WH = wall_h

    def _pt(self, gx, gy, gz, ox, oy, flip=False):
        tw, th, wh = self.TW, self.TH, self.WH
        if flip:
            sx = ox - (gx - gy) * tw // 2
        else:
            sx = ox + (gx - gy) * tw // 2
        sy = oy + (gx + gy) * th // 2 - int(gz * wh)
        return sx, sy

    def surface_for(self, bdef, scale=1.0, flip=False):
        """Return a transparent Surface with the building drawn on it."""
        tw = int(self.TW * scale)
        th = int(self.TH * scale)
        wh = int(self.WH * scale)

        bw, bh, floors = bdef["w"], bdef["h"], bdef["floors"]
        pal = bdef["palette"]
        roof = bdef.get("roof_style", "flat")
        garr = bdef.get("garrison", 0)

        # Canvas sizing: generous padding
        cw = (bw + bh) * tw + tw * 2
        ch = (bw + bh) * th // 2 + floors * wh + th * 4
        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)

        ox = cw // 2
        oy = ch - th

        iso = IsoBuilder(tw, th, wh)

        def pt(gx, gy, gz):
            return iso._pt(gx, gy, gz, ox, oy, flip)

        # ── Left wall ──────────────────────────────────────────────
        ll = [pt(0,bh,0), pt(bw,bh,0), pt(bw,bh,floors), pt(0,bh,floors)]
        pygame.draw.polygon(surf, pal["wall_l"], ll)

        # Window rows on left wall
        for f in range(1, floors):
            _draw_windows_left(surf, pt, bw, bh, f, pal["window"], wh, th)

        # Garrison embrasures on left wall
        if garr and "garrisonable" in bdef.get("flags", []):
            _draw_embrasures_left(surf, pt, bw, bh, floors, ORANGE)

        # ── Right wall ─────────────────────────────────────────────
        rr = [pt(bw,0,0), pt(bw,bh,0), pt(bw,bh,floors), pt(bw,0,floors)]
        pygame.draw.polygon(surf, pal["wall_r"], rr)

        for f in range(1, floors):
            _draw_windows_right(surf, pt, bw, bh, f, pal["window"])

        if garr and "garrisonable" in bdef.get("flags", []):
            _draw_embrasures_right(surf, pt, bw, bh, floors, ORANGE)

        # ── Top face ───────────────────────────────────────────────
        top = [pt(0,0,floors), pt(bw,0,floors), pt(bw,bh,floors), pt(0,bh,floors)]
        pygame.draw.polygon(surf, pal["top"], top)

        # ── Roof details ───────────────────────────────────────────
        _draw_roof(surf, pt, bw, bh, floors, pal, roof, wh, tw, th)

        # ── Edges ──────────────────────────────────────────────────
        for face in (ll, rr, top):
            pygame.draw.polygon(surf, pal["accent"], face, max(1, int(scale)))

        # Vertical corner lines
        for gx2, gy2 in [(0,bh),(bw,bh),(bw,0)]:
            a = pt(gx2, gy2, 0)
            b = pt(gx2, gy2, floors)
            pygame.draw.line(surf, pal["accent"], a, b, max(1, int(scale)))

        # ── Neon accent strip on top edge (TEAL for all) ───────────
        pygame.draw.polygon(surf, (*TEAL, 60), top, max(1, int(scale)))

        # ── Garrison badge ─────────────────────────────────────────
        if garr:
            mid = pt(bw / 2, bh / 2, floors + 0.5)
            _draw_garrison_badge(surf, mid, garr)

        return surf

    def preview_size(self, bdef, scale):
        tw = int(self.TW * scale)
        th = int(self.TH * scale)
        wh = int(self.WH * scale)
        bw, bh, floors = bdef["w"], bdef["h"], bdef["floors"]
        cw = (bw + bh) * tw + tw * 2
        ch = (bw + bh) * th // 2 + floors * wh + th * 4
        return cw, ch


# ── Window / embrasure helpers ─────────────────────────────────────────────────

def _draw_windows_left(surf, pt, bw, bh, floor, wincol, wh, th):
    """Horizontal window band across left wall at given floor."""
    row_a = pt(0, bh, floor)
    row_b = pt(bw, bh, floor)
    # Draw 2-pixel strip
    pygame.draw.line(surf, (*wincol, 180), row_a, row_b, max(2, wh // 5))


def _draw_windows_right(surf, pt, bw, bh, floor, wincol):
    row_a = pt(bw, 0, floor)
    row_b = pt(bw, bh, floor)
    pygame.draw.line(surf, (*wincol, 180), row_a, row_b, 2)


def _draw_embrasures_left(surf, pt, bw, bh, floors, col):
    """Gun port notches along top of left wall."""
    segs = max(1, bw)
    for i in range(segs):
        x = i / segs * bw
        a = pt(x + 0.2, bh, floors - 0.05)
        b = pt(x + 0.8, bh, floors - 0.05)
        pygame.draw.line(surf, (*col, 200), a, b, 2)


def _draw_embrasures_right(surf, pt, bw, bh, floors, col):
    segs = max(1, bh)
    for i in range(segs):
        y = i / segs * bh
        a = pt(bw, y + 0.2, floors - 0.05)
        b = pt(bw, y + 0.8, floors - 0.05)
        pygame.draw.line(surf, (*col, 200), a, b, 2)


def _draw_roof(surf, pt, bw, bh, floors, pal, style, wh, tw, th):
    """Draw roof details on the top face."""
    cx, cy = pt(bw / 2, bh / 2, floors)

    if style == "antenna":
        base = pt(bw / 2, bh / 2, floors)
        tip  = pt(bw / 2, bh / 2, floors + 1.5)
        pygame.draw.line(surf, TEAL_DIM, base, tip, 2)
        pygame.draw.circle(surf, ORANGE, tip, 4)
        pygame.draw.circle(surf, (*ORANGE, 80), tip, 8)

    elif style == "dish":
        base = pt(bw / 2, bh / 2, floors)
        # Dish arm
        arm  = pt(bw / 2, bh / 2, floors + 0.8)
        pygame.draw.line(surf, TEAL_DIM, base, arm, 2)
        # Dish oval
        pygame.draw.ellipse(surf, (*TEAL_DIM, 180),
            (arm[0] - 12, arm[1] - 6, 24, 12), 2)

    elif style == "tower":
        # Cooling tower / chimney
        top = pt(bw / 2, bh / 2, floors + 1.2)
        pygame.draw.line(surf, (60, 55, 20), pt(bw/2, bh/2, floors), top, 6)
        pygame.draw.circle(surf, (220, 200, 30), top, 4)

    elif style == "spire":
        base = pt(bw / 2, bh / 2, floors)
        tip  = pt(bw / 2, bh / 2, floors + 3)
        pygame.draw.line(surf, pal["accent"], base, tip, 3)
        pygame.draw.circle(surf, TEAL, tip, 5)

    elif style == "gable":
        # Ridge line across the top
        a = pt(0,   bh / 2, floors + 0.5)
        b = pt(bw,  bh / 2, floors + 0.5)
        pygame.draw.line(surf, pal["accent"], a, b, 2)

    elif style == "cross":
        # Medical cross
        a = pt(bw/2 - 0.3, bh/2, floors + 0.1)
        b = pt(bw/2 + 0.3, bh/2, floors + 0.1)
        c = pt(bw/2, bh/2 - 0.3, floors + 0.1)
        d = pt(bw/2, bh/2 + 0.3, floors + 0.1)
        pygame.draw.line(surf, (220, 30, 30), a, b, 4)
        pygame.draw.line(surf, (220, 30, 30), c, d, 4)

    elif style == "awning":
        a = pt(0,   0,  floors + 0.3)
        b = pt(bw,  0,  floors + 0.3)
        c = pt(bw, bh,  floors + 0.3)
        d = pt(0,  bh,  floors + 0.3)
        pygame.draw.polygon(surf, (*pal["accent"], 100), [a, b, c, d])

    elif style == "hangar":
        # Arched roof hint
        a = pt(0,   bh/2, floors)
        b = pt(bw,  bh/2, floors)
        mid = ((a[0]+b[0])//2, min(a[1], b[1]) - 8)
        pygame.draw.lines(surf, pal["accent"], False, [a, mid, b], 2)

    elif style == "crane":
        base = pt(bw - 0.5, 0.5, floors)
        arm  = pt(bw - 0.5, 0.5, floors + 2)
        tip  = pt(bw - 0.5 - 1.5, 0.5, floors + 2)
        cable= pt(bw - 0.5 - 0.8, 0.5 + 0.8, floors + 0.5)
        pygame.draw.line(surf, (80, 80, 70), base, arm, 3)
        pygame.draw.line(surf, (80, 80, 70), arm, tip, 2)
        pygame.draw.line(surf, (60, 60, 55), arm, cable, 1)
        pygame.draw.circle(surf, (90, 90, 80), cable, 3)

    elif style == "tent":
        a = pt(0, 0, floors)
        b = pt(bw, 0, floors)
        c = pt(bw, bh, floors)
        d = pt(0, bh, floors)
        ridge = pt(bw/2, bh/2, floors + 0.8)
        for corner in [a, b, c, d]:
            pygame.draw.line(surf, pal["accent"], ridge, corner, 2)


def _draw_garrison_badge(surf, pos, count):
    """Orange diamond badge showing garrison capacity."""
    x, y = int(pos[0]), int(pos[1])
    size = 10
    pts = [(x, y-size),(x+size,y),(x,y+size),(x-size,y)]
    pygame.draw.polygon(surf, (*ORANGE, 180), pts)
    pygame.draw.polygon(surf, ORANGE, pts, 1)
    f = pygame.font.SysFont("couriernew", 9, bold=True)
    lbl = f.render(str(count), True, DARK)
    surf.blit(lbl, (x - lbl.get_width()//2, y - lbl.get_height()//2))


# ── Main designer ──────────────────────────────────────────────────────────────

def main():
    pygame.init()
    W, H = 1280, 800
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("BUILDING DESIGNER — DEEP STATE RTS")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("couriernew", 20, bold=True)
    font_med = pygame.font.SysFont("couriernew", 13, bold=True)
    font_sm  = pygame.font.SysFont("couriernew", 10)
    font_px  = pygame.font.SysFont("couriernew", 9)

    iso = IsoBuilder()

    cat_idx    = 0
    bld_idx    = 0
    flip       = False
    zoom       = 1.0

    def current_cat():
        return CATEGORIES[cat_idx % len(CATEGORIES)]

    def current_list():
        return list(get_by_category(current_cat()).items())

    def current_bld():
        lst = current_list()
        if not lst: return None, None
        k, v = lst[bld_idx % len(lst)]
        return k, v

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                elif event.key == pygame.K_TAB:
                    cat_idx = (cat_idx + 1) % len(CATEGORIES)
                    bld_idx = 0
                elif event.key == pygame.K_LEFT:
                    bld_idx = (bld_idx - 1) % max(1, len(current_list()))
                elif event.key == pygame.K_RIGHT:
                    bld_idx = (bld_idx + 1) % max(1, len(current_list()))
                elif event.key == pygame.K_f:
                    flip = not flip
                elif event.key == pygame.K_s:
                    _export_current(iso, *current_bld(), zoom, flip)
                elif event.key == pygame.K_a:
                    _export_all(iso)
            elif event.type == pygame.MOUSEWHEEL:
                zoom = max(0.4, min(3.0, zoom + event.y * 0.15))

        screen.fill(DARK)

        bid, bdef = current_bld()
        if not bdef:
            continue

        # ── Render building preview ────────────────────────────────
        bsurf = iso.surface_for(bdef, scale=zoom, flip=flip)
        bx = (W - 280 - bsurf.get_width()) // 2
        by = (H - bsurf.get_height()) // 2 + 20
        screen.blit(bsurf, (bx, by))

        # ── Sidebar ────────────────────────────────────────────────
        sb_x = W - 280
        pygame.draw.rect(screen, PANEL, (sb_x, 0, 280, H))
        pygame.draw.line(screen, BORDER, (sb_x, 0), (sb_x, H))

        y = 12
        cat_lbl = font_px.render(CAT_LABELS[current_cat()], True, TEAL_DIM)
        screen.blit(cat_lbl, (sb_x + 10, y)); y += 16

        name_lbl = font_big.render(bdef["name"], True, ORANGE)
        screen.blit(name_lbl, (sb_x + 10, y)); y += 26

        sub_lbl = font_med.render(bdef["sub"], True, TEAL)
        screen.blit(sub_lbl, (sb_x + 10, y)); y += 22

        pygame.draw.line(screen, BORDER, (sb_x + 8, y), (W - 8, y)); y += 10

        # Stats
        stats = [
            ("FACTION",  bdef.get("faction", "NEUTRAL") or "NEUTRAL"),
            ("FOOTPRINT", f"{bdef['w']}×{bdef['h']} tiles"),
            ("FLOORS",   str(bdef["floors"])),
            ("HP",       str(bdef["hp"])),
            ("COST",     f"§{bdef['cost']}" if bdef["cost"] else "FREE"),
            ("POWER",    f"{bdef['power_draw']:+d} MW"),
            ("GARRISON", str(bdef["garrison"]) if bdef["garrison"] else "—"),
            ("PRODUCES", ", ".join(bdef["produces"]) if bdef["produces"] else "—"),
        ]
        for label, val in stats:
            ll = font_sm.render(label, True, TEAL_DIM)
            vl = font_sm.render(val.upper(), True, TEAL)
            screen.blit(ll, (sb_x + 10, y))
            screen.blit(vl, (sb_x + 115, y))
            y += 16

        pygame.draw.line(screen, BORDER, (sb_x + 8, y), (W - 8, y)); y += 10

        # Flags
        for flag in bdef.get("flags", []):
            col = ORANGE if flag in ("required","volatile","garrisonable") else TEAL_DIM
            fl = font_px.render(f"▸ {flag.upper()}", True, col)
            screen.blit(fl, (sb_x + 10, y)); y += 13

        pygame.draw.line(screen, BORDER, (sb_x + 8, y), (W - 8, y)); y += 10

        # Description
        desc_words = bdef["description"].split()
        line_buf, desc_y = [], y
        for w2 in desc_words:
            test = " ".join(line_buf + [w2])
            if font_px.size(test)[0] > 255:
                dl = font_px.render(" ".join(line_buf), True, (0, 120, 90))
                screen.blit(dl, (sb_x + 10, desc_y)); desc_y += 13
                line_buf = [w2]
            else:
                line_buf.append(w2)
        if line_buf:
            dl = font_px.render(" ".join(line_buf), True, (0, 120, 90))
            screen.blit(dl, (sb_x + 10, desc_y)); desc_y += 13

        # Palette swatches
        y = H - 80
        pygame.draw.line(screen, BORDER, (sb_x + 8, y), (W - 8, y)); y += 8
        pal_label = font_px.render("PALETTE", True, TEAL_DIM)
        screen.blit(pal_label, (sb_x + 10, y)); y += 12
        pal = bdef["palette"]
        for pk, col in [("TOP", pal["top"]), ("WALL L", pal["wall_l"]),
                         ("WALL R", pal["wall_r"]), ("ACCENT", pal["accent"])]:
            pygame.draw.rect(screen, col, (sb_x + 10, y, 18, 12))
            pygame.draw.rect(screen, BORDER, (sb_x + 10, y, 18, 12), 1)
            pl = font_px.render(pk, True, TEAL_DIM)
            screen.blit(pl, (sb_x + 32, y)); y += 14

        # ── Top bar ────────────────────────────────────────────────
        pygame.draw.rect(screen, PANEL, (0, 0, sb_x, 32))
        pygame.draw.line(screen, BORDER, (0, 32), (sb_x, 32))

        lst = current_list()
        nav = f"{bld_idx + 1} / {len(lst)}  ·  TAB: change category  ·  ←→: cycle  ·  F: flip  ·  S: save  ·  A: save all  ·  scroll: zoom"
        nl = font_px.render(nav, True, TEAL_DIM)
        screen.blit(nl, (12, 11))

        # Garrison indicator overlay (bottom left of preview)
        if bdef["garrison"]:
            gi = font_sm.render(
                f"◈ GARRISON  {bdef['garrison']} INFANTRY SLOTS", True, ORANGE)
            screen.blit(gi, (12, H - 20))

        pygame.display.flip()


def _export_current(iso, bid, bdef, zoom, flip):
    if not bdef: return
    surf = iso.surface_for(bdef, scale=zoom, flip=flip)
    path = os.path.join(OUT_DIR, f"{bid}.png")
    pygame.image.save(surf, path)
    print(f"Saved → {path}")


def _export_all(iso):
    for bid, bdef in BUILDINGS.items():
        surf = iso.surface_for(bdef, scale=1.0, flip=False)
        path = os.path.join(OUT_DIR, f"{bid}.png")
        pygame.image.save(surf, path)
        print(f"  {bid}.png")
    print(f"All buildings → {OUT_DIR}")


if __name__ == "__main__":
    main()
