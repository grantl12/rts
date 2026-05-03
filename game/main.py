"""
Deep State RTS — main game loop.
Run: python -m game.main
"""
import os, sys, math, pygame

from game.camera    import Camera
from game.world     import World
from game.selection import SelectionManager
from game.sidebar   import BuildSidebar
from game.renderer  import draw_terrain, draw_buildings, draw_minimap, DARK
from game.hud       import HUD, TOPBAR_H, SIDEBAR_W
import game.map_data as _MAP_MOD   # mutable — swapped per mission
from game.map_data  import KIRK_RALLY, BUILDINGS as MAP_BLDS
from game.fog       import FogManager
from game import menu as _menu_mod
from game import postop as _postop_mod
from game import executive_board as _eb_mod
from game import slot_select as _slot_mod
from game import save_manager as _save_mod
from game.notifications import NotificationManager
from game.advisor    import AdvisorSystem
from game.objectives import ObjectiveManager
from game.audio      import AudioManager

TITLE    = "DEEP STATE RTS — OP: WOLVERINE"
WIN_W, WIN_H = 1280, 800
FPS      = 60


def main():
    pygame.mixer.pre_init(22050, -16, 1, 256)
    pygame.init()
    os.makedirs("save", exist_ok=True)
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    while True:
        PLAYER_FACTION = _menu_mod.run(screen, clock, FPS)
        slot_result = _slot_mod.run(screen, clock, PLAYER_FACTION, mode="any", fps=FPS)
        if slot_result is None:
            continue   # player hit ESC back to menu
        slot_num, slot_data = slot_result
        map_id = _pick_theater(screen, clock)
        if map_id is None:
            continue
        _run_mission(screen, clock, PLAYER_FACTION, slot_num, slot_data, map_id=map_id)


