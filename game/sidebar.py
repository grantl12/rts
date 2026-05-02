"""
C&C-style build sidebar — two columns (structures left, units right).
Plugs into HUD's right panel area.
"""
import pygame
from game.building_defs import BUILDINGS as BDEF
from game.unit_entity   import UNIT_DEFS

TEAL    = (0, 255, 204)
TEAL_DIM= (0, 80, 60)
ORANGE  = (255, 102, 0)
DARK    = (6, 13, 10)
PANEL   = (10, 20, 16)
PANEL2  = (14, 28, 22)
BORDER  = (0, 50, 38)
GREEN   = (30, 180, 60)

# Buildings available to each faction in the sidebar
FACTION_BUILD_MENU = {
    "regency": {
        "structures": [
            "reg_power", "reg_barracks", "reg_depot",
            "reg_pen", "reg_tower", "reg_wall",
            "reg_propaganda", "reg_relay",
        ],
        "units": ["gravy_seal", "ice_agent", "ice_agent_tac", "proud_perimeter", "donor", "unmarked_van", "mrap", "compliance_bus", "patriot_lawyer"],
    },
    "frontline": {
        "structures": ["fl_drone", "fl_press", "fl_hacktivist"],
        "units": ["proxy", "drone_scout", "drone_assault", "drone_operator", "journalist", "agitator", "news_van"],
    },
    "sovereign": {
        "structures": ["sov_safehouse", "sov_cache", "sov_iron_dome"],
        "units": ["proxy", "contractor", "settler", "interpreter"],
    },
    "oligarchy": {
        "structures": ["olig_hq", "olig_salvage", "olig_troll"],
        "units": ["contractor", "gravy_seal", "wagner"],
    },
}

BTN_W  = 88
BTN_H  = 56
BTN_PAD= 6


