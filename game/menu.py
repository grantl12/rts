"""
Main menu — terminal boot aesthetic with faction selection.
Call MainMenu.run(screen, clock) → returns chosen faction string.
"""
import sys, math, random, pygame

TEAL      = (0, 255, 204)
TEAL_DIM  = (0, 80, 60)
TEAL_MID  = (0, 160, 120)
ORANGE    = (255, 102, 0)
RED       = (220, 40, 30)
DARK      = (4, 10, 8)
PANEL     = (8, 18, 14)

FACTIONS = [
    ("regency",   "REGENCY",   "ADMINISTRATIVE COMPLIANCE DIVISION", (28,  80, 180)),
    ("frontline", "FRONTLINE", "INFORMATION WARFARE BUREAU",         (80, 140,  40)),
    ("sovereign", "SOVEREIGN", "REVOLUTIONARY SAFEHOUSE NETWORK",    (140, 40, 200)),
    ("oligarchy", "OLIGARCHY", "STAFFING AGENCY INTERNATIONAL",      (120,  90,  20)),
]

BOOT_LINES = [
    ("DEEP STATE COMMAND SYSTEM v4.1.9",                        TEAL),
    ("COPYRIGHT ADMINISTRATIVE OVERSIGHT BUREAU — CLASSIFIED",  TEAL_DIM),
    ("",                                                        TEAL),
    ("INITIALIZING THREAT ASSESSMENT MODULE...",                TEAL_MID),
    ("LOADING CIVILIAN COMPLIANCE DATABASE......  [OK]",        (0, 200, 100)),
    ("SYNCING INFAMY LEDGER......................  [OK]",        (0, 200, 100)),
    ("ESTABLISHING SECTOR 7G UPLINK..............  [OK]",       (0, 200, 100)),
    ("BIOMETRIC ARCHIVE LINKED...................  [OK]",        (0, 200, 100)),
    ("REDACTING OPERATIONAL FOOTNOTES...........  [OK]",        (0, 200, 100)),
    ("",                                                        TEAL),
    ("ADVISORY: EPSTEIN DIDN'T KILL HIMSELF.",                  TEAL_DIM),
    ("ADVISORY: DO YOUR OWN RESEARCH.",                         TEAL_DIM),
    ("ADVISORY: THE ALGORITHM IS WATCHING. THIS IS NORMAL.",    TEAL_DIM),
    ("ADVISORY: [REDACTED]",                                    TEAL_DIM),
    ("",                                                        TEAL),
    ("!! KIRK CATALYST DETECTED — INCIDENT LOG ACTIVE !!",      ORANGE),
    ("   QUAD SECTOR COMPROMISED — IMMEDIATE RESPONSE REQUIRED",ORANGE),
    ("",                                                        TEAL),
    ("SELECT JURISDICTION TO PROCEED.",                         (200, 200, 200)),
]

CHARS_PER_SEC = 35.0


