"""
AI Faction Controller.
Handles production and strategic orders for non-player factions.
"""
import random, math
from game.unit_entity import UNIT_DEFS, STATE_IDLE, STATE_ATTACK, STATE_MOVING


class AIFaction:
    def __init__(self, faction):
        self.faction = faction
        self.produce_timer = 0.0
        self.order_timer = 0.0
        self.raid_timer = 0.0

        self.PRODUCE_INTERVAL = 12.0
        self.ORDER_INTERVAL = 6.0
        self.RAID_INTERVAL = 25.0

    def update(self, dt_sec, world):
        self.produce_timer -= dt_sec
        self.order_timer -= dt_sec
        self.raid_timer -= dt_sec

        if self.produce_timer <= 0:
            self.produce_timer = self.PRODUCE_INTERVAL
            self._do_production(world)

        if self.order_timer <= 0:
            self.order_timer = self.ORDER_INTERVAL
            self._do_orders(world)

        if self.raid_timer <= 0:
            self.raid_timer = self.RAID_INTERVAL
            self._do_raids(world)

    def _do_production(self, world):
        factories = [pb for pb in world.placed_buildings.values()
                     if pb.faction == self.faction and pb.bdef.get("produces")]
        if not factories:
            return

        factory = random.choice(factories)
        queue = world.unit_queues.get(factory.bid)
        if not queue:
            return

        options = factory.bdef["produces"]
        if not options:
            return

        choice = random.choice(options)
        cost = UNIT_DEFS.get(choice, (0,)*8)[7]

        if world.credits.get(self.faction, 0) >= cost:
            queue.enqueue(choice, cost, world.credits[self.faction])
            world.credits[self.faction] = world.credits.get(self.faction, 0) - cost

    def _do_orders(self, world):
        player_faction = world.player_faction
        idle_units = [u for u in world.units.values()
                      if u.faction == self.faction and u.state == STATE_IDLE]
        if not idle_units:
            return

        # Priority 1: capture unclaimed objectives
        objectives = [pb for pb in world.placed_buildings.values()
                      if "objective" in pb.bdef.get("flags", [])
                      and pb.faction != self.faction]
        if objectives:
            target = random.choice(objectives)
            self._move_squad(idle_units, target.gx + target.bdef["w"] / 2,
                             target.gy + target.bdef["h"] / 2, world)
            return

        # Priority 2: attack nearest player unit
        player_units = [u for u in world.units.values() if u.faction == player_faction]
        if player_units:
            target_unit = min(player_units,
                              key=lambda u: math.dist((idle_units[0].gx, idle_units[0].gy),
                                                      (u.gx, u.gy)))
            for u in idle_units:
                from game.pathfinding import find_path
                blocked = world.blocked_tiles()
                wp = find_path((u.gx, u.gy), (target_unit.gx, target_unit.gy), blocked)
                u.order_move(wp[1:] if len(wp) > 1 else [])
            return

        # Priority 3: attack player HQ
        player_hq = next((pb for pb in world.placed_buildings.values()
                          if pb.faction == player_faction
                          and "command" in pb.bdef.get("flags", [])), None)
        if player_hq:
            self._move_squad(idle_units, player_hq.gx, player_hq.gy, world)

    def _move_squad(self, units, tx, ty, world):
        from game.pathfinding import find_path
        blocked = world.blocked_tiles()
        for u in units:
            wp = find_path((u.gx, u.gy), (tx, ty), blocked)
            u.order_move(wp[1:] if len(wp) > 1 else [])

    def _do_raids(self, world):
        player_faction = world.player_faction
        pens = [pb for pb in world.placed_buildings.values()
                if pb.faction == player_faction and pb.civs_held > 0]
        if not pens:
            return

        target_pen = random.choice(pens)
        my_units = [u for u in world.units.values() if u.faction == self.faction]
        if not my_units:
            return

        raid_squad = random.sample(my_units, min(len(my_units), 3))
        self._move_squad(raid_squad, target_pen.gx, target_pen.gy, world)
