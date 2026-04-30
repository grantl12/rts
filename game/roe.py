"""
Rules of Engagement (ROE) and Infamy system.
"""

ROE_NAMES = [
    "RESTRAINED",
    "CONTROLLED",
    "STANDARD",
    "ESCALATED",
    "ABSOLUTE IMMUNITY",
]

ROE_COLORS = [
    (76, 217, 89),   # 1 green
    (76, 209, 242),  # 2 cyan
    (209, 209, 209), # 3 gray
    (255, 166, 25),  # 4 amber
    (255, 38, 25),   # 5 red
]

# Damage multipliers based on ROE
DAMAGE_MULTS = [0.35, 0.65, 1.00, 1.50, 2.50]

class ROEManager:
    def __init__(self):
        self.current_roe = 3 # Start at STANDARD
        self.infamy = 0
        self.is_butcher = False
        self._ambient_timer = 0.0
        
    def set_roe(self, level, world=None):
        level = max(1, min(5, level))
        if level == self.current_roe:
            return
        
        # Absolute Immunity is irreversible
        if self.current_roe == 5:
            return
            
        self.current_roe = level
        self._ambient_timer = 0.0
        
        if level == 5:
            self.is_butcher = True
            self.add_infamy(200)
            if world:
                for c in world.civilians.values():
                    c.panic()
                player_f = getattr(world, "player_faction", "regency")
                for u in world.units.values():
                    if u.faction != player_f:
                        u.suppress(8.0)
            
    def get_damage_mult(self):
        return DAMAGE_MULTS[self.current_roe - 1]
        
    def get_color(self):
        return ROE_COLORS[self.current_roe - 1]
        
    def get_name(self):
        return ROE_NAMES[self.current_roe - 1]
        
    def add_infamy(self, amount):
        self.infamy = max(0, self.infamy + amount)
        
    def update(self, dt_sec):
        # Ambient infamy at high ROE
        intervals = [0.0, 0.0, 0.0, 10.0, 5.0]
        amounts = [0, 0, 0, 1, 5]
        
        interval = intervals[self.current_roe - 1]
        if interval > 0:
            self._ambient_timer += dt_sec
            if self._ambient_timer >= interval:
                self._ambient_timer = 0.0
                self.add_infamy(amounts[self.current_roe - 1])
