"""Unit entity — movement, combat, rendering."""
import math, pygame

# ── Unit stat table ────────────────────────────────────────────────────────────
UNIT_DEFS = {
    #           hp   spd  dmg  range atk_cd  armor        faction       cost
    "gravy_seal":    (120, 2.8, 14,  4.0, 1.2,  "light",     "regency",   200),
    "ice_agent":     (180, 2.2, 18,  3.5, 1.5,  "medium",    "regency",   350),
    "protester":     ( 60, 3.2,  0,  0.0, 0.0,  "unarmored", "neutral",     0),
    "proxy":         (100, 3.5, 22,  5.0, 1.0,  "light",     "sovereign", 280),
    "contractor":    (300, 1.8, 30,  5.5, 2.0,  "heavy",     "oligarchy", 500),
    "drone_scout":   ( 80, 5.0, 10,  6.0, 0.8,  "light",     "frontline", 300),
    "drone_assault": (200, 3.5, 28,  5.5, 1.2,  "medium",    "frontline", 550),
    "unmarked_van":  (400, 3.0, 20,  4.0, 1.5,  "medium",    "regency",   450),
}

FACTION_COLORS = {
    "regency":   (28,  80, 180),
    "frontline": (80, 140,  40),
    "sovereign": (140, 40, 200),
    "oligarchy": ( 40,  40,  40),
    "neutral":   (160, 140, 100),
}

ARMOR_MOD = {
    # attacker vs armor type -> damage multiplier
    ("light",   "unarmored"): 1.5,
    ("light",   "light"):     1.0,
    ("light",   "medium"):    0.7,
    ("light",   "heavy"):     0.4,
    ("medium",  "unarmored"): 2.0,
    ("medium",  "light"):     1.2,
    ("medium",  "medium"):    1.0,
    ("medium",  "heavy"):     0.6,
    ("heavy",   "unarmored"): 2.5,
    ("heavy",   "light"):     1.5,
    ("heavy",   "medium"):    1.2,
    ("heavy",   "heavy"):     1.0,
}

STATE_IDLE     = "idle"
STATE_MOVING   = "moving"
STATE_ATTACK   = "attacking"
STATE_DEAD     = "dead"


