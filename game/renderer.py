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


def _phase_color(col, map_phase):
    """Shift terrain color toward burnt/ruined based on map phase."""
    r, g, b = col
    if map_phase >= 1:
        # Scarred: darken + slight brown tint
        r = min(255, int(r * 0.72 + 18))
        g = int(g * 0.62)
        b = int(b * 0.55)
    if map_phase >= 2:
        # Shattered: heavy desaturation toward ash grey
        avg = (r + g + b) // 3
        r = int(r * 0.35 + avg * 0.65)
        g = int(g * 0.35 + avg * 0.65)
        b = int(b * 0.35 + avg * 0.65)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def draw_terrain(surf: pygame.Surface, cam, fog=None, map_phase=0):
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

            col = _phase_color(list(TILE_COLORS[t]), map_phase)
            edge_col = _phase_color(list(TEAL_DIM), map_phase)

            if fstate == FOG:
                col      = tuple(int(c * 0.65) for c in col)
                edge_col = tuple(int(c * 0.65) for c in edge_col)

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


_FACTION_MINI_COLORS = {
    "regency":   (28,  80, 180),
    "frontline": (80, 140,  40),
    "sovereign": (140, 40, 200),
    "oligarchy": ( 40,  40,  40),
    "neutral":   (100, 100,  80),
}


def draw_minimap(surf: pygame.Surface, cam, rect: pygame.Rect,
                 world=None, fog=None, player_faction=None):
    """Draw a top-down minimap into rect."""
    pygame.draw.rect(surf, (3, 8, 6), rect)

    sx = rect.width  / W
    sy = rect.height / H

    for gy in range(H):
        for gx in range(W):
            t = TERRAIN[gy][gx]
            if t == 0:
                continue
            col = list(TILE_COLORS[t])
            if fog:
                fstate = fog.grid[gy][gx]
                if fstate == 0:   # SHROUD
                    col = [8, 8, 8]
                elif fstate == 1: # FOG
                    col = [c // 2 for c in col]
            pygame.draw.rect(surf, col,
                (rect.x + int(gx * sx), rect.y + int(gy * sy),
                 max(1, int(sx)), max(1, int(sy))))

    # Static map buildings (neutral/pre-placed)
    for bld in BUILDINGS:
        _, _, _, bx, by, bw, bh, *_ = bld
        pygame.draw.rect(surf, TEAL_DIM,
            (rect.x + int(bx * sx), rect.y + int(by * sy),
             max(2, int(bw * sx)), max(2, int(bh * sy))))

    # Dynamic placed buildings (faction-colored)
    if world:
        for pb in world.placed_buildings.values():
            col = _FACTION_MINI_COLORS.get(pb.faction, (80, 80, 80))
            pygame.draw.rect(surf, col,
                (rect.x + int(pb.gx * sx), rect.y + int(pb.gy * sy),
                 max(2, int(pb.bdef["w"] * sx)), max(2, int(pb.bdef["h"] * sy))))

        # Unit dots
        for u in world.units.values():
            from game.unit_entity import STATE_DEAD
            if u.state == STATE_DEAD or u.garrisoned_in:
                continue
            if fog and not fog.is_visible(u.gx, u.gy) and u.faction != player_faction:
                continue
            col = _FACTION_MINI_COLORS.get(u.faction, (128, 128, 128))
            ux = rect.x + int(u.gx * sx)
            uy = rect.y + int(u.gy * sy)
            pygame.draw.rect(surf, col, (ux, uy, max(2, int(sx)), max(2, int(sy))))

    # Camera viewport rectangle
    from game.iso import TILE_W, TILE_H
    def cam_to_mini(gx, gy):
        return rect.x + int(gx * sx), rect.y + int(gy * sy)
    # Approximate viewport corners in world space
    vp_corners = [
        cam.screen_to_world(0, 0),
        cam.screen_to_world(cam.w, 0),
        cam.screen_to_world(cam.w, cam.h),
        cam.screen_to_world(0, cam.h),
    ]
    mini_pts = [cam_to_mini(gx, gy) for gx, gy in vp_corners]
    pygame.draw.polygon(surf, (0, 255, 204), mini_pts, 1)

    pygame.draw.rect(surf, TEAL_DIM, rect, 1)
