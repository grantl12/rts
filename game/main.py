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
from game import postop as _postop_mod
from game.notifications import NotificationManager

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

    font_sm  = pygame.font.SysFont("couriernew", 9)
    notifs   = NotificationManager()

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
    roe5_confirm   = False  # waiting for Y/N confirmation before ROE 5
    show_help      = False  # ? key toggles keybind overlay
    _prev_infamy   = 0

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
                # Spawn 3 Runner HVPs near rally — they flee to map edges
                from game.civilian import RUNNER_DESTINATIONS
                import random as _rnd
                for dest in RUNNER_DESTINATIONS:
                    rx = KIRK_RALLY[0] + _rnd.uniform(-2, 2)
                    ry = KIRK_RALLY[1] + _rnd.uniform(-2, 2)
                    runner = world.spawn_civilian(rx, ry, ctype="runner")
                    runner.set_destination(*dest)

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
                    if roe5_confirm:
                        if event.key == pygame.K_y:
                            world.roe_manager.set_roe(5, world)
                            roe5_confirm = False
                        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                            roe5_confirm = False
                    else:
                        if event.key == pygame.K_1: world.roe_manager.set_roe(1, world)
                        if event.key == pygame.K_2: world.roe_manager.set_roe(2, world)
                        if event.key == pygame.K_3: world.roe_manager.set_roe(3, world)
                        if event.key == pygame.K_4: world.roe_manager.set_roe(4, world)
                        if event.key == pygame.K_5:
                            if world.roe_manager.current_roe < 5:
                                roe5_confirm = True
                    # ? = toggle help overlay
                    if event.key == pygame.K_SLASH and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        show_help = not show_help
                    if event.key == pygame.K_h:
                        show_help = not show_help
                    # Tab = end mission early → post-op screen
                    if event.key == pygame.K_TAB and not roe5_confirm:
                        detained = sum(pb.civs_held for pb in world.placed_buildings.values()
                                       if pb.faction == PLAYER_FACTION)
                        _postop_mod.run(screen, clock, detained,
                                        world.roe_manager.infamy,
                                        hud.mission_time,
                                        world.credits.get(PLAYER_FACTION, 0))

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
                    elif event.button == 1 and hud.minimap_rect.collidepoint(event.pos):
                        # Minimap click → pan camera
                        from game.map_data import W, H
                        mr = hud.minimap_rect
                        rel_x = (event.pos[0] - mr.left) / mr.width
                        rel_y = (event.pos[1] - mr.top) / mr.height
                        cam.gx = rel_x * W - cam.w / (2 * 64)
                        cam.gy = rel_y * H - cam.h / (2 * 32)
                        # Recalculate screen offset
                        from game.iso import TILE_W, TILE_H
                        cam.ox = cam.w // 2 - int((cam.gx - cam.gy) * TILE_W * cam.zoom // 2)
                        cam.oy = 80 - int((cam.gx + cam.gy) * TILE_H * cam.zoom // 2)
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

        # Game over detection → post-op screen
        if intro_state == "end" and world.game_over != 0:
            detained = sum(pb.civs_held for pb in world.placed_buildings.values()
                           if pb.faction == PLAYER_FACTION)
            _postop_mod.run(screen, clock, detained,
                            world.roe_manager.infamy,
                            hud.mission_time,
                            world.credits.get(PLAYER_FACTION, 0))
            pygame.quit(); sys.exit()

        extra_v = []
        if intro_state != "end":
            extra_v.append((*KIRK_RALLY, 12))
        fog.update(world, PLAYER_FACTION, extra_sources=extra_v)

        completed_struct, completed_unit = sidebar.update(dt, world, PLAYER_FACTION)
        if completed_struct:
            placing_bid = completed_struct
            notifs.add(f"STRUCTURE READY — PLACE {completed_struct.upper().replace('_',' ')}", (0, 255, 100))
        if completed_unit:
            world.spawn_unit(completed_unit, PLAYER_FACTION, 13, 19)
            notifs.add(f"UNIT DEPLOYED — {completed_unit.upper().replace('_',' ')}", (0, 220, 180))

        # Infamy threshold notifications
        cur_inf = world.roe_manager.infamy
        if _prev_infamy < 200 <= cur_inf:
            notifs.add("!! SCRUTINIZED — OVERSIGHT ACTIVE", (220, 180, 0))
        elif _prev_infamy < 400 <= cur_inf:
            notifs.add("!! SURVEILLED — FRONTLINE DRONES INCOMING", (255, 140, 0))
        elif _prev_infamy < 750 <= cur_inf:
            notifs.add("!! SANCTIONED — HEAVY PRODUCTION FROZEN", (220, 40, 30))
        _prev_infamy = cur_inf

        notifs.update(dt_sec)

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

        # Capture progress bars on buildings
        _draw_capture_bars(screen, cam, world, PLAYER_FACTION, font_sm)

        # Selection box + order marker
        selection.draw(screen)
        selection.draw_unit_selection(screen, world, cam)
        selection.draw_order_marker(screen)

        # HUD
        minimap_fn = lambda s: draw_minimap(s, cam, hud.minimap_rect,
                                            world=world, fog=fog,
                                            player_faction=PLAYER_FACTION)
        hud.draw(screen, minimap_draw_fn=minimap_fn)

        # Sidebar build menu
        click_zones = sidebar.draw(screen, sidebar_rect(), world, PLAYER_FACTION)

        # Selection info strip (bottom of screen, above sidebar bottom)
        _draw_selection_info(screen, selection, world, font_sm, WIN_H, WIN_W - SIDEBAR_W)

        # ROE 5 confirmation overlay (drawn last, over everything)
        if roe5_confirm:
            _draw_roe5_confirm(screen, font_sm, WIN_W, WIN_H)

        # Notifications (bottom-left, above selection info)
        notifs.draw(screen, x=8, bottom_y=WIN_H - 55)

        # Help overlay (? / H key)
        if show_help:
            _draw_help_overlay(screen, WIN_W, WIN_H)

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

    from game.unit_entity import FACTION_COLORS, Unit

    if len(units) == 1:
        bar_h = 48
        bar   = pygame.Rect(0, screen_h - bar_h, panel_w, bar_h)
        pygame.draw.rect(surf, (10, 20, 16), bar)
        pygame.draw.line(surf, (0, 50, 38), (0, screen_h - bar_h), (panel_w, screen_h - bar_h))

        u = units[0]
        f_med = pygame.font.SysFont("couriernew", 12, bold=True)
        f_sm  = font

        # Name + rank stars
        rank_str = "★" * u.rank + "☆" * (5 - u.rank)
        name_lbl = f_med.render(
            f"{u.utype.upper().replace('_',' ')}  {rank_str}",
            True, FACTION_COLORS.get(u.faction, (0, 200, 140)))
        surf.blit(name_lbl, (10, screen_h - bar_h + 4))

        # State + suppression
        state_txt = u.state.upper()
        if u.suppressed:
            state_txt += "  [SUPPRESSED]"
        state_lbl = f_sm.render(state_txt, True, (0, 160, 100))
        surf.blit(state_lbl, (10, screen_h - bar_h + 22))

        # HP bar
        bw = min(200, panel_w // 3)
        bx = 220
        by = screen_h - bar_h + 8
        pct = u.hp / u.max_hp
        bar_col = (40, 200, 60) if pct > 0.6 else (220, 180, 0) if pct > 0.3 else (220, 40, 40)
        pygame.draw.rect(surf, (30, 30, 30), (bx - 1, by - 1, bw + 2, 8))
        pygame.draw.rect(surf, bar_col, (bx, by, int(bw * pct), 6))
        hp_lbl = f_sm.render(f"HP  {u.hp}/{u.max_hp}", True, (0, 160, 100))
        surf.blit(hp_lbl, (bx, by + 10))

        # XP bar
        if u.rank < 5:
            xp_pct = u.xp / u.xp_to_next
            pygame.draw.rect(surf, (20, 20, 40), (bx - 1, by + 22, bw + 2, 5))
            pygame.draw.rect(surf, (60, 60, 220), (bx, by + 23, int(bw * xp_pct), 3))
            xp_lbl = f_sm.render(
                f"XP  {int(u.xp)}/{int(u.xp_to_next)}  [{Unit.RANK_NAMES[u.rank - 1]}]",
                True, (80, 80, 180))
            surf.blit(xp_lbl, (bx, by + 28))

        # Stats
        st_lbl = f_sm.render(
            f"DMG {u.damage}  RNG {u.attack_range:.1f}  SPD {u.speed:.1f}  ARMOR {u.armor_type.upper()}",
            True, (0, 100, 70))
        surf.blit(st_lbl, (bx + bw + 16, screen_h - bar_h + 14))

    else:
        bar_h = 38
        bar   = pygame.Rect(0, screen_h - bar_h, panel_w, bar_h)
        pygame.draw.rect(surf, (10, 20, 16), bar)
        pygame.draw.line(surf, (0, 50, 38), (0, screen_h - bar_h), (panel_w, screen_h - bar_h))

        count_lbl = pygame.font.SysFont("couriernew", 10).render(
            f"{len(units)} UNITS SELECTED", True, (0, 160, 100))
        surf.blit(count_lbl, (10, screen_h - bar_h + 4))

        x = 10
        for u in units[:30]:
            col = FACTION_COLORS.get(u.faction, (128, 128, 128))
            pygame.draw.circle(surf, col, (x + 7, screen_h - bar_h + 24), 6)
            pct = u.hp / u.max_hp
            bar_col = (40, 200, 60) if pct > 0.6 else (220, 180, 0) if pct > 0.3 else (220, 40, 40)
            pygame.draw.rect(surf, bar_col, (x + 1, screen_h - bar_h + 31, 12, 3))
            x += 16


def _draw_capture_bars(surf, cam, world, player_faction, font):
    from game.unit_entity import FACTION_COLORS
    for pb in world.placed_buildings.values():
        if pb._capture_progress <= 0:
            continue
        cx, cy = cam.world_to_screen(pb.gx + pb.bdef["w"] / 2,
                                     pb.gy + pb.bdef["h"] / 2,
                                     pb.bdef["floors"] + 0.5)
        bw = 28
        bx = int(cx) - bw // 2
        by = int(cy) - 10
        pct = min(1.0, pb._capture_progress / 100.0)
        pygame.draw.rect(surf, (20, 20, 20), (bx - 1, by - 1, bw + 2, 6))
        cap_col = (255, 200, 0)
        pygame.draw.rect(surf, cap_col, (bx, by, int(bw * pct), 4))
        pygame.draw.rect(surf, (80, 80, 0), (bx - 1, by - 1, bw + 2, 6), 1)
        lbl = font.render("CAPTURING", True, (255, 220, 80))
        surf.blit(lbl, (bx - lbl.get_width() // 2 + bw // 2, by - 10))


def _draw_help_overlay(surf, sw, sh):
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 10, 8, 210))
    surf.blit(overlay, (0, 0))

    f_title = pygame.font.SysFont("couriernew", 20, bold=True)
    f_med   = pygame.font.SysFont("couriernew", 11, bold=True)
    f_sm    = pygame.font.SysFont("couriernew", 10)

    TEAL   = (0, 255, 204)
    ORANGE = (255, 102, 0)
    DIM    = (0, 120, 90)

    title = f_title.render("FIELD OPERATIONS — KEYBINDING REFERENCE", True, TEAL)
    surf.blit(title, (sw // 2 - title.get_width() // 2, 60))
    pygame.draw.line(surf, DIM, (60, 88), (sw - 60, 88))

    KEYS = [
        ("SELECTION",  [
            ("Left-Click",        "Select unit / building"),
            ("Left-Drag",         "Box select units"),
            ("Shift + Click",     "Add to selection"),
            ("Ctrl + A",          "Select ALL friendly units"),
        ]),
        ("ORDERS",  [
            ("Right-Click unit",  "Attack order"),
            ("Right-Click ground","Move order (formation)"),
            ("Right-Click bldg", "Garrison order"),
            ("S",                 "Stop all selected"),
        ]),
        ("CAMERA",  [
            ("WASD / Arrow keys", "Pan camera"),
            ("Mouse edge",        "Pan camera"),
            ("Scroll Wheel",      "Zoom in / out"),
            ("Minimap click",     "Jump to location"),
        ]),
        ("ROE",  [
            ("1 – 4",             "Set Rules of Engagement"),
            ("5",                 "Request ABSOLUTE IMMUNITY (confirm)"),
            ("Y / N",             "Confirm / abort ROE 5"),
        ]),
        ("MISSION",  [
            ("Tab",               "End mission → post-op debrief"),
            ("H or ?",            "Toggle this help overlay"),
            ("Escape",            "Cancel placement / exit"),
        ]),
    ]

    col_w = (sw - 120) // 2
    cx = [70, 70 + col_w + 20]
    cy = 106
    col_i = 0
    y = cy

    for section, binds in KEYS:
        x = cx[col_i]
        sec_lbl = f_med.render(f"▸ {section}", True, ORANGE)
        surf.blit(sec_lbl, (x, y))
        y += 18
        for key, desc in binds:
            k = f_sm.render(key.ljust(22), True, TEAL)
            d = f_sm.render(desc, True, DIM)
            surf.blit(k, (x, y))
            surf.blit(d, (x + 190, y))
            y += 15
        y += 10
        if y > sh - 80:
            col_i = min(col_i + 1, 1)
            y = cy

    close = f_sm.render("[ H / ? — CLOSE ]", True, DIM)
    surf.blit(close, (sw // 2 - close.get_width() // 2, sh - 40))


def _draw_roe5_confirm(surf, font_sm, sw, sh):
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((20, 0, 0, 200))
    surf.blit(overlay, (0, 0))

    f_lg  = pygame.font.SysFont("couriernew", 28, bold=True)
    f_med = pygame.font.SysFont("couriernew", 13, bold=True)

    title = f_lg.render("!! ABSOLUTE IMMUNITY — CONFIRM ESCALATION !!",
                         True, (255, 38, 25))
    surf.blit(title, (sw // 2 - title.get_width() // 2, sh // 2 - 60))

    lines = [
        "ALL RULES OF ENGAGEMENT SUSPENDED.",
        "THIS ACTION IS IRREVERSIBLE.",
        "+200 INFAMY IMMEDIATELY.",
        "",
        "[ Y ] AUTHORIZE        [ N ] ABORT",
    ]
    for i, line in enumerate(lines):
        col = (255, 166, 25) if "Y]" in line else (200, 200, 200)
        lbl = f_med.render(line, True, col)
        surf.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh // 2 - 20 + i * 22))


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
