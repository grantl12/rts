"""AI Faction Controller — differentiated behavior per faction."""
import random, math
from game.unit_entity import UNIT_DEFS, STATE_IDLE, STATE_DEAD
from game.pathfinding import find_path

# Weighted production preferences per faction
_PRODUCE_WEIGHTS = {
    "sovereign": {"proxy": 3, "vbied": 1},
    "frontline": {"drone_scout": 3, "drone_assault": 1},
    "regency":   {"gravy_seal": 3, "ice_agent": 1},
    "oligarchy": {"gravy_seal": 2, "ice_agent": 1},
}

# (produce_interval, order_interval, raid_interval) in seconds
_INTERVALS = {
    "sovereign": (25.0,  8.0, 60.0),   # Slower buildup, rare raids
    "frontline": (20.0,  6.0, 75.0),   # Rapid response, light on raids
    "regency":   (28.0, 10.0, 60.0),   # Methodical, holds ground
    "oligarchy": (30.0, 12.0, 50.0),   # Slow buildup, heavy raid pens
}


class AIFaction:
    def __init__(self, faction, map_id="quad"):
        self.faction = faction
        self.map_id  = map_id
        prod, order, raid = _INTERVALS.get(faction, (12.0, 6.0, 25.0))
        om = {"district": 0.84}.get(map_id, 1.0)
        rm = {"district": 0.92}.get(map_id, 1.0)
        order *= om
        raid  *= rm
        self.produce_timer    = prod
        self.order_timer      = order
        self._raid_timer      = raid
        self.PRODUCE_INTERVAL = prod
        self.ORDER_INTERVAL   = order
        self.RAID_INTERVAL    = raid
        self._vbied_timer     = 45.0   # Sovereign only

    # ── Tick ──────────────────────────────────────────────────────────────────

    def update(self, dt_sec, world):
        self.produce_timer -= dt_sec
        self.order_timer   -= dt_sec
        self._raid_timer   -= dt_sec

        if self.produce_timer <= 0:
            self.produce_timer = self.PRODUCE_INTERVAL
            self._do_production(world)

        if self.order_timer <= 0:
            self.order_timer = self.ORDER_INTERVAL
            self._do_orders(world)

        if self._raid_timer <= 0:
            self._raid_timer = self.RAID_INTERVAL
            self._do_raids(world)

        if self.faction == "sovereign":
            self._vbied_timer -= dt_sec
            if self._vbied_timer <= 0:
                self._vbied_timer = random.uniform(50.0, 90.0)
                self._do_vbied(world)

    # ── Production ────────────────────────────────────────────────────────────

    def _do_production(self, world):
        factories = [pb for pb in world.placed_buildings.values()
                     if pb.faction == self.faction and pb.bdef.get("produces")]
        if not factories:
            return
        factory = random.choice(factories)
        queue   = world.unit_queues.get(factory.bid)
        if not queue:
            return
        options = factory.bdef["produces"]
        if not options:
            return

        weights = _PRODUCE_WEIGHTS.get(self.faction, {})
        pool    = []
        for utype in options:
            pool.extend([utype] * weights.get(utype, 1))
        choice = random.choice(pool)

        cost = UNIT_DEFS.get(choice, (0,)*8)[7]
        if world.credits.get(self.faction, 0) >= cost:
            if queue.enqueue(choice, cost, world.credits[self.faction]):
                world.credits[self.faction] -= cost

    # ── Orders — dispatch by faction ──────────────────────────────────────────

    def _do_orders(self, world):
        player_faction = world.player_faction
        idle = [u for u in world.units.values()
                if u.faction == self.faction and u.state == STATE_IDLE
                and u.state != STATE_DEAD]
        if not idle:
            return

        dispatch = {
            "sovereign": self._orders_sovereign,
            "frontline": self._orders_frontline,
            "regency":   self._orders_regency,
            "oligarchy": self._orders_oligarchy,
        }
        dispatch.get(self.faction, self._orders_default)(idle, player_faction, world)

    # ── Sovereign: disruption + split-squad flanking ──────────────────────────

    def _orders_sovereign(self, idle, player_faction, world):
        mid     = max(1, len(idle) // 2)
        squad_a = idle[:mid]
        squad_b = idle[mid:]

        player_units = self._targetable([u for u in world.units.values()
                        if u.faction == player_faction and u.state != STATE_DEAD])
        player_hq    = self._find_hq(player_faction, world)

        if player_units and squad_a:
            # Squad A hunts the nearest player unit
            nearest = min(player_units,
                          key=lambda u: math.dist((squad_a[0].gx, squad_a[0].gy),
                                                  (u.gx, u.gy)))
            self._move_squad(squad_a, nearest.gx, nearest.gy, world)

        if player_hq and squad_b:
            # Squad B approaches HQ from a randomised offset angle
            jx = random.uniform(-5, 5)
            jy = random.uniform(-5, 5)
            self._move_squad(squad_b, player_hq.gx + jx, player_hq.gy + jy, world)

    # ── Frontline: drone swarm + infamy pressure ──────────────────────────────

    def _orders_frontline(self, idle, player_faction, world):
        # Target audit/sensor nodes first to amplify infamy
        sensors = [pb for pb in world.placed_buildings.values()
                   if ("sensor" in pb.bdef.get("flags", [])
                       or "objective" in pb.bdef.get("flags", [])
                       or "infamy_amplify" in pb.bdef.get("flags", []))
                   and pb.faction != self.faction]
        if self.map_id == "district" and sensors and hasattr(world, "rally_point"):
            rx, ry = world.rally_point
            near = [s for s in sensors
                    if math.dist((s.gx, s.gy), (rx, ry)) < 20.0]
            if near:
                sensors = near
        if sensors:
            target = min(sensors,
                         key=lambda pb: math.dist((idle[0].gx, idle[0].gy),
                                                  (pb.gx, pb.gy)))
            self._move_squad(idle, target.gx, target.gy, world)
            return

        # Target the largest player cluster
        player_units = self._targetable([u for u in world.units.values()
                        if u.faction == player_faction and u.state != STATE_DEAD])
        if player_units:
            center = max(player_units,
                         key=lambda u: sum(1 for v in player_units
                                           if math.dist((u.gx, u.gy), (v.gx, v.gy)) < 5))
            self._move_squad(idle, center.gx, center.gy, world)
            return

        hq = self._find_hq(player_faction, world)
        if hq:
            self._move_squad(idle, hq.gx, hq.gy, world)

    # ── Regency: methodical capture-and-hold ──────────────────────────────────

    def _orders_regency(self, idle, player_faction, world):
        # Capture unclaimed or enemy buildings near our position
        capturable = [pb for pb in world.placed_buildings.values()
                      if pb.faction != self.faction]
        if capturable and len(idle) >= 2:
            if self.map_id == "district":
                rx, ry = getattr(world, "rally_point", (idle[0].gx, idle[0].gy))
                def _cap_score(pb):
                    d = math.dist((idle[0].gx, idle[0].gy), (pb.gx, pb.gy))
                    z = 0.0
                    if "objective" in pb.bdef.get("flags", []) or "scanner" in pb.bdef.get("flags", []):
                        z -= 5.0 * max(0.0, 1.0 - math.dist((pb.gx, pb.gy), (rx, ry)) / 22.0)
                    if pb.bdef.get("passive_income", 0) > 0:
                        z -= 3.0
                    return d + z
                target = min(capturable, key=_cap_score)
            else:
                target = min(capturable,
                             key=lambda pb: math.dist((idle[0].gx, idle[0].gy),
                                                      (pb.gx, pb.gy)))
            cap_squad = idle[:len(idle) // 2 + 1]
            self._move_squad(cap_squad, target.gx, target.gy, world)
            return

        player_units = self._targetable([u for u in world.units.values()
                        if u.faction == player_faction and u.state != STATE_DEAD])
        if player_units:
            nearest = min(player_units,
                          key=lambda u: math.dist((idle[0].gx, idle[0].gy),
                                                  (u.gx, u.gy)))
            self._move_squad(idle, nearest.gx, nearest.gy, world)
            return

        hq = self._find_hq(player_faction, world)
        if hq:
            self._move_squad(idle, hq.gx, hq.gy, world)

    # ── Oligarchy: economy-first, heavy assault when flush ────────────────────

    def _orders_oligarchy(self, idle, player_faction, world):
        # Prioritise income buildings
        income_blds = [pb for pb in world.placed_buildings.values()
                       if pb.bdef.get("passive_income", 0) > 0
                       and pb.faction != self.faction]
        if income_blds:
            target = min(income_blds,
                         key=lambda pb: math.dist((idle[0].gx, idle[0].gy),
                                                  (pb.gx, pb.gy)))
            self._move_squad(idle, target.gx, target.gy, world)
            return

        # Full assault only once credit reserves are comfortable
        if world.credits.get(self.faction, 0) > 2000:
            hq = self._find_hq(player_faction, world)
            if hq:
                self._move_squad(idle, hq.gx, hq.gy, world)
                return

        player_units = self._targetable([u for u in world.units.values()
                        if u.faction == player_faction and u.state != STATE_DEAD])
        if player_units:
            nearest = min(player_units,
                          key=lambda u: math.dist((idle[0].gx, idle[0].gy),
                                                  (u.gx, u.gy)))
            self._move_squad(idle, nearest.gx, nearest.gy, world)

    def _orders_default(self, idle, player_faction, world):
        player_units = self._targetable([u for u in world.units.values()
                        if u.faction == player_faction and u.state != STATE_DEAD])
        if player_units:
            nearest = min(player_units,
                          key=lambda u: math.dist((idle[0].gx, idle[0].gy),
                                                  (u.gx, u.gy)))
            self._move_squad(idle, nearest.gx, nearest.gy, world)
            return
        hq = self._find_hq(player_faction, world)
        if hq:
            self._move_squad(idle, hq.gx, hq.gy, world)

    # ── Sovereign VBIED — arm a parked car near player cluster ───────────────

    def _do_vbied(self, world):
        player_faction = world.player_faction
        parked = [v for v in world.vehicles.values() if v.state == "parked"]
        if not parked:
            return
        player_units = [u for u in world.units.values()
                        if u.faction == player_faction
                        and u.state not in ("dead",)]
        if not player_units:
            return
        # Pick the densest player cluster center
        target = max(player_units,
                     key=lambda u: sum(1 for v in player_units
                                       if math.dist((u.gx, u.gy), (v.gx, v.gy)) < 5))
        # Arm the parked car nearest the target
        car = min(parked, key=lambda v: math.dist((v.gx, v.gy), (target.gx, target.gy)))
        car.arm_vbied(target.gx, target.gy)
        world.events.append(("vbied_armed", {"gx": car.gx, "gy": car.gy}))

    # ── Raids ─────────────────────────────────────────────────────────────────

    def _do_raids(self, world):
        player_faction = world.player_faction
        pens = [pb for pb in world.placed_buildings.values()
                if pb.faction == player_faction and pb.civs_held > 0]
        if not pens:
            return
        my_units = [u for u in world.units.values()
                    if u.faction == self.faction and u.state != STATE_DEAD]
        if not my_units:
            return

        raid_size  = 4 if self.faction == "oligarchy" else 3
        raid_squad = random.sample(my_units, min(len(my_units), raid_size))
        target_pen = min(pens, key=lambda pb: pb.civs_held)  # hit the easiest pen
        self._move_squad(raid_squad, target_pen.gx, target_pen.gy, world)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _targetable(self, units):
        """Filter out units that AI should not auto-target (journalists, donors)."""
        _PROTECTED = {"journalist", "donor"}
        return [u for u in units if u.utype not in _PROTECTED]

    def _find_hq(self, faction, world):
        return next((pb for pb in world.placed_buildings.values()
                     if pb.faction == faction
                     and "command" in pb.bdef.get("flags", [])), None)

    def _move_squad(self, units, tx, ty, world):
        blocked = world.blocked_tiles()
        for u in units:
            wp = find_path((u.gx, u.gy), (tx, ty), blocked)
            u.order_move(wp[1:] if len(wp) > 1 else [])