def _run_mission(screen, clock, PLAYER_FACTION, slot_num=None, slot_data=None, map_id="quad"):
    global KIRK_RALLY, MAP_BLDS

    # ── Swap active map module in place so renderer/pathfinding see new terrain ──
    import game.map_data_2 as _MAP2
    if map_id == "district":
        _MAP_MOD.TERRAIN[:]    = _MAP2.TERRAIN
        _MAP_MOD.BUILDINGS[:]  = _MAP2.BUILDINGS
        _MAP_MOD.BTYPE_COLORS.clear()
        _MAP_MOD.BTYPE_COLORS.update(_MAP2.BTYPE_COLORS)
        _MAP_MOD.KIRK_RALLY    = _MAP2.KIRK_RALLY
        KIRK_RALLY             = _MAP2.KIRK_RALLY
        MAP_BLDS               = _MAP2.BUILDINGS
        _active_map            = _MAP2
    else:
        import game.map_data as _MAP1_orig
        _MAP_MOD.TERRAIN[:]    = _MAP1_orig.TERRAIN
        _MAP_MOD.BUILDINGS[:]  = _MAP1_orig.BUILDINGS
        _MAP_MOD.BTYPE_COLORS.clear()
        _MAP_MOD.BTYPE_COLORS.update(_MAP1_orig.BTYPE_COLORS)
        _MAP_MOD.KIRK_RALLY    = _MAP1_orig.KIRK_RALLY
        KIRK_RALLY             = _MAP1_orig.KIRK_RALLY
        MAP_BLDS               = _MAP1_orig.BUILDINGS
        _active_map            = _MAP1_orig

    if slot_data is None:
        slot_data = _save_mod.new_slot(PLAYER_FACTION)
    MAP_PHASE = slot_data.get("map_phase", 0)
    cam       = Camera(WIN_W, WIN_H)
    world     = World(PLAYER_FACTION, map_phase=MAP_PHASE, map_module=_active_map)
    fog       = FogManager(map_phase=MAP_PHASE)
    # Apply carry-over state from save slot
    if slot_data.get("infamy_carryover", 0) > 0:
        world.roe_manager.add_infamy(slot_data["infamy_carryover"])
    if slot_data.get("credits_carryover", 0):
        world.credits[PLAYER_FACTION] = slot_data["credits_carryover"]
    if slot_data.get("passive_income_bonus", 0):
        world._passive_income_bonus = slot_data["passive_income_bonus"]
    saved_wrecks = slot_data.get("persisted_wrecks", {}).get(map_id, [])
    if saved_wrecks:
        for w in saved_wrecks:
            if not isinstance(w, (list, tuple)) or len(w) != 3:
                continue
            wx, wy, wt = w
            try:
                wx = float(wx)
                wy = float(wy)
                wt = float(wt)
            except (TypeError, ValueError):
                continue
            if wt <= 0:
                continue
            world.wrecks.append([wx, wy, wt])
    selection = SelectionManager()
    sidebar   = BuildSidebar(PLAYER_FACTION)
    hud       = HUD(WIN_W, WIN_H)

    font_sm  = pygame.font.SysFont("couriernew", 9)
    notifs   = NotificationManager()
    advisor  = AdvisorSystem()
    audio    = AudioManager()
    enemy_f  = world._ENEMY_MAP.get(PLAYER_FACTION, "sovereign")
    objectives = ObjectiveManager(PLAYER_FACTION, enemy_f, map_id=map_id)
    _combat_sound_timer = 0.0   # rate-limits per-frame combat sound checks
    _deepfake_overlay = 0.0   # seconds remaining on deepfake reveal overlay
    _leak_overlay     = None  # (title, body, timer) for narrative leak popups

    # ── Intro State ──
    if map_id == "district":
        intro_state = "d_approach"
        intro_timer = 4.0
        _d_suv_gx   = float(KIRK_RALLY[0])
        _d_suv_gy   = float(KIRK_RALLY[1])
    else:
        intro_state = "rally"
        intro_timer = 5.0
        _d_suv_gx   = 0.0
        _d_suv_gy   = 0.0
    intro_text  = ""
    _subject_ctype = "normie" if map_id == "district" else "kirk"
    kirk_obj = world.spawn_civilian(*KIRK_RALLY, ctype=_subject_ctype)
    cam.pan_to(KIRK_RALLY[0] - 14, KIRK_RALLY[1] - 14)
    _intro_cam_start = (cam.ox, cam.oy)
    _ng_timer        = 300.0 if map_id == "district" else -1.0
    _ng_wave_done    = False   # mid-game enemy wave for district at T≈150s

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
    _ability_cd    = {"q": 0.0, "e": 0.0, "r": 0.0}  # seconds remaining on cooldown
    _scotus_zones  = []   # list of (cx,cy,radius,timer) — de-zoned areas
    _alert_flash   = 0.0   # seconds of red border flash remaining
    _hq_warned     = False  # "this is fine" warning fired this damage threshold
    _crime_scene_bid = None
    _crime_scene_secured = False
    _drive_unlocked = False
    _kirk_stage_sprite = None
    _kirk_stage_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "kirk_tent_table.png"))
    if os.path.exists(_kirk_stage_path):
        try:
            _kirk_stage_sprite = pygame.image.load(_kirk_stage_path).convert_alpha()
        except Exception:
            _kirk_stage_sprite = None

    while True:
        dt = clock.tick(FPS)
        dt_sec = dt / 1000.0

        # ── Intro Logic ──
        if intro_state != "end":
            intro_timer -= dt_sec
            # Smooth camera pan during rally (lerp from offset start to rally center)
            if intro_state == "rally":
                cam.pan_to(*KIRK_RALLY)
                target_ox, target_oy = cam.ox, cam.oy
                cam.ox = int(_intro_cam_start[0] + (target_ox - _intro_cam_start[0]) * (1 - intro_timer / 5.0))
                cam.oy = int(_intro_cam_start[1] + (target_oy - _intro_cam_start[1]) * (1 - intro_timer / 5.0))
                if intro_timer <= 0:
                    intro_state = "talk"
                    intro_timer = 4.0
                    intro_text  = "Actually, the truth about Epstein is—"
            
            elif intro_state == "talk":
                cam.pan_to(*KIRK_RALLY)
                if intro_timer <= 0:
                    intro_state = "wait"
                    intro_timer = 2.8   # long enough to read the full quote
            
            elif intro_state == "wait":
                cam.pan_to(*KIRK_RALLY)
                if intro_timer <= 0:
                    intro_state = "shot"
                    intro_timer = 0.5
                    kirk_obj.state = "dead"
                    intro_text = ""
                    audio.play("explosion")
            
            elif intro_state == "shot" and intro_timer <= 0:
                intro_state = "panic"
                intro_timer = 2.5
                for c in world.civilians.values():
                    if math.dist((c.gx, c.gy), KIRK_RALLY) < 15:
                        c.panic(world)
            elif intro_state == "panic" and intro_timer <= 0:
                intro_state = "end"
                world.intro_done = True
                cam.pan_to(48, 37)
                _STARTER = {
                    "regency":   [("gravy_seal",3),("ice_agent",2)],
                    "frontline": [("drone_scout",3),("proxy",2)],
                    "sovereign": [("proxy",3),("contractor",1)],
                    "oligarchy": [("contractor",2),("gravy_seal",2)],
                }
                _HQ_BID = {
                    "regency":   "reg_hq",
                    "frontline": "reg_hq",
                    "sovereign": "sov_hq",
                    "oligarchy": "oli_hq",
                }
                world.place_building(_HQ_BID.get(PLAYER_FACTION, "reg_hq"),
                                     PLAYER_FACTION, 46, 37)
                sx0, sy0 = 43, 38
                for utype, count in _STARTER.get(PLAYER_FACTION, [("gravy_seal",3)]):
                    for i in range(count):
                        world.spawn_unit(utype, PLAYER_FACTION, sx0 + i * 0.8, sy0)
                    sy0 += 1
                enemy = world._ENEMY_MAP.get(PLAYER_FACTION, "sovereign")
                for i in range(3):
                    world.spawn_unit("proxy", enemy, 6 + i, 4)
                if map_id == "quad":
                    _crime_scene = world.place_building("audit_point", "neutral",
                                                        int(KIRK_RALLY[0] - 1), int(KIRK_RALLY[1] - 1))
                    if _crime_scene:
                        _crime_scene.display_name = "KIRK CRIME SCENE"
                        _crime_scene.display_sub = "SECURE SITE TO RECOVER EVIDENCE"
                        _crime_scene_bid = _crime_scene.bid
                    # Static route pressure: pickets on approach lanes.
                    if PLAYER_FACTION == "regency":
                        for px, py in [(37, 31), (34, 28), (31, 25), (27, 23), (23, 21), (20, 19)]:
                            p = world.spawn_unit("proxy", "frontline", px, py)
                            p.order_move([])
                import random as _rnd
                _r_dests = getattr(_active_map, "RUNNER_DESTINATIONS", None)
                if _r_dests is None:
                    from game.civilian import RUNNER_DESTINATIONS as _r_dests
                for dest in _r_dests:
                    rx = KIRK_RALLY[0] + _rnd.uniform(-2, 2)
                    ry = KIRK_RALLY[1] + _rnd.uniform(-2, 2)
                    runner = world.spawn_civilian(rx, ry, ctype="runner")
                    runner.set_destination(*dest)

            # ── District map intro states ──────────────────────────────────────
            elif intro_state == "d_approach":
                cam.pan_to(*KIRK_RALLY)
                target_ox, target_oy = cam.ox, cam.oy
                cam.ox = int(_intro_cam_start[0] + (target_ox - _intro_cam_start[0]) * (1 - intro_timer / 4.0))
                cam.oy = int(_intro_cam_start[1] + (target_oy - _intro_cam_start[1]) * (1 - intro_timer / 4.0))
                if intro_timer <= 0:
                    intro_state = "d_check"
                    intro_timer = 3.0
                    intro_text  = "LICENSE AND REGISTRATION. STEP OUT OF THE VEHICLE."

            elif intro_state == "d_check":
                cam.pan_to(*KIRK_RALLY)
                if intro_timer <= 0:
                    intro_state = "d_shot"
                    intro_timer = 0.5
                    kirk_obj.state = "dead"
                    intro_text = ""
                    audio.play("explosion")

            elif intro_state == "d_shot" and intro_timer <= 0:
                intro_state = "d_crash"
                intro_timer = 2.2

            elif intro_state == "d_crash":
                _crash_target = getattr(_active_map, "INCIDENT_SUV_CRASH_TARGET",
                                        (KIRK_RALLY[0], KIRK_RALLY[1] - 3.5))
                _dtx = _crash_target[0] - _d_suv_gx
                _dty = _crash_target[1] - _d_suv_gy
                _ddist = math.sqrt(_dtx * _dtx + _dty * _dty)
                if _ddist > 0.15:
                    _suv_spd = 3.0
                    _d_suv_gx += (_dtx / _ddist) * _suv_spd * dt_sec
                    _d_suv_gy += (_dty / _ddist) * _suv_spd * dt_sec
                if intro_timer <= 0 or _ddist <= 0.15:
                    intro_state = "d_panic"
                    intro_timer = 2.5
                    audio.play("explosion")
                    world.wrecks.append([_d_suv_gx, _d_suv_gy, 99999])
                    for c in world.civilians.values():
                        if math.dist((c.gx, c.gy), (_d_suv_gx, _d_suv_gy)) < 12:
                            c.panic(world)

            elif intro_state == "d_panic" and intro_timer <= 0:
                intro_state = "end"
                world.intro_done = True
                cam.pan_to(30, 36)
                _STARTER_D = {
                    "regency":   [("gravy_seal",3),("ice_agent",2)],
                    "frontline": [("drone_scout",3),("proxy",2)],
                    "sovereign": [("proxy",3),("contractor",1)],
                    "oligarchy": [("contractor",2),("gravy_seal",2)],
                }
                _HQ_BID_D = {
                    "regency":   "reg_hq",
                    "frontline": "reg_hq",
                    "sovereign": "sov_hq",
                    "oligarchy": "oli_hq",
                }
                world.place_building(_HQ_BID_D.get(PLAYER_FACTION, "reg_hq"),
                                     PLAYER_FACTION, 30, 36)
                sx0, sy0 = 28, 37
                for utype, count in _STARTER_D.get(PLAYER_FACTION, [("gravy_seal",3)]):
                    for i in range(count):
                        world.spawn_unit(utype, PLAYER_FACTION, sx0 + i * 0.8, sy0)
                    sy0 += 1
                enemy = world._ENEMY_MAP.get(PLAYER_FACTION, "sovereign")
                for px, py in getattr(_active_map, "AI_INTRO_PROXIES", [(50, 3), (51, 3), (52, 3)]):
                    world.spawn_unit("proxy", enemy, px, py)
                import random as _rnd2
                for dest in _active_map.RUNNER_DESTINATIONS:
                    rx = KIRK_RALLY[0] + _rnd2.uniform(-2, 2)
                    ry = KIRK_RALLY[1] + _rnd2.uniform(-2, 2)
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
                    if event.key == pygame.K_a and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        all_u = [u for u in world.units.values() if u.faction == PLAYER_FACTION]
                        selection._set_selection(all_u, world)
                    if event.key == pygame.K_s:
                        for uid in selection.selected_uids:
                            if uid in world.units:
                                world.units[uid].order_stop()

                    if event.key == pygame.K_f:
                        sel_units = [world.units[uid] for uid in selection.selected_uids
                                     if uid in world.units]
                        if sel_units:
                            cx = sum(u.gx for u in sel_units) / len(sel_units)
                            cy = sum(u.gy for u in sel_units) / len(sel_units)
                            cam.pan_to(cx, cy)

                    if event.key == pygame.K_g:
                        sel_units = [world.units[uid] for uid in selection.selected_uids
                                     if uid in world.units and not world.units[uid].garrisoned_in]
                        if sel_units:
                            from game.pathfinding import find_path
                            for u in sel_units:
                                best_pb, best_dist = None, 999.0
                                for pb in world.placed_buildings.values():
                                    if (pb.faction == u.faction
                                            and pb.bdef.get("garrison", 0) > 0
                                            and len(pb.garrison) < pb.bdef["garrison"]):
                                        d = math.dist((u.gx, u.gy), (pb.gx, pb.gy))
                                        if d < best_dist:
                                            best_pb, best_dist = pb, d
                                if best_pb:
                                    blocked = world.blocked_tiles()
                                    wp = find_path((u.gx, u.gy),
                                                   (best_pb.gx + best_pb.bdef["w"] / 2,
                                                    best_pb.gy + best_pb.bdef["h"] / 2), blocked)
                                    u.order_garrison(best_pb.bid, wp[1:])

                    # ROE keys
                    if roe5_confirm:
                        if event.key == pygame.K_y:
                            world.roe_manager.set_roe(5, world)
                            advisor.trigger("roe_5")
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
                    if event.key == pygame.K_SLASH and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        show_help = not show_help
                    if event.key == pygame.K_h:
                        show_help = not show_help
                    if event.key == pygame.K_m:
                        audio.toggle_mute()
                        notifs.add("AUDIO " + ("MUTED" if not audio._enabled else "UNMUTED"), (0, 160, 100))

                    # Q ability — faction-specific
                    if event.key == pygame.K_q and _ability_cd["q"] <= 0:
                        sel_units = [world.units[uid] for uid in selection.selected_uids
                                     if uid in world.units]
                        if PLAYER_FACTION == "regency":
                            if sel_units:
                                for su in sel_units:
                                    for e in world.units.values():
                                        if e.faction in world.enemies_of(su.faction) and e.state != "dead":
                                            if math.dist((su.gx, su.gy), (e.gx, e.gy)) <= su.attack_range * 2:
                                                e.suppress(4.0)
                                _ability_cd["q"] = 20.0
                                notifs.add("Q — RED TAPE BURST (REGENCY)", (0, 200, 255))
                                advisor.trigger("cease_desist")
                        elif PLAYER_FACTION == "frontline":
                            world.credits[PLAYER_FACTION] = world.credits.get(PLAYER_FACTION, 0) + 300
                            _ability_cd["q"] = 30.0
                            notifs.add("Q — CROWDFUNDING SURGE +§300", (80, 200, 80))
                            advisor.trigger("crowdfunding")
                        elif PLAYER_FACTION == "oligarchy":
                            cost = 100
                            if world.credits.get(PLAYER_FACTION, 0) >= cost and sel_units:
                                cx = sum(u.gx for u in sel_units) / len(sel_units)
                                cy = sum(u.gy for u in sel_units) / len(sel_units)
                                for i in range(5):
                                    ox = (i % 3 - 1) * 1.5
                                    oy = (i // 3) * 1.5
                                    world.spawn_unit("wagner", PLAYER_FACTION, cx + ox, cy + oy)
                                world.credits[PLAYER_FACTION] -= cost
                                _ability_cd["q"] = 35.0
                                notifs.add("Q — MEAT GRINDER: 5 WAGNERS DEPLOYED (−§100)", (180, 80, 40))
                                advisor.trigger("meat_grinder")
                        elif PLAYER_FACTION == "sovereign":
                            world.credits[PLAYER_FACTION] = world.credits.get(PLAYER_FACTION, 0) + 250
                            _ability_cd["q"] = 25.0
                            notifs.add("Q — BLACK MARKET FUNDS +§250", (140, 40, 200))

                    # E ability — faction-specific
                    if event.key == pygame.K_e and _ability_cd["e"] <= 0:
                        sel_units = [world.units[uid] for uid in selection.selected_uids
                                     if uid in world.units]
                        if PLAYER_FACTION == "regency":
                            cost = 200
                            if world.credits.get(PLAYER_FACTION, 0) >= cost and sel_units:
                                cx = sum(u.gx for u in sel_units) / len(sel_units)
                                cy = sum(u.gy for u in sel_units) / len(sel_units)
                                world.spawn_unit("gravy_seal", PLAYER_FACTION, cx + 1, cy)
                                world.spawn_unit("gravy_seal", PLAYER_FACTION, cx - 1, cy)
                                world.credits[PLAYER_FACTION] -= cost
                                _ability_cd["e"] = 45.0
                                notifs.add("E — STIMULUS DROP: 2 GRAVY SEALS (−§200)", (0, 255, 100))
                        elif PLAYER_FACTION == "frontline":
                            if sel_units:
                                for su in sel_units:
                                    for e in world.units.values():
                                        if e.faction in world.enemies_of(su.faction) and e.state != "dead":
                                            if math.dist((su.gx, su.gy), (e.gx, e.gy)) <= 8.0:
                                                e.suppress(5.0)
                                _ability_cd["e"] = 40.0
                                notifs.add("E — DRONE OVERWATCH: AREA SUPPRESSED", (80, 200, 200))
                        elif PLAYER_FACTION == "oligarchy":
                            # Kickback: steal from nearest enemy building
                            steal_amt = 150
                            enemy_buildings = [pb for pb in world.placed_buildings.values()
                                               if pb.faction not in ("neutral", PLAYER_FACTION)]
                            if enemy_buildings and sel_units:
                                cx = sum(u.gx for u in sel_units) / len(sel_units)
                                cy = sum(u.gy for u in sel_units) / len(sel_units)
                                nearest = min(enemy_buildings, key=lambda pb: math.dist((pb.gx, pb.gy), (cx, cy)))
                                ef = nearest.faction
                                stolen = min(steal_amt, world.credits.get(ef, 0))
                                world.credits[ef] = world.credits.get(ef, 0) - stolen
                                world.credits[PLAYER_FACTION] = world.credits.get(PLAYER_FACTION, 0) + stolen
                                _ability_cd["e"] = 50.0
                                notifs.add(f"E — KICKBACK: §{stolen} SIPHONED", (200, 160, 0))
                                advisor.trigger("kickback")
                        elif PLAYER_FACTION == "sovereign":
                            cost = 150
                            if world.credits.get(PLAYER_FACTION, 0) >= cost and sel_units:
                                cx = sum(u.gx for u in sel_units) / len(sel_units)
                                cy = sum(u.gy for u in sel_units) / len(sel_units)
                                world.spawn_unit("proxy", PLAYER_FACTION, cx + 1, cy)
                                world.spawn_unit("proxy", PLAYER_FACTION, cx - 1, cy)
                                world.credits[PLAYER_FACTION] -= cost
                                _ability_cd["e"] = 45.0
                                notifs.add("E — SHADOW CELL: 2 PROXIES DEPLOYED (−§150)", (140, 40, 200))
                                advisor.trigger("shadow_cell")

                    # R = Superweapon (faction-specific, long CD)
                    if event.key == pygame.K_r and _ability_cd["r"] <= 0:
                        sel_units = [world.units[uid] for uid in selection.selected_uids
                                     if uid in world.units]
                        if PLAYER_FACTION == "regency":
                            # SCOTUS GAVEL: de-zone area — enemy can't build in radius for 60s
                            if sel_units:
                                cx = sum(u.gx for u in sel_units) / len(sel_units)
                                cy = sum(u.gy for u in sel_units) / len(sel_units)
                                _scotus_zones.append([cx, cy, 8.0, 60.0])
                                world._platform_ban_timer = 30.0
                                _ability_cd["r"] = 120.0
                                notifs.add("R — SCOTUS GAVEL + PLATFORM BAN: AREA DE-ZONED 60s / JOURNALIST IMMUNITY SUSPENDED 30s", (200, 180, 0))
                                advisor.trigger("scotus_gavel")
                                _alert_flash = 0.5
                        elif PLAYER_FACTION == "frontline":
                            # DRONE SWARM: 4 drone_scouts attack random enemies
                            enemies = [u for u in world.units.values()
                                       if u.faction in world.enemies_of(PLAYER_FACTION)
                                       and u.state != "dead"]
                            if enemies:
                                import random as _r
                                targets = _r.sample(enemies, min(4, len(enemies)))
                                for t in targets:
                                    d = world.spawn_unit("drone_scout", PLAYER_FACTION,
                                                         t.gx + _r.uniform(-3, 3),
                                                         t.gy + _r.uniform(-3, 3))
                                    if d and hasattr(d, "order_attack"):
                                        d.order_attack(t.uid)
                                _ability_cd["r"] = 90.0
                                notifs.add("R — DRONE SWARM: 4 FPV DRONES LAUNCHED", (80, 200, 80))
                                advisor.trigger("drone_swarm")
                        elif PLAYER_FACTION == "oligarchy":
                            # TROLL SURGE: double troll farm erosion for 60s
                            has_troll = any("troll" in pb.bdef.get("flags", [])
                                            and pb.faction == PLAYER_FACTION
                                            for pb in world.placed_buildings.values())
                            if has_troll:
                                world._troll_surge_timer = 60.0
                                _ability_cd["r"] = 90.0
                                notifs.add("R — TROLL SURGE: TROLL FARMS AT MAXIMUM EFFICIENCY 60s", (180, 80, 40))
                                advisor.trigger("troll_surge")
                                _alert_flash = 0.5
                        elif PLAYER_FACTION == "sovereign":
                            # EPSTEIN FILE LEAK: reveal full map for 45s, freeze enemy income
                            if not hasattr(world, "_epstein_timer"):
                                world._epstein_timer = 0.0
                            world._epstein_timer = 45.0
                            _ability_cd["r"] = 150.0
                            notifs.add("R — EPSTEIN FILE LEAK: MAP REVEALED — ENEMY INCOME FROZEN 45s",
                                       (140, 40, 200))
                            advisor.trigger("epstein_leak")
                            _alert_flash = 1.0

                    # Tab = end mission early
                    if event.key == pygame.K_TAB and not roe5_confirm:
                        _end_mission(screen, clock, world, hud, PLAYER_FACTION, map_id, slot_num, slot_data)
                        return

            cam.handle_event(event)

            if intro_state == "end":
                if event.type == pygame.MOUSEMOTION:
                    selection.mouse_move(event.pos)
                    if placing_bid:
                        gx, gy = cam.screen_to_world(*event.pos)
                        placing_ghost = (int(gx), int(gy))

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3 and not placing_bid and selection.selected_uids:
                        audio.play("move_order")
                    if placing_bid:
                        if event.button == 1 and placing_ghost:
                            # Block placement inside SCOTUS de-zones (enemy can't build)
                            gx_p, gy_p = placing_ghost
                            in_scotus = any(
                                math.dist((gx_p, gy_p), (z[0], z[1])) <= z[2]
                                for z in _scotus_zones
                            )
                            if in_scotus and PLAYER_FACTION != "regency":
                                notifs.add("SCOTUS GAVEL — CONSTRUCTION BLOCKED IN DE-ZONE", (200, 180, 0))
                            else:
                                pb = world.place_building(placing_bid, PLAYER_FACTION, *placing_ghost)
                            placing_bid   = None
                            placing_ghost = None
                        elif event.button == 3:
                            placing_bid   = None
                            placing_ghost = None
                    elif event.button == 1 and hud.minimap_rect.collidepoint(event.pos):
                        from game.map_data import W, H
                        mr = hud.minimap_rect
                        rel_x = (event.pos[0] - mr.left) / mr.width
                        rel_y = (event.pos[1] - mr.top) / mr.height
                        cam.pan_to(rel_x * W, rel_y * H)
                    else:
                        result = sidebar.handle_click(event.pos, click_zones, world, PLAYER_FACTION)
                        if result:
                            if result[0] == "upgrade_purchased":
                                notifs.add(f"RESEARCH COMPLETE: {result[1].replace('upg_','').replace('_',' ').upper()}", (0, 200, 255))
                                advisor.trigger("upgrade_purchased")
                        else:
                            selection.mouse_down(event.pos, event.button, cam, world, hud)

                if event.type == pygame.MOUSEBUTTONUP:
                    selection.mouse_up(event.pos, event.button, cam, world, hud)

        # ── Update ────────────────────────────────────────────────────────────
        cam.update()
        world.update(dt, PLAYER_FACTION)

        # HQ low-HP warning — "This is fine"
        if intro_state == "end":
            player_hqs = [pb for pb in world.placed_buildings.values()
                          if pb.faction == PLAYER_FACTION
                          and "command" in pb.bdef.get("flags", [])]
            if player_hqs:
                hq_pct = min(pb.hp / max(pb.max_hp, 1) for pb in player_hqs)
                if hq_pct < 0.3 and not _hq_warned:
                    notifs.add("!! HQ STRUCTURE CRITICAL — THIS IS FINE", (255, 40, 20))
                    advisor.trigger("hq_under_fire")
                    _alert_flash = max(_alert_flash, 1.5)
                    _hq_warned = True
                elif hq_pct > 0.5:
                    _hq_warned = False

        # Game over detection → post-op → executive board → menu
        if intro_state == "end" and world.game_over != 0:
            _draw_game_over_splash(screen, clock, world.game_over, WIN_W, WIN_H)
            _end_mission(screen, clock, world, hud, PLAYER_FACTION, map_id, slot_num, slot_data)
            return

        extra_v = []
        if intro_state != "end":
            extra_v.append((*KIRK_RALLY, 12))
        # Epstein File Leak: full map reveal while active
        if getattr(world, "_epstein_timer", 0.0) > 0:
            from game.map_data import W as _MW, H as _MH
            extra_v.append((_MW // 2, _MH // 2, max(_MW, _MH)))
        fog.update(world, PLAYER_FACTION, extra_sources=extra_v)

        # Tick SCOTUS de-zone timers
        for zone in _scotus_zones:
            zone[3] = max(0.0, zone[3] - dt_sec)
        _scotus_zones[:] = [z for z in _scotus_zones if z[3] > 0]

        completed_struct, completed_unit = sidebar.update(dt, world, PLAYER_FACTION)
        if completed_struct:
            placing_bid = completed_struct
            placing_ghost = None  # Don't snap ghost until mouse moves
            notifs.add(f"STRUCTURE READY — CLICK TO PLACE {completed_struct.upper().replace('_',' ')}", (0, 255, 100))
        if completed_unit:
            pb = sidebar._has_producer(completed_unit, world, PLAYER_FACTION)
            if pb:
                sx = pb.gx + pb.bdef["w"] + 0.5
                sy = pb.gy + pb.bdef["h"] / 2
            else:
                sx, sy = 13, 19
            world.spawn_unit(completed_unit, PLAYER_FACTION, sx, sy)
            notifs.add(f"UNIT DEPLOYED — {completed_unit.upper().replace('_',' ')}", (0, 220, 180))
            audio.play("spawn")

        # Infamy threshold notifications
        cur_inf = world.roe_manager.infamy
        if _prev_infamy < 200 <= cur_inf:
            notifs.add("!! SCRUTINIZED — OVERSIGHT ACTIVE", (220, 180, 0))
            advisor.trigger("infamy_scrutinized")
            audio.play("infamy_tick")
            _alert_flash = 0.5
        elif _prev_infamy < 400 <= cur_inf:
            notifs.add("!! SURVEILLED — FRONTLINE DRONES INCOMING", (255, 140, 0))
            advisor.trigger("infamy_surveilled")
            audio.play("alert")
            _alert_flash = 0.8
        elif _prev_infamy < 750 <= cur_inf:
            notifs.add("!! SANCTIONED — HEAVY PRODUCTION FROZEN", (220, 40, 30))
            advisor.trigger("infamy_sanctioned")
            audio.play("alert")
            _alert_flash = 1.2
        _prev_infamy = cur_inf
        _alert_flash = max(0.0, _alert_flash - dt_sec)

        if intro_state == "end":
            objectives.ng_timer = _ng_timer
            objectives.update(world)

        if _ng_timer > 0 and intro_state == "end":
            _ng_timer -= dt_sec

            # Mid-game hostile reinforcement wave at ~150s remaining
            if not _ng_wave_done and _ng_timer <= 150.0:
                _ng_wave_done = True
                _wave_enemy = world._ENEMY_MAP.get(PLAYER_FACTION, "sovereign")
                for px, py in getattr(_active_map, "AI_HOSTILE_WAVE_PROXIES", [(50, 3), (51, 3), (52, 3)]):
                    world.spawn_unit("proxy", _wave_enemy, px, py)
                _ew_f, _ew_u, _ew_x, _ew_y = getattr(
                    _active_map, "AI_HOSTILE_WAVE_EXTRA", ("frontline", "drone_scout", 48, 5))
                world.spawn_unit(_ew_u, _ew_f, _ew_x, _ew_y)
                notifs.add("!! HOSTILE REINFORCEMENTS — PERIMETER BREACH NORTH", (220, 80, 40))
                advisor.trigger("surveilled")
                _alert_flash = max(_alert_flash, 1.0)

            if _ng_timer <= 0:
                _ng_timer = -1.0
                _ng_g = getattr(_active_map, "AI_NG_GRAVY_POSITIONS", None)
                if _ng_g is None:
                    _ng_g = [(42 + _i * 0.9, 11) for _i in range(3)]
                for _ngx, _ngy in _ng_g:
                    world.spawn_unit("gravy_seal", PLAYER_FACTION, _ngx, _ngy)
                _mx, _my = getattr(_active_map, "AI_NG_MRAP_POSITION", (43, 12))
                world.spawn_unit("mrap", PLAYER_FACTION, _mx, _my)
                notifs.add("!! NATIONAL GUARD ARRIVES — WHIPPLE DISTRICT SECURED", (0, 200, 255))
                advisor.trigger("ng_arrival_district")
                _alert_flash = max(_alert_flash, 1.5)
                world.game_over = world.GAME_OVER_VICTORY

        advisor.update(dt_sec)
        audio.update(dt_sec)

        # Rate-limited combat ambient sound
        _combat_sound_timer = max(0.0, _combat_sound_timer - dt_sec)
        if _combat_sound_timer <= 0 and intro_state == "end":
            in_combat = any(u.state == "attacking" and u.faction == PLAYER_FACTION
                            for u in world.units.values())
            enemy_combat = any(u.state == "attacking"
                               and u.faction != PLAYER_FACTION
                               for u in world.units.values())
            if in_combat or enemy_combat:
                heavy = any(u.utype in ("mrap", "contractor", "drone_assault")
                            for u in world.units.values() if u.state == "attacking")
                audio.play_combat(heavy=heavy)
                _combat_sound_timer = 0.22

        # Consume world events → notifications + advisor
        for ev_type, payload in world.events:
            if ev_type == "building_captured":
                by = payload["by"]
                name = payload["name"]
                _CAPTURE_VOICE = {
                    "regency":   "PROCESSED AND SECURED",
                    "frontline": "LIBERATED — FOOTAGE LEAKED",
                    "sovereign": "OUTPOST DECLARED",
                    "oligarchy": "ANNEXED — SEE EXHIBIT A",
                }
                if by == PLAYER_FACTION:
                    voice = _CAPTURE_VOICE.get(PLAYER_FACTION, "CAPTURED")
                    notifs.add(f"{voice}: {name}", (0, 255, 100))
                    advisor.trigger("building_captured_player")
                    audio.play("capture")
                    if (map_id == "quad" and not _crime_scene_secured
                            and payload.get("bid") == _crime_scene_bid):
                        _crime_scene_secured = True
                        if not _drive_unlocked:
                            _drive_unlocked = True
                            world.spawn_tape(*KIRK_RALLY)
                            world.escalate_objective_harassment(1)
                            notifs.add("OBJECTIVE COMPLETE — CRIME SCENE SECURED. THUMB DRIVE RECOVERED.", (80, 220, 255))
                else:
                    voice = _CAPTURE_VOICE.get(by, by.upper())
                    notifs.add(f"LOST: {name} — {voice}", (255, 100, 40))
                    advisor.trigger("building_captured_enemy")
                    audio.play("building_lost")
            elif ev_type == "building_destroyed":
                notifs.add(f"DESTROYED: {payload['name']}", (220, 40, 30))
                advisor.trigger("building_destroyed")
                audio.play("explosion")
            elif ev_type == "press_amplify":
                notifs.add("PRESS BUREAU RECORDING — +5 INFAMY", (255, 140, 0))
            elif ev_type == "bolo_identified":
                notifs.add("!! ALPR HIT — BOLO TARGET IDENTIFIED", (255, 220, 0))
                _alert_flash = 0.4
            elif ev_type == "bolo_captured":
                if payload["faction"] == PLAYER_FACTION:
                    notifs.add("!! BOLO TARGET SECURED — +§500 BONUS", (0, 255, 100))
                    advisor.trigger("bolo_captured_player")
                    audio.play("capture")
                else:
                    notifs.add("!! BOLO TARGET ACQUIRED BY ENEMY", (255, 80, 30))
                    advisor.trigger("bolo_captured_enemy")
                    audio.play("alert")
                    _alert_flash = 0.4
            elif ev_type == "bus_unloaded":
                notifs.add(f"BUS DELIVERED: {payload['count']} DETAINEES — +§{payload['credits']}", (0, 200, 160))
                advisor.trigger("bus_unloaded")
                audio.play("bus_unload")
            elif ev_type == "runner_arrived":
                notifs.add("!! HVP REACHED EXTRACTION — ENEMY REINFORCEMENTS INBOUND", (255, 60, 30))
                advisor.trigger("runner_arrived")
                audio.play("alert")
                _alert_flash = 1.2
            elif ev_type == "leak_comms":
                notifs.add(f"!! LEAK: COMMS INTERCEPTED — +{payload['infamy']} INFAMY", (180, 60, 255))
                _leak_overlay = ("OPERATIONAL SECURITY BREACH",
                                 "INTERNAL COMMS INTERCEPTED BY FRONTLINE.\nAGENT IDENTITIES COMPROMISED.",
                                 5.0)
                _alert_flash = 0.8
            elif ev_type == "leak_footage":
                notifs.add(f"!! LEAK: INCIDENT FOOTAGE OBTAINED — +{payload['infamy']} INFAMY", (200, 60, 255))
                _leak_overlay = ("RAW FOOTAGE LEAKED",
                                 "FRONTLINE DRONE CAPTURED INCIDENT ON RECORD.\nNARRATIVE INTEGRITY: COMPROMISED.\nENEMY UNITS INBOUND.",
                                 5.0)
                _alert_flash = 1.0
            elif ev_type == "leak_assets":
                notifs.add(f"!! LEAK: PEN MANIFEST PUBLISHED — +{payload['infamy']} INFAMY  RAID INCOMING", (255, 80, 30))
                _leak_overlay = ("ASSET MANIFEST COMPROMISED",
                                 "HOLDING PEN OCCUPANT LIST PUBLISHED ONLINE.\nENEMY FORCES TARGETING YOUR PENS NOW.",
                                 5.0)
                _alert_flash = 1.2
            elif ev_type == "leak_defector":
                notifs.add(f"!! LEAK: FIELD CONTRACTOR DEFECTS — +{payload['infamy']} INFAMY", (200, 80, 255))
                _leak_overlay = ("ASSET DEFECTION CONFIRMED",
                                 "A CONTRACTED FIELD OPERATIVE HAS SWITCHED ALLEGIANCE.\nENEMY FORCE COMPOSITION UPDATED.",
                                 5.0)
                _alert_flash = 0.6
            elif ev_type == "deepfake_live":
                notifs.add("!! KIRK AI DEEPFAKE DEPLOYED — +50 INFAMY", (180, 40, 255))
                advisor.trigger("deepfake_live")
                audio.play("infamy_tick")
                _deepfake_overlay = 6.0
                _alert_flash = 1.5
            elif ev_type == "salvage":
                notifs.add(f"SALVAGE YARD — +§{payload['credits']}", (200, 160, 30))
                advisor.trigger("salvage")
            elif ev_type == "witness_empowered":
                notifs.add("FRONTLINE: WITNESS EMPOWERED — BROADCASTING LIVE", (80, 220, 80))
            elif ev_type == "witness_radicalized":
                notifs.add("SOVEREIGN: WITNESS RADICALIZED — MILITIA SPAWNED", (160, 40, 220))
                advisor.trigger("witness_radicalized")
            elif ev_type == "witness_assetized":
                notifs.add("OLIGARCHY: WITNESS ASSETIZED — LEVERAGE ACQUIRED", (220, 180, 40))
            elif ev_type == "insurance_payout":
                notifs.add(f"OLIGARCHY: INSURANCE PAYOUT +§{payload['credits']}", (220, 180, 40))
            elif ev_type == "vbied_armed":
                notifs.add("!! CIVILIAN VEHICLE INBOUND — POSSIBLE VBIED", (255, 140, 0))
                advisor.trigger("vbied_armed")
                _alert_flash = 0.6
            elif ev_type == "vbied_explode":
                notifs.add("!! SOVEREIGN VBIED DETONATED — AREA COMPROMISED", (255, 60, 20))
                advisor.trigger("vbied_explode")
                audio.play("explosion")
                _alert_flash = 1.0
            elif ev_type == "power_low":
                advisor.trigger("power_low")
            elif ev_type == "rank_5_promotion":
                name = payload.get("hero_name", "UNKNOWN OPERATIVE")
                utype = payload.get("utype", "").replace("_", " ").upper()
                notifs.add("★ EXECUTIVE RANK: {} — {}".format(name, utype), (220, 180, 40))
                advisor.trigger("rank_5_promotion")
                _alert_flash = 0.5
            elif ev_type == "tape_acquired":
                faction = payload["faction"].upper()
                notifs.add("!! EPSTEIN TAPE ACQUIRED BY {} — INTEL BUFF ACTIVE".format(faction), (80, 200, 255))
                advisor.trigger("tape_acquired")
                _alert_flash = 0.8
                if map_id == "quad" and payload.get("faction") == PLAYER_FACTION:
                    world.escalate_objective_harassment(2)
                    notifs.add("HOSTILE RESPONSE ESCALATING — ENEMY SWEEPS INBOUND", (255, 140, 0))
            elif ev_type == "tape_lost":
                notifs.add("!! EPSTEIN TAPE DROPPED — CONTEST IT NOW", (255, 140, 0))
                advisor.trigger("tape_lost")
                _alert_flash = 0.5
            elif ev_type == "cease_desist":
                notifs.add("PATRIOT LAWYER: CEASE & DESIST FILED — AREA SUPPRESSED", (28, 80, 180))
                advisor.trigger("cease_desist")
            elif ev_type == "journalist_killed":
                notifs.add("!! JOURNALIST NEUTRALIZED — +30 INFAMY — INTERNATIONAL INCIDENT", (255, 60, 20))
                advisor.trigger("journalist_killed")
                _alert_flash = 0.8
            elif ev_type == "bolo_identified":
                notifs.add("ALPR HIT — BOLO TARGET IDENTIFIED: {}".format(payload.get("unit", "?").upper()), (255, 166, 0))
                _alert_flash = 0.4
            elif ev_type == "donor_killed":
                notifs.add("!! DONOR NEUTRALIZED — ALLY MORALE COLLAPSED — AREA SUPPRESSED", (255, 100, 20))
                advisor.trigger("donor_killed")
                _alert_flash = 0.6
            elif ev_type == "ddos_hit":
                bname = payload.get("building", "TARGET")
                notifs.add(f"HACKTIVIST DDoS — {bname.upper()} OFFLINE 30s", (80, 200, 255))
                advisor.trigger("ddos_hit")
            elif ev_type == "direktor_killed":
                killer = payload.get("killer_faction", "unknown").upper()
                notifs.add(f"!! THE DIREKTOR ELIMINATED BY {killer} — +§500 BOUNTY", (220, 180, 40))
                advisor.trigger("direktor_killed")
                _alert_flash = 1.0
            elif ev_type == "protester_detained":
                notifs.add("PROTESTER DETAINED — +5 INFAMY", (255, 140, 0))
            elif ev_type == "iron_dome_intercept":
                utype = payload.get("utype", "DRONE").replace("_", " ").upper()
                notifs.add(f"IRON DOME — {utype} SUPPRESSED", (80, 180, 255))
        world.events.clear()

        for k in _ability_cd:
            _ability_cd[k] = max(0.0, _ability_cd[k] - dt_sec)
        _deepfake_overlay = max(0.0, _deepfake_overlay - dt_sec)
        if _leak_overlay:
            title, body, timer = _leak_overlay
            timer = max(0.0, timer - dt_sec)
            _leak_overlay = (title, body, timer) if timer > 0 else None

        notifs.update(dt_sec)

        hud.credits       = world.credits.get(PLAYER_FACTION, 0)
        hud.infamy        = world.roe_manager.infamy
        hud.roe_name      = world.roe_manager.get_name()
        hud.roe_col       = world.roe_manager.get_color()
        hud.power_balance = world.power_balance
        hud.mission_time  = int(world._mission_elapsed)
        hud.map_phase     = world.map_phase
        hud.update(dt)

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(DARK)

        draw_terrain(screen, cam, fog, map_phase=world.map_phase)

        _draw_placed_buildings(screen, cam, world, font_sm, selection, fog)

        # Kirk rally / incident marker
        kx, ky = cam.world_to_screen(*KIRK_RALLY)
        _live_label = "COMPLIANCE CHECK" if map_id == "district" else "LIVE RALLY"
        _site_label = getattr(_active_map, "INCIDENT_LABEL", "AURORA AVE") + " — INCIDENT" if map_id == "district" else "KIRK RALLY"
        if intro_state != "end":
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 8, 2)
            lbl = font_sm.render(_live_label, True, (255, 255, 255))
            screen.blit(lbl, (int(kx) - lbl.get_width() // 2, int(ky) - 30))
            if map_id == "quad" and _kirk_stage_sprite is not None:
                stage_w = int(_kirk_stage_sprite.get_width() * max(0.6, cam.zoom))
                stage_h = int(_kirk_stage_sprite.get_height() * max(0.6, cam.zoom))
                stage = pygame.transform.smoothscale(_kirk_stage_sprite, (stage_w, stage_h))
                sx, sy = cam.world_to_screen(KIRK_RALLY[0] - 0.8, KIRK_RALLY[1] - 1.0)
                screen.blit(stage, (int(sx - stage_w // 2), int(sy - stage_h + 6)))
        elif fog.is_explored(*KIRK_RALLY):
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 8, 2)
            pygame.draw.circle(screen, (220, 50, 50), (int(kx), int(ky)), 16, 1)
            lbl = font_sm.render(_site_label, True, (220, 50, 50))
            screen.blit(lbl, (int(kx) - lbl.get_width() // 2, int(ky) - 20))

        # Civilian vehicles
        for v in world.vehicles.values():
            v.draw(screen, cam, fog)

        # District intro: animate SUV
        if map_id == "district" and intro_state in ("d_approach", "d_check", "d_crash"):
            _svx, _svy = cam.world_to_screen(_d_suv_gx, _d_suv_gy)
            _suv_body_col = (180, 50, 40) if intro_state == "d_crash" else (90, 75, 45)
            pygame.draw.ellipse(screen, _suv_body_col, (int(_svx)-14, int(_svy)-6, 28, 12))
            pygame.draw.ellipse(screen, (50, 35, 20), (int(_svx)-14, int(_svy)-6, 28, 12), 1)
            if intro_state != "d_crash":
                _f_suv = pygame.font.SysFont("couriernew", 8)
                _suv_lbl = _f_suv.render("ICE SUV", True, (140, 100, 55))
                screen.blit(_suv_lbl, (int(_svx) - _suv_lbl.get_width()//2, int(_svy) - 18))

        # SCOTUS de-zone rings
        for cx, cy, radius, timer in _scotus_zones:
            sx, sy = cam.world_to_screen(cx, cy)
            r_px = int(radius * cam.zoom * 36)  # approx tile-width scale
            alpha = min(200, int(timer * 4))
            ring_col = (200, 180, 0)
            pygame.draw.circle(screen, ring_col, (sx, sy), r_px, 2)
            f_scotus = pygame.font.SysFont("couriernew", 9, bold=True)
            lbl = f_scotus.render(f"DE-ZONED {int(timer)}s", True, ring_col)
            screen.blit(lbl, (sx - lbl.get_width() // 2, sy - r_px - 14))

        # Building aura rings when a building is selected
        _BLD_AURA_RANGES = {
            "troll":       (10.0, (160, 80, 40),  "TROLL RANGE"),
            "iron_dome":   ( 6.0, (80, 180, 255), "DOME RANGE"),
            "vision":      (28.0, (0,  200, 140), "VISION RANGE"),
            "propaganda":  ( 8.0, (200, 40, 200), "PROPAGANDA"),
            "infamy_amplify": (12.0, (220, 100, 20), "AMPLIFY RANGE"),
            "ddos":        (10.0, (80, 200, 255), "DDoS RANGE"),
        }
        if hud.selected_bld:
            pb = hud.selected_bld
            flags = pb.bdef.get("flags", [])
            bcx = pb.gx + pb.bdef["w"] / 2
            bcy = pb.gy + pb.bdef["h"] / 2
            bsx, bsy = cam.world_to_screen(bcx, bcy)
            for flag, (radius, col, label) in _BLD_AURA_RANGES.items():
                if flag in flags:
                    r_px = int(radius * cam.zoom * 36)
                    rsy  = int(r_px * 0.5)
                    a_surf = pygame.Surface((r_px * 2, rsy * 2), pygame.SRCALPHA)
                    pygame.draw.ellipse(a_surf, (*col, 30), (0, 0, r_px * 2, rsy * 2))
                    pygame.draw.ellipse(a_surf, (*col, 100), (0, 0, r_px * 2, rsy * 2), 1)
                    screen.blit(a_surf, (bsx - r_px, bsy - rsy))
                    f_aura = pygame.font.SysFont("couriernew", 9)
                    lbl = f_aura.render(label, True, col)
                    screen.blit(lbl, (bsx - lbl.get_width() // 2, bsy - rsy - 12))

        # Wreck markers
        for gx, gy, timer in world.wrecks:
            wx, wy = cam.world_to_screen(gx, gy)
            permanent = (timer == 99999)
            alpha = 200 if permanent else min(255, int(timer * 6))
            if permanent:
                # Rubble: dark heap silhouette
                pygame.draw.ellipse(screen, (30, 22, 14), (wx - 9, wy - 3, 18, 7))
                pygame.draw.line(screen, (55, 40, 25), (wx - 5, wy - 7), (wx + 2, wy - 4), 2)
                pygame.draw.line(screen, (45, 32, 18), (wx + 4, wy - 6), (wx - 1, wy - 3), 2)
            else:
                # Unit wreck: X cross + smoke ellipse, fades over time
                col = tuple(int(c * alpha / 255) for c in (80, 60, 40))
                pygame.draw.line(screen, col, (wx - 6, wy - 10), (wx + 6, wy - 2), 2)
                pygame.draw.line(screen, col, (wx + 6, wy - 10), (wx - 6, wy - 2), 2)
                pygame.draw.ellipse(screen, (int(40 * alpha / 255), 8, 6),
                                    (wx - 8, wy - 2, 16, 5))

        # Tape MacGuffin
        if world.tape["active"]:
            tx, ty = cam.world_to_screen(world.tape["gx"], world.tape["gy"])
            t_ms = pygame.time.get_ticks()
            pulse = int(8 + math.sin(t_ms * 0.008) * 3)
            col_tape = (80, 200, 255) if world.tape["holder_uid"] is None else (220, 180, 40)
            pygame.draw.circle(screen, col_tape, (int(tx), int(ty) - 8), pulse, 2)
            pygame.draw.rect(screen, col_tape, (int(tx) - 5, int(ty) - 13, 10, 8), 1)
            f_tape = pygame.font.SysFont("couriernew", 8, bold=True)
            if world.tape["holder_uid"] is None:
                lbl_tape = f_tape.render("TAPE", True, col_tape)
                screen.blit(lbl_tape, (int(tx) - lbl_tape.get_width() // 2, int(ty) - 24))

        # Units
        for u in sorted(world.units.values(), key=lambda u: u.gy):
            if u.faction == PLAYER_FACTION or fog.is_visible(u.gx, u.gy):
                u.draw(screen, cam)

        # Civilians
        for c in world.civilians.values():
            if intro_state != "end" or fog.is_visible(c.gx, c.gy):
                c.draw(screen, cam)

        # Kirk highlight — prominent pulsing ring during intro
        if intro_state in ("rally", "talk", "wait", "d_approach", "d_check") and kirk_obj.state != "dead":
            ksx, ksy = cam.world_to_screen(kirk_obj.gx, kirk_obj.gy)
            t_ms = pygame.time.get_ticks()
            pulse = int(16 + math.sin(t_ms * 0.006) * 4)
            pygame.draw.circle(screen, (255, 200, 0), (int(ksx), int(ksy) - 8), pulse, 2)
            pygame.draw.circle(screen, (255, 120, 0), (int(ksx), int(ksy) - 8), pulse + 5, 1)
            f_kirk = pygame.font.SysFont("couriernew", 9, bold=True)
            klbl = f_kirk.render("◆ KIRK", True, (255, 220, 60))
            screen.blit(klbl, (int(ksx) - klbl.get_width() // 2, int(ksy) - pulse - 22))

        # Intro Overlay
        if intro_state in ("shot", "d_shot"):
            screen.fill((255, 255, 255))
        elif intro_state == "rally":
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WIN_W, 80))
            pygame.draw.rect(overlay, (0, 0, 0, 180), (0, WIN_H - 120, WIN_W, 120))
            screen.blit(overlay, (0, 0))
            f_lg = pygame.font.SysFont("couriernew", 24, bold=True)
            msg = f_lg.render("UVU QUAD — 14:02 LOCAL", True, (0, 255, 160))
            screen.blit(msg, (50, WIN_H - 100))
            msg2 = font_sm.render("MONITORING INDIVIDUALIST GATHERING...", True, (0, 200, 120))
            screen.blit(msg2, (50, WIN_H - 65))
            pygame.draw.rect(screen, (255, 0, 0), (40, 40, 100, 40), 2)
            rec_lbl = font_sm.render("● REC", True, (255, 0, 0))
            screen.blit(rec_lbl, (50, 50))

        elif intro_state == "d_approach":
            _ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            pygame.draw.rect(_ov, (0, 0, 0, 180), (0, 0, WIN_W, 80))
            pygame.draw.rect(_ov, (0, 0, 0, 180), (0, WIN_H - 120, WIN_W, 120))
            screen.blit(_ov, (0, 0))
            f_lg = pygame.font.SysFont("couriernew", 24, bold=True)
            msg = f_lg.render("AURORA AVE — 09:14 LOCAL", True, (60, 120, 255))
            screen.blit(msg, (50, WIN_H - 100))
            msg2 = font_sm.render("ICE FIELD OPERATION — COMPLIANCE CHECK IN PROGRESS...", True, (40, 80, 200))
            screen.blit(msg2, (50, WIN_H - 65))
            pygame.draw.rect(screen, (60, 120, 255), (40, 40, 100, 40), 2)
            rec_lbl = font_sm.render("● REC", True, (60, 120, 255))
            screen.blit(rec_lbl, (50, 50))

        elif intro_state in ("d_crash", "d_panic"):
            _ov2 = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            pygame.draw.rect(_ov2, (0, 0, 0, 180), (0, WIN_H - 80, WIN_W, 80))
            screen.blit(_ov2, (0, 0))
            f_lg2 = pygame.font.SysFont("couriernew", 16, bold=True)
            msg3 = f_lg2.render("SHOTS FIRED — SUBJECT DOWN — NARRATIVE CONTAINMENT ACTIVE",
                                True, (255, 60, 30))
            screen.blit(msg3, (WIN_W // 2 - msg3.get_width() // 2, WIN_H - 55))

        if intro_state in ("talk", "wait") and intro_text:
            f_talk = pygame.font.SysFont("couriernew", 20, bold=True)
            if intro_state == "talk":
                chars_to_show = int(len(intro_text) * (1 - intro_timer / 4.0))
                current_str = intro_text[:chars_to_show]
                if chars_to_show > 0 and chars_to_show % 3 == 0:
                    audio.play("infamy_tick")
            else:
                current_str = intro_text
            if current_str:
                txt_surf = f_talk.render(current_str, True, (255, 255, 255))
                tx = WIN_W // 2 - txt_surf.get_width() // 2
                ty = WIN_H - 150
                bg_surf = pygame.Surface((txt_surf.get_width() + 20, txt_surf.get_height() + 10), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 160))
                screen.blit(bg_surf, (tx - 10, ty - 5))
                screen.blit(txt_surf, (tx, ty))
                spk = font_sm.render("// KIRK :", True, (255, 200, 80))
                screen.blit(spk, (tx - 10, ty - 18))

        if intro_state == "d_check" and intro_text:
            f_talk = pygame.font.SysFont("couriernew", 18, bold=True)
            chars_to_show = int(len(intro_text) * max(0.0, 1 - intro_timer / 3.0))
            current_str = intro_text[:chars_to_show]
            if current_str:
                txt_surf = f_talk.render(current_str, True, (255, 255, 255))
                tx = WIN_W // 2 - txt_surf.get_width() // 2
                ty = WIN_H - 150
                bg_surf = pygame.Surface((txt_surf.get_width() + 20, txt_surf.get_height() + 10), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 160))
                screen.blit(bg_surf, (tx - 10, ty - 5))
                screen.blit(txt_surf, (tx, ty))
                spk = font_sm.render("// ICE OFFICER :", True, (80, 140, 255))
                screen.blit(spk, (tx - 10, ty - 18))

        # Ghost building preview
        if placing_bid and placing_ghost:
            _draw_ghost_building(screen, cam, placing_bid, placing_ghost, world)

        # Capture progress bars
        _draw_capture_bars(screen, cam, world, PLAYER_FACTION, font_sm)

        selection.draw(screen)
        selection.draw_unit_selection(screen, world, cam)
        selection.draw_order_marker(screen)

        # Aura range rings for selected aura units
        _AURA_RANGES = {
            "patriot_lawyer": (3.5, (28, 80, 200)),
            "agitator":       (3.5, (80, 200, 80)),
            "direktor":       (8.0, (200, 160, 30)),
            "settler":        (3.0, (160, 80, 220)),
            "journalist":     (5.0, (80, 200, 220)),
        }
        for uid in selection.selected_uids:
            u = world.units.get(uid)
            if not u or u.utype not in _AURA_RANGES:
                continue
            radius, col = _AURA_RANGES[u.utype]
            cx, cy = cam.world_to_screen(u.gx, u.gy)
            # Approximate iso ellipse: x radius stays, y radius halved
            rx = int(radius * cam.zoom * 36)
            ry = int(rx * 0.5)
            aura_surf = pygame.Surface((rx * 2 + 2, ry * 2 + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, (*col, 40), (0, 0, rx * 2, ry * 2))
            pygame.draw.ellipse(aura_surf, (*col, 120), (0, 0, rx * 2, ry * 2), 1)
            screen.blit(aura_surf, (cx - rx, cy - ry))

        # HUD
        minimap_fn = lambda s: draw_minimap(s, cam, hud.minimap_rect,
                                            world=world, fog=fog,
                                            player_faction=PLAYER_FACTION)
        hud.draw(screen, minimap_draw_fn=minimap_fn)

        click_zones = sidebar.draw(screen, sidebar_rect(), world, PLAYER_FACTION)

        _draw_selection_info(screen, selection, world, font_sm, WIN_H, WIN_W - SIDEBAR_W)

        if intro_state == "end":
            objectives.draw(screen, WIN_W, WIN_H)
        advisor.draw(screen, WIN_W, WIN_H)

        if _alert_flash > 0:
            alpha = min(200, int(_alert_flash * 300))
            bw = max(2, int(_alert_flash * 8))
            pygame.draw.rect(screen, (220, 30, 30), (0, 0, WIN_W, WIN_H), bw)

        if roe5_confirm:
            _draw_roe5_confirm(screen, font_sm, WIN_W, WIN_H)

        if intro_state == "end":
            _draw_ability_hud(screen, _ability_cd, font_sm, WIN_W, WIN_H, PLAYER_FACTION)

        notifs.draw(screen, x=8, bottom_y=WIN_H - 55)

        if _deepfake_overlay > 0:
            _draw_deepfake_overlay(screen, WIN_W, WIN_H, _deepfake_overlay)

        if _leak_overlay:
            _draw_leak_overlay(screen, WIN_W, WIN_H, *_leak_overlay)

        if world.map_phase >= 2:
            _draw_phase2_overlay(screen, WIN_W, WIN_H)

        if show_help:
            _draw_help_overlay(screen, WIN_W, WIN_H)

        pygame.display.flip()


def _pick_theater(screen, clock):
    """Theater selection screen — returns 'quad' or 'district', or None on ESC."""
    f_title = pygame.font.SysFont("couriernew", 26, bold=True)
    f_opt   = pygame.font.SysFont("couriernew", 18, bold=True)
    f_sub   = pygame.font.SysFont("couriernew", 11)
    options = [
        ("quad",     "THE QUAD",         "UVU CAMPUS — KIRK CATALYST EVENT"),
        ("district", "WHIPPLE DISTRICT", "MN GOVT QUARTER — AURORA AVE INCIDENT"),
    ]
    sel = 0
    while True:
        sw, sh = screen.get_size()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(options)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(options)
                elif ev.key == pygame.K_1:
                    return options[0][0]
                elif ev.key == pygame.K_2:
                    return options[1][0]
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return options[sel][0]
                elif ev.key == pygame.K_ESCAPE:
                    return None

        screen.fill((6, 12, 10))
        title = f_title.render("SELECT OPERATIONAL THEATER", True, (0, 255, 180))
        screen.blit(title, (sw // 2 - title.get_width() // 2, 110))
        pygame.draw.line(screen, (0, 80, 60), (60, 148), (sw - 60, 148))

        for i, (_mid, name, sub) in enumerate(options):
            y = 220 + i * 100
            active = (i == sel)
            col    = (0, 255, 160) if active else (0, 80, 60)
            bg_col = (8, 24, 18)   if active else (4, 10, 8)
            rect   = pygame.Rect(sw // 2 - 300, y - 8, 600, 72)
            pygame.draw.rect(screen, bg_col, rect)
            pygame.draw.rect(screen, col, rect, 2 if active else 1)
            num_lbl  = f_opt.render(f"[{i+1}]", True, col)
            name_lbl = f_opt.render(name, True, col)
            sub_lbl  = f_sub.render(sub, True, (0, 130, 90) if active else (0, 50, 40))
            screen.blit(num_lbl,  (rect.left + 16, y + 8))
            screen.blit(name_lbl, (rect.left + 64, y + 8))
            screen.blit(sub_lbl,  (rect.left + 64, y + 34))

        hint = f_sub.render("[ UP/DOWN ] SELECT    [ ENTER ] CONFIRM    [ ESC ] BACK", True, (0, 60, 50))
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 60))
        pygame.display.flip()
        clock.tick(FPS)


def _end_mission(screen, clock, world, hud, player_faction, map_id,
                 slot_num=None, slot_data=None):
    """Run post-op → press briefing → executive board, then save slot."""
    detained = sum(pb.civs_held for pb in world.placed_buildings.values()
                   if pb.faction == player_faction)
    result = _postop_mod.run(screen, clock, detained,
                              world.roe_manager.infamy,
                              hud.mission_time,
                              world.credits.get(player_faction, 0))
    lp = _eb_mod.compute_lp(result, hud.mission_time)

    # Collect rank-5 heroes for Hall of Heroes
    heroes = []
    for u in world.units.values():
        if u.rank >= 5 and u.hero_name and u.faction == player_faction:
            heroes.append({
                "name": u.hero_name,
                "utype": u.utype,
                "kills": getattr(u, "kills", 0),
                "faction": u.faction,
            })
    if slot_data is not None:
        existing = slot_data.get("hall_of_heroes", [])
        existing_names = {h["name"] for h in existing}
        for h in heroes:
            if h["name"] not in existing_names:
                existing.append(h)
        slot_data["hall_of_heroes"] = existing

    _eb_mod.run(screen, clock, lp,
                hall_of_heroes=slot_data.get("hall_of_heroes", []) if slot_data else [])

    if slot_num is not None and slot_data is not None:
        updated = _save_mod.apply_postop(
            slot_data, result,
            world.roe_manager.infamy,
            world.credits.get(player_faction, 0),
            lp,
        )
        # Persist visual wrecks by theater so map swaps do not leak state.
        _saved_by_map = dict(slot_data.get("persisted_wrecks", {}))
        _uniq_wrecks = []
        _seen_wrecks = set()
        for gx, gy, timer in world.wrecks:
            if timer <= 0:
                continue
            item = [round(float(gx), 2), round(float(gy), 2), round(float(timer), 1)]
            key = (item[0], item[1], item[2])
            if key in _seen_wrecks:
                continue
            _seen_wrecks.add(key)
            _uniq_wrecks.append(item)
            if len(_uniq_wrecks) >= 400:
                break
        _saved_by_map[map_id] = _uniq_wrecks
        updated["persisted_wrecks"] = _saved_by_map
        # Carry forward executive board upgrades
        updated["upgrades"]  = _eb_mod._load().get("upgrades", {})
        updated["lp"]        = _eb_mod._load().get("lp", updated.get("lp", 0))
        updated["hall_of_heroes"] = slot_data.get("hall_of_heroes", [])
        # Advance map phase each mission (caps at 2 — shattered)
        updated["map_phase"] = min(2, slot_data.get("map_phase", 0) + 1)
        _save_mod.save(slot_num, updated)


def _draw_game_over_splash(surf, clock, game_over_state, sw, sh):
    """Brief full-screen splash shown between game over and post-op debrief."""
    from game.world import World
    victory = game_over_state == World.GAME_OVER_VICTORY
    bg_col  = (0, 30, 20) if victory else (30, 0, 0)
    txt     = "MISSION COMPLETE" if victory else "MISSION FAILED"
    sub     = "Compiling operational report..." if victory else "Damage assessment in progress..."
    txt_col = (0, 255, 180) if victory else (220, 40, 40)

    f_big = pygame.font.SysFont("couriernew", 42, bold=True)
    f_sm  = pygame.font.SysFont("couriernew", 14)

    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < 2200:
        for ev in pygame.event.get():
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return   # skip on any input
        elapsed = (pygame.time.get_ticks() - start) / 2200.0
        alpha = int(min(1.0, elapsed * 3) * 255)
        surf.fill(bg_col)
        big = f_big.render(txt, True, txt_col)
        big.set_alpha(alpha)
        surf.blit(big, (sw // 2 - big.get_width() // 2, sh // 2 - 40))
        sm = f_sm.render(sub, True, (0, 120, 80) if victory else (160, 60, 60))
        sm.set_alpha(alpha)
        surf.blit(sm, (sw // 2 - sm.get_width() // 2, sh // 2 + 20))
        pygame.display.flip()
        clock.tick(60)


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
            pal = {k: [c // 2 for c in v] for k, v in pal.items()}

        hl  = pb.selected
        bw, bh, fl = pb.bdef["w"], pb.bdef["h"], pb.bdef["floors"]

        from game.iso import TILE_W, TILE_H, WALL_H
        tw = int(TILE_W * cam.zoom)
        th = int(TILE_H * cam.zoom)
        wh = int(WALL_H * cam.zoom)
        hw, hh = tw // 2, th // 2

        _draw_building(surf, cam, pb.gx, pb.gy, bw, bh, fl, pal, hw, hh, wh, hl)

        if pb.bdef.get("garrison", 0):
            mx, my = cam.world_to_screen(pb.gx + bw / 2, pb.gy + bh / 2, fl + 0.5)
            slots = pb.bdef["garrison"]
            occ   = len(pb.garrison)
            gcol  = (255, 102, 0) if occ == 0 else (0, 200, 100)
            badge = font.render(f"[{occ}/{slots}]", True, gcol)
            surf.blit(badge, (int(mx) - badge.get_width() // 2, int(my)))

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

        rank_str = "★" * u.rank + "☆" * (5 - u.rank)
        display_name = u.hero_name if (u.rank >= 5 and u.hero_name) else u.utype.upper().replace("_", " ")
        name_lbl = f_med.render(
            f"{display_name}  {rank_str}",
            True, (220, 180, 40) if (u.rank >= 5 and u.hero_name) else FACTION_COLORS.get(u.faction, (0, 200, 140)))
        surf.blit(name_lbl, (10, screen_h - bar_h + 4))

        state_txt = u.state.upper()
        if u.suppressed:
            state_txt += "  [SUPPRESSED]"
        state_lbl = f_sm.render(state_txt, True, (0, 160, 100))
        surf.blit(state_lbl, (10, screen_h - bar_h + 22))

        bw = min(200, panel_w // 3)
        bx = 220
        by = screen_h - bar_h + 8
        pct = u.hp / u.max_hp
        bar_col = (40, 200, 60) if pct > 0.6 else (220, 180, 0) if pct > 0.3 else (220, 40, 40)
        pygame.draw.rect(surf, (30, 30, 30), (bx - 1, by - 1, bw + 2, 8))
        pygame.draw.rect(surf, bar_col, (bx, by, int(bw * pct), 6))
        hp_lbl = f_sm.render(f"HP  {u.hp}/{u.max_hp}", True, (0, 160, 100))
        surf.blit(hp_lbl, (bx, by + 10))

        if u.rank < 5:
            xp_pct = u.xp / u.xp_to_next
            pygame.draw.rect(surf, (20, 20, 40), (bx - 1, by + 22, bw + 2, 5))
            pygame.draw.rect(surf, (60, 60, 220), (bx, by + 23, int(bw * xp_pct), 3))
            xp_lbl = f_sm.render(
                f"XP  {int(u.xp)}/{int(u.xp_to_next)}  [{Unit.RANK_NAMES[u.rank - 1]}]",
                True, (80, 80, 180))
            surf.blit(xp_lbl, (bx, by + 28))

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


def _draw_ability_hud(surf, ability_cd, font, sw, sh, player_faction="regency"):
    from game.hud import SIDEBAR_W, TOPBAR_H
    _q_labels = {
        "regency":   ("Q", "RED TAPE",   20.0, (0, 200, 255)),
        "frontline": ("Q", "CROWDFUND",  30.0, (80, 200, 80)),
        "oligarchy": ("Q", "GRINDER",    35.0, (180, 80, 40)),
        "sovereign": ("Q", "BLK MKT",    25.0, (140, 40, 200)),
    }
    _e_labels = {
        "regency":   ("E", "STIMULUS",   45.0, (0, 255, 100)),
        "frontline": ("E", "OVERWATCH",  40.0, (80, 200, 200)),
        "oligarchy": ("E", "KICKBACK",   50.0, (200, 160, 0)),
        "sovereign": ("E", "SHADOW CELL",45.0, (140, 40, 200)),
    }
    _r_labels = {
        "regency":   ("R", "SCOTUS",    120.0, (200, 180, 0)),
        "frontline": ("R", "DRN SWARM",  90.0, (80, 220, 80)),
        "oligarchy": ("R", "T.SURGE",    90.0, (180, 80, 40)),
        "sovereign": ("R", "EPSTEIN",   150.0, (140, 40, 200)),
    }
    q = _q_labels.get(player_faction, ("Q", "SUPPRESS", 20.0, (0, 200, 255)))
    e = _e_labels.get(player_faction, ("E", "BACKUP",   45.0, (0, 255, 100)))
    r = _r_labels.get(player_faction, ("R", "WEAPON",  120.0, (200, 180, 0)))
    abilities = [
        (q[0], q[1], ability_cd.get("q", 0), q[2], q[3]),
        (e[0], e[1], ability_cd.get("e", 0), e[2], e[3]),
        (r[0], r[1], ability_cd.get("r", 0), r[2], r[3]),
    ]
    btn_w, btn_h = 64, 44
    gap = 8
    total_w = len(abilities) * btn_w + (len(abilities) - 1) * gap
    x0 = (sw - SIDEBAR_W) // 2 - total_w // 2
    y0 = sh - btn_h - 2

    for i, (key, name, cd, max_cd, col) in enumerate(abilities):
        bx = x0 + i * (btn_w + gap)
        brect = pygame.Rect(bx, y0, btn_w, btn_h)
        ready = cd <= 0
        bg = (10, 22, 18) if ready else (14, 10, 10)
        pygame.draw.rect(surf, bg, brect)
        pygame.draw.rect(surf, col if ready else (40, 40, 40), brect, 1)

        key_lbl = pygame.font.SysFont("couriernew", 16, bold=True).render(
            f"[{key}]", True, col if ready else (60, 60, 60))
        surf.blit(key_lbl, (bx + btn_w // 2 - key_lbl.get_width() // 2, y0 + 4))

        nm_lbl = font.render(name, True, col if ready else (50, 50, 50))
        surf.blit(nm_lbl, (bx + btn_w // 2 - nm_lbl.get_width() // 2, y0 + 24))

        if not ready:
            pct = 1.0 - (cd / max_cd)
            pygame.draw.rect(surf, (20, 40, 30), (bx + 2, y0 + btn_h - 6, btn_w - 4, 4))
            pygame.draw.rect(surf, col, (bx + 2, y0 + btn_h - 6, int((btn_w - 4) * pct), 4))


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
        pygame.draw.rect(surf, (255, 200, 0), (bx, by, int(bw * pct), 4))
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
            ("Double-Click",      "Select all of type on screen"),
            ("Ctrl + A",          "Select ALL friendly units"),
        ]),
        ("ORDERS",  [
            ("Right-Click unit",  "Attack order"),
            ("Right-Click ground","Move order (formation)"),
            ("Right-Click bldg", "Garrison order"),
            ("G",                 "Garrison selected into nearest building"),
            ("S",                 "Stop all selected"),
        ]),
        ("ABILITIES",  [
            ("Q",                 "Primary ability (faction-specific)"),
            ("E",                 "Secondary ability (faction-specific)"),
            ("R",                 "Superweapon — long cooldown"),
            ("B",                 "Toggle build menu"),
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
            ("F",                 "Toggle fog of war"),
            ("M",                 "Mute / unmute audio"),
            ("H or ?",            "Toggle this help overlay"),
            ("Escape",            "Cancel placement / deselect"),
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


def _draw_deepfake_overlay(surf, sw, sh, timer):
    fade = min(1.0, timer) * min(1.0, (timer - 0.0) / 0.3)
    if timer < 1.5:
        fade = timer / 1.5
    alpha = int(fade * 210)

    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((20, 0, 40, alpha))
    surf.blit(overlay, (0, 0))

    if alpha < 30:
        return

    f_title = pygame.font.SysFont("couriernew", 30, bold=True)
    f_med   = pygame.font.SysFont("couriernew", 13, bold=True)
    f_sm    = pygame.font.SysFont("couriernew", 10)

    PURPLE = (180, 40, 255)
    DIM    = (100, 20, 160)

    glitch = int(math.sin(pygame.time.get_ticks() * 0.03) * 3)

    t = f_title.render("BREAKING: KIRK AI DEEPFAKE DEPLOYED", True, PURPLE)
    surf.blit(t, (sw // 2 - t.get_width() // 2 + glitch, sh // 2 - 80))

    lines = [
        "TECH-STATE HAS RELEASED A SYNTHETIC RECONSTRUCTION OF KIRK.",
        "THE AI IS CURRENTLY LIVESTREAMING ON ALL PLATFORMS.",
        "INITIAL ENGAGEMENT: 4.2M VIEWERS. INFAMY COST: +50.",
        "",
        "THE OFFICIAL VERSION IS NOW CONTESTED.",
    ]
    for i, line in enumerate(lines):
        col = (220, 180, 255) if line else DIM
        lbl = f_sm.render(line, True, col)
        surf.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh // 2 - 30 + i * 18))

    wm = f_med.render("[ TECH-STATE MEDIA DIVISION — UNAUTHORIZED REDISTRIBUTION PROHIBITED ]",
                       True, DIM)
    surf.blit(wm, (sw // 2 - wm.get_width() // 2, sh // 2 + 80))

    for y in range(0, sh, 4):
        pygame.draw.line(surf, (0, 0, 0, 30), (0, y), (sw, y))


def _draw_leak_overlay(surf, sw, sh, title, body, timer):
    fade = min(1.0, timer / 0.4) if timer > 0 else 0.0
    if timer < 1.0:
        fade = timer
    alpha = int(fade * 200)
    if alpha < 10:
        return

    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((20, 0, 30, alpha))
    surf.blit(overlay, (0, 0))

    f_title = pygame.font.SysFont("couriernew", 22, bold=True)
    f_body  = pygame.font.SysFont("couriernew", 11)
    f_sm    = pygame.font.SysFont("couriernew", 9)

    PURPLE = (200, 80, 255)
    DIM    = (100, 30, 140)

    t_lbl = f_title.render(f"// INTEL BREACH: {title}", True, PURPLE)
    surf.blit(t_lbl, (sw // 2 - t_lbl.get_width() // 2, sh // 2 - 60))
    pygame.draw.line(surf, DIM, (sw // 2 - 200, sh // 2 - 36),
                     (sw // 2 + 200, sh // 2 - 36), 1)

    for i, line in enumerate(body.split("\n")):
        lbl = f_body.render(line, True, (200, 160, 240))
        surf.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh // 2 - 20 + i * 18))

    dismiss = f_sm.render("[ ACKNOWLEDGE — CONTINUE OPERATION ]", True, DIM)
    surf.blit(dismiss, (sw // 2 - dismiss.get_width() // 2, sh // 2 + 52))


def _draw_phase2_overlay(surf, sw, sh):
    """Phase III — The Redaction: night vignette + scanlines."""
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 18, 55))
    surf.blit(overlay, (0, 0))
    for y in range(0, sh, 5):
        pygame.draw.line(surf, (0, 0, 0, 18), (0, y), (sw, y))
    # Corner vignette (dark edges)
    for edge_w in range(30, 0, -10):
        alpha = 4
        pygame.draw.rect(surf, (0, 0, 0, alpha), (0, 0, sw, edge_w))
        pygame.draw.rect(surf, (0, 0, 0, alpha), (0, sh - edge_w, sw, edge_w))


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
