"""
World state — units, placed buildings, production queues, game logic tick.
"""
import math
from typing import Optional
from game.unit_entity import Unit, ComplianceBus, VBIEDUnit, STATE_DEAD
from game.building_defs import BUILDINGS as BDEF
from game.map_data import BUILDINGS as MAP_BLDS, TERRAIN, PATH, W as MAP_W, H as MAP_H
from game.roe import ROEManager
from game.civilian import Civilian, PROTESTER
from game.vehicles import CivilianCar
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

    GAME_OVER_NONE    = 0
    GAME_OVER_DEFEAT  = 1   # player HQ destroyed
    GAME_OVER_VICTORY = 2   # enemy HQ destroyed

    # Enemy faction chosen based on player faction
    _ENEMY_MAP = {
        "regency":   "sovereign",
        "frontline": "oligarchy",
        "sovereign": "regency",
        "oligarchy": "frontline",
    }

    # Units blocked from production at SANCTIONED infamy tier
    _HEAVY_TIER = {"contractor", "drone_assault", "unmarked_van"}

    def __init__(self, player_faction="regency", map_phase=0):
        self.player_faction   = player_faction
        self.map_phase        = map_phase
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
        self._surveilled_timer = 0.0
        self.power_balance    = 0    # net power (negative = underpowered)
        self._deepfake_fired  = False  # Kirk Deepfake mid-game reveal
        self._mission_elapsed = 0.0   # seconds since intro ended
        self._troll_surge_timer = 0.0
        self.unit_tier = {}   # base_utype → upgraded_utype, set by sidebar upgrades
        self.game_over        = self.GAME_OVER_NONE
        self.events           = []   # [(event_type, payload)] consumed each frame by main
        self.wrecks           = []   # [(gx, gy, timer)] visual wreck markers

        # Narrative leak events: (trigger_sec, event_type, infamy_hit, effect)
        # effect: None | "raid" | "reinforce"
        self._narrative_events = [
            (90,  "leak_comms",    25, None),
            (180, "leak_footage",  35, "reinforce"),
            (240, "leak_assets",   20, "raid"),
            (420, "leak_defector", 15, "reinforce"),
        ]
        self._narrative_fired = set()

        enemy = self._ENEMY_MAP.get(player_faction, "sovereign")
        self.ai_factions = {enemy: AIFaction(enemy)}

        # Spawn rally crowd — tight cluster, wander locked until intro ends
        from game.map_data import KIRK_RALLY
        kx, ky = KIRK_RALLY
        for i in range(30):
            c = self.spawn_civilian(kx + random.uniform(-2.5, 2.5),
                                    ky + random.uniform(-2.5, 2.5))
            c._wander_timer = 60.0   # won't wander during the ~12s intro

        # Protesters — distributed across the quad near audit points
        _PROTESTER_SPAWNS = [
            (kx + 3, ky - 2), (kx - 3, ky + 1), (kx + 5, ky + 3),
            (kx - 4, ky - 3), (kx + 8, ky - 1), (kx - 6, ky + 4),
        ]
        for px, py in _PROTESTER_SPAWNS:
            self.spawn_civilian(px, py, ctype=PROTESTER)

        self._bolo_uid = None   # uid of the BOLO target civilian
        self.vehicles  = {}      # uid -> CivilianCar
        self._vbied_timer = 45.0  # seconds until next Sovereign VBIED attempt

        self.tape = {
            "active": False,
            "gx": 0.0, "gy": 0.0,
            "holder_uid": None,
            "holder_faction": None,
        }

        # Pre-place map buildings as neutral/capturable
        self._place_map_buildings()

        # Enemy base — faction-appropriate buildings
        _ENEMY_BASE = {
            "sovereign": [("sov_safehouse", 4, 3), ("sov_cache",    10, 3)],
            "frontline": [("fl_hq",         4, 3), ("fl_drone",     10, 3)],
            "regency":   [("reg_hq",        4, 3), ("reg_barracks", 10, 3)],
            "oligarchy": [("olig_hq",       4, 3), ("reg_barracks", 10, 3)],
        }
        for bid, bx, by in _ENEMY_BASE.get(enemy, [("reg_hq", 4, 3), ("reg_barracks", 10, 3)]):
            self.place_building(bid, enemy, bx, by)

        # Spawn ambient civilian cars on road tiles
        road_tiles = [(x, y) for y in range(MAP_H) for x in range(MAP_W)
                      if TERRAIN[y][x] == PATH]
        _rng_cars = random.Random(map_phase * 3 + 99)
        for _ in range(12):
            if road_tiles:
                rx, ry = _rng_cars.choice(road_tiles)
                car = CivilianCar(rx + _rng_cars.uniform(0.1, 0.9),
                                  ry + _rng_cars.uniform(0.1, 0.9))
                self.vehicles[car.uid] = car

        # Designate one random civilian as BOLO target
        if self.civilians:
            bolo = random.choice(list(self.civilians.values()))
            bolo.is_bolo = True
            self._bolo_uid = bolo.uid

        # Pre-place wreck markers for scarred/shattered phases
        if map_phase >= 1:
            _rng = random.Random(map_phase * 7 + 13)  # deterministic per phase
            count = 10 if map_phase == 1 else 22
            for _ in range(count):
                wx = _rng.uniform(4, 23)
                wy = _rng.uniform(3, 20)
                self.wrecks.append([wx, wy, 99999.0])  # permanent phase wrecks


    # ── Spawn ─────────────────────────────────────────────────────────────────

    def spawn_unit(self, utype, faction, gx, gy) -> Unit:
        if utype == "compliance_bus":
            u = ComplianceBus(gx, gy, faction)
        elif utype == "vbied":
            u = VBIEDUnit(faction, gx, gy)
        else:
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
        self._mission_elapsed += dt
        self.roe_manager.update(dt)
        self._apply_infamy_consequences(dt, player_faction)

        # Epstein File Leak superweapon timer
        if getattr(self, "_epstein_timer", 0.0) > 0:
            self._epstein_timer -= dt
        # Platform Ban timer (Regency — journalist/donor protections suspended)
        if getattr(self, "_platform_ban_timer", 0.0) > 0:
            self._platform_ban_timer -= dt
        # Troll Surge timer (Oligarchy — doubled troll farm erosion)
        if self._troll_surge_timer > 0:
            self._troll_surge_timer -= dt

        # Kirk Deepfake reveal at 5 minutes
        if not self._deepfake_fired and self._mission_elapsed >= 300.0:
            self._deepfake_fired = True
            self.roe_manager.add_infamy(50)
            self.events.append(("deepfake_live", {}))

        # Narrative leak events
        enemy = self._ENEMY_MAP.get(player_faction, "sovereign")
        for i, (t, etype, infamy_hit, effect) in enumerate(self._narrative_events):
            if i not in self._narrative_fired and self._mission_elapsed >= t:
                self._narrative_fired.add(i)
                self.roe_manager.add_infamy(infamy_hit)
                self.events.append((etype, {"infamy": infamy_hit}))
                if effect == "raid":
                    for ai in self.ai_factions.values():
                        ai._raid_timer = 0.0
                elif effect == "reinforce":
                    spawn_x = 14 + random.uniform(-6, 6)
                    spawn_y = 20 + random.uniform(-4, 4)
                    self.spawn_unit("proxy", enemy, spawn_x, spawn_y)
                    self.spawn_unit("proxy", enemy, spawn_x + 1.2, spawn_y)

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
                self.events.append(("runner_arrived", {"gx": c.gx, "gy": c.gy}))
        
        # Compliance Bus — board nearby civs, unload at friendly pen/HQ
        for u in self.units.values():
            if not isinstance(u, ComplianceBus) or u.state == STATE_DEAD:
                continue
            if not u.is_full:
                for c in list(self.civilians.values()):
                    if c.state == "dead":
                        continue
                    if math.dist((u.gx, u.gy), (c.gx, c.gy)) < ComplianceBus.BOARD_RANGE:
                        u.board(c)
                        c.state = "dead"
                        if u.is_full:
                            break
            if u.passengers:
                for pb in self.placed_buildings.values():
                    if pb.faction != player_faction:
                        continue
                    flags = pb.bdef.get("flags", [])
                    if "holding_pen" not in flags and "command" not in flags:
                        continue
                    cx = pb.gx + pb.bdef["w"] / 2
                    cy = pb.gy + pb.bdef["h"] / 2
                    if math.dist((u.gx, u.gy), (cx, cy)) < ComplianceBus.UNLOAD_RANGE:
                        self._unload_bus(u, pb, player_faction)
                        break

        # Vehicles + VBIED trigger for Sovereign enemy
        for v in self.vehicles.values():
            v.update(dt, self)
        if "sovereign" in self.ai_factions and player_faction != "sovereign":
            self._vbied_timer -= dt
            if self._vbied_timer <= 0:
                self._vbied_timer = random.uniform(50.0, 80.0)
                player_units = [u for u in self.units.values()
                                if u.faction == player_faction and u.state != STATE_DEAD]
                parked = [v for v in self.vehicles.values() if v.state == "parked"]
                if player_units and parked:
                    target_u = random.choice(player_units)
                    car = min(parked,
                              key=lambda v: math.dist((v.gx, v.gy), (target_u.gx, target_u.gy)))
                    car.arm_vbied(target_u.gx, target_u.gy)

        # Cleanup dead civs
        dead_civs = [cid for cid, c in self.civilians.items() if c.state == "dead"]
        for cid in dead_civs:
            del self.civilians[cid]

        # Remove dead units — leave wrecks for heavy units
        dead = [uid for uid, u in self.units.items() if u.state == STATE_DEAD]
        for uid in dead:
            u = self.units[uid]
            if u.garrisoned_in:
                pb = self.placed_buildings.get(u.garrisoned_in)
                if pb and uid in pb.garrison:
                    pb.garrison.remove(uid)
            if u.armor_type in ("heavy", "medium"):
                self.wrecks.append([u.gx, u.gy, 300.0])  # 5-min wreck marker
            elif u.armor_type == "light":
                self.wrecks.append([u.gx, u.gy, 120.0])
            del self.units[uid]

        # Tick + cull wrecks (permanent phase wrecks have t == 99999)
        self.wrecks = [[gx, gy, t - dt] for gx, gy, t in self.wrecks
                       if t == 99999 or t - dt > 0]

        # Buildings (Capture + Income)
        for iid in list(self.placed_buildings.keys()):
            pb = self.placed_buildings[iid]
            if pb.hp <= 0:
                for uid in pb.garrison:
                    if uid in self.units:
                        u = self.units[uid]
                        u.garrisoned_in = None
                        u.take_damage(20)
                self.events.append(("building_destroyed",
                                    {"name": getattr(pb, "display_name", pb.bdef["name"]),
                                     "faction": pb.faction}))
                # Leave rubble wreck markers at building footprint corners
                cx = pb.gx + pb.bdef["w"] / 2
                cy = pb.gy + pb.bdef["h"] / 2
                for ox, oy in [(-.5, -.5), (.5, -.5), (0, .3)]:
                    self.wrecks.append([cx + ox, cy + oy, 99999.0])
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
                # Command/HQ buildings require damage before capture can begin
                if "required" in pb.bdef.get("flags", []):
                    if pb.hp > pb.max_hp * 0.5:
                        pb._capture_progress = 0.0
                        continue
                # Journalist in the area doubles capture speed
                journalist_bonus = 1.0
                for ju in self.units.values():
                    if ju.utype == "journalist" and ju.faction == strongest and ju.state != STATE_DEAD:
                        if math.dist((ju.gx, ju.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) <= 5.0:
                            journalist_bonus = 2.0
                            break
                # Interpreter halves enemy capture rate within 5r
                interpreter_slow = 1.0
                for iu in self.units.values():
                    if iu.utype != "interpreter" or iu.state == STATE_DEAD:
                        continue
                    if strongest in self.enemies_of(iu.faction):
                        if math.dist((iu.gx, iu.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) <= 5.0:
                            interpreter_slow = 0.5
                            break
                pb._capture_progress += dt * 20.0 * max_n * journalist_bonus * interpreter_slow
                if pb._capture_progress >= 100.0:
                    old_faction = pb.faction
                    pb.faction = strongest
                    pb._capture_progress = 0.0
                    self.events.append(("building_captured",
                                        {"name": getattr(pb, "display_name", pb.bdef["name"]),
                                         "by": strongest, "from": old_faction}))
            elif pb._capture_progress > 0:
                pb._capture_progress = max(0, pb._capture_progress - dt * 10.0)

            # Pull civilians into holding pens
            if pb.bdef.get("garrison", 0) > 0 and pb.faction != "neutral":
                for c in list(self.civilians.values()):
                    if math.dist((c.gx, c.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) < 3.0:
                        if pb.civs_held < pb.bdef["garrison"]:
                            pb.civs_held += 1
                            reward = 25
                            if c.uid == self._bolo_uid:
                                reward = 500
                                self._bolo_uid = None
                                self.events.append(("bolo_captured",
                                                    {"faction": pb.faction}))
                            c.state = "dead"
                            self.credits[pb.faction] = self.credits.get(pb.faction, 0) + reward
                            if c.ctype == PROTESTER and pb.faction == player_faction:
                                self.roe_manager.add_infamy(5)
                                self.events.append(("protester_detained", {}))

        # Win/loss detection — only after intro ends (_mission_elapsed > 0)
        if self.game_over == self.GAME_OVER_NONE and self._mission_elapsed > 0:
            enemy = self._ENEMY_MAP.get(player_faction, "sovereign")
            player_hq_alive = any(pb.faction == player_faction and "command" in pb.bdef.get("flags", [])
                                  for pb in self.placed_buildings.values())
            enemy_hq_alive  = any(pb.faction == enemy and "command" in pb.bdef.get("flags", [])
                                  for pb in self.placed_buildings.values())
            if not player_hq_alive:
                self.game_over = self.GAME_OVER_DEFEAT
            elif not enemy_hq_alive:
                self.game_over = self.GAME_OVER_VICTORY

        # Iron Dome — suppress hostile drone units within 6r
        for pb in self.placed_buildings.values():
            if "iron_dome" not in pb.bdef.get("flags", []):
                continue
            dome_cx = pb.gx + pb.bdef["w"] / 2
            dome_cy = pb.gy + pb.bdef["h"] / 2
            for u in self.units.values():
                if u.state == STATE_DEAD or u.faction == pb.faction:
                    continue
                if u.utype not in ("drone_scout", "drone_assault", "drone_operator"):
                    continue
                if math.dist((u.gx, u.gy), (dome_cx, dome_cy)) <= 6.0:
                    if not getattr(u, "_dome_notified", False):
                        u._dome_notified = True
                        self.events.append(("iron_dome_intercept", {"utype": u.utype}))
                    u.suppress(2.0)
                else:
                    u._dome_notified = False

        # ALPR Scanner Logic
        for pb in self.placed_buildings.values():
            if "scanner" in pb.bdef.get("flags", []):
                for u in self.units.values():
                    if u.state == STATE_DEAD: continue
                    if u.faction == "sovereign" and math.dist((pb.gx, pb.gy), (u.gx, u.gy)) < 8.0:
                        u.scanned_timer = 2.0  # Show visual feedback
                        if not u.is_bolo:
                            u.is_bolo = True
                            self.events.append(("bolo_identified", {"unit": u.utype, "uid": u.uid}))

        # Witness War
        self._tick_witness_war(dt, player_faction)

        # Tape MacGuffin
        self._tick_tape(dt, player_faction)

        # Special unit abilities
        self._tick_special_units(dt)

        # Production queues
        self._income_timer += dt
        if self._income_timer >= self.PASSIVE_INCOME_TICK:
            self._income_timer = 0.0
            self._tick_income(player_faction)

        for iid, queue in list(self.unit_queues.items()):
            pb = self.placed_buildings.get(iid)
            if not pb:
                continue
            if pb.faction == player_faction and self.power_balance < 0:
                continue  # No production when underpowered
            # DDoS disabled building: tick down timer, stall production
            if getattr(pb, "_ddos_disabled", 0.0) > 0:
                pb._ddos_disabled = max(0.0, pb._ddos_disabled - dt)
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

    def _tick_witness_war(self, dt: float, player_faction: str):
        from game.civilian import _CONVERT_RANGE, _CONVERT_TIME

        # Build set of which civs are being converted this frame, and by whom
        converting: dict[int, str] = {}   # civ uid → faction converting them

        for u in self.units.values():
            if u.state == "dead":
                continue
            if u.faction not in ("frontline", "sovereign", "oligarchy"):
                continue
            rng = 6.0 if u.utype == "news_van" else _CONVERT_RANGE[u.faction]
            for c in self.civilians.values():
                if c.state == "dead" or c.witness_state != "free":
                    continue
                if math.dist((u.gx, u.gy), (c.gx, c.gy)) <= rng:
                    # Sovereign wins ties (most urgent)
                    if c.uid not in converting or u.faction == "sovereign":
                        converting[c.uid] = u.faction

        # Apply conversion ticks or decay
        radicalized_done = []
        for c in list(self.civilians.values()):
            if c.state == "dead" or c.witness_state != "free":
                continue
            if c.uid in converting:
                faction = converting[c.uid]
                if c.tick_conversion(dt, faction):
                    if faction == "sovereign":
                        radicalized_done.append(c)
                    elif faction == "frontline":
                        c.witness_state = "empowered"
                        self.events.append(("witness_empowered", {"gx": c.gx, "gy": c.gy}))
                    elif faction == "oligarchy":
                        c.witness_state = "assetized"
                        self.events.append(("witness_assetized", {"gx": c.gx, "gy": c.gy}))
            else:
                c.decay_conversion(dt)

        # Radicalization: remove civ, spawn Militia for Sovereign
        for c in radicalized_done:
            c.witness_state = "radicalized"
            self.spawn_unit("militia", "sovereign", c.gx, c.gy)
            del self.civilians[c.uid]
            self.events.append(("witness_radicalized", {"gx": c.gx, "gy": c.gy}))

        # Empowered civs generate Viral Clout for Frontline; protesters give 2.5× more
        empowered = [c for c in self.civilians.values() if c.witness_state == "empowered"]
        if empowered:
            clout = sum(7.5 if c.ctype == PROTESTER else 3.0 for c in empowered) * dt
            self.credits["frontline"] = self.credits.get("frontline", 0) + clout

        # Assetized civs: if an Oligarchy unit dies nearby, +§75 insurance payout
        # (handled in unit death → events, checked here via recent dead units)
        for uid, u in list(self.units.items()):
            if u.state == "dead" and u.faction == "oligarchy" and not getattr(u, "_insured", False):
                u._insured = True
                nearby_assets = sum(
                    1 for c in self.civilians.values()
                    if c.witness_state == "assetized"
                    and math.dist((c.gx, c.gy), (u.gx, u.gy)) < 6.0
                )
                if nearby_assets:
                    payout = nearby_assets * 75
                    self.credits["oligarchy"] = self.credits.get("oligarchy", 0) + payout
                    self.events.append(("insurance_payout", {"credits": payout}))

    def _tick_income(self, player_faction):
        # Power balance
        net_power = 0
        for pb in self.placed_buildings.values():
            if pb.faction == player_faction:
                net_power += pb.bdef.get("power_draw", 0)
        self.power_balance = net_power
        underpowered = net_power < 0

        tape_faction = self.tape_holder_faction
        epstein_active = getattr(self, "_epstein_timer", 0.0) > 0
        for pb in self.placed_buildings.values():
            if pb.faction != player_faction:
                continue
            income = pb.bdef.get("passive_income", 0)
            if pb.civs_held > 0:
                income += pb.civs_held * self.PEN_INCOME_RATE
            if income:
                if tape_faction == player_faction:
                    income = income * 1.15
                self.credits[player_faction] = \
                    self.credits.get(player_faction, 0) + income

        # Infrastructure silo carry-over bonus from previous missions
        bonus = getattr(self, "_passive_income_bonus", 0)
        if bonus:
            self.credits[player_faction] = \
                self.credits.get(player_faction, 0) + bonus

        # Building auras: propaganda (infamy reduce), medical (unit heal), salvage
        for pb in self.placed_buildings.values():
            flags = pb.bdef.get("flags", [])
            cx = pb.gx + pb.bdef["w"] / 2
            cy = pb.gy + pb.bdef["h"] / 2
            if "infamy_reduce" in flags and pb.faction == player_faction:
                self.roe_manager.add_infamy(-2)
            if "heal_aura" in flags:
                for u in self.units.values():
                    if u.faction == pb.faction and u.state != STATE_DEAD:
                        if math.dist((u.gx, u.gy), (cx, cy)) <= 8.0:
                            u.hp = min(u.max_hp, u.hp + 2)
            if "salvage" in flags and pb.faction == player_faction:
                # Oligarchy salvage yard: consume nearby wrecks for credits
                consumed = []
                for i, (wx, wy, _t) in enumerate(self.wrecks):
                    if math.dist((wx, wy), (cx, cy)) <= 10.0:
                        consumed.append(i)
                for i in reversed(consumed):
                    self.wrecks.pop(i)
                    self.credits[player_faction] = \
                        self.credits.get(player_faction, 0) + 200
                    self.events.append(("salvage", {"credits": 200}))
            if "troll" in flags:
                # Erodes capture progress of enemy-held buildings in radius
                troll_mult = 2.0 if self._troll_surge_timer > 0 else 1.0
                troll_cx = pb.gx + pb.bdef["w"] / 2
                troll_cy = pb.gy + pb.bdef["h"] / 2
                for target in self.placed_buildings.values():
                    if target is pb:
                        continue
                    if target.faction == pb.faction or target.faction == "neutral":
                        continue
                    dist = math.dist((target.gx + target.bdef["w"] / 2,
                                      target.gy + target.bdef["h"] / 2),
                                     (troll_cx, troll_cy))
                    if dist <= 10.0 and target._capture_progress > 0:
                        target._capture_progress = max(0.0, target._capture_progress - 8.0 * troll_mult)

        # Underpowered: stall production queues for player (skip progress)
        if underpowered:
            self.events.append(("power_low", {"balance": net_power}))

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

    def _unload_bus(self, bus: "ComplianceBus", pen: PlacedBuilding, player_faction: str):
        count   = len(bus.passengers)
        payout  = count * ComplianceBus.DELIVERY_RATE
        cap     = pen.bdef.get("garrison", 999)
        pen.civs_held = min(cap, pen.civs_held + count)
        if bus.bolo_aboard:
            payout += 500
            self._bolo_uid = None
            self.events.append(("bolo_captured", {"faction": player_faction}))
            bus.bolo_aboard = False
        self.credits[player_faction] = self.credits.get(player_faction, 0) + payout
        self.events.append(("bus_unloaded", {"count": count, "credits": payout}))
        bus.passengers = []

    # ── Tape MacGuffin ────────────────────────────────────────────────────────

    def spawn_tape(self, gx, gy):
        self.tape["active"] = True
        self.tape["gx"] = float(gx)
        self.tape["gy"] = float(gy)
        self.tape["holder_uid"] = None
        self.tape["holder_faction"] = None

    @property
    def tape_holder_faction(self):
        if self.tape["active"]:
            return self.tape["holder_faction"]
        return None

    def _tick_tape(self, dt, player_faction):
        if not self.tape["active"]:
            return
        holder_uid = self.tape["holder_uid"]
        if holder_uid is not None:
            u = self.units.get(holder_uid)
            if u is None or u.state == STATE_DEAD:
                old_faction = self.tape["holder_faction"]
                if u is not None:
                    self.tape["gx"] = u.gx
                    self.tape["gy"] = u.gy
                self.tape["holder_uid"] = None
                self.tape["holder_faction"] = None
                self.events.append(("tape_lost", {"faction": old_faction}))
            else:
                self.tape["gx"] = u.gx
                self.tape["gy"] = u.gy
        else:
            best, best_dist = None, 1.5
            for u in self.units.values():
                if u.state == STATE_DEAD:
                    continue
                d = math.dist((u.gx, u.gy), (self.tape["gx"], self.tape["gy"]))
                if d < best_dist:
                    best, best_dist = u, d
            if best is not None:
                self.tape["holder_uid"] = best.uid
                self.tape["holder_faction"] = best.faction
                self.events.append(("tape_acquired", {
                    "faction": best.faction,
                    "utype": best.utype,
                }))

    # ── Special Unit Abilities ────────────────────────────────────────────────

    def _tick_special_units(self, dt):
        for u in self.units.values():
            if u.state == STATE_DEAD:
                continue
            if u.utype == "patriot_lawyer":
                if not hasattr(u, "_cd_timer"):
                    u._cd_timer = 0.0
                u._cd_timer -= dt
                if u._cd_timer <= 0:
                    u._cd_timer = 8.0
                    for target in self.units.values():
                        if target.faction != u.faction and target.state != STATE_DEAD:
                            if math.dist((u.gx, u.gy), (target.gx, target.gy)) <= 3.5:
                                target.suppress(3.5)
                    self.events.append(("cease_desist", {"gx": u.gx, "gy": u.gy}))
            if u.utype == "agitator":
                # Burns down suppress timers 2× faster for nearby allies
                for ally in self.units.values():
                    if ally.faction == u.faction and ally is not u and ally.state != STATE_DEAD:
                        if math.dist((u.gx, u.gy), (ally.gx, ally.gy)) <= 4.0:
                            if hasattr(ally, "_suppress_timer") and ally._suppress_timer > 0:
                                ally._suppress_timer = max(0.0, ally._suppress_timer - dt)
            if u.utype == "settler":
                # Settler converts nearby neutral buildings 3× faster than normal capture
                if u.state not in (STATE_MOVING, STATE_DEAD):
                    for pb in self.placed_buildings.values():
                        if pb.faction == "neutral":
                            if math.dist((u.gx, u.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) <= 3.0:
                                pb._capture_progress = min(100.0, pb._capture_progress + dt * 40.0)
                                if pb._capture_progress >= 100.0:
                                    old_f = pb.faction
                                    pb.faction = u.faction
                                    pb._capture_progress = 0.0
                                    self.events.append(("building_captured",
                                                        {"name": getattr(pb, "display_name", pb.bdef["name"]),
                                                         "by": u.faction, "from": old_f}))
            if u.utype == "proud_perimeter":
                # Intercepts suppression: if nearby ally gets suppressed, PP takes it instead
                if not hasattr(u, "_shield_range"):
                    u._shield_range = 3.5
                for ally in self.units.values():
                    if ally.faction == u.faction and ally is not u and ally.state != STATE_DEAD:
                        if math.dist((u.gx, u.gy), (ally.gx, ally.gy)) <= u._shield_range:
                            if hasattr(ally, "_suppress_timer") and ally._suppress_timer > 0:
                                excess = ally._suppress_timer
                                ally._suppress_timer = 0.0
                                if hasattr(u, "_suppress_timer"):
                                    u._suppress_timer = max(u._suppress_timer, excess * 0.5)
            if u.utype == "direktor":
                # Resource aura: §3/s for each friendly building within 8r
                for pb in self.placed_buildings.values():
                    if pb.faction != u.faction:
                        continue
                    if math.dist((u.gx, u.gy), (pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2)) <= 8.0:
                        self.credits[u.faction] = self.credits.get(u.faction, 0) + 3.0 * dt

        # Hacktivist Cell: DDoS pulse every 45s on nearest enemy scanner/command
        for pb in self.placed_buildings.values():
            if "ddos" not in pb.bdef.get("flags", []):
                continue
            if not hasattr(pb, "_ddos_timer"):
                pb._ddos_timer = 45.0
            pb._ddos_timer -= dt
            if pb._ddos_timer <= 0:
                pb._ddos_timer = 45.0
                cx = pb.gx + pb.bdef["w"] / 2
                cy = pb.gy + pb.bdef["h"] / 2
                targets = [t for t in self.placed_buildings.values()
                           if t.faction != pb.faction
                           and any(f in t.bdef.get("flags", []) for f in ("sensor", "command", "scanner"))]
                if targets:
                    target = min(targets, key=lambda t: math.dist((t.gx, t.gy), (cx, cy)))
                    if not hasattr(target, "_ddos_disabled"):
                        target._ddos_disabled = 0.0
                    target._ddos_disabled = 30.0
                    self.events.append(("ddos_hit", {"building": target.bdef["name"]}))

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
