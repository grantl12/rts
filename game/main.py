"""
Deep State RTS — main game loop.
Run: python -m game.main
"""
import sys, math, pygame

from game.camera    import Camera
from game.world     import World
from game.selection import SelectionManager
from game.sidebar   import BuildSidebar
from game.renderer  import draw_terrain, draw_buildings, draw_minimap, DARK
from game.hud       import HUD, TOPBAR_H, SIDEBAR_W
from game.map_data  import KIRK_RALLY, BUILDINGS as MAP_BLDS
from game.fog       import FogManager
from game import menu as _menu_mod

TITLE    = "DEEP STATE RTS — OP: WOLVERINE"
WIN_W, WIN_H = 1280, 800
FPS      = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    PLAYER_FACTION = _menu_mod.run(screen, clock, FPS)

    cam       = Camera(WIN_W, WIN_H)
    world     = World(PLAYER_FACTION)
    fog       = FogManager()
    selection = SelectionManager()
    sidebar   = BuildSidebar(PLAYER_FACTION)
    hud       = HUD(WIN_W, WIN_H)

    font_sm = pygame.font.SysFont("couriernew", 9)

    # ── Intro State ──
    intro_state = "rally" # rally, shot, panic, end
    intro_timer = 5.0
    kirk_obj = world.spawn_civilian(*KIRK_RALLY, ctype="kirk")
    # Camera start at rally
    cam.gx, cam.gy = KIRK_RALLY[0] - 8, KIRK_RALLY[1] - 8

    # Build sidebar rect (bottom portion of right sidebar)
    def sidebar_rect():
        sr = hud.sidebar_rect
        top = hud.minimap_rect.bottom + 110
        return pygame.Rect(sr.left, top, sr.width, sr.bottom - top - 80)

    placing_bid    = None   # building being ghost-placed
    placing_ghost  = None   # (gx, gy) of ghost
    click_zones    = []     # updated each draw by sidebar

    while True:
        dt = clock.tick(FPS)
        dt_sec = dt / 1000.0

        # ── Intro Logic ──
        if intro_state != "end":
            intro_timer -= dt_sec
            if intro_state == "rally" and intro_timer <= 0:
                intro_state = "shot"
                intro_timer = 0.5
                kirk_obj.state = "dead"
                # Screen flash simulated in draw
            elif intro_state == "shot" and intro_timer <= 0:
                intro_state = "panic"
                intro_timer = 2.5
                for c in world.civilians.values():
                    if math.dist((c.gx, c.gy), KIRK_RALLY) < 15:
                        c.panic()
            elif intro_state == "panic" and intro_timer <= 0:
                intro_state = "end"
                # Starter squads keyed by faction
                _STARTER = {
                    "regency":   [("gravy_seal",3),("ice_agent",2)],
                    "frontline": [("drone_scout",3),("proxy",2)],
                    "sovereign": [("proxy",3),("contractor",1)],
                    "oligarchy": [("contractor",2),("gravy_seal",2)],
                }
                sx0, sy0 = 13, 19
                for utype, count in _STARTER.get(PLAYER_FACTION, [("gravy_seal",3)]):
                    for i in range(count):
                        world.spawn_unit(utype, PLAYER_FACTION, sx0 + i * 0.8, sy0)
                    sy0 += 1
                # Enemy scouts emerge from their base
                enemy = world._ENEMY_MAP.get(PLAYER_FACTION, "sovereign")
                for i in range(3):
                    world.spawn_unit("proxy", enemy, 6 + i, 5)

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if intro_state == "end":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if placing_bid:
                            placing_bid = None
                        else:
                            pygame.quit(); sys.exit()
                    # Double-click type: ctrl+A selects all player units
                    if event.key == pygame.K_a and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        all_u = [u for u in world.units.values() if u.faction == PLAYER_FACTION]
                        selection._set_selection(all_u, world)
                    # S = stop selected units
                    if event.key == pygame.K_s:
                        for uid in selection.selected_uids:
                            if uid in world.units:
                                world.units[uid].order_stop()
                    
                    # ROE keys
                    if event.key == pygame.K_1: world.roe_manager.set_roe(1, world)
                    if event.key == pygame.K_2: world.roe_manager.set_roe(2, world)
                    if event.key == pygame.K_3: world.roe_manager.set_roe(3, world)
                    if event.key == pygame.K_4: world.roe_manager.set_roe(4, world)
                    if event.key == pygame.K_5: world.roe_manager.set_roe(5, world)

            cam.handle_event(event)

            if intro_state == "end":
                if event.type == pygame.MOUSEMOTION:
                    selection.mouse_move(event.pos)
                    if placing_bid:
                        gx, gy = cam.screen_to_world(*event.pos)
                        placing_ghost = (int(gx), int(gy))

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if placing_bid:
                        if event.button == 1 and placing_ghost:
                            pb = world.place_building(placing_bid, PLAYER_FACTION, *placing_ghost)
                            placing_bid   = None
                            placing_ghost = None
                        elif event.button == 3:
                            placing_bid   = None
                            placing_ghost = None
                    else:
                        # Check sidebar click zones
                        result = sidebar.handle_click(event.pos, click_zones, world, PLAYER_FACTION)
                        if result:
                            pass  # queued; could flash a message
                        else:
                            selection.mouse_down(event.pos, event.button, cam, world, hud)

                if event.type == pygame.MOUSEBUTTONUP:
                    selection.mouse_up(event.pos, event.button, cam, world, hud)

        # ── Update ────────────────────────────────────────────────────────────
        cam.update()
        world.update(dt, PLAYER_FACTION)

        extra_v = []
        if intro_state != "end":
            extra_v.append((*KIRK_RALLY, 12))
        fog.update(world, PLAYER_FACTION, extra_sources=extra_v)

        completed_struct, completed_unit = sidebar.update(dt, world, PLAYER_FACTION)
        if completed_struct:
            placing_bid = completed_struct   # enter placement mode
        if completed_unit:
            # Auto-spawn near barracks
            world.spawn_unit(completed_unit, PLAYER_FACTION, 13, 19)

        hud.credits      = world.credits.get(PLAYER_FACTION, 0)
        hud.infamy       = world.roe_manager.infamy
        hud.roe_name     = world.roe_manager.get_name()
        hud.roe_col      = world.roe_manager.get_color()
        hud.mission_time += dt // 1000 if dt >= 1000 else 0
        hud.update(dt)

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(DARK)

        draw_terrain(screen, cam, fog)

        # Draw placed buildings (world buildings + map static)
        _draw_placed_buildings(screen, cam, world, font_sm, selection, fog)


        # Kirk rally marker
        kx, ky = cam.world_to_screen(*KIRK_RALLY)
        if intro_state != "end":
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 8, 2)
            lbl = font_sm.render("LIVE RALLY", True, (255, 255, 255))
            screen.blit(lbl, (int(kx) - lbl.get_width() // 2, int(ky) - 30))
        elif fog.is_explored(*KIRK_RALLY):
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 8, 2)
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 16, 1)
            lbl = font_sm.render("KIRK RALLY", True, (220, 50, 50))
            screen.blit(lbl, (int(kx) - lbl.get_width() // 2, int(ky) - 20))

        # Draw units
        for u in sorted(world.units.values(), key=lambda u: u.gy):
            if u.faction == PLAYER_FACTION or fog.is_visible(u.gx, u.gy):
                u.draw(screen, cam)

        # Draw civilians
        for c in world.civilians.values():
            if intro_state != "end" or fog.is_visible(c.gx, c.gy):
                c.draw(screen, cam)

        # Intro Overlay
        if intro_state == "shot":
            screen.fill((255, 255, 255)) # Flash
        elif intro_state == "rally":
            # Semi-transparent dark bars at top/bottom
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WIN_W, 80))
            pygame.draw.rect(overlay, (0, 0, 0, 180), (0, WIN_H - 120, WIN_W, 120))
            screen.blit(overlay, (0, 0))
            
            f_lg = pygame.font.SysFont("couriernew", 24, bold=True)
            msg = f_lg.render("UVU QUAD — 14:02 LOCAL", True, (0, 255, 160))
            screen.blit(msg, (50, WIN_H - 100))
            msg2 = font_sm.render("MONITORING INDIVIDUALIST GATHERING...", True, (0, 200, 120))
            screen.blit(msg2, (50, WIN_H - 65))
            
            # Rec border
            pygame.draw.rect(screen, (255, 0, 0), (40, 40, 100, 40), 2)
            rec_lbl = font_sm.render("● REC", True, (255, 0, 0))
            screen.blit(rec_lbl, (50, 50))

        # Ghost building preview
        if placing_bid and placing_ghost:
            _draw_ghost_building(screen, cam, placing_bid, placing_ghost, world)

        # Selection box + order marker
        selection.draw(screen)
        selection.draw_unit_selection(screen, world, cam)
        selection.draw_order_marker(screen)

        # HUD
        minimap_fn = lambda s: draw_minimap(s, cam, hud.minimap_rect)
        hud.draw(screen, minimap_draw_fn=minimap_fn)

        # Sidebar build menu
        click_zones = sidebar.draw(screen, sidebar_rect(), world, PLAYER_FACTION)

        # Selection info strip (bottom of screen, above sidebar bottom)
        _draw_selection_info(screen, selection, world, font_sm, WIN_H, WIN_W - SIDEBAR_W)

        pygame.display.flip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _draw_placed_buildings(surf, cam, world, font, selection, fog=None):
    from game.renderer import _draw_building, TEAL, ORANGE
    sorted_blds = sorted(world.placed_buildings.values(),
                         key=lambda pb: pb.gx + pb.gy)
    for pb in sorted_blds:
        if fog and not fog.is_explored(pb.gx, pb.gy):
            continue
        
        is_visible = not fog or fog.is_visible(pb.gx, pb.gy)
        pal = pb.bdef["palette"]
        if not is_visible:
            # Dim the palette for fog
            pal = {k: [c // 2 for c in v] for k, v in pal.items()}
            
        hl  = pb.selected
        bw, bh, fl = pb.bdef["w"], pb.bdef["h"], pb.bdef["floors"]

        from game.iso import TILE_W, TILE_H, WALL_H
        tw = int(TILE_W * cam.zoom)
        th = int(TILE_H * cam.zoom)
        wh = int(WALL_H * cam.zoom)
        hw, hh = tw // 2, th // 2

        _draw_building(surf, cam, pb.gx, pb.gy, bw, bh, fl, pal, hw, hh, wh, hl)

        # Garrison badge
        if pb.bdef.get("garrison", 0):
            mx, my = cam.world_to_screen(pb.gx + bw / 2, pb.gy + bh / 2, fl + 0.5)
            slots = pb.bdef["garrison"]
            occ   = len(pb.garrison)
            gcol  = (255, 102, 0) if occ == 0 else (0, 200, 100)
            badge = font.render(f"[{occ}/{slots}]", True, gcol)
            surf.blit(badge, (int(mx) - badge.get_width() // 2, int(my)))

        # Building name
        if font:
            lx, ly = cam.world_to_screen(pb.gx + bw / 2, pb.gy + bh / 2, fl + 0.3)
            name = getattr(pb, "display_name", pb.bdef["name"])
            col  = ORANGE if hl else (*TEAL, 140)
            l2   = font.render(name, True, col[:3])
            surf.blit(l2, (int(lx) - l2.get_width() // 2, int(ly) - l2.get_height() // 2))


def _draw_ghost_building(surf, cam, bid, ghost_pos, world):
    from game.building_defs import BUILDINGS as BDEF
    from game.renderer import _draw_building
    from game.iso import TILE_W, TILE_H, WALL_H
    bdef = BDEF.get(bid)
    if not bdef:
        return
    gx, gy = ghost_pos
    blocked = world.blocked_tiles()
    can_place = not any((gx + dx, gy + dy) in blocked
                        for dx in range(bdef["w"]) for dy in range(bdef["h"]))
    pal = dict(bdef["palette"])
    if not can_place:
        pal = {k: (180, 30, 30) for k in pal}

    tw = int(TILE_W * cam.zoom)
    th = int(TILE_H * cam.zoom)
    wh = int(WALL_H * cam.zoom)
    # Draw at 50% alpha via a temp surface
    ghost = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    _draw_building(ghost, cam, gx, gy, bdef["w"], bdef["h"], bdef["floors"],
                   pal, tw // 2, th // 2, wh, False)
    ghost.set_alpha(140)
    surf.blit(ghost, (0, 0))


def _draw_selection_info(surf, selection, world, font, screen_h, panel_w):
    if not selection.selected_uids:
        return
    units = [world.units[uid] for uid in selection.selected_uids if uid in world.units]
    if not units:
        return
    bar_h = 32
    bar   = pygame.Rect(0, screen_h - bar_h, panel_w, bar_h)
    pygame.draw.rect(surf, (10, 20, 16), bar)
    pygame.draw.line(surf, (0, 50, 38), (0, screen_h - bar_h), (panel_w, screen_h - bar_h))

    if len(units) == 1:
        u = units[0]
        txt = f"{u.utype.upper().replace('_',' ')}  HP {u.hp}/{u.max_hp}  [{u.state.upper()}]"
        lbl = font.render(txt, True, (0, 200, 140))
        surf.blit(lbl, (10, screen_h - bar_h + 10))
    else:
        # Show icons for each selected unit
        x = 10
        for u in units[:20]:
            from game.unit_entity import FACTION_COLORS
            col = FACTION_COLORS.get(u.faction, (128, 128, 128))
            pygame.draw.circle(surf, col, (x + 8, screen_h - bar_h + 16), 7)
            pct = u.hp / u.max_hp
            bar_col = (40,200,60) if pct>0.6 else (220,180,0) if pct>0.3 else (220,40,40)
            pygame.draw.rect(surf, bar_col, (x + 2, screen_h - bar_h + 24, 12, 3))
            x += 22


def _point_in_poly(px, py, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


if __name__ == "__main__":
    main()
