"""
Fog of War system — "Data Blackout".
Handles visibility grid (shroud/fog/vision) and provides masking for the renderer.
"""
import pygame
from game.map_data import W, H

# Visibility states
SHROUD = 0  # Black (unexplored)
FOG    = 1  # Grey (explored but no vision)
VISION = 2  # Clear

class FogManager:
    def __init__(self, width=W, height=H):
        self.w = width
        self.h = height
        # Start fully explored (FOG) so map layout is always visible;
        # VISION requires active unit/building line-of-sight.
        self.grid = [[FOG for _ in range(width)] for _ in range(height)]
        # last_vision stores which tiles were visible in the last update to update FOG
        self.vision_sources = [] # list of (gx, gy, radius)
        
    def update(self, world, player_faction, extra_sources=None):
        # 1. Turn current VISION into FOG
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == VISION:
                    self.grid[y][x] = FOG
        
        # 2. Gather vision sources
        sources = []
        if extra_sources:
            sources.extend(extra_sources)

        # Units
        for u in world.units.values():
            if u.faction == player_faction and u.state != "dead" and not u.garrisoned_in:
                # Default vision radius for units
                rad = 10 if u.utype != "drone_scout" else 15
                sources.append((u.gx, u.gy, rad))
        
        # Buildings
        for pb in world.placed_buildings.values():
            if pb.faction == player_faction:
                # Buildings give vision
                rad = 12
                if pb.bdef.get("produces") == "sensor": # Sensor towers
                    rad = 20
                # Center of building
                sources.append((pb.gx + pb.bdef["w"]/2, pb.gy + pb.bdef["h"]/2, rad))
                
        # 3. Apply VISION
        for vx, vy, vrad in sources:
            # Simple circular vision
            ix, iy = int(vx), int(vy)
            ir = int(vrad)
            for dy in range(-ir, ir + 1):
                for dx in range(-ir, ir + 1):
                    tx, ty = ix + dx, iy + dy
                    if 0 <= tx < self.w and 0 <= ty < self.h:
                        if dx*dx + dy*dy <= vrad*vrad:
                            self.grid[ty][tx] = VISION
                            
    def is_visible(self, gx, gy):
        ix, iy = int(gx), int(gy)
        if 0 <= ix < self.w and 0 <= iy < self.h:
            return self.grid[iy][ix] == VISION
        return False

    def is_explored(self, gx, gy):
        ix, iy = int(gx), int(gy)
        if 0 <= ix < self.w and 0 <= iy < self.h:
            return self.grid[iy][ix] != SHROUD
        return False