class MainMenu:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h

        self._boot_timer   = 0.0
        self._boot_done    = False
        self._cursor_blink = 0.0
        self._selected_idx = 0
        self._hover_idx    = None
        self._confirmed    = None

        # Noise particles for background atmosphere
        self._particles = [
            [random.randint(0, screen_w), random.randint(0, screen_h),
             random.uniform(0.1, 0.6), random.uniform(0.5, 3.0)]
            for _ in range(60)
        ]
        self._scanlines   = None
        self._thermal_bg  = None
        self._fonts_loaded = False

    def _load_fonts(self):
        if self._fonts_loaded:
            return
        self._f_title = pygame.font.SysFont("couriernew", 52, bold=True)
        self._f_med   = pygame.font.SysFont("couriernew", 14, bold=True)
        self._f_sm    = pygame.font.SysFont("couriernew", 11)
        self._f_px    = pygame.font.SysFont("couriernew",  9)
        self._fonts_loaded = True

    def _make_scanlines(self):
        if self._scanlines:
            return
        s = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        for y in range(0, self.sh, 3):
            pygame.draw.line(s, (0, 0, 0, 50), (0, y), (self.sw, y))
        self._scanlines = s

    def _make_thermal_bg(self):
        """Pre-bake a static satellite thermal image (heat-map blobs on dark ground)."""
        if self._thermal_bg:
            return
        import random as _r
        surf = pygame.Surface((self.sw, self.sh))
        surf.fill((4, 8, 6))

        # Draw heat blobs representing buildings / crowd zones
        heat_spots = [
            # (x_frac, y_frac, radius, intensity 0-1)
            (0.14, 0.42, 55, 0.55),   # west block
            (0.28, 0.58, 40, 0.45),
            (0.50, 0.52, 70, 0.80),   # quad center — Kirk rally
            (0.50, 0.48, 30, 0.95),   # hot crowd core
            (0.68, 0.38, 45, 0.50),
            (0.80, 0.62, 38, 0.40),
            (0.35, 0.25, 50, 0.60),   # north campus
            (0.60, 0.70, 42, 0.35),
            (0.20, 0.72, 35, 0.30),
        ]
        for (xf, yf, rad, intensity) in heat_spots:
            cx = int(xf * self.sw)
            cy = int(yf * self.sh)
            for _ in range(220):
                angle  = _r.uniform(0, 2 * math.pi)
                dist   = _r.gauss(0, rad * 0.45)
                px     = int(cx + math.cos(angle) * dist)
                py     = int(cy + math.sin(angle) * dist)
                if not (0 <= px < self.sw and 0 <= py < self.sh):
                    continue
                t = max(0.0, 1.0 - abs(dist) / rad) * intensity
                # Thermal palette: cold=dark teal, warm=orange, hot=white
                if t < 0.3:
                    col = (0, int(t / 0.3 * 60), int(t / 0.3 * 40))
                elif t < 0.65:
                    v   = (t - 0.3) / 0.35
                    col = (int(v * 180), int(60 + v * 60), 0)
                else:
                    v   = (t - 0.65) / 0.35
                    col = (180 + int(v * 75), 120 + int(v * 135), int(v * 200))
                # Smooth dot
                r = max(1, int(rad * 0.07))
                pygame.draw.circle(surf, col, (px, py), r)

        # Road-grid (cool lines — asphalt reads cold in thermal)
        road_col = (0, 18, 12)
        for x in range(0, self.sw, int(self.sw / 7)):
            pygame.draw.line(surf, road_col, (x, 0), (x, self.sh), 2)
        for y in range(0, self.sh, int(self.sh / 5)):
            pygame.draw.line(surf, road_col, (0, y), (self.sw, y), 2)

        # Blur pass (simple box-blur via scale trick)
        small = pygame.transform.smoothscale(surf, (self.sw // 4, self.sh // 4))
        surf  = pygame.transform.smoothscale(small, (self.sw, self.sh))

        self._thermal_bg = surf

    # ── Public ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if self._boot_done:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self._confirmed = FACTIONS[self._selected_idx][0]
                if event.key == pygame.K_UP:
                    self._selected_idx = (self._selected_idx - 1) % len(FACTIONS)
                if event.key == pygame.K_DOWN:
                    self._selected_idx = (self._selected_idx + 1) % len(FACTIONS)
            else:
                # Skip boot animation
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._boot_done  = True
                    self._boot_timer = 9999.0

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._boot_done and self._hover_idx is not None:
                self._selected_idx = self._hover_idx
                self._confirmed = FACTIONS[self._selected_idx][0]

    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        self._cursor_blink = (self._cursor_blink + dt * 2.0) % 1.0
        self._boot_timer  += dt

        # Advance particles
        for p in self._particles:
            p[0] += p[3] * 0.3
            if p[0] > self.sw:
                p[0] = 0
                p[1] = random.randint(0, self.sh)

        # Boot-text completion check
        total_chars = sum(len(line) + 1 for line, _ in BOOT_LINES)
        if self._boot_timer * CHARS_PER_SEC >= total_chars:
            self._boot_done = True

    def draw(self, surf):
        self._load_fonts()
        self._make_scanlines()

        self._make_thermal_bg()
        surf.blit(self._thermal_bg, (0, 0))

        # Pulsing teal vignette overlay (gives the "live satellite feed" look)
        t = pygame.time.get_ticks() / 6000.0
        pulse_a = int(28 + 8 * math.sin(t))
        vignette = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, pulse_a, pulse_a // 2, 60), (0, 0, self.sw, self.sh))
        surf.blit(vignette, (0, 0))

        # Drift particles (hot sparks over the thermal)
        for p in self._particles:
            a = int(p[2] * 255)
            pygame.draw.circle(surf, (min(255, a * 2), a // 2, 0), (int(p[0]), int(p[1])), 1)

        # ── Title ──
        title = self._f_title.render("THE DEEP STATE", True, TEAL)
        tx = self.sw // 2 - title.get_width() // 2
        ty = 36
        # Glitch shadow
        shadow = self._f_title.render("THE DEEP STATE", True, (0, 40, 30))
        surf.blit(shadow, (tx + 2, ty + 2))
        surf.blit(title,  (tx,     ty))
        # Accent line under title
        pygame.draw.line(surf, RED,      (tx, ty + 62),     (tx + title.get_width(), ty + 62), 2)
        pygame.draw.line(surf, TEAL_DIM, (tx, ty + 64),     (tx + title.get_width(), ty + 64), 1)

        sub = self._f_px.render(
            "OPERATION: WOLVERINE  |  SECTOR 7G  |  UVU VALLEY — OREM, UTAH  |  INCIDENT LOG ACTIVE",
            True, ORANGE)
        surf.blit(sub, (self.sw // 2 - sub.get_width() // 2, ty + 68))

        # ── Boot text ──
        chars_shown = int(self._boot_timer * CHARS_PER_SEC)
        by = ty + 90
        remaining = chars_shown
        for line, col in BOOT_LINES:
            if remaining <= 0:
                break
            shown = line[:remaining]
            remaining -= len(line) + 1
            lbl = self._f_sm.render(shown, True, col)
            surf.blit(lbl, (80, by))
            by += 18

        # Cursor blink at end of boot text
        if not self._boot_done and self._cursor_blink < 0.5:
            pygame.draw.rect(surf, TEAL, (80, by, 8, 13))

        # ── Faction cards ──
        if self._boot_done:
            self._draw_faction_cards(surf)

        # ── Scanlines ──
        surf.blit(self._scanlines, (0, 0))

        # ── REC indicator ──
        if int(pygame.time.get_ticks() / 700) % 2 == 0:
            pygame.draw.circle(surf, RED, (self.sw - 60, 20), 5)
        rec = self._f_px.render("● REC", True, RED)
        surf.blit(rec, (self.sw - 80, 15))

        # ── Version stamp ──
        ver = self._f_px.render("BUILD 0.4.1 — UNCLASSIFIED // FOR OFFICIAL USE ONLY", True, TEAL_DIM)
        surf.blit(ver, (10, self.sh - 16))

    def _draw_faction_cards(self, surf):
        card_w = 270
        card_h = 82
        gap    = 14
        cols   = 2
        total_w = cols * card_w + (cols - 1) * gap
        x0 = self.sw // 2 - total_w // 2
        y0 = self.sh - 230

        mx, my = pygame.mouse.get_pos()
        self._hover_idx = None

        for i, (fid, fname, fsub, fcol) in enumerate(FACTIONS):
            col_i = i % cols
            row_i = i // cols
            cx = x0 + col_i * (card_w + gap)
            cy = y0 + row_i * (card_h + gap)
            crect = pygame.Rect(cx, cy, card_w, card_h)

            locked = (fid != "regency")
            hover  = crect.collidepoint(mx, my) and not locked
            sel    = (i == self._selected_idx) and not locked
            
            if hover:
                self._hover_idx = i

            # Background
            if sel:
                bg = tuple(min(60, c // 4 + 10) for c in fcol)
            elif hover:
                bg = (14, 28, 22)
            elif locked:
                bg = (4, 8, 6)
            else:
                bg = (10, 20, 16)
            pygame.draw.rect(surf, bg, crect)

            # Border
            bw = 2 if sel else 1
            if locked:
                bc = (40, 40, 40)
            else:
                t  = pygame.time.get_ticks() / 600.0
                bc = tuple(int(c * (0.7 + 0.3 * math.sin(t))) for c in fcol) if sel else (TEAL_DIM if not hover else TEAL_MID)
            pygame.draw.rect(surf, bc, crect, bw)

            # Faction color swatch (greyscale for locked)
            swatch = pygame.Rect(cx + 10, cy + 14, 16, 16)
            scol = fcol if not locked else (60, 60, 60)
            pygame.draw.rect(surf, scol, swatch)
            pygame.draw.rect(surf, (255, 255, 255) if not locked else (100, 100, 100), swatch, 1)

            # Text
            name_col = (fcol if sel else (TEAL if hover else TEAL_MID)) if not locked else (80, 80, 80)
            nl = self._f_med.render(fname, True, name_col)
            surf.blit(nl, (cx + 34, cy + 12))

            sl = self._f_px.render(fsub if not locked else "ACCESS RESTRICTED — PENDING AUDIT", True, (60, 60, 60) if locked else TEAL_DIM)
            surf.blit(sl, (cx + 34, cy + 30))

            # Locked / X Overlay
            if locked:
                # Large Red X
                pygame.draw.line(surf, (150, 0, 0), (cx + 5, cy + 5), (cx + card_w - 5, cy + card_h - 5), 2)
                pygame.draw.line(surf, (150, 0, 0), (cx + card_w - 5, cy + 5), (cx + 5, cy + card_h - 5), 2)
                
                # REDACTED Stamp
                f_redact = pygame.font.SysFont("impact", 20)
                rtxt = f_redact.render("REDACTED", True, (200, 30, 0))
                # Rotate a bit
                rtxt = pygame.transform.rotate(rtxt, 15)
                surf.blit(rtxt, (cx + card_w//2 - rtxt.get_width()//2, cy + card_h//2 - rtxt.get_height()//2))
            else:
                # Deploy prompt on selected
                if sel:
                    blink = int(pygame.time.get_ticks() / 400) % 2 == 0
                    if blink:
                        dep = self._f_sm.render("[ ENTER TO DEPLOY ]", True,
                                                tuple(min(255, c + 60) for c in fcol))
                        dep_shadow = self._f_sm.render("[ ENTER TO DEPLOY ]", True, (0,0,0))
                        surf.blit(dep_shadow, (cx + 12, cy + 58))
                        surf.blit(dep, (cx + 10, cy + 56))
                elif hover:
                    dep = self._f_px.render("click to select", True, TEAL_DIM)
                    surf.blit(dep, (cx + 10, cy + 58))

        # Nav instructions
        inst_y = y0 + 2 * (card_h + gap) + 10
        inst = self._f_px.render(
            "↑ ↓  NAVIGATE  ·  ENTER / CLICK  DEPLOY  ·  ESC  ABORT MISSION",
            True, TEAL_DIM)
        surf.blit(inst, (self.sw // 2 - inst.get_width() // 2, inst_y))

    @property
    def confirmed(self):
        return self._confirmed


def run(screen, clock, fps=60):
    """Block until player selects a faction. Returns faction string."""
    w, h = screen.get_size()
    menu = MainMenu(w, h)
    while menu.confirmed is None:
        dt = clock.tick(fps)
        for event in pygame.event.get():
            menu.handle_event(event)
        menu.update(dt)
        menu.draw(screen)
        pygame.display.flip()
    return menu.confirmed
