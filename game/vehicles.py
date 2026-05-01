"""Civilian vehicle system — ambient cars, wrecks, VBIED (Sovereign paranoia mechanic)."""
import math, random, pygame

# Visual palette variants for parked cars
_CAR_COLS = [
    (55, 70, 60),   # dark teal
    (50, 60, 50),   # muted green
    (60, 55, 45),   # brown-grey
    (45, 55, 65),   # slate
    (65, 50, 50),   # dark red-grey
]


class CivilianCar:
    _next_id   = 0
    VBIED_SPEED   = 5.5   # tiles / sec when armed
    VBIED_RADIUS  = 3.0   # explosion radius in tiles
    VBIED_DAMAGE  = 90    # HP damage on direct hit
    VBIED_INFAMY  = 40    # infamy added on detonation

    def __init__(self, gx, gy):
        CivilianCar._next_id += 1
        self.uid   = CivilianCar._next_id
        self.gx    = float(gx)
        self.gy    = float(gy)
        self.col   = random.choice(_CAR_COLS)
        self.state = "parked"             # parked / vbied / wrecked
        self._vbied_tx = None             # target tile (gx, gy)
        self._vbied_ty = None

    # ── API ───────────────────────────────────────────────────────────────────

    def arm_vbied(self, target_gx, target_gy):
        self.state      = "vbied"
        self._vbied_tx  = float(target_gx)
        self._vbied_ty  = float(target_gy)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt, world):
        if self.state != "vbied":
            return
        tx, ty = self._vbied_tx, self._vbied_ty
        dx, dy = tx - self.gx, ty - self.gy
        dist   = math.sqrt(dx * dx + dy * dy)
        if dist < 0.6:
            self._detonate(world)
        else:
            step    = self.VBIED_SPEED * dt
            self.gx += dx / dist * min(step, dist)
            self.gy += dy / dist * min(step, dist)

    def _detonate(self, world):
        self.state = "wrecked"
        from game.unit_entity import STATE_DEAD
        for u in list(world.units.values()):
            if u.state == STATE_DEAD:
                continue
            if math.dist((u.gx, u.gy), (self.gx, self.gy)) <= self.VBIED_RADIUS:
                u.take_damage(self.VBIED_DAMAGE, world)
        world.roe_manager.add_infamy(self.VBIED_INFAMY)
        world.events.append(("vbied_explode", {"gx": self.gx, "gy": self.gy}))

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, cam, fog):
        if not fog.is_explored(int(self.gx), int(self.gy)):
            return

        sx, sy = cam.world_to_screen(self.gx, self.gy)
        sy_top = sy - 8   # offset so car sits on tile surface

        if self.state == "wrecked":
            # Charred wreck X
            pygame.draw.ellipse(surf, (25, 15, 8), (sx - 10, sy_top - 2, 20, 8))
            pygame.draw.line(surf, (70, 45, 20), (sx - 8, sy_top - 7), (sx + 8, sy_top + 1), 2)
            pygame.draw.line(surf, (70, 45, 20), (sx + 8, sy_top - 7), (sx - 8, sy_top + 1), 2)
            return

        # Shadow
        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 10, sy - 3, 20, 7))

        # Pulsing glow when armed as VBIED
        if self.state == "vbied":
            pulse = int(7 + math.sin(pygame.time.get_ticks() * 0.009) * 3)
            pygame.draw.circle(surf, (200, 30, 30), (sx, sy_top), pulse, 1)

        col = (200, 40, 40) if self.state == "vbied" else self.col

        # Body (small rectangle sedan)
        pts = [
            (sx - 9, sy_top - 4),
            (sx + 9, sy_top - 4),
            (sx + 9, sy_top + 4),
            (sx - 9, sy_top + 4),
        ]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

        # Windshield glint
        pygame.draw.line(surf, (100, 160, 130),
                         (sx - 5, sy_top - 3), (sx + 5, sy_top - 3), 1)
