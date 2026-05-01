"""Draw tiles, buildings, and units onto a pygame surface."""
import pygame, math
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

    # Wall colors with height-based shading
    win_col = pal.get("window", (0, 60, 80))
    accent  = pal.get("accent", pal["top"])

    # --- 0. Drop Shadow ---
    # Draw a semi-transparent black shadow on the ground
    sh_off = floors * 0.2
    shadow = [pt(bx+sh_off, by+sh_off, 0), pt(bx+bw+sh_off, by+sh_off, 0), 
              pt(bx+bw+sh_off, by+bh+sh_off, 0), pt(bx+sh_off, by+bh+sh_off, 0)]
    pygame.draw.polygon(surf, (0, 0, 0, 100), shadow)

    # --- 1. Draw Walls ---
    # Left wall (SW facing)
    ll = [pt(bx, by+bh, 0), pt(bx+bw, by+bh, 0), pt(bx+bw, by+bh, floors), pt(bx, by+bh, floors)]
    pygame.draw.polygon(surf, pal["wall_l"], ll)

    # Right wall (SE facing)
    rr = [pt(bx+bw, by, 0), pt(bx+bw, by+bh, 0), pt(bx+bw, by+bh, floors), pt(bx+bw, by, floors)]
    pygame.draw.polygon(surf, pal["wall_r"], rr)

    # --- 2. Procedural Windows ---
    # Draw a grid of windows on each floor
    for f in range(floors):
        # Left wall windows
        for x in range(int(bw * 2)):
            wx = bx + (x + 0.25) / 2.0
            if wx + 0.25 > bx + bw: break
            w_pts = [pt(wx, by+bh, f+0.3), pt(wx+0.3, by+bh, f+0.3), 
                     pt(wx+0.3, by+bh, f+0.7), pt(wx, by+bh, f+0.7)]
            pygame.draw.polygon(surf, win_col, w_pts)
        
        # Right wall windows
        for y in range(int(bh * 2)):
            wy = by + (y + 0.25) / 2.0
            if wy + 0.25 > by + bh: break
            w_pts = [pt(bx+bw, wy, f+0.3), pt(bx+bw, wy+0.3, f+0.3), 
                     pt(bx+bw, wy+0.3, f+0.7), pt(bx+bw, wy, f+0.7)]
            pygame.draw.polygon(surf, win_col, w_pts)

    # --- 3. Top Face & Roof Details ---
    top = [pt(bx, by, floors), pt(bx+bw, by, floors), pt(bx+bw, by+bh, floors), pt(bx, by+bh, floors)]
    pygame.draw.polygon(surf, pal["top"], top)

    # Roof Greebles (AC units, vents) - random but stable based on position
    import random
    rng = random.Random(int(bx * 100 + by))
    if bw >= 2 and bh >= 2:
        for _ in range(rng.randint(1, 3)):
            gx, gy = bx + rng.uniform(0.5, bw-0.5), by + rng.uniform(0.5, bh-0.5)
            # Small AC box
            ac_top = [pt(gx, gy, floors+0.2), pt(gx+0.4, gy, floors+0.2), 
                      pt(gx+0.4, gy+0.4, floors+0.2), pt(gx, gy+0.4, floors+0.2)]
            pygame.draw.polygon(surf, (120, 120, 110), ac_top)
            pygame.draw.polygon(surf, (20, 20, 20), ac_top, 1)

    # --- 4. Specialized Roof Styles ---
    style = pal.get("roof_style", "flat")
    if style == "hat":
        # The "Red Hat" roof for Patriot HQ
        hat_pts = [pt(bx+0.5, by+0.5, floors), pt(bx+bw-0.5, by+0.5, floors),
                   pt(bx+bw-0.5, by+bh-0.5, floors), pt(bx+0.5, by+bh-0.5, floors),
                   pt(bx+bw/2, by+bh/2, floors+0.8)]
        # Draw sides of the hat
        for i in range(4):
            side = [hat_pts[i], hat_pts[(i+1)%4], hat_pts[4]]
            pygame.draw.polygon(surf, (180, 30, 20), side)
            pygame.draw.polygon(surf, (40, 0, 0), side, 1)

    elif style == "antenna":
        # Communication / Scanner towers
        base_z = floors
        for i in range(3):
            z = base_z + i * 0.4
            pygame.draw.line(surf, accent, pt(bx+bw/2, by+bh/2, z), pt(bx+bw/2, by+bh/2, z+0.4), 2)
            # Cross-bars
            pygame.draw.line(surf, accent, pt(bx+bw/2-0.2, by+bh/2, z+0.2), pt(bx+bw/2+0.2, by+bh/2, z+0.2), 1)

    elif style == "dish":
        # Satellite dish
        cx, cy = bx + bw/2, by + bh/2
        dish_pts = []
        for i in range(8):
            ang = i * (math.pi / 4)
            dx, dy = math.cos(ang) * 0.4, math.sin(ang) * 0.4
            dish_pts.append(pt(cx + dx, cy + dy, floors + 0.5))
        pygame.draw.polygon(surf, (150, 150, 160), dish_pts)
        pygame.draw.polygon(surf, (40, 40, 50), dish_pts, 1)
        # Dish arm
        pygame.draw.line(surf, (100, 100, 110), pt(cx, cy, floors), pt(cx, cy, floors+0.5), 2)

    elif style == "spire":
        # Clock tower / Spire
        tip = pt(bx+bw/2, by+bh/2, floors + 2.0)
        for dx, dy in [(0,0), (bw,0), (bw,bh), (0,bh)]:
            pygame.draw.line(surf, pal["top"], pt(bx+dx, by+dy, floors), tip, 1)

    elif style == "gable":
        # Residential peaked roof
        peak_y = by + bh/2
        p1, p2 = pt(bx, peak_y, floors+0.8), pt(bx+bw, peak_y, floors+0.8)
        # Roof slants
        s1 = [pt(bx, by, floors), pt(bx+bw, by, floors), p2, p1]
        s2 = [pt(bx, by+bh, floors), pt(bx+bw, by+bh, floors), p2, p1]
        pygame.draw.polygon(surf, pal["top"], s1)
        pygame.draw.polygon(surf, pal["top"], s2)
        pygame.draw.polygon(surf, (20,20,20), s1, 1)
        pygame.draw.polygon(surf, (20,20,20), s2, 1)

    elif style == "awning":
        # Shopfront awning
        awn = [pt(bx, by+bh, 0.8), pt(bx+bw, by+bh, 0.8), pt(bx+bw, by+bh+0.3, 0.5), pt(bx, by+bh+0.3, 0.5)]
        pygame.draw.polygon(surf, accent, awn)
        pygame.draw.polygon(surf, (0,0,0), awn, 1)

    elif style == "cross":
        # Medical cross
        cx, cy = bx + bw/2, by + bh/2
        # Vertical bar
        pygame.draw.polygon(surf, accent, [pt(cx-0.2, cy-0.5, floors+0.1), pt(cx+0.2, cy-0.5, floors+0.1),
                                           pt(cx+0.2, cy+0.5, floors+0.1), pt(cx-0.2, cy+0.5, floors+0.1)])
        # Horizontal bar
        pygame.draw.polygon(surf, accent, [pt(cx-0.5, cy-0.2, floors+0.1), pt(cx+0.5, cy-0.2, floors+0.1),
                                           pt(cx+0.5, cy+0.2, floors+0.1), pt(cx-0.5, cy+0.2, floors+0.1)])

    elif style == "tower":
        # Substation tower
        for dz in [0.2, 0.6]:
            t_pts = [pt(bx+0.2, by+0.2, floors+dz), pt(bx+bw-0.2, by+0.2, floors+dz),
                     pt(bx+bw-0.2, by+bh-0.2, floors+dz), pt(bx+0.2, by+bh-0.2, floors+dz)]
            pygame.draw.polygon(surf, accent, t_pts, 1)

    elif style == "hangar":
        # Rounded depot roof
        steps = 6
        for i in range(steps):
            z1 = floors + math.sin(i / steps * math.pi) * 0.8
            z2 = floors + math.sin((i+1) / steps * math.pi) * 0.8
            y1 = by + (i / steps) * bh
            y2 = by + ((i+1) / steps) * bh
            panel = [pt(bx, y1, z1), pt(bx+bw, y1, z1), pt(bx+bw, y2, z2), pt(bx, y2, z2)]
            pygame.draw.polygon(surf, pal["top"], panel)
            pygame.draw.polygon(surf, (0,0,0), panel, 1)

    elif style == "tent":
        # HQ tent peak
        peak = pt(bx+bw/2, by+bh/2, floors+0.6)
        for dx, dy in [(0,0), (bw,0), (bw,bh), (0,bh)]:
            pygame.draw.polygon(surf, pal["top"], [pt(bx+dx, by+dy, floors), pt(bx+bw/2, by+bh/2, floors+0.6), pt(bx+dx, by+dy, floors)]) # simplified tent sides
            # Actually need proper triangles
            pass 
        # Better tent:
        corners = [(bx,by), (bx+bw,by), (bx+bw,by+bh), (bx,by+bh)]
        for i in range(4):
            c1, c2 = corners[i], corners[(i+1)%4]
            tri = [pt(c1[0], c1[1], floors), pt(c2[0], c2[1], floors), peak]
            pygame.draw.polygon(surf, pal["top"], tri)
            pygame.draw.polygon(surf, (0,0,0), tri, 1)

    # --- 5. Outlines ---
    edge_col = ORANGE if highlight else (0, 60, 45)
    edge_w   = 2 if highlight else 1
    for face in (ll, rr, top):
        pygame.draw.polygon(surf, edge_col, face, edge_w)

    # --- 6. Blinking Beacon ---
    # High-impact tactical blinker for all tall structures
    if floors >= 2 or style in ("antenna", "dish", "spire"):
        import time
        if int(time.time() * 2) % 2 == 0:
            bz = floors + 0.1
            if style == "antenna": bz = floors + 1.2
            if style == "spire": bz = floors + 2.0
            bx_c, by_c = bx + bw/2, by + bh/2
            b_pos = pt(bx_c, by_c, bz)
            pygame.draw.circle(surf, (255, 30, 0), b_pos, 3)
            pygame.draw.circle(surf, (255, 100, 100), b_pos, 1)


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
