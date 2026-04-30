"""
World state — units, placed buildings, production queues, game logic tick.
"""
import math
from typing import Optional
from game.unit_entity import Unit, STATE_DEAD
from game.building_defs import BUILDINGS as BDEF
from game.map_data import BUILDINGS as MAP_BLDS
from game.roe import ROEManager
from game.civilian import Civilian
from game.ai import AIFaction
import random


class PlacedBuilding:
    """A building that has been constructed on the map."""
    def __init__(self, bid, bdef, gx, gy, faction):
        self.bid      = bid
        self.bdef     = bdef
        self.gx       = gx
        self.gy       = gy
        self.faction  = faction
        self.hp       = bdef["hp"]
        self.max_hp   = bdef["hp"]
        self.garrison = []   # list of unit uids
        self.civs_held = 0
        self.selected = False
        self._capture_progress = 0.0

    @property
    def tile_set(self):
        s = set()
        for dy in range(self.bdef["h"]):
            for dx in range(self.bdef["w"]):
                s.add((self.gx + dx, self.gy + dy))
        return s

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    @property
    def destroyed(self):
        return self.hp <= 0


class ProductionQueue:
    """Manages a single building's unit or building production queue."""

    def __init__(self, max_queue=5):
        self.items     = []   # list of utype strings
        self.progress  = 0.0  # 0.0–1.0
        self.max_queue = max_queue

    def enqueue(self, utype, cost, world_credits):
        if len(self.items) >= self.max_queue:
            return False
        if world_credits < cost:
            return False
        self.items.append(utype)
        return True

    def cancel_front(self):
        if self.items:
            self.items.pop(0)
            self.progress = 0.0

    def update(self, dt_sec, build_time=8.0):
        """Returns completed utype or None."""
        if not self.items:
            return None
        self.progress += dt_sec / build_time
        if self.progress >= 1.0:
            self.progress = 0.0
            return self.items.pop(0)
        return None


