"""Mission objective system — primary + secondary directives."""
import pygame

STATUS_ACTIVE   = "active"
STATUS_COMPLETE = "complete"

TEAL  = (0, 220, 180)
GREEN = (40, 220, 100)
DIM   = (0, 120, 90)
GOLD  = (220, 180, 40)


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
    def __init__(self, player_faction, enemy_faction):
        self.player_faction = player_faction
        self.enemy_faction  = enemy_faction
        self._font_hdr = None
        self._font_sm  = None

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
            self._font_hdr = pygame.font.SysFont("couriernew", 9, bold=True)
            self._font_sm  = pygame.font.SysFont("couriernew", 8)

        from game.hud import TOPBAR_H, SIDEBAR_W
        obj_h   = 17
        panel_w = 230
        total_h = 13 + obj_h * (1 + len(self.secondaries)) + 6
        x = sw - SIDEBAR_W - panel_w - 8
        y = TOPBAR_H + 8

        bg = pygame.Surface((panel_w, total_h), pygame.SRCALPHA)
        bg.fill((4, 12, 10, 210))
        surf.blit(bg, (x, y))
        pygame.draw.rect(surf, (0, 55, 40), (x, y, panel_w, total_h), 1)

        hdr = self._font_hdr.render("▸ DIRECTIVES", True, TEAL)
        surf.blit(hdr, (x + 6, y + 3))

        oy = y + 13
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
