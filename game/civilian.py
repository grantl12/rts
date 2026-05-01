"""
Civilian NPCs — the Witness War resource.
Every civilian is a tug-of-war between factions:
  free       — wandering, unclaimed
  empowered  — Frontline converted; stationary, generates Viral Clout
  radicalized— Sovereign converted; becomes Militia unit on completion
  assetized  — Oligarchy converted; generates Insurance Payout on nearby unit death
  detained   — Regency absorbed; removed into pen's civs_held count
"""
import random, math, pygame
from game.unit_entity import FACTION_COLORS

NORMIE      = "normie"
PURPLE_HAIR = "purple_hair"
RIOT_GEAR   = "riot_gear"
RUNNER      = "runner"
KIRK        = "kirk"

RUNNER_DESTINATIONS = [(51, 4), (4, 21), (4, 39)]

# Witness War conversion constants
_CONVERT_TIME = {
    "frontline": 8.0,    # seconds to empower
    "sovereign": 12.0,   # seconds to radicalize
    "oligarchy": 5.0,    # seconds to assetize
}
_CONVERT_RANGE = {
    "frontline": 3.5,
    "sovereign": 2.5,
    "oligarchy": 4.0,
}
# Colour for each witness state (used in draw)
_STATE_COLS = {
    "empowered":  (80, 220, 80),
    "radicalized":(160, 40, 220),
    "assetized":  (220, 180, 40),
}


