"""
Civilian NPCs — the "Kirk Protesters" (Tiberium equivalent).
Wander the map, generate credits when processed/detained.
"""
import random, math, pygame
from game.unit_entity import FACTION_COLORS

# Civilian Types
NORMIE      = "normie"
PURPLE_HAIR = "purple_hair" # Higher threat/value
RIOT_GEAR   = "riot_gear"   # Self-taught tactician
RUNNER      = "runner"      # HVP (High Value Person)

class Civilian:
    _next_id = 0

    def __init__(self, gx, gy, ctype=NORMIE):
        Civilian._next_id += 1
        self.uid = Civilian._next_id
        self.gx = float(gx)
        self.gy = float(gy)
        self.ctype = ctype
        self.faction = "neutral"
        
        self.hp = 50
        self.speed = 1.2
        if ctype == RUNNER:
            self.speed = 4.5
            
        self.state = "idle"
        self.waypoints = []
        self._wander_timer = 0.0
        self._panic_timer = 0.0
        
    def update(self, dt_sec, world):
        if self.state == "dead":
            return
            
        if self._panic_timer > 0:
            self._panic_timer -= dt_sec
            self.speed = 3.5
        else:
            self.speed = 1.2 if self.ctype != RUNNER else 4.5

        if world.roe_manager.current_roe == 5:
            self.panic()

        if self.waypoints:
            self._move_along_path(dt_sec)
        else:
            self._wander_logic(dt_sec)
            
    def panic(self):
        self._panic_timer = 10.0
        # Set a random waypoint far away
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(5, 10)
        self.waypoints = [(int(self.gx + math.cos(angle) * dist), 
                          int(self.gy + math.sin(angle) * dist))]

    def _wander_logic(self, dt_sec):
        self._wander_timer -= dt_sec
        if self._wander_timer <= 0:
            self._wander_timer = random.uniform(2, 6)
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1, 4)
            self.waypoints = [(int(self.gx + math.cos(angle) * dist), 
                              int(self.gy + math.sin(angle) * dist))]

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

    def take_damage(self, amount, world):
        self.hp -= amount
        if self.hp <= 0:
            self.state = "dead"
            world.roe_manager.add_infamy(50) # Big infamy for killing civs
        else:
            self.panic()

    def draw(self, surf, cam):
        if self.state == "dead": return
        sx, sy = cam.world_to_screen(self.gx, self.gy)
        
        # Simple dot for now
        col = (180, 180, 160)
        if self.ctype == PURPLE_HAIR: col = (180, 50, 255)
        if self.ctype == RIOT_GEAR:   col = (255, 140, 0)
        if self.ctype == RUNNER:      col = (255, 255, 0)
        if self.ctype == KIRK:        col = (255, 255, 255)
        
        if self._panic_timer > 0:
            # flash red
            if int(pygame.time.get_ticks() / 200) % 2 == 0:
                col = (255, 0, 0)

        pygame.draw.circle(surf, (0, 0, 0, 100), (sx, sy - 2), 6) # shadow
        
        if self.ctype == KIRK:
            # Draw a little podium
            pygame.draw.rect(surf, (60, 60, 60), (sx - 8, sy - 4, 16, 6))
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy - 8), 6)
            # pulsing halo
            s = math.sin(pygame.time.get_ticks() * 0.005) * 2
            pygame.draw.circle(surf, (255, 255, 200), (sx, sy - 8), int(8 + s), 1)
        else:
            pygame.draw.circle(surf, col, (sx, sy - 6), 5)
