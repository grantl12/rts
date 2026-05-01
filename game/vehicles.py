"""Civilian vehicle system — ambient cars, wrecks, VBIED (Sovereign paranoia mechanic)."""
import math, random, pygame

_CAR_COLS = [
    (55, 70, 60),
    (50, 60, 50),
    (60, 55, 45),
    (45, 55, 65),
    (65, 50, 50),
]


def _facing_from_dir(dx, dy):
    """Map world-space movement vector to facing index (0=SW 1=SE 2=NE 3=NW)."""
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        return 1
    if dx >= 0 and dy >= 0:
        return 1   # SE
    if dx >= 0 and dy < 0:
        return 2   # NE
    if dx < 0 and dy >= 0:
        return 0   # SW
    return 3       # NW


class CivilianCar:
    _next_id   = 0
    VBIED_SPEED   = 5.5
    VBIED_RADIUS  = 3.0
    VBIED_DAMAGE  = 90
    VBIED_INFAMY  = 40

    def __init__(self, gx, gy):
        CivilianCar._next_id += 1
        self.uid    = CivilianCar._next_id
        self.gx     = float(gx)
        self.gy     = float(gy)
        self.col    = random.choice(_CAR_COLS)
        self.state  = "parked"
        self.facing = random.randint(0, 3)
        self._vbied_tx = None
        self._vbied_ty = None

    def arm_vbied(self, target_gx, target_gy):
        self.state      = "vbied"
        self._vbied_tx  = float(target_gx)
        self._vbied_ty  = float(target_gy)

    def update(self, dt, world):
        if self.state != "vbied":
            return
        tx, ty = self._vbied_tx, self._vbied_ty
        dx, dy = tx - self.gx, ty - self.gy
        dist   = math.sqrt(dx * dx + dy * dy)
        if dist < 0.6:
            self._detonate(world)
        else:
            step        = self.VBIED_SPEED * dt
            self.gx    += dx / dist * min(step, dist)
            self.gy    += dy / dist * min(step, dist)
            self.facing = _facing_from_dir(dx, dy)

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

    def draw(self, surf, cam, fog):
        if not fog.is_explored(int(self.gx), int(self.gy)):
            return

        sx, sy = cam.world_to_screen(self.gx, self.gy)
        sy_top = sy - 8

        if self.state == "wrecked":
            pygame.draw.ellipse(surf, (25, 15, 8), (sx - 10, sy_top - 2, 20, 8))
            pygame.draw.line(surf, (70, 45, 20), (sx - 8, sy_top - 7), (sx + 8, sy_top + 1), 2)
            pygame.draw.line(surf, (70, 45, 20), (sx + 8, sy_top - 7), (sx - 8, sy_top + 1), 2)
            return

        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 10, sy - 3, 20, 7))

        if self.state == "vbied":
            pulse = int(7 + math.sin(pygame.time.get_ticks() * 0.009) * 3)
            pygame.draw.circle(surf, (200, 30, 30), (sx, sy_top), pulse, 1)

        # Try sprite first
        from game.sprites import get_manager
        stype  = "vbied" if self.state == "vbied" else "civilian_car"
        moving = self.state == "vbied"
        frame  = get_manager().get_frame(stype, self.facing, moving)

        if frame:
            if self.state == "vbied":
                # Red tint overlay for armed car
                tinted = frame.copy()
                tinted.fill((255, 80, 80, 100), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(tinted, (sx - frame.get_width() // 2, sy_top - frame.get_height() // 2))
            else:
                surf.blit(frame, (sx - frame.get_width() // 2, sy_top - frame.get_height() // 2))
        else:
            col = (200, 40, 40) if self.state == "vbied" else self.col
            pts = [
                (sx - 9, sy_top - 4),
                (sx + 9, sy_top - 4),
                (sx + 9, sy_top + 4),
                (sx - 9, sy_top + 4),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (0, 0, 0), pts, 1)
            pygame.draw.line(surf, (100, 160, 130),
                             (sx - 5, sy_top - 3), (sx + 5, sy_top - 3), 1)
