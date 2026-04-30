"""Selection manager — drag-box select, right-click orders."""
import math, pygame
from game.pathfinding import find_path, formation_goals
from game.unit_entity import STATE_DEAD

TEAL  = (0, 255, 204)
GREEN = (0, 220, 80)


class SelectionManager:
    def __init__(self):
        self.selected_uids  = set()
        self._drag_start    = None
        self._drag_rect     = None
        self.attack_move    = False   # A key held = attack-move order

    # ── Input ─────────────────────────────────────────────────────────────────

    def mouse_down(self, pos, button, cam, world, hud):
        if hud.hit_sidebar(pos):
            return

        mx, my = pos

        if button == 1:  # left — start selection drag
            self._drag_start = pos
            self._drag_rect  = None

        elif button == 3:  # right — give order to selected units
            self._give_order(mx, my, cam, world)

    def mouse_up(self, pos, button, cam, world, hud):
        if button != 1:
            return

        mx, my = pos

        if self._drag_rect and (self._drag_rect.width > 4 or self._drag_rect.height > 4):
            # Box select — prefer player units
            hits = world.units_in_screen_rect(self._drag_rect, cam)
            player_units = [u for u in hits if u.faction == world.player_faction]
            if player_units:
                hits = player_units
            self._set_selection(hits, world)
        else:
            # Single click
            if not hud.hit_sidebar(pos):
                u = world.unit_at_screen(mx, my, cam)
                if u:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        self._toggle(u.uid, world)
                    else:
                        self._set_selection([u], world)
                else:
                    # Click on building?
                    pb = world.building_at_screen(mx, my, cam)
                    if pb:
                        hud.selected_bld = pb
                    else:
                        self._set_selection([], world)
                        hud.selected_bld = None

        self._drag_start = None
        self._drag_rect  = None

    def mouse_move(self, pos):
        if self._drag_start:
            x0, y0 = self._drag_start
            x1, y1 = pos
            rx, ry = min(x0, x1), min(y0, y1)
            rw, rh = abs(x1 - x0), abs(y1 - y0)
            self._drag_rect = pygame.Rect(rx, ry, rw, rh)

    # ── Orders ────────────────────────────────────────────────────────────────

    def _give_order(self, mx, my, cam, world):
        if not self.selected_uids:
            return

        # Check if right-clicking a building
        target_pb = world.building_at_screen(mx, my, cam)
        
        # Check if right-clicking an enemy unit
        target_unit = world.unit_at_screen(mx, my, cam)
        selected_units = [world.units[uid] for uid in self.selected_uids
                          if uid in world.units and world.units[uid].state != STATE_DEAD]
        if not selected_units:
            return

        blocked = world.blocked_tiles()

        if target_unit and target_unit.faction in world.enemies_of(selected_units[0].faction):
            # Attack order
            for u in selected_units:
                from game.pathfinding import find_path
                wp = find_path((u.gx, u.gy), (target_unit.gx, target_unit.gy), blocked)
                u.order_attack(target_unit.uid, wp[1:-1] if len(wp) > 2 else [])
        elif target_pb and target_pb.bdef.get("garrison", 0) > 0 and target_pb.faction == selected_units[0].faction:
            # Garrison order
            for u in selected_units:
                from game.pathfinding import find_path
                wp = find_path((u.gx, u.gy), (target_pb.gx + target_pb.bdef["w"]/2, target_pb.gy + target_pb.bdef["h"]/2), blocked)
                u.order_garrison(target_pb.bid, wp[1:])
        else:
            # Move order — spread into formation
            gx, gy = cam.screen_to_world(mx, my)
            goals = formation_goals(int(gx), int(gy), len(selected_units), blocked)
            for u, goal in zip(selected_units, goals):
                wp = find_path((u.gx, u.gy), goal, blocked)
                if wp:
                    u.order_move(wp[1:])

        # Move order marker flash
        self._order_marker = (mx, my, 0.4)

    # ── Selection helpers ─────────────────────────────────────────────────────

    def _set_selection(self, units, world):
        for uid in self.selected_uids:
            if uid in world.units:
                world.units[uid].selected = False
        self.selected_uids = {u.uid for u in units}
        for u in units:
            u.selected = True

    def _toggle(self, uid, world):
        if uid in self.selected_uids:
            self.selected_uids.discard(uid)
            if uid in world.units:
                world.units[uid].selected = False
        else:
            self.selected_uids.add(uid)
            if uid in world.units:
                world.units[uid].selected = True

    def select_all_of_type(self, utype, world):
        units = [u for u in world.units.values()
                 if u.utype == utype and u.faction == world.player_faction
                 and u.state != STATE_DEAD]
        self._set_selection(units, world)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface):
        if self._drag_rect and (self._drag_rect.width > 2 or self._drag_rect.height > 2):
            drag_surf = pygame.Surface(
                (self._drag_rect.width, self._drag_rect.height), pygame.SRCALPHA)
            drag_surf.fill((0, 255, 100, 25))
            surf.blit(drag_surf, self._drag_rect.topleft)
            pygame.draw.rect(surf, GREEN, self._drag_rect, 1)

    def draw_unit_selection(self, surf, world, cam):
        # Draw the 16-bit glitch boxes and Hex IDs
        font = pygame.font.SysFont("couriernew", 10)
        for uid in self.selected_uids:
            u = world.units.get(uid)
            if not u: continue
            
            sx, sy = cam.world_to_screen(u.gx, u.gy)
            # Glitchy bracket look
            offset = 12
            pygame.draw.lines(surf, (0, 255, 100), False, [(sx-offset, sy-offset+4), (sx-offset, sy-offset), (sx-offset+4, sy-offset)], 2)
            pygame.draw.lines(surf, (0, 255, 100), False, [(sx+offset, sy-offset+4), (sx+offset, sy-offset), (sx+offset-4, sy-offset)], 2)
            pygame.draw.lines(surf, (0, 255, 100), False, [(sx-offset, sy+offset-4), (sx-offset, sy+offset), (sx-offset+4, sy+offset)], 2)
            pygame.draw.lines(surf, (0, 255, 100), False, [(sx+offset, sy+offset-4), (sx+offset, sy+offset), (sx+offset-4, sy+offset)], 2)
            
            # Unique Hex ID
            hex_id = f"0x{uid:04X}"
            lbl = font.render(hex_id, True, (0, 255, 100))
            surf.blit(lbl, (sx + offset + 4, sy - offset))

    _order_marker = None

    def draw_order_marker(self, surf):
        if not self._order_marker:
            return
        mx, my, timer = self._order_marker
        self._order_marker = (mx, my, timer - 0.02)
        r = int(timer * 20)
        if r <= 0:
            self._order_marker = None
            return
        pygame.draw.circle(surf, (0, 255, 100), (mx, my), r, 1)
