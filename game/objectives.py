"""Mission objective system — primary + secondary directives."""
import pygame

STATUS_ACTIVE   = "active"
STATUS_COMPLETE = "complete"

TEAL  = (0, 220, 180)
GREEN = (40, 220, 100)
DIM   = (0, 120, 90)
GOLD  = (220, 180, 40)
RED   = (220, 80, 60)


class Objective:
    def __init__(self, label, check_fn, secondary=False):
        self.label     = label
        self.check_fn  = check_fn
        self.secondary = secondary
        self.status    = STATUS_ACTIVE
        self.progress  = ""

    def update(self, world):
        if self.status == STATUS_COMPLETE:
            return
        complete, prog = self.check_fn(world)
        self.progress = prog
        if complete:
            self.status = STATUS_COMPLETE


class ObjectiveManager:
    def __init__(self, player_faction, enemy_faction, map_id="quad"):
        self.player_faction = player_faction
        self.enemy_faction  = enemy_faction
        self.map_id         = map_id
        self.ng_timer       = -1.0   # updated each frame by main.py for district map
        self._font_hdr = None
        self._font_sm  = None
        self._font_cdown = None

        if map_id == "district":
            self.primary = Objective(
                "HOLD UNTIL NG ARRIVAL",
                self._check_ng_arrived,
            )
            self.secondaries = [
                Objective(
                    "DETAIN 5 CIVILIANS",
                    lambda w: self._check_civs_detained(w, 5),
                    secondary=True,
                ),
                Objective(
                    "CONTROL 4 LOCATIONS",
                    lambda w: self._check_locations_held(w, 4),
                    secondary=True,
                ),
            ]
        else:
            self.primary = Objective(
                "NEUTRALIZE ENEMY COMMAND",
                self._check_enemy_hq,
            )
            self.secondaries = [
                Objective(
                    "PROCESS 10 CIVILIANS",
                    lambda w: self._check_civs_detained(w, 10),
                    secondary=True,
                ),
                Objective(
                    "CONTROL 4 LOCATIONS",
                    lambda w: self._check_locations_held(w, 4),
                    secondary=True,
                ),
            ]

    # ── Checks ────────────────────────────────────────────────────────────────

    def _check_enemy_hq(self, world):
        alive = any(
            pb.faction == self.enemy_faction
            and "command" in pb.bdef.get("flags", [])
            for pb in world.placed_buildings.values()
        )
        return not alive, ""

    def _check_ng_arrived(self, world):
        return world.game_over == world.GAME_OVER_VICTORY, ""

    def _check_civs_detained(self, world, target):
        total = sum(
            pb.civs_held for pb in world.placed_buildings.values()
            if pb.faction == self.player_faction
        )
        return total >= target, f"{min(total, target)}/{target}"

    def _check_locations_held(self, world, target):
        held = sum(
            1 for pb in world.placed_buildings.values()
            if pb.faction == self.player_faction
            and "command" not in pb.bdef.get("flags", [])
        )
        return held >= target, f"{min(held, target)}/{target}"

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, world):
        self.primary.update(world)
        for obj in self.secondaries:
            obj.update(world)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, sw, sh):
        if self._font_hdr is None:
            self._font_hdr   = pygame.font.SysFont("couriernew", 11, bold=True)
            self._font_sm    = pygame.font.SysFont("couriernew", 10)
            self._font_cdown = pygame.font.SysFont("couriernew", 18, bold=True)

        from game.hud import TOPBAR_H, SIDEBAR_W
        obj_h   = 20
        panel_w = 260
        # Extra height for NG countdown row when active
        ng_row  = 30 if (self.map_id == "district" and self.ng_timer > 0
                         and self.primary.status != STATUS_COMPLETE) else 0
        total_h = 13 + obj_h * (1 + len(self.secondaries)) + ng_row + 6
        x = sw - SIDEBAR_W - panel_w - 8
        y = TOPBAR_H + 8

        bg = pygame.Surface((panel_w, total_h), pygame.SRCALPHA)
        bg.fill((4, 12, 10, 210))
        surf.blit(bg, (x, y))
        pygame.draw.rect(surf, (0, 55, 40), (x, y, panel_w, total_h), 1)

        hdr = self._font_hdr.render("▸ DIRECTIVES", True, TEAL)
        surf.blit(hdr, (x + 6, y + 3))

        oy = y + 13

        # NG countdown bar — shown above the objective list for district map
        if ng_row:
            secs_left = max(0, int(self.ng_timer))
            mins = secs_left // 60
            secs = secs_left % 60
            frac = self.ng_timer / 300.0
            bar_w = panel_w - 12
            # background track
            pygame.draw.rect(surf, (20, 40, 30), (x + 6, oy, bar_w, 10))
            # fill — green → yellow → red as timer shrinks
            if frac > 0.5:
                fill_col = (40, 200, 100)
            elif frac > 0.25:
                fill_col = (220, 180, 40)
            else:
                fill_col = (220, 60, 40)
            pygame.draw.rect(surf, fill_col, (x + 6, oy, int(bar_w * frac), 10))
            pygame.draw.rect(surf, (0, 80, 60), (x + 6, oy, bar_w, 10), 1)

            cd_txt = self._font_cdown.render(f"T-{mins}:{secs:02d}", True, fill_col)
            surf.blit(cd_txt, (x + panel_w // 2 - cd_txt.get_width() // 2, oy + 10))
            oy += ng_row

        for obj in [self.primary] + self.secondaries:
            if obj.status == STATUS_COMPLETE:
                col  = GREEN
                icon = "✓"
            elif obj.secondary:
                col  = DIM
                icon = "○"
            else:
                col  = GOLD
                icon = "●"

            lbl = self._font_sm.render(f"{icon} {obj.label}", True, col)
            surf.blit(lbl, (x + 6, oy + 3))

            if obj.progress:
                prog = self._font_sm.render(obj.progress, True, (0, 150, 100))
                surf.blit(prog, (x + panel_w - prog.get_width() - 6, oy + 3))

            oy += obj_h