class World:
    BUILD_TIME_UNIT = 8.0
    BUILD_TIME_BLDG = 15.0
    PASSIVE_INCOME_TICK = 1.0   # seconds between credit ticks
    PEN_INCOME_RATE = 5          # §/sec per detained civilian

    # Enemy faction chosen based on player faction
    _ENEMY_MAP = {
        "regency":   "sovereign",
        "frontline": "oligarchy",
        "sovereign": "regency",
        "oligarchy": "frontline",
    }

    # Units blocked from production at SANCTIONED infamy tier
    _HEAVY_TIER = {"contractor", "drone_assault", "unmarked_van"}

    def __init__(self, player_faction="regency"):
        self.player_faction   = player_faction
        self.units            = {}   # uid -> Unit
        self.civilians        = {}   # uid -> Civilian
        self.placed_buildings = {}   # bid_instance_id -> PlacedBuilding
        self._bld_id_counter  = 0

        self.credits          = {"regency": 5000, "frontline": 3000,
                                  "sovereign": 5000, "oligarchy": 4000}
        self.roe_manager      = ROEManager()
        self.power            = {player_faction: 100}

        self.unit_queues      = {}   # bld_instance_id -> ProductionQueue
        self._income_timer    = 0.0
        self._surveilled_timer = 0.0  # cooldown for SURVEILLED drone spawns

        enemy = self._ENEMY_MAP.get(player_faction, "sovereign")
        self.ai_factions = {enemy: AIFaction(enemy)}

        # Spawn civilians at Kirk Rally
        from game.map_data import KIRK_RALLY
        kx, ky = KIRK_RALLY
        for i in range(25):
            self.spawn_civilian(kx + random.uniform(-4, 4), ky + random.uniform(-4, 4))

        # Pre-place map buildings as neutral/capturable
        self._place_map_buildings()

        # Enemy base (upper-left corner)
        self.place_building("reg_hq",       enemy, 3,  2)
        self.place_building("reg_barracks",  enemy, 8,  2)


    # ── Spawn ─────────────────────────────────────────────────────────────────

    def spawn_unit(self, utype, faction, gx, gy) -> Unit:
        u = Unit(utype, faction, gx, gy)
        self.units[u.uid] = u
        return u

    def spawn_civilian(self, gx, gy, ctype="normie") -> Civilian:
        c = Civilian(gx, gy, ctype)
        self.civilians[c.uid] = c
        return c

    def place_building(self, bid, faction, gx, gy) -> Optional[PlacedBuilding]:
        bdef = BDEF.get(bid)
        if not bdef:
            return None
        self._bld_id_counter += 1
        iid = self._bld_id_counter
        pb  = PlacedBuilding(iid, bdef, gx, gy, faction)
        self.placed_buildings[iid] = pb
        if bdef.get("produces"):
            self.unit_queues[iid] = ProductionQueue()
        return pb

    # ── Queries ───────────────────────────────────────────────────────────────

    def blocked_tiles(self):
        """Set of (gx,gy) that are impassable (buildings)."""
        blocked = set()
        for pb in self.placed_buildings.values():
            blocked |= pb.tile_set
        return blocked

    def unit_at_screen(self, sx, sy, cam, radius=14):
        best, best_dist = None, radius
        for u in self.units.values():
            if u.state == STATE_DEAD or u.garrisoned_in:
                continue
            ux, uy = cam.world_to_screen(u.gx, u.gy)
            d = math.dist((sx, sy), (ux, uy - 8))
            if d < best_dist:
                best, best_dist = u, d
        return best

    def units_in_screen_rect(self, rect: "pygame.Rect", cam):
        result = []
        for u in self.units.values():
            if u.state == STATE_DEAD or u.garrisoned_in:
                continue
            ux, uy = cam.world_to_screen(u.gx, u.gy)
            if rect.collidepoint(ux, uy - 8):
                result.append(u)
        return result

    def building_at_screen(self, sx, sy, cam):
        from game.main import _point_in_poly
        for pb in reversed(list(self.placed_buildings.values())):
            bx, by = pb.gx, pb.gy
            bw, bh = pb.bdef["w"], pb.bdef["h"]
            fl = pb.bdef["floors"]
            pts = [
                cam.world_to_screen(bx,      by,      fl),
                cam.world_to_screen(bx + bw, by,      fl),
                cam.world_to_screen(bx + bw, by + bh, fl),
                cam.world_to_screen(bx,      by + bh, fl),
                cam.world_to_screen(bx,      by + bh, 0),
                cam.world_to_screen(bx + bw, by + bh, 0),
            ]
            if _point_in_poly(sx, sy, pts):
                return pb
        return None

    def enemies_of(self, faction):
        enemies = {"regency": {"frontline","sovereign"},
                   "frontline": {"regency","oligarchy"},
                   "sovereign": {"regency"},
                   "oligarchy": {"frontline","sovereign"},}
        return enemies.get(faction, set())

    def nearest_enemy(self, unit: Unit, max_range=8.0):
        best, best_dist = None, max_range
        enemy_factions = self.enemies_of(unit.faction)
        for u in self.units.values():
            if u.state == STATE_DEAD or u.faction not in enemy_factions:
                continue
            d = math.dist((unit.gx, unit.gy), (u.gx, u.gy))
            if d < best_dist:
                best, best_dist = u, d
        return best

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt_ms: int, player_faction="regency"):
        dt = dt_ms / 1000.0
        self.roe_manager.update(dt)
        self._apply_infamy_consequences(dt, player_faction)

        for ai in self.ai_factions.values():
            ai.update(dt, self)

        # Units
        for u in list(self.units.values()):
            if u.state == STATE_DEAD:
                continue
            # Auto-acquire target if idle
            if u.state == "idle" and u.damage > 0:
                enemy = self.nearest_enemy(u, max_range=u.attack_range * 1.5)
                if enemy:
                    u.order_attack(enemy.uid)
            u.update(dt, self)

        # Civilians + runner arrival check
        for c in list(self.civilians.values()):
            if c.state == "dead":
                continue
            c.update(dt, self)
            # Runner HVP reached destination — spawn enemy ambush
            if (c.ctype == "runner" and getattr(c, "_reached_dest", False)
                    and not getattr(c, "_ambush_spawned", False)):
                c._ambush_spawned = True
                enemy = self._ENEMY_MAP.get(player_faction, "sovereign")
                for i in range(3):
                    self.spawn_unit("proxy", enemy, c.gx + i * 0.8, c.gy)
                self.roe_manager.add_infamy(25)
        
        # Cleanup dead civs
        dead_civs = [cid for cid, c in self.civilians.items() if c.state == "dead"]
        for cid in dead_civs:
            del self.civilians[cid]

        # Remove dead units after a delay (keep for death render)
        dead = [uid for uid, u in self.units.items() if u.state == STATE_DEAD]
        for uid in dead:
            u = self.units[uid]
            if u.garrisoned_in:
                pb = self.placed_buildings.get(u.garrisoned_in)
                if pb and uid in pb.garrison:
                    pb.garrison.remove(uid)
            del self.units[uid]

        # Buildings (Capture + Income)
        for iid in list(self.placed_buildings.keys()):
            pb = self.placed_buildings[iid]
            if pb.hp <= 0:
                # Eject garrisoned units
                for uid in pb.garrison:
                    if uid in self.units:
                        u = self.units[uid]
                        u.garrisoned_in = None
                        u.take_damage(20) # Collapse damage
                del self.placed_buildings[iid]
                continue
                
            # Capture logic
            capture_rad = 5.0
            nearby_units = [u for u in self.units.values() if math.dist((u.gx, u.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) <= capture_rad]
            
            f_counts = {}
            for u in nearby_units:
                f_counts[u.faction] = f_counts.get(u.faction, 0) + 1
            
            # Simple capture: majority wins
            strongest = None
            max_n = 0
            for f, n in f_counts.items():
                if n > max_n:
                    max_n = n
                    strongest = f
            
            if strongest and strongest != pb.faction:
                pb._capture_progress += dt * 20.0 * max_n # Rate
                if pb._capture_progress >= 100.0:
                    pb.faction = strongest
                    pb._capture_progress = 0.0
            elif pb._capture_progress > 0:
                pb._capture_progress = max(0, pb._capture_progress - dt * 10.0)

            # Pull civilians into holding pens
            if pb.bdef.get("garrison", 0) > 0 and pb.faction != "neutral":
                # Check for nearby civs
                for c in list(self.civilians.values()):
                    if math.dist((c.gx, c.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) < 3.0:
                        if pb.civs_held < pb.bdef["garrison"]:
                            pb.civs_held += 1
                            c.state = "dead" # Captured
                            # Reward for capture?
                            self.credits[pb.faction] = self.credits.get(pb.faction, 0) + 25

        # Production queues
        self._income_timer += dt
        if self._income_timer >= self.PASSIVE_INCOME_TICK:
            self._income_timer = 0.0
            self._tick_income(player_faction)

        for iid, queue in list(self.unit_queues.items()):
            pb = self.placed_buildings.get(iid)
            if not pb:
                continue
            completed = queue.update(dt, self.BUILD_TIME_UNIT)
            if completed:
                # SANCTIONED: freeze heavy-tier production for player
                if (self.roe_manager.infamy >= 750
                        and pb.faction == player_faction
                        and completed in self._HEAVY_TIER):
                    queue.items.insert(0, completed)
                    queue.progress = 0.95
                else:
                    ex = pb.gx + pb.bdef["w"] // 2
                    ey = pb.gy + pb.bdef["h"]
                    self.spawn_unit(completed, pb.faction, ex, ey)

    def _tick_income(self, player_faction):
        # Passive building income
        for pb in self.placed_buildings.values():
            if pb.faction != player_faction:
                continue
            income = pb.bdef.get("passive_income", 0)
            
            # Civilian income from holding pens
            if pb.civs_held > 0:
                income += pb.civs_held * self.PEN_INCOME_RATE
                
            if income:
                self.credits[player_faction] = \
                    self.credits.get(player_faction, 0) + income

    def _apply_infamy_consequences(self, dt, player_faction):
        infamy = self.roe_manager.infamy
        if infamy < 400:
            self._surveilled_timer = 0.0
            return
        # SURVEILLED (≥400): Frontline drone harasses player every 30s
        self._surveilled_timer += dt
        if self._surveilled_timer >= 30.0:
            self._surveilled_timer = 0.0
            # Spawn near map center so player sees it approaching
            self.spawn_unit("drone_scout", "frontline",
                            14 + random.uniform(-3, 3), 12 + random.uniform(-3, 3))

    # ── Map pre-placement ─────────────────────────────────────────────────────

    def _place_map_buildings(self):
        """Turn the static map_data building list into PlacedBuilding objects."""
        type_to_bid = {
            "intel":    "civ_library",
            "tech":     "garr_office",
            "command":  "reg_hq",
            "resource": "civ_cafe",
            "barracks": "reg_barracks",
            "sensor":   "audit_point",
            "depot":    "garr_parking",
        }
        for bld in MAP_BLDS:
            _, name, sub, bx, by, bw, bh, floors, btype, hp, max_hp = bld
            bid = type_to_bid.get(btype, "garr_office")
            bdef = BDEF.get(bid)
            if not bdef:
                continue
            self._bld_id_counter += 1
            iid = self._bld_id_counter
            pb  = PlacedBuilding(iid, bdef, bx, by, "neutral")
            pb.hp = hp
            pb.max_hp = max_hp
            # Override display name from map data
            pb.display_name = name
            pb.display_sub  = sub
            self.placed_buildings[iid] = pb
            if bdef.get("produces"):
                self.unit_queues[iid] = ProductionQueue()
