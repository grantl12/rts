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
        
    def set_roe(self, level, world=None):
        level = max(1, min(5, level))
        if level == self.current_roe:
            return

        # Absolute Immunity is irreversible
        if self.current_roe == 5:
            return

        # If ROE 5 is requested, set a flag indicating confirmation is needed
        if level == 5:
            self.pending_roe_confirmation = True
            # Do not change current_roe or apply effects yet
            return

        # For levels 1-4, apply changes directly
        self.current_roe = level
        self._ambient_timer = 0.0
        
        # Effects that were previously here for level 5 are now conditional
        # (These will be triggered after confirmation)
        if level == 5: # This check will now be based on confirmation, not direct level setting
            self.is_butcher = True
            self.add_infamy(200)
            if world:
                for c in world.civilians.values():
                    c.panic()
                player_f = getattr(world, "player_faction", "regency")
                for u in world.units.values():
                    if u.faction != player_f:
                        u.suppress(8.0)
    
    def confirm_roe_5(self, world=None):
        """Activates ROE 5 after user confirmation."""
        if not self.pending_roe_confirmation:
            return # Should not happen if called correctly

        self.current_roe = 5
        self.is_butcher = True
        self.add_infamy(200)
        self._ambient_timer = 0.0 # Reset timer on activation

        if world:
            for c in world.civilians.values():
                c.panic()
            player_f = getattr(world, "player_faction", "regency")
            for u in world.units.values():
                if u.faction != player_f:
                    u.suppress(8.0)
        
        self.pending_roe_confirmation = False # Reset confirmation flag

        return DAMAGE_MULTS[self.current_roe - 1]
        
    def get_color(self):
        return ROE_COLORS[self.current_roe - 1]
        
    def get_name(self):
        return ROE_NAMES[self.current_roe - 1]
        
    def add_infamy(self, amount, world=None):
        old_infamy = self.infamy
        self.infamy = max(0, self.infamy + amount)
        
        # Check for infamy threshold crossings
        if old_infamy < 400 <= self.infamy:
            # SURVEILLED: Spawn Frontline observer unit
            if world:
                from game.map_data import W, H
                # Spawn near map center
                center_gx = W / 2.0
                center_gy = H / 2.0
                world.spawn_unit("drone_scout", "frontline", center_gx, center_gy)
                print(f"Infamy reached 400: SURVEILLED. Spawning observer unit near ({center_gx}, {center_gy}).") # Debug print

        if old_infamy < 750 <= self.infamy:
            # SANCTIONED: Freeze high-tier production
            if world:
                world.set_production_frozen(True, "high_tier")
                print(f"Infamy reached 750: SANCTIONED. Freezing high-tier production.") # Debug print

        # Ambient infamy at high ROE
        intervals = [0.0, 0.0, 0.0, 10.0, 5.0]
        amounts = [0, 0, 0, 1, 5]
        
        interval = intervals[self.current_roe - 1]
        if interval > 0:
            self._ambient_timer += dt_sec
            if self._ambient_timer >= interval:
                self._ambient_timer = 0.0
                self.add_infamy(amounts[self.current_roe - 1])
