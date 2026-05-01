"""
Executive Board — meta-progression screen.
Legacy Points (LP) are earned each mission and spent on persistent upgrades
that carry forward across all missions.
"""
import json, os, pygame

SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "save", "legacy.json")

DARK   = (4, 10, 8)
PANEL  = (8, 18, 14)
TEAL   = (0, 255, 204)
TEAL_D = (0, 80, 60)
ORANGE = (255, 102, 0)
DIM    = (0, 120, 90)
GREEN  = (40, 200, 80)
RED    = (180, 40, 40)

# (id, display_name, description, lp_cost, max_rank)
UPGRADES = [
    ("extra_credits", "EXTRA APPROPRIATIONS", "+500 starting credits/rank",    150, 3),
    ("infamy_head",   "MEDIA SUPPRESSION",    "Start with -25 infamy/rank",    100, 3),
    ("rapid_deploy",  "RAPID DEPLOYMENT",     "+1 starter unit/rank",          200, 2),
    ("pen_capacity",  "ASSET RETENTION",      "Holding pens +5 capacity/rank", 175, 2),
    ("fog_reveal",    "FIELD INTELLIGENCE",   "Partial fog revealed at start",  225, 1),
    ("admin_cover",   "ADMIN COVER",          "+50 infamy tolerance/rank",      250, 2),
]


def _load() -> dict:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH) as f:
                data = json.load(f)
                data.setdefault("map_phase", 0)
                return data
        except Exception:
            pass
    return {"lp": 0, "upgrades": {}, "map_phase": 0}


def get_map_phase() -> int:
    return _load().get("map_phase", 0)


def increment_map_phase():
    data = _load()
    data["map_phase"] = min(2, data.get("map_phase", 0) + 1)
    _save(data)


def _save(data: dict):
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def compute_lp(result: dict, mission_time: int) -> int:
    """Compute LP earned from a postop result dict."""
    lp = 50
    lp += sum(result.get("allocated", [])) * 5
    choice = result.get("press_choice", "")
    if choice == "GASLIGHT":      lp += 10
    elif choice == "DOUBLE DOWN": lp += 20
    elif choice == "REDACT":      lp += 5
    if mission_time < 600:        lp += 25
    return lp


def get_upgrades() -> dict:
    """Return {upgrade_id: rank} for use during mission setup."""
    return _load().get("upgrades", {})


def run(screen, clock, lp_earned: int, fps: int = 60):
    """Show Executive Board. Blocks until player continues."""
    data = _load()
    data["lp"] += lp_earned
    _save(data)

    board = _Board(data, lp_earned)
    while not board.done:
        clock.tick(fps)
        for event in pygame.event.get():
            board.handle_event(event)
        board.draw(screen)
        pygame.display.flip()

    _save(board.data)


