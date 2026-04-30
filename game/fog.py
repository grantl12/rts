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
    def __init__(self, width=W, height=H, map_phase=0):
        self.w = width
        self.h = height
        self.grid = [[FOG for _ in range(width)] for _ in range(height)]
        self.vision_sources = []

        if map_phase >= 2:
            # Shattered — 60% SHROUD; only a corridor around the center starts explored
            cx, cy = width // 2, height // 2
            for y in range(height):
                for x in range(width):
                    if abs(x - cx) > 9 or abs(y - cy) > 7:
                        self.grid[y][x] = SHROUD
        elif map_phase >= 1:
            # Scarred — outer border tiles are SHROUD
            border = 4
            for y in range(height):
                for x in range(width):
                    if x < border or x >= width - border or y < border or y >= height - border:
                        self.grid[y][x] = SHROUD
        
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
                flags = pb.bdef.get("flags", [])
                if "vision" in flags:
                    rad = 28  # surveillance tower
                elif "command" in flags:
                    rad = 16
                else:
                    rad = 10
                sources.append((pb.gx + pb.bdef["w"] / 2,
                                pb.gy + pb.bdef["h"] / 2, rad))
                
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
