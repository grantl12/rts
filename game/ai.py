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
        # Find buildings owned by this faction that can produce
        factories = [pb for pb in world.placed_buildings.values() if pb.faction == self.faction and pb.bdef.get("produces")]
        if not factories:
            return
            
        factory = random.choice(factories)
        queue = world.unit_queues.get(factory.bid)
        if not queue:
            return
            
        # Try to produce the cheapest unit available
        options = factory.bdef["produces"]
        if not options: return
        
        # In this simple AI, we just enqueue if we have credits
        choice = random.choice(options)
        cost = UNIT_DEFS[choice][7]
        
        if world.credits.get(self.faction, 0) >= cost:
            queue.enqueue(choice, cost, world.credits[self.faction])
            world.credits[self.faction] -= cost

    def _do_orders(self, world):
        # Find idle units
        idle_units = [u for u in world.units.values() if u.faction == self.faction and u.state == STATE_IDLE]
        if not idle_units:
            return
            
        # 1. Prioritize uncaptured Audit Points
        objectives = [pb for pb in world.placed_buildings.values() if pb.bdef.get("flags") and "objective" in pb.bdef["flags"] and pb.faction != self.faction]
        
        if objectives:
            target = random.choice(objectives)
            for u in idle_units:
                from game.pathfinding import find_path
                blocked = world.blocked_tiles()
                wp = find_path((u.gx, u.gy), (target.gx + target.bdef["w"]/2, target.gy + target.bdef["h"]/2), blocked)
                u.order_move(wp[1:] if len(wp)>1 else [])
            return

        # 2. Find player units or buildings to attack
        player_faction = "regency"
...

    def _do_raids(self, world):
        # Target player holding pens specifically
        player_faction = "regency"
        pens = [pb for pb in world.placed_buildings.values() if pb.faction == player_faction and pb.civs_held > 0]
        if not pens:
            return
            
        target_pen = random.choice(pens)
        
        # Take some units (even if not idle) and send them to the pen
        my_units = [u for u in world.units.values() if u.faction == self.faction]
        if not my_units: return
        
        raid_squad = random.sample(my_units, min(len(my_units), 3))
        for u in raid_squad:
            from game.pathfinding import find_path
            blocked = world.blocked_tiles()
            wp = find_path((u.gx, u.gy), (target_pen.gx, target_pen.gy), blocked)
            u.order_move(wp[1:] if len(wp)>1 else [])