class Unit:
    _next_id = 0
    RANK_STAT_BONUS = 0.08
    RANK_NAMES = ["AGENT", "FIELD AGENT", "SR. OPERATIVE", "DEPT. HEAD", "EXECUTIVE"]

    def __init__(self, utype: str, faction: str, gx: float, gy: float):
        Unit._next_id += 1
        self.uid     = Unit._next_id
        self.utype   = utype
        self.faction = faction
        self.gx      = float(gx)
        self.gy      = float(gy)

        hp, spd, dmg, rng, atk_cd, armor, _f, _c = UNIT_DEFS.get(
            utype, (100, 2.0, 10, 3.0, 1.0, "light", faction, 0))
        self.max_hp      = hp
        self.hp          = hp
        self.speed       = spd          # tiles per second
        self.damage      = dmg
        self.attack_range= rng          # tiles
        self.atk_cooldown_max = atk_cd  # seconds
        self.armor_type  = armor

        self.rank         = 1
        self.xp           = 0.0
        self.xp_to_next   = 100.0

        self.state        = STATE_IDLE
        self.waypoints    = []          # list of (gx,gy) ints
        self.target_uid   = None        # enemy uid
        self.atk_timer    = 0.0
        self.flash_timer  = 0.0         # white flash on hit
        self.facing       = 0           # 0=SW 1=SE 2=NE 3=NW

        self.selected     = False
        self.garrisoned_in= None        # building id if inside
        self.target_building_id = None  # ID of building to enter

        self.suppressed      = False
        self._suppress_timer = 0.0      # counts down; >0 = suppressed

    # ── Orders ────────────────────────────────────────────────────────────────

    def order_move(self, waypoints):
        self.waypoints  = list(waypoints)
        self.target_uid = None
        self.target_building_id = None
        self.state      = STATE_MOVING

    def order_attack(self, target_uid, waypoints=None):
        self.target_uid = target_uid
        self.target_building_id = None
        self.waypoints  = list(waypoints) if waypoints else []
        self.state      = STATE_ATTACK if not waypoints else STATE_MOVING

    def order_garrison(self, bid, waypoints):
        self.target_building_id = bid
        self.target_uid = None
        self.waypoints = list(waypoints)
        self.state = STATE_MOVING

    def order_stop(self):
        self.waypoints  = []
        self.target_uid = None
        self.target_building_id = None
        self.state      = STATE_IDLE

    def suppress(self, duration=3.0):
        self._suppress_timer = max(self._suppress_timer, duration)
        self.suppressed = True

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt_sec: float, world):
        if self.state == STATE_DEAD:
            return

        self.flash_timer = max(0.0, self.flash_timer - dt_sec)
        self.atk_timer   = max(0.0, self.atk_timer - dt_sec)
        if self._suppress_timer > 0:
            self._suppress_timer -= dt_sec
            self.suppressed = self._suppress_timer > 0
        else:
            self.suppressed = False

        # Panic retreat at <10% HP — flee toward nearest friendly building
        if (self.hp > 0 and self.hp / self.max_hp < 0.10
                and self.state != STATE_MOVING and not self.waypoints
                and not self.garrisoned_in):
            hq = next((pb for pb in world.placed_buildings.values()
                       if pb.faction == self.faction
                       and "command" in pb.bdef.get("flags", [])), None)
            if hq:
                from game.pathfinding import find_path
                blocked = world.blocked_tiles()
                wp = find_path((self.gx, self.gy), (hq.gx, hq.gy), blocked)
                if wp:
                    self.order_move(wp[1:])

        # ── Garrisoned Logic ──
        if self.garrisoned_in:
            pb = world.placed_buildings.get(self.garrisoned_in)
            if not pb or pb.hp <= 0:
                self.garrisoned_in = None
                self.state = STATE_IDLE
                return
            
            # Fire from windows
            if self.damage > 0:
                enemy = world.nearest_enemy(self, max_range=self.attack_range * 1.3) # Bonus range from windows
                if enemy:
                    self._do_attack(enemy, dt_sec, world)
            return

        # ── Standard Update ──
        target = world.units.get(self.target_uid)
        if target and target.state == STATE_DEAD:
            self.target_uid = None
            target = None

        # Check for entering target building
        if self.target_building_id:
            pb = world.placed_buildings.get(self.target_building_id)
            if pb:
                dist = math.dist((self.gx, self.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2))
                if dist < 1.5:
                    if pb.faction == self.faction and len(pb.garrison) < pb.bdef.get("garrison", 0):
                        pb.garrison.append(self.uid)
                        self.garrisoned_in = pb.bid
                        self.waypoints = []
                        self.state = STATE_IDLE
                        return
                    else:
                        # Building full or not mine, stop
                        self.target_building_id = None
                        self.state = STATE_IDLE
            else:
                self.target_building_id = None

        if self.state == STATE_ATTACK or (self.state == STATE_MOVING and target):
            dist = math.dist((self.gx, self.gy), (target.gx, target.gy)) if target else 999
            if target and dist <= self.attack_range:
                self.waypoints = []
                self.state = STATE_ATTACK
                self._do_attack(target, dt_sec, world)
                return
            elif not self.waypoints and target:
                # Re-path toward target
                from game.pathfinding import find_path
                blocked = world.blocked_tiles()
                wp = find_path((self.gx, self.gy), (target.gx, target.gy), blocked)
                self.waypoints = wp[1:] if len(wp) > 1 else []

        if self.waypoints:
            self._move_along_path(dt_sec)
        elif self.state == STATE_MOVING:
            self.state = STATE_IDLE

    def _move_along_path(self, dt_sec):
        tx, ty = self.waypoints[0]
        dx, dy = tx - self.gx, ty - self.gy
        dist   = math.sqrt(dx*dx + dy*dy)
        step   = self.speed * dt_sec

        if dist < 0.05:
            self.gx, self.gy = float(tx), float(ty)
            self.waypoints.pop(0)
        else:
            self.gx += dx / dist * min(step, dist)
            self.gy += dy / dist * min(step, dist)
            # facing direction from movement angle
            angle = math.atan2(dy, dx) * 180 / math.pi
            if   -135 <= angle < -45:  self.facing = 2  # NE
            elif  -45 <= angle <  45:  self.facing = 1  # SE
            elif   45 <= angle < 135:  self.facing = 3  # NW (going south in iso)
            else:                       self.facing = 0  # SW

        self.state = STATE_MOVING if self.waypoints else STATE_IDLE

    def _do_attack(self, target, dt_sec, world):
        if self.suppressed:
            return
        if self.atk_timer <= 0:
            # ROE damage multiplier
            roe_mult = world.roe_manager.get_damage_mult() if self.faction == "regency" else 1.0
            # Rank bonus
            rank_mult = 1.0 + (self.rank - 1) * self.RANK_STAT_BONUS
            
            atk_dmg = self.damage * roe_mult * rank_mult
            
            mod = ARMOR_MOD.get(("light", target.armor_type), 1.0)
            # rough weapon class mapping
            if self.armor_type == "heavy":
                mod = ARMOR_MOD.get(("heavy", target.armor_type), 1.0)
            elif self.armor_type == "medium":
                mod = ARMOR_MOD.get(("medium", target.armor_type), 1.0)
            
            target.take_damage(int(atk_dmg * mod), world, attacker=self)
            self._gain_xp(5.0)
            
            self.atk_timer = self.atk_cooldown_max
            # face the target
            dx = target.gx - self.gx
            dy = target.gy - self.gy
            angle = math.atan2(dy, dx) * 180 / math.pi
            if   -135 <= angle < -45:  self.facing = 2
            elif  -45 <= angle <  45:  self.facing = 1
            elif   45 <= angle < 135:  self.facing = 3
            else:                       self.facing = 0

    def _gain_xp(self, amount):
        if self.rank >= 5:
            return
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.rank += 1
            self.xp_to_next *= 1.5
            # Heal on rank up
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.2)

    def take_damage(self, amount, world=None, attacker=None):
        self.hp = max(0, self.hp - amount)
        self.flash_timer = 0.12
        if self.hp == 0:
            self.state = STATE_DEAD
            if attacker:
                attacker._gain_xp(25.0)  # kill bonus XP
            if world and self.faction == "neutral":
                world.roe_manager.add_infamy(10)
                for pb in world.placed_buildings.values():
                    if "infamy_amplify" in pb.bdef.get("flags", []):
                        if math.dist((self.gx, self.gy), (pb.gx, pb.gy)) < 12.0:
                            world.roe_manager.add_infamy(5)
                            world.events.append(("press_amplify",
                                                 {"building": pb.bdef["name"]}))

    # ── Draw ──────────────────────────────────────────────────────────────────

    # Shape definitions per utype: list of (dx,dy) polygon relative to (sx, sy-8)
    _SHAPES = {
        # Gravy Seal — wide helmet box
        "gravy_seal":    [(-6,-10),(6,-10),(8,-4),(8,4),(6,8),(-6,8),(-8,4),(-8,-4)],
        # ICE Agent — tall narrow wedge
        "ice_agent":     [(-4,-12),(4,-12),(7,6),(-7,6)],
        # Proxy — diamond
        "proxy":         [(0,-11),(8,0),(0,9),(-8,0)],
        # Contractor — heavy square
        "contractor":    [(-9,-9),(9,-9),(9,9),(-9,9)],
        # Drone Scout — small cross/plus
        "drone_scout":   [(0,-9),(3,-3),(9,-3),(4,2),(6,9),(0,5),(-6,9),(-4,2),(-9,-3),(-3,-3)],
        # Drone Assault — larger cross
        "drone_assault": [(0,-11),(4,-4),(11,-4),(5,3),(7,11),(0,7),(-7,11),(-5,3),(-11,-4),(-4,-4)],
        # Unmarked Van — wide flat rectangle
        "unmarked_van":  [(-12,-6),(12,-6),(12,6),(-12,6)],
    }
    _DEFAULT_SHAPE = [(-7,-7),(7,-7),(7,7),(-7,7)]  # square fallback

    def draw(self, surf: pygame.Surface, cam):
        if self.state == STATE_DEAD or self.garrisoned_in:
            return

        sx, sy = cam.world_to_screen(self.gx, self.gy)
        base_col = FACTION_COLORS.get(self.faction, (128, 128, 128))
        col = (255, 255, 255) if self.flash_timer > 0 else base_col

        # Ground shadow (solid dark ellipse — no alpha needed)
        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 10, sy - 2, 20, 6))

        # Selection ring
        if self.selected:
            pygame.draw.circle(surf, (0, 255, 100), (sx, sy - 8), 13, 2)

        # Unit body — distinct polygon per type
        raw = self._SHAPES.get(self.utype, self._DEFAULT_SHAPE)
        pts = [(sx + dx, sy - 8 + dy) for dx, dy in raw]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

        # Direction pip
        angle = [225, 315, 45, 135][self.facing] * math.pi / 180
        px = sx + int(math.cos(angle) * 10)
        py = sy - 8 + int(math.sin(angle) * 10)
        pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)

        # HP bar
        self._draw_hp_bar(surf, sx, sy)

        # Suppression — "RED TAPE" bar
        if self.suppressed:
            tape_w = 28
            tape_rect = pygame.Rect(sx - tape_w // 2, sy - 30, tape_w, 5)
            pygame.draw.rect(surf, (180, 10, 10), tape_rect)
            pct = self._suppress_timer / 5.0
            pygame.draw.rect(surf, (255, 40, 40),
                pygame.Rect(tape_rect.left, tape_rect.top, int(tape_w * min(1, pct)), 5))
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("RED TAPE", True, (255, 200, 200))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 40))

        # Unit type label when selected
        if self.selected:
            f = pygame.font.SysFont("couriernew", 8)
            lbl = f.render(self.utype[:10].upper().replace("_", " "), True, (200, 200, 200))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 26))

    def _draw_hp_bar(self, surf, sx, sy):
        bar_w = 18
        bar_h = 3
        bx = sx - bar_w // 2
        by = sy - 20
        pct = self.hp / self.max_hp
        bar_col = (40, 200, 60) if pct > 0.6 else (220, 180, 0) if pct > 0.3 else (220, 40, 40)
        pygame.draw.rect(surf, (30, 30, 30), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surf, bar_col, (bx, by, int(bar_w * pct), bar_h))

    @property
    def tile(self):
        return (int(self.gx), int(self.gy))
