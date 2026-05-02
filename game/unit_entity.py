"""Unit entity — movement, combat, rendering."""
import math, pygame

# ── Unit stat table ────────────────────────────────────────────────────────────
UNIT_DEFS = {
    #           hp   spd  dmg  range atk_cd  armor        faction       cost
    "gravy_seal":    (120, 2.8, 14,  4.0, 1.2,  "light",     "regency",   200),
    "ice_agent":     (180, 2.2, 18,  3.5, 1.5,  "medium",    "regency",   350),
    "ice_agent_tac": (260, 2.0, 26,  4.0, 1.3,  "medium",    "regency",   520),
    "protester":     ( 60, 3.2,  0,  0.0, 0.0,  "unarmored", "neutral",     0),
    "proxy":         (100, 3.5, 22,  5.0, 1.0,  "light",     "sovereign", 280),
    "contractor":    (300, 1.8, 30,  5.5, 2.0,  "heavy",     "oligarchy", 500),
    "drone_scout":   ( 80, 5.0, 10,  6.0, 0.8,  "light",     "frontline", 300),
    "drone_assault": (200, 3.5, 28,  5.5, 1.2,  "medium",    "frontline", 550),
    "drone_operator":(150, 2.5, 15,  4.5, 1.0,  "light",     "frontline", 400),
    "unmarked_van":  (400, 3.0, 20,  4.0, 1.5,  "medium",    "regency",   450),
    "compliance_bus":(350, 2.5,  0,  0.0, 0.0,  "medium",    "regency",   800),
    "mrap":          (700, 1.6, 40,  4.5, 2.2,  "heavy",     "regency",   750),
    "vbied":         ( 80, 5.5,  0,  1.8, 99.0, "light",     "sovereign", 350),
    "civilian_car":  (120, 3.5,  0,  0.0, 0.0,  "light",     "neutral",     0),
    "militia":       ( 45, 2.5,  8,  2.0, 1.2,  "unarmored", "sovereign",   0),
    "news_van":      (200, 1.5,  0,  0.0, 0.0,  "light",     "frontline", 450),
    "patriot_lawyer":(  80, 2.0, 0,  0.0, 0.0,  "unarmored", "regency",   300),
    "wagner":           (  55, 3.0, 10, 3.5, 1.4,  "unarmored", "oligarchy",  60),
    "journalist":       (  50, 2.8,  0, 0.0, 0.0,  "unarmored", "frontline", 250),
    "agitator":         (  70, 2.6,  0, 0.0, 0.0,  "unarmored", "frontline", 200),
    "proud_perimeter":  ( 200, 1.6, 20, 1.8, 1.8,  "medium",    "regency",   380),
    "donor":            (  30, 1.2,  0, 0.0, 0.0,  "unarmored", "regency",   450),
    "settler":          (  80, 2.4,  0, 0.0, 0.0,  "unarmored", "sovereign", 320),
    "interpreter":      (  60, 2.3,  0, 0.0, 0.0,  "unarmored", "sovereign", 280),
    "direktor":         ( 400, 1.0,  0, 0.0, 0.0,  "heavy",     "oligarchy", 1200),
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

    _HERO_NAMES = {
        "regency":   (["Chad","Brad","Todd","Dale","Keith","Wayne","Gary","Larry"],
                      ["Morrison","Henderson","Jenkins","Tucker","Patterson","Thompson"]),
        "frontline": (["Alex","Jordan","Sam","Riley","Morgan","Taylor","Casey","Jamie"],
                      ["Chen","Williams","Okafor","Reyes","Kowalski","Baptiste","Kim"]),
        "sovereign": (None, ["The Prepper","Ghost Cell","Red Fox","Black Flag","Iron Gate","Cipher","Static"]),
        "oligarchy": (["Preston","Sterling","Reginald","Clifford","Montgomery","Beaumont"],
                      ["Worthington","Bancroft","Hartwell","Pemberton","Ashcroft","Windsor"]),
    }

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
        self.kills        = 0
        self.hero_name    = None

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

        self.scanned_timer   = 0.0      # time remaining for "SCANNED" visual
        self.is_bolo         = False    # True if identified by ALPR tower
        import random, string
        self.license_plate   = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

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

        self.flash_timer   = max(0.0, self.flash_timer - dt_sec)
        self.atk_timer     = max(0.0, self.atk_timer - dt_sec)
        self.scanned_timer = max(0.0, self.scanned_timer - dt_sec)

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
            # Auto-retarget: find nearest enemy in range after a kill
            if self.damage > 0:
                next_t = world.nearest_enemy(self, max_range=self.attack_range * 1.5)
                if next_t:
                    self.order_attack(next_t.uid)

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
            self._gain_xp(5.0, world)
            
            self.atk_timer = self.atk_cooldown_max
            # face the target
            dx = target.gx - self.gx
            dy = target.gy - self.gy
            angle = math.atan2(dy, dx) * 180 / math.pi
            if   -135 <= angle < -45:  self.facing = 2
            elif  -45 <= angle <  45:  self.facing = 1
            elif   45 <= angle < 135:  self.facing = 3
            else:                       self.facing = 0

    def _gain_xp(self, amount, world=None):
        if self.rank >= 5:
            return
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.rank += 1
            self.xp_to_next *= 1.5
            # Heal on rank up
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.2)
            if self.rank == 5 and self.hero_name is None:
                import random as _rnd
                pool = self._HERO_NAMES.get(self.faction, (None, ["Unknown"]))
                firsts, lasts = pool
                if firsts:
                    self.hero_name = "{} {}".format(_rnd.choice(firsts), _rnd.choice(lasts))
                else:
                    self.hero_name = _rnd.choice(lasts)
                if world is not None:
                    world.events.append(("rank_5_promotion", {
                        "uid": self.uid,
                        "utype": self.utype,
                        "faction": self.faction,
                        "hero_name": self.hero_name,
                    }))

    def take_damage(self, amount, world=None, attacker=None):
        self.hp = max(0, self.hp - amount)
        self.flash_timer = 0.12
        if self.hp == 0:
            self.state = STATE_DEAD
            if attacker:
                attacker.kills += 1
                attacker._gain_xp(25.0, world)  # kill bonus XP
            if world and self.faction == "neutral":
                world.roe_manager.add_infamy(10)
                for pb in world.placed_buildings.values():
                    if "infamy_amplify" in pb.bdef.get("flags", []):
                        if math.dist((self.gx, self.gy), (pb.gx, pb.gy)) < 12.0:
                            world.roe_manager.add_infamy(5)
                            world.events.append(("press_amplify",
                                                 {"building": pb.bdef["name"]}))
            if world and self.utype == "journalist":
                platform_banned = getattr(world, "_platform_ban_timer", 0.0) > 0
                if not platform_banned:
                    world.roe_manager.add_infamy(30)
                    world.events.append(("journalist_killed", {"faction": getattr(attacker, "faction", "unknown")}))
            if world and self.utype == "donor":
                platform_banned = getattr(world, "_platform_ban_timer", 0.0) > 0
                if not platform_banned:
                    world.roe_manager.add_infamy(20)
                    attacker_faction = getattr(attacker, "faction", None)
                    if attacker_faction:
                        for u in world.units.values():
                            if u.faction == attacker_faction and u.state != STATE_DEAD:
                                if math.dist((u.gx, u.gy), (self.gx, self.gy)) <= 6.0:
                                    u.suppress(5.0)
                world.events.append(("donor_killed", {}))
            if world and self.utype == "direktor":
                # Killing the Direktor: credit bounty to attacker's faction + event
                attacker_faction = getattr(attacker, "faction", None)
                if attacker_faction:
                    world.credits[attacker_faction] = world.credits.get(attacker_faction, 0) + 500
                world.events.append(("direktor_killed", {"killer_faction": attacker_faction}))

    # ── Draw ──────────────────────────────────────────────────────────────────

    # Shape definitions per utype: list of (dx,dy) polygon relative to (sx, sy-8)
    _SHAPES = {
        # Gravy Seal — wide helmet box
        "gravy_seal":    [(-6,-10),(6,-10),(8,-4),(8,4),(6,8),(-6,8),(-8,4),(-8,-4)],
        # ICE Agent — tall narrow wedge
        "ice_agent":     [(-4,-12),(4,-12),(7,6),(-7,6)],
        # ICE Agent Tac — wider wedge, shoulder gear added
        "ice_agent_tac": [(-5,-12),(5,-12),(10,4),(6,8),(-6,8),(-10,4)],
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
        # Compliance Bus — longer than the van, rounded front hint
        "compliance_bus":[(-16,-8),(-12,-10),(12,-10),(16,-8),(16,8),(12,10),(-12,10),(-16,8)],
        # MRAP — wide armored box with angled front
        "mrap":          [(-10,-13),(-5,-15),(5,-15),(10,-13),(13,-6),(13,8),(10,12),(-10,12),(-13,8),(-13,-6)],
        # VBIED — small car silhouette
        "vbied":         [(-8,-5),(8,-5),(9,0),(8,5),(-8,5),(-9,0)],
        # News Van — wide box with antenna nub
        "news_van":      [(-13,-7),(-11,-10),(11,-10),(13,-7),(13,7),(-13,7)],
        # Patriot Lawyer — slim upright rectangle (briefcase silhouette)
        "patriot_lawyer":[(-5,-12),(5,-12),(6,6),(3,10),(-3,10),(-6,6)],
        # Wagner — crude triangle (cannon fodder)
        "wagner":        [(0,-10),(7,8),(-7,8)],
        # Journalist — camera silhouette (wide top, narrow base)
        "journalist":    [(-8,-10),(8,-10),(10,-4),(10,2),(5,8),(-5,8),(-10,2),(-10,-4)],
        # Agitator — megaphone triangle pointing right
        "agitator":          [(-4,-8),(8,0),(-4,8),(-6,4),(-6,-4)],
        # Proud Perimeter — wide shield shape
        "proud_perimeter":   [(-9,-6),(-5,-12),(5,-12),(9,-6),(9,4),(5,10),(-5,10),(-9,4)],
        # Donor — fat oval (golf shirt, unthreatening)
        "donor":             [(-7,-5),(-4,-10),(4,-10),(7,-5),(7,5),(4,9),(-4,9),(-7,5)],
        # Settler — stake/flag shape (narrow body, wide top)
        "settler":           [(-3,-12),(3,-12),(5,-6),(5,2),(8,2),(8,6),(-8,6),(-8,2),(-5,2),(-5,-6)],
        # Interpreter — slim earpiece hexagon (diplomatic support)
        "interpreter":       [(0,-11),(5,-7),(5,7),(0,11),(-5,7),(-5,-7)],
        # Direktor (Kraznov) — wide-shouldered suit, dome head, imposing silhouette
        "direktor":          [(-11,-4),(-7,-12),(7,-12),(11,-4),(11,6),(6,11),(-6,11),(-11,6)],
    }
    _DEFAULT_SHAPE = [(-7,-7),(7,-7),(7,7),(-7,7)]  # square fallback

    def draw(self, surf: pygame.Surface, cam):
        if self.state == STATE_DEAD or self.garrisoned_in:
            return

        sx, sy = cam.world_to_screen(self.gx, self.gy)
        base_col = FACTION_COLORS.get(self.faction, (128, 128, 128))
        col = (255, 255, 255) if self.flash_timer > 0 else base_col

        # ALPR Scanning Visuals
        if self.scanned_timer > 0:
            f_license = pygame.font.SysFont("couriernew", 9, bold=True)
            txt = f_license.render(f"AUDITING: {self.license_plate}", True, (0, 255, 200))
            surf.blit(txt, (sx - txt.get_width() // 2, sy - 45))
            # Glitch lines
            import random
            for _ in range(2):
                lx = sx + random.randint(-15, 15)
                pygame.draw.line(surf, (0, 255, 200), (lx, sy - 45), (lx + 5, sy - 45), 1)

        if self.is_bolo:
            f_bolo = pygame.font.SysFont("couriernew", 10, bold=True)
            txt = f_bolo.render("BOLO TARGET", True, (255, 30, 0))
            # Shake effect for BOLO
            off_x = int(math.sin(pygame.time.get_ticks() * 0.05) * 2)
            surf.blit(txt, (sx - txt.get_width() // 2 + off_x, sy - 58))

        # Ground shadow
        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 10, sy - 2, 20, 6))

        # Try sprite sheet first
        from game.sprites import get_manager
        moving  = self.state == STATE_MOVING
        frame   = get_manager().get_frame(self.utype, self.facing, moving)

        raw = self._SHAPES.get(self.utype, self._DEFAULT_SHAPE)
        pts = [(sx + dx, sy - 8 + dy) for dx, dy in raw]

        if frame:
            # Selection outline using polygon footprint behind sprite
            if self.selected:
                pygame.draw.polygon(surf, base_col, pts, 2)
                pygame.draw.polygon(surf, (255, 50, 50),
                                    [(sx + dx - 2, sy - 8 + dy - 1) for dx, dy in raw], 1)
                pygame.draw.polygon(surf, (50, 50, 255),
                                    [(sx + dx + 1, sy - 8 + dy + 2) for dx, dy in raw], 1)

            # Flash tint: blit white-modulated copy on hit
            if self.flash_timer > 0:
                flash = frame.copy()
                flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(flash, (sx - frame.get_width() // 2, sy - frame.get_height() // 2 - 4))
            else:
                surf.blit(frame, (sx - frame.get_width() // 2, sy - frame.get_height() // 2 - 4))
        else:
            # Polygon fallback
            if self.selected:
                pygame.draw.polygon(surf, base_col if self.flash_timer <= 0 else col, pts, 2)
                pygame.draw.polygon(surf, (255, 50, 50),
                                    [(sx + dx - 2, sy - 8 + dy - 1) for dx, dy in raw], 1)
                pygame.draw.polygon(surf, (50, 50, 255),
                                    [(sx + dx + 1, sy - 8 + dy + 2) for dx, dy in raw], 1)

            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

            # Direction pip (only shown for polygon units)
            angle = [225, 315, 45, 135][self.facing] * math.pi / 180
            px = sx + int(math.cos(angle) * 10)
            py = sy - 8 + int(math.sin(angle) * 10)
            pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)

        # HP bar
        self._draw_hp_bar(surf, sx, sy)

        # Hero name for rank-5 units
        if self.rank >= 5 and self.hero_name:
            f_hero = pygame.font.SysFont("couriernew", 8, bold=True)
            hlbl = f_hero.render(self.hero_name, True, (220, 180, 40))
            surf.blit(hlbl, (sx - hlbl.get_width() // 2, sy - 46))

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


class ComplianceBus(Unit):
    MAX_PASSENGERS = 30
    BOARD_RANGE    = 2.5   # tiles — civs within this are auto-boarded
    UNLOAD_RANGE   = 2.0   # tiles from pen/HQ center to trigger unload
    DELIVERY_RATE  = 75    # § per passenger delivered (3× the standard 25)

    def __init__(self, gx, gy, faction="regency"):
        super().__init__("compliance_bus", faction, gx, gy)
        self.passengers  = []    # civilian uids currently aboard
        self.bolo_aboard = False

    @property
    def is_full(self):
        return len(self.passengers) >= self.MAX_PASSENGERS

    def board(self, civ):
        if self.is_full:
            return False
        self.passengers.append(civ.uid)
        if getattr(civ, "is_bolo", False):
            self.bolo_aboard = True
        return True

    def update(self, dt_sec, world):
        # Slow down when heavily loaded
        self.speed = 2.0 if len(self.passengers) > 15 else 2.5
        super().update(dt_sec, world)

    def draw(self, surf: pygame.Surface, cam):
        if self.state == STATE_DEAD or self.garrisoned_in:
            return

        sx, sy = cam.world_to_screen(self.gx, self.gy)
        col = (255, 255, 255) if self.flash_timer > 0 else (28, 80, 180)

        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 18, sy - 3, 36, 8))

        if self.selected:
            pygame.draw.circle(surf, (0, 255, 100), (sx, sy - 8), 20, 2)

        raw = self._SHAPES["compliance_bus"]
        pts = [(sx + dx, sy - 8 + dy) for dx, dy in raw]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

        # Yellow side stripe
        stripe_pts = [(sx - 12, sy - 10), (sx + 12, sy - 10),
                      (sx + 12, sy - 7),  (sx - 12, sy - 7)]
        pygame.draw.polygon(surf, (255, 220, 0), stripe_pts)

        # Passenger count badge — always visible
        f = pygame.font.SysFont("couriernew", 8, bold=True)
        pax = len(self.passengers)
        badge_col = (0, 200, 100) if pax < 20 else (255, 180, 0) if pax < 28 else (255, 60, 60)
        badge = f.render(f"{pax}/{self.MAX_PASSENGERS}", True, badge_col)
        surf.blit(badge, (sx - badge.get_width() // 2, sy - 26))

        if self.selected:
            f2 = pygame.font.SysFont("couriernew", 7)
            lbl = f2.render("SAFE HARBOR EXPRESS", True, (200, 220, 255))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 36))

        self._draw_hp_bar(surf, sx, sy)


class VBIEDUnit(Unit):
    """Sovereign suicide vehicle — drives at enemies and detonates on contact."""
    BLAST_RADIUS = 3.5
    BLAST_DAMAGE = 110

    def __init__(self, faction, gx, gy):
        super().__init__("vbied", faction, gx, gy)
        self._detonated = False

    def _do_attack(self, target, dt_sec, world):
        if self._detonated:
            return
        self._detonated = True
        for u in list(world.units.values()):
            if u.state == STATE_DEAD or u is self:
                continue
            if math.dist((self.gx, self.gy), (u.gx, u.gy)) <= self.BLAST_RADIUS:
                u.take_damage(self.BLAST_DAMAGE, world)
        world.roe_manager.add_infamy(30)
        world.events.append(("vbied_explode", {"gx": self.gx, "gy": self.gy}))
        self.state = STATE_DEAD

    def draw(self, surf: pygame.Surface, cam):
        if self.state == STATE_DEAD or self.garrisoned_in:
            return
        sx, sy = cam.world_to_screen(self.gx, self.gy)

        pulse = int(7 + math.sin(pygame.time.get_ticks() * 0.008) * 3)
        pygame.draw.circle(surf, (180, 30, 30), (sx, sy - 8), pulse, 1)

        pygame.draw.ellipse(surf, (0, 8, 6), (sx - 10, sy - 3, 20, 7))

        raw = self._SHAPES.get("vbied", self._DEFAULT_SHAPE)
        pts = [(sx + dx, sy - 8 + dy) for dx, dy in raw]
        col = (220, 50, 50) if self.flash_timer <= 0 else (255, 255, 255)
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)

        if self.selected:
            f = pygame.font.SysFont("couriernew", 7)
            lbl = f.render("V-BIED", True, (255, 80, 80))
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 22))

        self._draw_hp_bar(surf, sx, sy)
