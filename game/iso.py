"""Isometric coordinate transforms. Grid origin is top-center of screen."""

TILE_W = 72   # diamond width
TILE_H = 36   # diamond height
WALL_H = 22   # pixels per floor of elevation


def world_to_screen(gx: float, gy: float, gz: float = 0, ox: int = 0, oy: int = 0):
    """Grid cell → screen pixel (top-center of tile diamond)."""
    sx = ox + (gx - gy) * TILE_W // 2
    sy = oy + (gx + gy) * TILE_H // 2 - int(gz * WALL_H)
    return sx, sy


def screen_to_world(sx: float, sy: float, ox: int = 0, oy: int = 0):
    """Screen pixel → fractional grid coords (gz=0 plane)."""
    rx = sx - ox
    ry = sy - oy
    gx = rx / TILE_W + ry / TILE_H
    gy = ry / TILE_H - rx / TILE_W
    return gx, gy


def tile_diamond(gx: int, gy: int, ox: int, oy: int):
    """Return the 4 screen-space points of a tile's top diamond face."""
    cx, cy = world_to_screen(gx + 0.5, gy + 0.5, 0, ox, oy)
    return [
        (cx,              cy - TILE_H // 2),  # top
        (cx + TILE_W // 2, cy),               # right
        (cx,              cy + TILE_H // 2),  # bottom
        (cx - TILE_W // 2, cy),               # left
    ]
