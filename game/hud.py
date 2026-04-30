"""Top bar + right sidebar HUD (C&C sidebar style)."""
import pygame

TEAL    = (0, 255, 204)
TEAL_DIM= (0, 80, 60)
ORANGE  = (255, 102, 0)
DARK    = (6, 13, 10)
PANEL   = (8, 19, 15)
BORDER  = (0, 60, 45)

SIDEBAR_W  = 220
TOPBAR_H   = 34


class HUD:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self.sidebar_rect  = pygame.Rect(screen_w - SIDEBAR_W, TOPBAR_H, SIDEBAR_W, screen_h - TOPBAR_H)
        self.minimap_rect  = pygame.Rect(screen_w - SIDEBAR_W + 12, TOPBAR_H + 40, SIDEBAR_W - 24, 130)
        self.topbar_rect   = pygame.Rect(0, 0, screen_w, TOPBAR_H)

        self.credits       = 5000
        self.infamy        = 0
        self.roe_name      = "STANDARD"
        self.roe_col       = (209, 209, 209)
        self.selected_bld  = None
        self.mission_time  = 0   # seconds
        self._tick         = 0

        self._font_sm  = None
        self._font_med = None
        self._font_px  = None

    def _load_fonts(self):
        if self._font_sm:
            return
        self._font_sm  = pygame.font.SysFont("couriernew", 10)
        self._font_med = pygame.font.SysFont("couriernew", 13, bold=True)
        self._font_px  = pygame.font.SysFont("couriernew", 9)

    def update(self, dt_ms):
        self._tick += dt_ms
        if self._tick >= 1000:
            self._tick -= 1000
            self.mission_time += 1
            self.credits += 3   # passive income tick

    def draw(self, surf: pygame.Surface, minimap_draw_fn=None):
        self._load_fonts()
        self._draw_topbar(surf)
        self._draw_sidebar(surf, minimap_draw_fn)

    # ── TOP BAR ──────────────────────────────────────────────────────
    def _draw_topbar(self, surf):
        pygame.draw.rect(surf, PANEL, self.topbar_rect)
        pygame.draw.line(surf, BORDER, (0, TOPBAR_H - 1), (self.sw, TOPBAR_H - 1))

        t = self.mission_time
        ts = f"{t//3600:02d}:{(t%3600)//60:02d}:{t%60:02d}"

        title  = self._font_med.render("DEEP STATE RTS", True, ORANGE)
        op     = self._font_sm.render("OP: WOLVERINE  ·  UVU VALLEY SECTOR — OREM, UTAH", True, TEAL_DIM)
        roe    = self._font_med.render(f"ROE: {self.roe_name}", True, self.roe_col)
        cred   = self._font_med.render(f"§{self.credits:,}", True, TEAL)
        clock  = self._font_sm.render(ts, True, TEAL)

        surf.blit(title, (12, 9))
        surf.blit(op,    (190, 12))
        surf.blit(roe,   (190, 24))
        surf.blit(clock, (self.sw - SIDEBAR_W - 90, 11))
        surf.blit(cred,  (self.sw - SIDEBAR_W - 190, 9))

    # ── SIDEBAR ───────────────────────────────────────────────────────
    def _draw_sidebar(self, surf, minimap_draw_fn):
        pygame.draw.rect(surf, PANEL, self.sidebar_rect)
        pygame.draw.line(surf, BORDER,
            (self.sidebar_rect.left, TOPBAR_H),
            (self.sidebar_rect.left, self.sh))

        y = TOPBAR_H + 8
        label = self._font_px.render("▸ RADAR — SECTOR 7G", True, TEAL_DIM)
        surf.blit(label, (self.sidebar_rect.left + 8, y))
        y += 14

        if minimap_draw_fn:
            minimap_draw_fn(surf)
        pygame.draw.rect(surf, BORDER, self.minimap_rect, 1)

        y = self.minimap_rect.bottom + 12
        line = self._font_px.render("▸ STRUCTURE INFO", True, TEAL_DIM)
        surf.blit(line, (self.sidebar_rect.left + 8, y))
        y += 14

        if self.selected_bld:
            self._draw_bld_panel(surf, y)
        else:
            no = self._font_px.render("[ NO STRUCTURE SELECTED ]", True, (0, 50, 38))
            surf.blit(no, (self.sidebar_rect.left + 8, y + 20))

        # Credits section at bottom
        res_y = self.sh - 70
        pygame.draw.line(surf, BORDER,
            (self.sidebar_rect.left, res_y),
            (self.sw, res_y))
        rl = self._font_px.render("▸ RESOURCES", True, TEAL_DIM)
        surf.blit(rl, (self.sidebar_rect.left + 8, res_y + 8))
        cv = self._font_med.render(f"§{self.credits:,}", True, TEAL)
        surf.blit(cv, (self.sidebar_rect.left + 8, res_y + 22))

        # Infamy bar with tier markers
        _TIERS = [(200, "SCRUTINIZED", (200, 200, 0)),
                  (400, "SURVEILLED",  (255, 140, 0)),
                  (750, "SANCTIONED",  (220, 40,  30))]
        tier_name = "CLEAN"
        tier_col  = TEAL_DIM
        for thresh, tname, tcol in _TIERS:
            if self.infamy >= thresh:
                tier_name, tier_col = tname, tcol

        inf_label = self._font_px.render(
            f"INFAMY  {self.infamy}/1000  [{tier_name}]", True, tier_col)
        surf.blit(inf_label, (self.sidebar_rect.left + 8, res_y + 44))
        bar_rect = pygame.Rect(self.sidebar_rect.left + 8, res_y + 56, SIDEBAR_W - 20, 6)
        pygame.draw.rect(surf, (20, 5, 5), bar_rect)
        fill_w = int(bar_rect.width * min(self.infamy, 1000) / 1000)
        if fill_w:
            r = min(255, 80 + int(175 * self.infamy / 1000))
            pygame.draw.rect(surf, (r, 20, 20),
                pygame.Rect(bar_rect.left, bar_rect.top, fill_w, bar_rect.height))
        pygame.draw.rect(surf, BORDER, bar_rect, 1)
        # Tier threshold ticks
        for thresh, _, tcol in _TIERS:
            tx = bar_rect.left + int(bar_rect.width * thresh / 1000)
            pygame.draw.line(surf, tcol, (tx, bar_rect.top - 1), (tx, bar_rect.bottom + 1))

    def _draw_bld_panel(self, surf, y):
        b = self.selected_bld
        lx = self.sidebar_rect.left + 8
        # Support both tuple (map data) and PlacedBuilding objects
        if hasattr(b, "bdef"):
            name_str = getattr(b, "display_name", b.bdef["name"])
            sub_str  = getattr(b, "display_sub",  b.bdef["sub"])
            hp, max_hp = b.hp, b.max_hp
        else:
            name_str, sub_str, hp, max_hp = b[1], b[2], b[9], b[10]
        name = self._font_med.render(name_str, True, TEAL)
        sub  = self._font_px.render(sub_str,   True, ORANGE)
        surf.blit(name, (lx, y));      y += 16
        surf.blit(sub,  (lx, y));      y += 16
        hp_pct = hp / max_hp
        hp_col = (0,200,120) if hp_pct > 0.6 else (255,160,0) if hp_pct > 0.3 else (220,40,40)
        hp_lbl = self._font_px.render(f"HP  {hp}/{max_hp}", True, TEAL_DIM)
        surf.blit(hp_lbl, (lx, y));    y += 12
        bar = pygame.Rect(lx, y, SIDEBAR_W - 20, 5)
        pygame.draw.rect(surf, (20, 20, 20), bar)
        pygame.draw.rect(surf, hp_col, pygame.Rect(lx, y, int(bar.width * hp_pct), 5))
        pygame.draw.rect(surf, BORDER, bar, 1)

    # ── INPUT ────────────────────────────────────────────────────────
    def hit_sidebar(self, pos):
        return self.sidebar_rect.collidepoint(pos) or self.topbar_rect.collidepoint(pos)