class Civilian:
    _next_id = 0

    def __init__(self, gx, gy, ctype=NORMIE):
        Civilian._next_id += 1
        self.uid   = Civilian._next_id
        self.gx    = float(gx)
        self.gy    = float(gy)
        self.ctype = ctype
        self.faction = "neutral"

        self.hp    = 50
        self.speed = 1.2
        if ctype == RUNNER:
            self.speed = 4.5

        self.state = "idle"
        self.waypoints    = []
        self._wander_timer = 0.0
        self._panic_timer  = 0.0

        self._destination    = None
        self._reached_dest   = False
        self._ambush_spawned = False
        self.is_bolo = False

        # Witness War
        self.witness_state    = "free"   # free / empowered / radicalized / assetized
        self._convert_progress = 0.0    # 0.0 → 1.0
        self._convert_faction  = None   # which faction is currently converting this civ

    # ── API ───────────────────────────────────────────────────────────────────

    def set_destination(self, gx, gy):
        self._destination = (int(gx), int(gy))

    def tick_conversion(self, dt_sec, converting_faction):
        """Called each frame if a converting unit is in range. Returns True when complete."""
        if self.witness_state != "free":
            return False
        if converting_faction != self._convert_faction:
            self._convert_faction  = converting_faction
            self._convert_progress = 0.0
        total = _CONVERT_TIME.get(converting_faction, 10.0)
        self._convert_progress = min(1.0, self._convert_progress + dt_sec / total)
        return self._convert_progress >= 1.0

    def decay_conversion(self, dt_sec):
        """Called when no converting unit is in range — progress fades."""
        if self._convert_progress > 0:
            self._convert_progress = max(0.0, self._convert_progress - dt_sec * 0.25)
        if self._convert_progress == 0:
            self._convert_faction = None

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt_sec, world):
        if self.state == "dead":
            return

        # Empowered civs stand their ground and broadcast
        if self.witness_state == "empowered":
            self.waypoints = []
            self._wander_timer = 99.0
            return

        if self._panic_timer > 0:
            self._panic_timer -= dt_sec
            self.speed = 3.5
        else:
            self.speed = 1.2 if self.ctype != RUNNER else 4.5

        if world.roe_manager.current_roe == 5:
            self.panic(world)

        if self.ctype == RUNNER and self._destination and not self._reached_dest:
            dist_to_dest = math.dist((self.gx, self.gy), self._destination)
            if dist_to_dest < 1.5:
                self._reached_dest = True
            elif not self.waypoints:
                from game.pathfinding import find_path
                blocked = world.blocked_tiles()
                path = find_path((int(self.gx), int(self.gy)), self._destination, blocked)
                self.waypoints = path[1:] if len(path) > 1 else [self._destination]

        if self.waypoints:
            self._move_along_path(dt_sec)
        else:
            self._wander_logic(dt_sec, world)

    def panic(self, world=None):
        self._panic_timer = 10.0
        angle = random.uniform(0, math.pi * 2)
        dist  = random.uniform(5, 10)
        from game.map_data import W, H
        dx = max(1, min(W - 2, int(self.gx + math.cos(angle) * dist)))
        dy = max(1, min(H - 2, int(self.gy + math.sin(angle) * dist)))
        if world:
            from game.pathfinding import find_path
            path = find_path((int(self.gx), int(self.gy)), (dx, dy), world.blocked_tiles())
            self.waypoints = path[1:] if len(path) > 1 else []
        else:
            self.waypoints = [(dx, dy)]

    def _wander_logic(self, dt_sec, world=None):
        self._wander_timer -= dt_sec
        if self._wander_timer <= 0:
            self._wander_timer = random.uniform(2, 6)
            from game.map_data import W, H
            angle = random.uniform(0, math.pi * 2)
            dist  = random.uniform(1, 4)
            dest  = (max(1, min(W - 2, int(self.gx + math.cos(angle) * dist))),
                     max(1, min(H - 2, int(self.gy + math.sin(angle) * dist))))
            if world:
                from game.pathfinding import find_path
                path = find_path((int(self.gx), int(self.gy)), dest, world.blocked_tiles())
                self.waypoints = path[1:] if len(path) > 1 else []
            else:
                self.waypoints = [dest]

    def _move_along_path(self, dt_sec):
        tx, ty = self.waypoints[0]
        dx, dy = tx - self.gx, ty - self.gy
        dist   = math.sqrt(dx*dx + dy*dy)
        step   = self.speed * dt_sec
        if dist < 0.1:
            self.gx, self.gy = float(tx), float(ty)
            self.waypoints.pop(0)
        else:
            self.gx += dx / dist * min(step, dist)
            self.gy += dy / dist * min(step, dist)

    def take_damage(self, amount, world, attacker=None):
        self.hp -= amount
        if self.hp <= 0:
            self.state = "dead"
            world.roe_manager.add_infamy(50)
        else:
            self.panic(world)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, cam):
        if self.state == "dead":
            return
        sx, sy = cam.world_to_screen(self.gx, self.gy)

        col = (180, 180, 160)
        if self.ctype == PURPLE_HAIR: col = (180, 50, 255)
        if self.ctype == RIOT_GEAR:   col = (255, 140, 0)
        if self.ctype == RUNNER:      col = (255, 255, 0)
        if self.ctype == KIRK:        col = (255, 255, 255)

        if self._panic_timer > 0 and int(pygame.time.get_ticks() / 200) % 2 == 0:
            col = (255, 0, 0)

        # Witness state ring — drawn behind the figure
        ws = self.witness_state
        if ws in _STATE_COLS:
            wc  = _STATE_COLS[ws]
            t   = pygame.time.get_ticks()
            if ws == "empowered":
                # Pulsing broadcast ring
                r = int(9 + math.sin(t * 0.007) * 3)
                pygame.draw.circle(surf, wc, (sx, sy - 6), r, 1)
                pygame.draw.circle(surf, wc, (sx, sy - 6), r + 5, 1)
            elif ws == "radicalized":
                # Conversion progress arc
                r = 10
                prog_angle = int(360 * self._convert_progress)
                pygame.draw.circle(surf, wc, (sx, sy - 6), r, 1)
                # Fill arc as progress bar around the circle
                for a in range(0, prog_angle, 6):
                    rad = math.radians(a - 90)
                    px  = sx + int(math.cos(rad) * r)
                    py  = (sy - 6) + int(math.sin(rad) * r)
                    pygame.draw.circle(surf, wc, (px, py), 1)
            elif ws == "assetized":
                # Gold bracket corners
                for ox, oy in ((-8, -14), (3, -14), (-8, -1), (3, -1)):
                    pygame.draw.rect(surf, wc, (sx + ox, sy + oy, 5, 1))
                    pygame.draw.rect(surf, wc, (sx + ox, sy + oy, 1, 5))
        elif ws == "free" and self._convert_progress > 0:
            # In-progress conversion — show faction-coloured partial ring
            fc  = FACTION_COLORS.get(self._convert_faction, (200, 200, 200))
            r   = 10
            prog_angle = int(360 * self._convert_progress)
            for a in range(0, prog_angle, 8):
                rad = math.radians(a - 90)
                px  = sx + int(math.cos(rad) * r)
                py  = (sy - 6) + int(math.sin(rad) * r)
                pygame.draw.circle(surf, fc, (px, py), 1)

        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 5, sy - 2, 10, 4))

        if self.is_bolo:
            r = int(10 + math.sin(pygame.time.get_ticks() * 0.006) * 2)
            pygame.draw.circle(surf, (220, 30, 30), (sx, sy - 6), r, 1)
            pygame.draw.line(surf, (220, 30, 30), (sx - r, sy - 6), (sx + r, sy - 6), 1)
            pygame.draw.line(surf, (220, 30, 30), (sx, sy - 6 - r), (sx, sy - 6 + r), 1)
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("BOLO", True, (255, 80, 80))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 22))

        if self.ctype == KIRK:
            pygame.draw.rect(surf, (60, 60, 60), (sx - 8, sy - 4, 16, 6))
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy - 8), 6)
            s = math.sin(pygame.time.get_ticks() * 0.005) * 2
            pygame.draw.circle(surf, (255, 255, 200), (sx, sy - 8), int(8 + s), 1)
        elif self.ctype == RUNNER:
            pts = [(sx, sy - 10), (sx + 5, sy - 5), (sx, sy), (sx - 5, sy - 5)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (0, 0, 0), pts, 1)
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("HVP", True, (255, 255, 100))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 18))
        else:
            pygame.draw.circle(surf, col, (sx, sy - 6), 5)
            pygame.draw.circle(surf, (0, 0, 0), (sx, sy - 6), 5, 1)

        # Witness state label
        if ws == "empowered":
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("LIVE", True, _STATE_COLS["empowered"])
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 20))
        elif ws == "assetized":
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("ASSET", True, _STATE_COLS["assetized"])
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 20))
