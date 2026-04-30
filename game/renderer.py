"""Draw tiles, buildings, and units onto a pygame surface."""
import pygame
from game.map_data import TERRAIN, BUILDINGS, TILE_COLORS, BTYPE_COLORS, W, H, VOID
from game.iso import TILE_W, TILE_H, WALL_H
from game.fog import SHROUD, FOG, VISION

TEAL        = (0, 255, 204)
TEAL_DIM    = (0, 100, 80)
ORANGE      = (255, 102, 0)
DARK        = (6, 13, 10)


def _scaled(cam, tw, th, wh):
    return int(tw * cam.zoom), int(th * cam.zoom), int(wh * cam.zoom)


def draw_terrain(surf: pygame.Surface, cam, fog=None):
    tw, th, _ = _scaled(cam, TILE_W, TILE_H, WALL_H)
    hw, hh = tw // 2, th // 2

    for gy in range(H):
        for gx in range(W):
            t = TERRAIN[gy][gx]
            if t == VOID:
                continue
            
            # Fog of War check
            fstate = VISION
            if fog:
                fstate = fog.grid[gy][gx]
            
            if fstate == SHROUD:
                continue
                
            cx, cy = cam.world_to_screen(gx + 0.5, gy + 0.5)
            pts = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
            
            col = list(TILE_COLORS[t])
            edge_col = list(TEAL_DIM)
            
            if fstate == FOG:
                # Dim the color
                col = [c // 1.5 for c in col]
                edge_col = [c // 1.5 for c in edge_col]
                
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, edge_col, pts, 1)


def draw_buildings(surf: pygame.Surface, cam, selected_id=None, font=None):
    tw, th, wh = _scaled(cam, TILE_W, TILE_H, WALL_H)
    hw, hh = tw // 2, th // 2

    # Sort back-to-front (painter's algorithm)
    sorted_blds = sorted(BUILDINGS, key=lambda b: b[3] + b[4])

    for bld in sorted_blds:
        bid, name, sub, bx, by, bw, bh, floors, btype, hp, max_hp = bld
        pal = BTYPE_COLORS.get(btype, BTYPE_COLORS["depot"])
        highlight = (bid == selected_id)

        _draw_building(surf, cam, bx, by, bw, bh, floors, pal, hw, hh, wh, highlight)

        if font:
            lx, ly = cam.world_to_screen(bx + bw / 2, by + bh / 2, floors + 0.4)
            col = ORANGE if highlight else (*TEAL, 140)
            label = font.render(name, True, col[:3])
            surf.blit(label, (lx - label.get_width() // 2, ly - label.get_height() // 2))


def _draw_building(surf, cam, bx, by, bw, bh, floors, pal, hw, hh, wh, highlight):
    def pt(gx, gy, gz):
        return cam.world_to_screen(gx, gy, gz)

    # Left wall
    ll = [pt(bx, by+bh, 0), pt(bx+bw, by+bh, 0), pt(bx+bw, by+bh, floors), pt(bx, by+bh, floors)]
    pygame.draw.polygon(surf, pal["wall_l"], ll)

    # Right wall
    rr = [pt(bx+bw, by, 0), pt(bx+bw, by+bh, 0), pt(bx+bw, by+bh, floors), pt(bx+bw, by, floors)]
    pygame.draw.polygon(surf, pal["wall_r"], rr)

    # Top face
    top = [pt(bx, by, floors), pt(bx+bw, by, floors), pt(bx+bw, by+bh, floors), pt(bx, by+bh, floors)]
    pygame.draw.polygon(surf, pal["top"], top)

    edge_col = ORANGE if highlight else (0, 60, 45)
    edge_w   = 2 if highlight else 1
    for face in (ll, rr, top):
        pygame.draw.polygon(surf, edge_col, face, edge_w)

    # Floor lines on walls
    line_col = (0, 40, 30) if not highlight else (80, 40, 0)
    for f in range(1, floors):
        la, lb = pt(bx, by+bh, f), pt(bx+bw, by+bh, f)
        ra, rb = pt(bx+bw, by, f), pt(bx+bw, by+bh, f)
        pygame.draw.line(surf, line_col, la, lb, 1)
        pygame.draw.line(surf, line_col, ra, rb, 1)


def draw_minimap(surf: pygame.Surface, cam, rect: pygame.Rect):
    """Draw a top-down minimap into rect."""
    pygame.draw.rect(surf, (3, 8, 6), rect)
    pygame.draw.rect(surf, TEAL_DIM, rect, 1)

    sx = rect.width  / W
    sy = rect.height / H

    for gy in range(H):
        for gx in range(W):
            t = TERRAIN[gy][gx]
            if t == 0:
                continue
            col = TILE_COLORS[t]
            pygame.draw.rect(surf, col,
                (rect.x + int(gx * sx), rect.y + int(gy * sy),
                 max(1, int(sx)), max(1, int(sy))))

    for bld in BUILDINGS:
        _, _, _, bx, by, bw, bh, *_ = bld
        pygame.draw.rect(surf, TEAL_DIM,
            (rect.x + int(bx * sx), rect.y + int(by * sy),
             max(2, int(bw * sx)), max(2, int(bh * sy))))
        pygame.draw.rect(surf, TEAL,
            (rect.x + int(bx * sx), rect.y + int(by * sy),
             max(2, int(bw * sx)), max(2, int(bh * sy))), 1)