class _Board:
    def __init__(self, data: dict, lp_earned: int):
        self.data      = data
        self.lp_earned = lp_earned
        self._done     = False
        self._hover    = None
        self._notify   = ""
        self._notify_t = 0.0
        self._card_rects = []
        self._back_rect  = None
        self._fonts      = {}

    @property
    def done(self):
        return self._done

    def _load_fonts(self):
        if self._fonts:
            return
        self._fonts["title"] = pygame.font.SysFont("couriernew", 22, bold=True)
        self._fonts["med"]   = pygame.font.SysFont("couriernew", 12, bold=True)
        self._fonts["sm"]    = pygame.font.SysFont("couriernew", 10)
        self._fonts["px"]    = pygame.font.SysFont("couriernew", 9)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self._done = True
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = None
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    self._hover = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._back_rect and self._back_rect.collidepoint(mx, my):
                self._done = True
                return
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    self._purchase(i)

    def _purchase(self, i: int):
        uid, name, _desc, cost, max_rank = UPGRADES[i]
        rank = self.data["upgrades"].get(uid, 0)
        if rank >= max_rank:
            self._notify = f"{name}: FULLY UPGRADED"
        elif self.data["lp"] < cost:
            self._notify = f"INSUFFICIENT LP — NEED {cost}"
        else:
            self.data["lp"] -= cost
            self.data["upgrades"][uid] = rank + 1
            self._notify = f"{name} — RANK {rank + 1} ACQUIRED"
        self._notify_t = 2.5

    def draw(self, surf):
        self._load_fonts()
        self._card_rects = []
        sw, sh = surf.get_size()
        surf.fill(DARK)

        # Header
        pygame.draw.rect(surf, PANEL, (0, 0, sw, 56))
        pygame.draw.line(surf, TEAL_D, (0, 56), (sw, 56))
        t = self._fonts["title"].render("EXECUTIVE BOARD — LEGACY ALLOCATIONS", True, TEAL)
        surf.blit(t, (sw // 2 - t.get_width() // 2, 10))

        lp_txt = f"LEGACY POINTS: {self.data['lp']:,}   (+{self.lp_earned} THIS MISSION)"
        lp_lbl = self._fonts["med"].render(lp_txt, True, ORANGE)
        surf.blit(lp_lbl, (sw // 2 - lp_lbl.get_width() // 2, 36))

        # Upgrade grid — 3 × 2
        cols = 3
        pad_x, top_y = 60, 72
        gap = 14
        card_w = (sw - pad_x * 2 - gap * (cols - 1)) // cols
        card_h = (sh - top_y - gap - 80) // 2

        for i, (uid, name, desc, cost, max_rank) in enumerate(UPGRADES):
            col_i = i % cols
            row_i = i // cols
            cx = pad_x + col_i * (card_w + gap)
            cy = top_y + row_i * (card_h + gap)
            crect = pygame.Rect(cx, cy, card_w, card_h)
            self._card_rects.append(crect)

            rank     = self.data["upgrades"].get(uid, 0)
            maxed    = rank >= max_rank
            afford   = self.data["lp"] >= cost
            hover    = (self._hover == i)

            if maxed:
                border = GREEN
            elif hover and afford:
                border = TEAL
            elif hover:
                border = RED
            else:
                border = TEAL_D

            bg = (12, 28, 20) if hover else PANEL
            pygame.draw.rect(surf, bg, crect)
            pygame.draw.rect(surf, border, crect, 2 if hover else 1)

            # Name
            n = self._fonts["med"].render(name, True, border)
            surf.blit(n, (cx + card_w // 2 - n.get_width() // 2, cy + 10))

            # Rank pips
            pip_total = max_rank * 16
            pip_x0 = cx + card_w // 2 - pip_total // 2
            for r in range(max_rank):
                pip_col = (0, 220, 120) if r < rank else (25, 55, 35)
                pygame.draw.rect(surf, pip_col, (pip_x0 + r * 16, cy + 34, 12, 6))
            rank_lbl = self._fonts["px"].render(
                f"RANK {rank}/{max_rank}", True, DIM)
            surf.blit(rank_lbl, (cx + card_w // 2 - rank_lbl.get_width() // 2, cy + 46))

            # Description
            d = self._fonts["px"].render(desc, True, DIM)
            surf.blit(d, (cx + card_w // 2 - d.get_width() // 2, cy + 62))

            # Cost / status
            if maxed:
                st = self._fonts["sm"].render("FULLY UPGRADED", True, GREEN)
            else:
                cost_col = TEAL if afford else (120, 40, 40)
                st = self._fonts["sm"].render(f"{cost} LP", True, cost_col)
            surf.blit(st, (cx + card_w // 2 - st.get_width() // 2, cy + card_h - 22))

        # Notification
        if self._notify_t > 0:
            self._notify_t = max(0.0, self._notify_t - 1 / 60)
            n_lbl = self._fonts["sm"].render(self._notify, True, ORANGE)
            surf.blit(n_lbl, (sw // 2 - n_lbl.get_width() // 2, sh - 64))

        # Continue button
        btn_w, btn_h = 200, 34
        btn_x = sw // 2 - btn_w // 2
        btn_y = sh - 46
        self._back_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        blink = int(pygame.time.get_ticks() / 600) % 2 == 0
        bcol = TEAL if blink else TEAL_D
        pygame.draw.rect(surf, PANEL, self._back_rect)
        pygame.draw.rect(surf, bcol, self._back_rect, 2)
        bl = self._fonts["med"].render("[ CONTINUE ]", True, bcol)
        surf.blit(bl, (btn_x + btn_w // 2 - bl.get_width() // 2,
                        btn_y + btn_h // 2 - bl.get_height() // 2))

        foot = self._fonts["px"].render(
            "CLICK UPGRADE TO PURCHASE  ·  ENTER / ESC — CONTINUE TO MENU",
            True, TEAL_D)
        surf.blit(foot, (sw // 2 - foot.get_width() // 2, sh - 16))
