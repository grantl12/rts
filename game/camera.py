"""Pan/zoom camera. Tracks a screen-space origin offset."""
import pygame
from game.iso import screen_to_world

SCROLL_SPEED = 8
SCROLL_MARGIN = 12
ZOOM_LEVELS = (0.5, 0.75, 1.0, 1.25, 1.5)


class Camera:
    def __init__(self, screen_w: int, screen_h: int):
        self.w = screen_w
        self.h = screen_h
        self.ox = screen_w // 2
        self.oy = 80
        self._zoom_idx = 2
        self.zoom = ZOOM_LEVELS[self._zoom_idx]

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            delta = event.y
            self._zoom_idx = max(0, min(len(ZOOM_LEVELS) - 1, self._zoom_idx + delta))
            self.zoom = ZOOM_LEVELS[self._zoom_idx]

    def update(self):
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        spd = SCROLL_SPEED

        ctrl  = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        left  = keys[pygame.K_LEFT]  or (keys[pygame.K_a] and not ctrl) or mx < SCROLL_MARGIN
        right = keys[pygame.K_RIGHT] or (keys[pygame.K_d] and not ctrl) or mx > self.w - SCROLL_MARGIN
        up    = keys[pygame.K_UP]    or keys[pygame.K_w] or my < SCROLL_MARGIN
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s] or my > self.h - SCROLL_MARGIN

        if left:  self.ox += spd
        if right: self.ox -= spd
        if up:    self.oy += spd
        if down:  self.oy -= spd

    def world_to_screen(self, gx, gy, gz=0):
        from game.iso import world_to_screen, TILE_W, TILE_H, WALL_H
        sx = self.ox + (gx - gy) * int(TILE_W * self.zoom) // 2
        sy = self.oy + (gx + gy) * int(TILE_H * self.zoom) // 2 - int(gz * WALL_H * self.zoom)
        return sx, sy

    def screen_to_world(self, sx, sy):
        from game.iso import TILE_W, TILE_H
        tw = TILE_W * self.zoom
        th = TILE_H * self.zoom
        rx = sx - self.ox
        ry = sy - self.oy
        gx = rx / tw + ry / th
        gy = ry / th - rx / tw
        return gx, gy

    def pan_to(self, gx, gy):
        """Center the camera on world tile (gx, gy)."""
        from game.iso import TILE_W, TILE_H
        tw = int(TILE_W * self.zoom)
        th = int(TILE_H * self.zoom)
        self.ox = self.w // 2 - (gx - gy) * tw // 2
        self.oy = self.h // 2 - (gx + gy) * th // 2

    def tile_diamond(self, gx, gy):
        cx, cy = self.world_to_screen(gx + 0.5, gy + 0.5)
        from game.iso import TILE_W, TILE_H
        hw = int(TILE_W * self.zoom) // 2
        hh = int(TILE_H * self.zoom) // 2
        return [
            (cx,      cy - hh),
            (cx + hw, cy),
            (cx,      cy + hh),
            (cx - hw, cy),
        ]
