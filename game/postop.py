"""
Post-operation allocation screen.
Shows after mission ends: allocate detained civilians to three silos.
"""
import math, pygame

DARK   = (4, 10, 8)
PANEL  = (8, 18, 14)
TEAL   = (0, 255, 204)
TEAL_D = (0, 80, 60)
ORANGE = (255, 102, 0)
RED    = (220, 40, 30)
GREEN  = (40, 200, 80)

SILOS = [
    ("BIO-METRIC DATABASE",   "§150 per unit",   (28,  80, 180), "credits"),
    ("INFRASTRUCTURE FUND",   "+2 §/sec passive", (80, 140,  40), "passive"),
    ("PUBLIC RELATIONS DEPT", "-40 infamy each",  (140, 40, 200), "pr"),
]


class PostOpScreen:
    """Runs blocking until player files the report. Returns allocation dict."""

    def __init__(self, detained: int, infamy: int, mission_time: int, credits: int):
        self.detained     = detained
        self.infamy       = infamy
        self.mission_time = mission_time
        self.credits_in   = credits

        # Unallocated pool + per-silo counts
        self.pool      = detained
        self.allocated = [0, 0, 0]

        self._done   = False
        self._result = None
        self._fonts  = {}
        self._hover_btn = None  # index of hovered +/- button

    def _load_fonts(self):
        if self._fonts:
            return
        self._fonts["title"] = pygame.font.SysFont("couriernew", 26, bold=True)
        self._fonts["med"]   = pygame.font.SysFont("couriernew", 13, bold=True)
        self._fonts["sm"]    = pygame.font.SysFont("couriernew", 10)
        self._fonts["px"]    = pygame.font.SysFont("couriernew", 9)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._file_report()
            if event.key == pygame.K_ESCAPE:
                self._file_report()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._file_rect and self._file_rect.collidepoint(mx, my):
                self._file_report()
            for i, (plus, minus) in enumerate(self._btn_rects):
                if plus.collidepoint(mx, my) and self.pool > 0:
                    self.pool -= 1
                    self.allocated[i] += 1
                if minus.collidepoint(mx, my) and self.allocated[i] > 0:
                    self.allocated[i] -= 1
                    self.pool += 1

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover_btn = None
            for i, (plus, minus) in enumerate(self._btn_rects):
                if plus.collidepoint(mx, my) or minus.collidepoint(mx, my):
                    self._hover_btn = i

    def _file_report(self):
        self._done = True
        self._result = {
            "allocated": self.allocated,
            "silos": [s[3] for s in SILOS],
        }

    def update(self, dt_ms):
        pass

    def draw(self, surf):
        self._load_fonts()
        sw, sh = surf.get_size()
        surf.fill(DARK)

        # Header
        pygame.draw.rect(surf, PANEL, (0, 0, sw, 56))
        pygame.draw.line(surf, TEAL_D, (0, 56), (sw, 56))

        t = self._fonts["title"].render("POST-OPERATION DEBRIEF", True, TEAL)
        surf.blit(t, (sw // 2 - t.get_width() // 2, 12))

        sub = self._fonts["px"].render(
            "ASSET ALLOCATION — ADMINISTRATIVE COMPLIANCE DIVISION", True, ORANGE)
        surf.blit(sub, (sw // 2 - sub.get_width() // 2, 40))

        # Stats row
        mm = self.mission_time
        ts = f"{mm//3600:02d}:{(mm%3600)//60:02d}:{mm%60:02d}"
        stats = [
            ("MISSION TIME", ts),
            ("INFAMY SCORE", str(self.infamy)),
            ("DETAINED ASSETS", str(self.detained)),
            ("UNALLOCATED", str(self.pool)),
        ]
        stat_w = sw // len(stats)
        for i, (label, val) in enumerate(stats):
            x = i * stat_w + stat_w // 2
            col = RED if label == "INFAMY SCORE" and self.infamy >= 400 else TEAL
            lbl = self._fonts["sm"].render(label, True, TEAL_D)
            val_lbl = self._fonts["med"].render(val, True, col)
            surf.blit(lbl, (x - lbl.get_width() // 2, 68))
            surf.blit(val_lbl, (x - val_lbl.get_width() // 2, 82))

        # Silo cards
        card_w = min(260, (sw - 80) // 3)
        card_h = 180
        gap = 20
        total_w = 3 * card_w + 2 * gap
        x0 = sw // 2 - total_w // 2
        y0 = 130

        self._btn_rects = []
        for i, (name, effect, col, _key) in enumerate(SILOS):
            cx = x0 + i * (card_w + gap)
            crect = pygame.Rect(cx, y0, card_w, card_h)
            pygame.draw.rect(surf, PANEL, crect)
            pygame.draw.rect(surf, col, crect, 1 + (self._hover_btn == i))

            # Name
            n = self._fonts["med"].render(name, True, col)
            surf.blit(n, (cx + card_w // 2 - n.get_width() // 2, y0 + 10))

            # Effect
            e = self._fonts["px"].render(effect, True, TEAL_D)
            surf.blit(e, (cx + card_w // 2 - e.get_width() // 2, y0 + 30))

            # Count
            cnt = self._fonts["title"].render(str(self.allocated[i]), True, col)
            surf.blit(cnt, (cx + card_w // 2 - cnt.get_width() // 2, y0 + 60))

            lbl_a = self._fonts["px"].render("UNITS ALLOCATED", True, TEAL_D)
            surf.blit(lbl_a, (cx + card_w // 2 - lbl_a.get_width() // 2, y0 + 105))

            # +/- buttons
            plus_r  = pygame.Rect(cx + card_w // 2 - 30, y0 + 130, 26, 26)
            minus_r = pygame.Rect(cx + card_w // 2 + 4,  y0 + 130, 26, 26)
            pygame.draw.rect(surf, GREEN, plus_r, 0 if self.pool > 0 else 1)
            pygame.draw.rect(surf, RED,   minus_r, 0 if self.allocated[i] > 0 else 1)
            p = self._fonts["med"].render("+", True, DARK if self.pool > 0 else GREEN)
            m = self._fonts["med"].render("−", True, DARK if self.allocated[i] > 0 else RED)
            surf.blit(p, (plus_r.x  + 7, plus_r.y  + 4))
            surf.blit(m, (minus_r.x + 7, minus_r.y + 4))
            self._btn_rects.append((plus_r, minus_r))

        # Unallocated warning
        if self.pool > 0:
            warn = self._fonts["sm"].render(
                f"⚠  {self.pool} UNALLOCATED — ASSETS WILL BE PROCESSED PER STANDARD PROTOCOL",
                True, ORANGE)
            surf.blit(warn, (sw // 2 - warn.get_width() // 2, y0 + card_h + 18))

        # File Report button
        btn_w, btn_h = 220, 36
        btn_x = sw // 2 - btn_w // 2
        btn_y = y0 + card_h + 50
        self._file_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        bcol = TEAL if blink else TEAL_D
        pygame.draw.rect(surf, PANEL, self._file_rect)
        pygame.draw.rect(surf, bcol, self._file_rect, 2)
        file_lbl = self._fonts["med"].render("[ FILE REPORT ]", True, bcol)
        surf.blit(file_lbl, (btn_x + btn_w // 2 - file_lbl.get_width() // 2,
                              btn_y + btn_h // 2 - file_lbl.get_height() // 2))

        # Footer
        foot = self._fonts["px"].render(
            "ENTER / ESC — FILE REPORT  ·  CLICK +/− TO ALLOCATE", True, TEAL_D)
        surf.blit(foot, (sw // 2 - foot.get_width() // 2, sh - 24))

    @property
    def done(self):
        return self._done

    @property
    def result(self):
        return self._result


BRIEFING_OPTIONS = [
    ("GASLIGHT",     "Deny all incidents. −60 Infamy, −§200.",    -60, -200, (80, 140, 40)),
    ("DOUBLE DOWN",  "Stand by all actions. +20 Infamy, +§400.",  +20,  400, (255, 166, 25)),
    ("REDACT",       "Classify the record. −30 Infamy, −§500.",   -30, -500, (140, 40, 200)),
]


class PressBriefing:
    """One-shot press briefing screen following the post-op allocation."""

    def __init__(self, infamy):
        self.infamy   = infamy
        self._choice  = None
        self._hover   = None
        self._fonts   = {}
        self._btn_rects = []

    def _load_fonts(self):
        if self._fonts:
            return
        self._fonts["title"] = pygame.font.SysFont("couriernew", 22, bold=True)
        self._fonts["med"]   = pygame.font.SysFont("couriernew", 13, bold=True)
        self._fonts["sm"]    = pygame.font.SysFont("couriernew", 10)
        self._fonts["px"]    = pygame.font.SysFont("couriernew", 9)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._choice = 0  # gaslight by default
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = None
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(mx, my):
                    self._hover = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hover is not None:
                self._choice = self._hover

    def draw(self, surf):
        self._load_fonts()
        sw, sh = surf.get_size()
        surf.fill(DARK)

        pygame.draw.rect(surf, PANEL, (0, 0, sw, 52))
        pygame.draw.line(surf, TEAL_D, (0, 52), (sw, 52))
        t = self._fonts["title"].render("PRESS BRIEFING — SELECT NARRATIVE", True, TEAL)
        surf.blit(t, (sw // 2 - t.get_width() // 2, 14))

        sub = self._fonts["px"].render(
            f"CURRENT INFAMY: {self.infamy}  ·  CHOOSE HOW TO FRAME THE OPERATION",
            True, ORANGE)
        surf.blit(sub, (sw // 2 - sub.get_width() // 2, 40))

        card_w, card_h = 240, 120
        gap = 20
        total_w = len(BRIEFING_OPTIONS) * card_w + (len(BRIEFING_OPTIONS)-1) * gap
        x0 = sw // 2 - total_w // 2
        y0 = sh // 2 - card_h // 2 - 20

        self._btn_rects = []
        for i, (name, desc, dinf, dcred, col) in enumerate(BRIEFING_OPTIONS):
            cx = x0 + i * (card_w + gap)
            crect = pygame.Rect(cx, y0, card_w, card_h)
            hover = (self._hover == i)
            bg = tuple(min(50, c // 5 + 10) for c in col) if hover else PANEL
            pygame.draw.rect(surf, bg, crect)
            pygame.draw.rect(surf, col, crect, 2 if hover else 1)

            n = self._fonts["med"].render(name, True, col)
            surf.blit(n, (cx + card_w // 2 - n.get_width() // 2, y0 + 10))

            words = desc.split()
            line, lines = [], []
            for w in words:
                if len(" ".join(line + [w])) > 28:
                    lines.append(" ".join(line)); line = [w]
                else:
                    line.append(w)
            if line: lines.append(" ".join(line))
            for j, l in enumerate(lines):
                lbl = self._fonts["px"].render(l, True, TEAL_D)
                surf.blit(lbl, (cx + 8, y0 + 34 + j * 13))

            inf_col = GREEN if dinf < 0 else RED
            cred_col = GREEN if dcred > 0 else RED
            surf.blit(self._fonts["sm"].render(
                f"INFAMY  {dinf:+d}", True, inf_col), (cx + 8, y0 + card_h - 36))
            surf.blit(self._fonts["sm"].render(
                f"CREDITS {dcred:+d}", True, cred_col), (cx + 8, y0 + card_h - 20))

            self._btn_rects.append(crect)

        foot = self._fonts["px"].render("CLICK OPTION TO PROCEED", True, TEAL_D)
        surf.blit(foot, (sw // 2 - foot.get_width() // 2, sh - 30))

    @property
    def done(self):
        return self._choice is not None


def run(screen, clock, detained, infamy, mission_time, credits, fps=60):
    """Block until player files report + press briefing. Returns result dict."""
    ps = PostOpScreen(detained, infamy, mission_time, credits)
    ps._btn_rects = [(pygame.Rect(0,0,1,1), pygame.Rect(0,0,1,1))] * 3
    ps._file_rect = None
    while not ps.done:
        dt = clock.tick(fps)
        for event in pygame.event.get():
            ps.handle_event(event)
        ps.update(dt)
        ps.draw(screen)
        pygame.display.flip()

    # Press Briefing
    pb = PressBriefing(infamy)
    while not pb.done:
        dt = clock.tick(fps)
        for event in pygame.event.get():
            pb.handle_event(event)
        pb.draw(screen)
        pygame.display.flip()

    choice_idx = pb._choice or 0
    _, _, dinf, dcred, _ = BRIEFING_OPTIONS[choice_idx]
    result = ps.result or {}
    result["press_choice"]  = BRIEFING_OPTIONS[choice_idx][0]
    result["infamy_delta"]  = dinf
    result["credits_delta"] = dcred
    return result
