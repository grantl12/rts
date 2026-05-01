"""
Slot picker screen — shown before every mission.
Returns (slot_number: int, slot_data: dict) or raises SystemExit.
"""
import sys, math, pygame
from game import save_manager as sm

DARK    = (4, 10, 8)
PANEL   = (8, 18, 14)
TEAL    = (0, 255, 204)
TEAL_D  = (0, 80, 60)
TEAL_M  = (0, 160, 120)
ORANGE  = (255, 102, 0)
RED     = (220, 40, 30)
GREEN   = (40, 200, 80)
GOLD    = (220, 180, 40)

FACTION_COL = {
    "regency":   (28,  80, 180),
    "frontline": (80, 140,  40),
    "sovereign": (140, 40, 200),
    "oligarchy": ( 40,  40,  40),
}


class SlotSelect:
    def __init__(self, screen_w, screen_h, faction: str, mode: str = "any"):
        """
        mode: "new"  — highlight empty slots, warn on overwrite
              "continue" — highlight filled slots only
              "any"  — all slots selectable
        """
        self.sw      = screen_w
        self.sh      = screen_h
        self.faction = faction
        self.mode    = mode
        self.slots   = sm.all_slots()   # [dict|None, dict|None, dict|None]

        self._hover  = None
        self._result = None   # (slot_num, slot_data)
        self._confirm_overwrite = None   # slot index awaiting confirm
        self._fonts  = {}
        self._card_rects = []

    def _load_fonts(self):
        if self._fonts:
            return
        self._fonts["title"] = pygame.font.SysFont("couriernew", 18, bold=True)
        self._fonts["med"]   = pygame.font.SysFont("couriernew", 12, bold=True)
        self._fonts["sm"]    = pygame.font.SysFont("couriernew", 10)
        self._fonts["px"]    = pygame.font.SysFont("couriernew", 9)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._confirm_overwrite is not None:
                    self._confirm_overwrite = None
                else:
                    self._result = None
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"back": True}))

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = None
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my):
                    if self._is_selectable(i):
                        self._hover = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._confirm_overwrite is not None:
                # Check yes/no rects
                if hasattr(self, "_yes_rect") and self._yes_rect.collidepoint(mx, my):
                    self._select(self._confirm_overwrite)
                elif hasattr(self, "_no_rect") and self._no_rect.collidepoint(mx, my):
                    self._confirm_overwrite = None
                return
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(mx, my) and self._is_selectable(i):
                    slot = self.slots[i]
                    if (slot is not None
                            and self.mode == "new"
                            and slot.get("faction") != self.faction):
                        self._confirm_overwrite = i
                    else:
                        self._select(i)

    def _is_selectable(self, i: int) -> bool:
        slot = self.slots[i]
        if self.mode == "continue":
            return slot is not None
        return True

    def _select(self, i: int):
        slot = self.slots[i]
        if slot is None:
            slot = sm.new_slot(self.faction)
        self._result = (i + 1, slot)   # 1-indexed slot number

    @property
    def result(self):
        return self._result

    def draw(self, surf):
        self._load_fonts()
        surf.fill(DARK)
        self._card_rects = []

        # Header
        pygame.draw.rect(surf, PANEL, (0, 0, self.sw, 52))
        pygame.draw.line(surf, TEAL_D, (0, 52), (self.sw, 52))
        mode_lbl = "SELECT SAVE SLOT" if self.mode != "continue" else "CONTINUE CAMPAIGN"
        t = self._fonts["title"].render(f"// {mode_lbl}", True, TEAL)
        surf.blit(t, (self.sw // 2 - t.get_width() // 2, 14))

        sub_text = f"FACTION: {sm.FACTION_DISPLAY.get(self.faction, self.faction.upper())}" \
                   if self.mode == "new" else "SELECT AN EXISTING CAMPAIGN TO RESUME"
        sub = self._fonts["px"].render(sub_text, True, ORANGE)
        surf.blit(sub, (self.sw // 2 - sub.get_width() // 2, 38))

        # Slot cards
        card_w = 320
        card_h = 200
        gap    = 24
        total_w = sm.NUM_SLOTS * card_w + (sm.NUM_SLOTS - 1) * gap
        x0 = self.sw // 2 - total_w // 2
        y0 = self.sh // 2 - card_h // 2 - 20

        for i, slot in enumerate(self.slots):
            cx = x0 + i * (card_w + gap)
            crect = pygame.Rect(cx, y0, card_w, card_h)
            self._card_rects.append(crect)
            selectable = self._is_selectable(i)
            hover      = (self._hover == i)

            # Background
            bg = (14, 30, 22) if hover and selectable else PANEL
            pygame.draw.rect(surf, bg, crect)

            # Border
            if not selectable:
                bc = (30, 35, 32)
            elif hover:
                bc = TEAL
            elif slot and slot.get("faction") == self.faction:
                bc = FACTION_COL.get(self.faction, TEAL_M)
            else:
                bc = TEAL_D
            pygame.draw.rect(surf, bc, crect, 2 if hover else 1)

            # Slot number
            sn = self._fonts["px"].render(f"SLOT {i + 1}", True, TEAL_D)
            surf.blit(sn, (cx + 8, y0 + 8))

            if slot is None:
                # Empty slot
                emp = self._fonts["med"].render("[ EMPTY ]", True,
                                                TEAL_M if selectable else (40, 50, 45))
                surf.blit(emp, (cx + card_w // 2 - emp.get_width() // 2,
                                y0 + card_h // 2 - emp.get_height() // 2))
                if selectable and self.mode != "continue":
                    new_lbl = self._fonts["px"].render("NEW CAMPAIGN", True, TEAL_D)
                    surf.blit(new_lbl, (cx + card_w // 2 - new_lbl.get_width() // 2,
                                        y0 + card_h // 2 + 14))
            else:
                # Filled slot — show details
                faction   = slot.get("faction", "unknown")
                fcol      = FACTION_COL.get(faction, TEAL_M)
                fname     = sm.FACTION_DISPLAY.get(faction, faction.upper())
                phase     = slot.get("map_phase", 0)
                missions  = slot.get("mission_count", 0)
                timestamp = slot.get("timestamp", "")
                infamy    = slot.get("infamy_carryover", 0)
                credits   = slot.get("credits_carryover", 0)
                lp        = slot.get("lp", 0)

                # Faction swatch + name
                pygame.draw.rect(surf, fcol, (cx + 10, y0 + 24, 14, 14))
                fn = self._fonts["med"].render(fname, True, fcol if selectable else (60, 70, 65))
                surf.blit(fn, (cx + 30, y0 + 24))

                # Phase badge
                phase_str = sm.PHASE_DISPLAY[min(phase, 2)]
                phase_col = (GREEN, GOLD, RED)[min(phase, 2)]
                pb = self._fonts["px"].render(f"MAP: {phase_str}", True, phase_col)
                surf.blit(pb, (cx + card_w - pb.get_width() - 8, y0 + 8))

                # Stats
                rows = [
                    ("MISSIONS COMPLETED", str(missions)),
                    ("CARRY-IN INFAMY",    str(infamy)),
                    ("CARRY-IN CREDITS",   f"§{credits}"),
                    ("LEGACY POINTS",      str(lp)),
                ]
                for j, (label, val) in enumerate(rows):
                    ry = y0 + 54 + j * 24
                    lbl = self._fonts["px"].render(label, True, TEAL_D)
                    vl  = self._fonts["sm"].render(val,   True, TEAL if selectable else (60, 80, 70))
                    surf.blit(lbl, (cx + 12,                    ry))
                    surf.blit(vl,  (cx + card_w - vl.get_width() - 12, ry))
                    pygame.draw.line(surf, (12, 28, 20),
                                     (cx + 12, ry + 14), (cx + card_w - 12, ry + 14))

                # Timestamp
                ts = self._fonts["px"].render(timestamp, True, (40, 60, 50))
                surf.blit(ts, (cx + card_w // 2 - ts.get_width() // 2, y0 + card_h - 18))

                # Overwrite warning
                if (self.mode == "new" and selectable
                        and slot.get("faction") != self.faction and hover):
                    warn = self._fonts["px"].render("⚠ CLICK TO OVERWRITE", True, RED)
                    surf.blit(warn, (cx + card_w // 2 - warn.get_width() // 2,
                                     y0 + card_h - 32))

        # Overwrite confirm dialog
        if self._confirm_overwrite is not None:
            self._draw_confirm(surf)

        # Footer
        foot = self._fonts["px"].render(
            "CLICK SLOT TO SELECT  ·  ESC — BACK TO MENU", True, TEAL_D)
        surf.blit(foot, (self.sw // 2 - foot.get_width() // 2, self.sh - 20))

    def _draw_confirm(self, surf):
        dw, dh = 340, 120
        dx = self.sw // 2 - dw // 2
        dy = self.sh // 2 - dh // 2

        pygame.draw.rect(surf, (6, 14, 10), (dx, dy, dw, dh))
        pygame.draw.rect(surf, RED, (dx, dy, dw, dh), 2)

        f = self._fonts["sm"]
        t = f.render("OVERWRITE THIS CAMPAIGN SLOT?", True, RED)
        surf.blit(t, (dx + dw // 2 - t.get_width() // 2, dy + 14))
        s = self._fonts["px"].render("Existing progress will be lost.", True, TEAL_D)
        surf.blit(s, (dx + dw // 2 - s.get_width() // 2, dy + 34))

        btn_w, btn_h = 100, 30
        self._yes_rect = pygame.Rect(dx + 40,        dy + 68, btn_w, btn_h)
        self._no_rect  = pygame.Rect(dx + dw - 140,  dy + 68, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        for rect, label, col in [
            (self._yes_rect, "OVERWRITE", RED),
            (self._no_rect,  "CANCEL",    TEAL),
        ]:
            hover_col = tuple(min(255, c + 40) for c in col) if rect.collidepoint(mx, my) else col
            pygame.draw.rect(surf, PANEL, rect)
            pygame.draw.rect(surf, hover_col, rect, 2)
            lbl = self._fonts["med"].render(label, True, hover_col)
            surf.blit(lbl, (rect.x + rect.w // 2 - lbl.get_width() // 2,
                            rect.y + rect.h // 2 - lbl.get_height() // 2))


def run(screen, clock, faction: str, mode: str = "any", fps: int = 60):
    """Block until player selects a slot. Returns (slot_num, slot_data)."""
    w, h   = screen.get_size()
    picker = SlotSelect(w, h, faction, mode)
    while picker.result is None:
        dt = clock.tick(fps)
        for event in pygame.event.get():
            picker.handle_event(event)
            if event.type == pygame.USEREVENT and event.dict.get("back"):
                return None   # player pressed ESC → back to menu
        picker.draw(screen)
        pygame.display.flip()
    return picker.result