class BuildSidebar:
    def __init__(self, faction="regency"):
        self.faction       = faction
        self.menu          = FACTION_BUILD_MENU.get(faction, {"structures": [], "units": []})

        # Active queues: {"type": "structure"|"unit", "id": str, "progress": 0-1, "timer": 0}
        self.struct_queue  = []   # list of {"id", "progress", "timer"}
        self.unit_queue    = []

        self._font_sm   = None
        self._font_med  = None
        self._font_px   = None

        self.panel_rect    = None   # set by HUD
        self.placing       = None   # building id being ghost-placed

    def _fonts(self):
        if not self._font_sm:
            self._font_sm  = pygame.font.SysFont("couriernew", 10)
            self._font_med = pygame.font.SysFont("couriernew", 12, bold=True)
            self._font_px  = pygame.font.SysFont("couriernew", 9)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt_ms, world, player_faction):
        dt = dt_ms / 1000.0
        underpowered = getattr(world, "power_balance", 0) < 0

        completed_struct = self._tick_queue(self.struct_queue, dt, build_time=15.0, stall=underpowered)
        completed_unit   = self._tick_queue(self.unit_queue,   dt, build_time=8.0,  stall=underpowered)

        return completed_struct, completed_unit

    def _tick_queue(self, queue, dt, build_time, stall=False):
        if not queue:
            return None
        item = queue[0]
        if not stall:
            item["progress"] += dt / build_time
        if item["progress"] >= 1.0:
            queue.pop(0)
            return item["id"]
        return None

    def _has_producer(self, utype, world, player_faction):
        """Return the PlacedBuilding that can produce utype, or None."""
        for pb in world.placed_buildings.values():
            if pb.faction == player_faction and utype in pb.bdef.get("produces", []):
                return pb
        return None

    def enqueue_structure(self, bid, world, player_faction):
        bdef = BDEF.get(bid)
        if not bdef:
            return False
        cost = bdef["cost"]
        creds = world.credits.get(player_faction, 0)
        if creds < cost:
            return False
        is_power = "power" in bdef.get("flags", [])
        if not is_power and getattr(world, "power_balance", 0) < 0:
            return False   # underpowered — must build power first
        world.credits[player_faction] -= cost
        self.struct_queue.append({"id": bid, "progress": 0.0})
        return True

    UNIT_QUEUE_CAP = 5

    def enqueue_unit(self, utype, world, player_faction):
        row = UNIT_DEFS.get(utype)
        if not row:
            return False
        if len(self.unit_queue) >= self.UNIT_QUEUE_CAP:
            return False   # queue full
        cost = row[7]
        creds = world.credits.get(player_faction, 0)
        if creds < cost:
            return False
        if not self._has_producer(utype, world, player_faction):
            return False   # no production building for this unit
        if getattr(world, "power_balance", 0) < 0:
            return False   # underpowered
        world.credits[player_faction] -= cost
        self.unit_queue.append({"id": utype, "progress": 0.0})
        return True

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, rect, world, player_faction):
        self._fonts()
        if rect is None:
            return []

        self.panel_rect = rect
        click_zones = []   # (pygame.Rect, "structure"|"unit", id)

        # Split rect into two columns
        col_w  = (rect.width - BTN_PAD * 3) // 2
        col_lx = rect.left + BTN_PAD
        col_rx = col_lx + col_w + BTN_PAD

        # Column headers
        hl = self._font_px.render("STRUCTURES", True, TEAL_DIM)
        hr = self._font_px.render("UNITS", True, TEAL_DIM)
        surf.blit(hl, (col_lx, rect.top + 2))
        surf.blit(hr, (col_rx, rect.top + 2))

        creds = world.credits.get(player_faction, 0)
        underpowered = getattr(world, "power_balance", 0) < 0

        # Draw buttons for structures
        sy = rect.top + 14
        for bid in self.menu["structures"]:
            bdef = BDEF.get(bid, {})
            cost = bdef.get("cost", 0)
            affordable = creds >= cost
            is_power = "power" in bdef.get("flags", [])
            locked = underpowered and not is_power
            brect = pygame.Rect(col_lx, sy, col_w, BTN_H)
            self._draw_btn(surf, brect, bdef.get("name", bid)[:12], cost, affordable and not locked,
                           bid in [q["id"] for q in self.struct_queue], locked)
            click_zones.append((brect, "structure", bid))
            sy += BTN_H + BTN_PAD

        # Draw buttons for units
        uy = rect.top + 14
        for utype in self.menu["units"]:
            row = UNIT_DEFS.get(utype)
            cost = row[7] if row else 0
            affordable = creds >= cost
            has_prereq = self._has_producer(utype, world, player_faction) is not None
            locked = not has_prereq or underpowered
            brect = pygame.Rect(col_rx, uy, col_w, BTN_H)
            self._draw_btn(surf, brect, utype.replace("_", " ").upper()[:12], cost,
                           affordable and not locked,
                           utype in [q["id"] for q in self.unit_queue], locked)
            click_zones.append((brect, "unit", utype))
            uy += BTN_H + BTN_PAD

        # Queue progress bars
        qy = max(sy, uy) + 8
        if self.struct_queue:
            self._draw_queue_bar(surf, col_lx, qy, col_w, self.struct_queue[0], "BLDG")
        if self.unit_queue:
            self._draw_queue_bar(surf, col_rx, qy, col_w, self.unit_queue[0], "UNIT")
            # Show queued items behind the active one
            if len(self.unit_queue) > 1:
                pending_y = qy + 26
                for qi in self.unit_queue[1:]:
                    lbl = self._font_px.render(
                        f"  + {qi['id'][:10].upper()}", True, (0, 100, 70))
                    surf.blit(lbl, (col_rx, pending_y))
                    pending_y += 12
            # Queue count indicator
            cap_lbl = self._font_px.render(
                f"{len(self.unit_queue)}/{self.UNIT_QUEUE_CAP}", True,
                (200, 80, 20) if len(self.unit_queue) >= self.UNIT_QUEUE_CAP else (0, 80, 60))
            surf.blit(cap_lbl, (col_rx + col_w - cap_lbl.get_width() - 2, qy))

        return click_zones

    def _draw_btn(self, surf, rect, name, cost, affordable, queued, locked=False):
        if locked:
            bg, border_col = (14, 10, 10), (40, 20, 20)
        elif queued:
            bg, border_col = (28, 20, 10), ORANGE
        elif affordable:
            bg, border_col = (16, 32, 24), TEAL
        else:
            bg, border_col = (20, 15, 12), (0, 40, 30)

        pygame.draw.rect(surf, bg, rect)
        pygame.draw.rect(surf, border_col, rect, 1)

        name_col = (60, 40, 40) if locked else (TEAL if affordable else TEAL_DIM)
        nl = self._font_px.render(name, True, name_col)
        surf.blit(nl, (rect.left + 4, rect.top + 4))

        cl = self._font_px.render(f"§{cost}", True, ORANGE if not affordable else (0, 180, 100))
        surf.blit(cl, (rect.left + 4, rect.top + 18))

        if locked:
            ll = self._font_px.render("LOCKED", True, (100, 40, 40))
            surf.blit(ll, (rect.left + 4, rect.top + 30))
        elif queued:
            ql = self._font_px.render("QUEUED", True, ORANGE)
            surf.blit(ql, (rect.left + 4, rect.top + 30))

    def _draw_queue_bar(self, surf, x, y, w, item, label):
        lbl = self._font_px.render(f"{label}: {item['id'][:10].upper()}", True, TEAL_DIM)
        surf.blit(lbl, (x, y))
        bar = pygame.Rect(x, y + 12, w, 8)
        pygame.draw.rect(surf, (20, 20, 20), bar)
        fill_w = int(bar.width * item["progress"])
        pygame.draw.rect(surf, (30, 180, 60), pygame.Rect(x, y + 12, fill_w, 8))
        pygame.draw.rect(surf, BORDER, bar, 1)

    def handle_click(self, pos, click_zones, world, player_faction):
        """Call with result of draw(). Returns ("place", bid) or ("spawned", utype) or None."""
        for rect, kind, iid in click_zones:
            if rect.collidepoint(pos):
                if kind == "structure":
                    ok = self.enqueue_structure(iid, world, player_faction)
                    if ok:
                        return ("queued_struct", iid)
                elif kind == "unit":
                    ok = self.enqueue_unit(iid, world, player_faction)
                    if ok:
                        return ("queued_unit", iid)
        return None
