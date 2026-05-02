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
CYAN    = (0, 200, 255)

# Buildings available to each faction in the sidebar
FACTION_BUILD_MENU = {
    "regency": {
        "structures": [
            "reg_power", "reg_barracks", "reg_depot",
            "reg_pen", "reg_tower", "reg_wall",
            "reg_propaganda", "reg_relay",
        ],
        "units": ["gravy_seal", "ice_agent", "proud_perimeter", "donor", "unmarked_van", "mrap", "compliance_bus", "patriot_lawyer"],
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
        "units": ["contractor", "gravy_seal", "wagner", "direktor"],
    },
}

# One-time research upgrades per faction.
# Each entry: id (unique key), name, cost, base unit → upgraded unit, requires building flag
UNIT_UPGRADES = {
    "regency": [
        {
            "id":       "upg_tac_gear",
            "name":     "TAC GEAR",
            "desc":     "ICE AGENT → TAC",
            "cost":     350,
            "base":     "ice_agent",
            "upgraded": "ice_agent_tac",
            "requires": "reg_barracks",
        },
    ],
    "frontline": [],
    "sovereign": [],
    "oligarchy": [],
}

BTN_W  = 88
BTN_H  = 56
BTN_PAD= 6
UPG_H  = 28   # height of upgrade buttons


class BuildSidebar:
    def __init__(self, faction="regency"):
        self.faction       = faction
        self.menu          = FACTION_BUILD_MENU.get(faction, {"structures": [], "units": []})
        self.upgrades      = UNIT_UPGRADES.get(faction, [])

        self.struct_queue  = []   # list of {"id", "progress"}
        self.unit_queue    = []

        self._font_sm   = None
        self._font_med  = None
        self._font_px   = None

        self.panel_rect    = None
        self.placing       = None

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
        for pb in world.placed_buildings.values():
            if pb.faction == player_faction and utype in pb.bdef.get("produces", []):
                return pb
        return None

    def _resolve_tier(self, utype, world):
        """Return the actual unit type to produce, honoring any active upgrade."""
        return world.unit_tier.get(utype, utype)

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
            return False
        world.credits[player_faction] -= cost
        self.struct_queue.append({"id": bid, "progress": 0.0})
        return True

    UNIT_QUEUE_CAP = 5

    def enqueue_unit(self, utype, world, player_faction):
        actual = self._resolve_tier(utype, world)
        row = UNIT_DEFS.get(actual)
        if not row:
            return False
        if len(self.unit_queue) >= self.UNIT_QUEUE_CAP:
            return False
        cost = row[7]
        creds = world.credits.get(player_faction, 0)
        if creds < cost:
            return False
        # Check prereq against actual (upgraded) type — barracks lists both tiers
        if not self._has_producer(actual, world, player_faction):
            # Fall back: check if base type has a producer (handles legacy produces lists)
            if not self._has_producer(utype, world, player_faction):
                return False
        if getattr(world, "power_balance", 0) < 0:
            return False
        world.credits[player_faction] -= cost
        self.unit_queue.append({"id": actual, "progress": 0.0})
        return True

    def purchase_upgrade(self, upg, world, player_faction):
        """Buy a one-time unit upgrade. Returns True on success."""
        if upg["id"] in world.unit_tier:
            return False   # already purchased (key exists means base→upgraded set)
        creds = world.credits.get(player_faction, 0)
        if creds < upg["cost"]:
            return False
        # Check requires building
        req = upg.get("requires")
        if req:
            has_bld = any(req in pb.bid and pb.faction == player_faction
                          for pb in world.placed_buildings.values())
            if not has_bld:
                return False
        world.credits[player_faction] -= upg["cost"]
        world.unit_tier[upg["base"]] = upg["upgraded"]
        return True

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf, rect, world, player_faction):
        self._fonts()
        if rect is None:
            return []

        self.panel_rect = rect
        click_zones = []

        col_w  = (rect.width - BTN_PAD * 3) // 2
        col_lx = rect.left + BTN_PAD
        col_rx = col_lx + col_w + BTN_PAD

        hl = self._font_px.render("STRUCTURES", True, TEAL_DIM)
        hr = self._font_px.render("UNITS", True, TEAL_DIM)
        surf.blit(hl, (col_lx, rect.top + 2))
        surf.blit(hr, (col_rx, rect.top + 2))

        creds = world.credits.get(player_faction, 0)
        underpowered = getattr(world, "power_balance", 0) < 0

        # Structure buttons
        sy = rect.top + 14
        for bid in self.menu["structures"]:
            bdef = BDEF.get(bid, {})
            cost = bdef.get("cost", 0)
            affordable = creds >= cost
            is_power = "power" in bdef.get("flags", [])
            locked = underpowered and not is_power
            brect = pygame.Rect(col_lx, sy, col_w, BTN_H)
            self._draw_btn(surf, brect, bdef.get("name", bid)[:12], cost,
                           affordable and not locked,
                           bid in [q["id"] for q in self.struct_queue], locked)
            click_zones.append((brect, "structure", bid))
            sy += BTN_H + BTN_PAD

        # Unit buttons — resolve actual tier for cost/name display
        uy = rect.top + 14
        for utype in self.menu["units"]:
            actual = self._resolve_tier(utype, world)
            row = UNIT_DEFS.get(actual)
            cost = row[7] if row else 0
            affordable = creds >= cost
            # prereq check against actual type (with base fallback)
            has_prereq = (self._has_producer(actual, world, player_faction) is not None
                          or self._has_producer(utype, world, player_faction) is not None)
            locked = not has_prereq or underpowered
            is_upgraded = actual != utype
            queued = actual in [q["id"] for q in self.unit_queue]
            display = actual.replace("_", " ").upper()[:12]
            brect = pygame.Rect(col_rx, uy, col_w, BTN_H)
            self._draw_btn(surf, brect, display, cost,
                           affordable and not locked, queued, locked, is_upgraded)
            click_zones.append((brect, "unit", utype))
            uy += BTN_H + BTN_PAD

        # Queue progress bars
        qy = max(sy, uy) + 8
        if self.struct_queue:
            self._draw_queue_bar(surf, col_lx, qy, col_w, self.struct_queue[0], "BLDG")
        if self.unit_queue:
            self._draw_queue_bar(surf, col_rx, qy, col_w, self.unit_queue[0], "UNIT")
            if len(self.unit_queue) > 1:
                pending_y = qy + 26
                for qi in self.unit_queue[1:]:
                    lbl = self._font_px.render(
                        f"  + {qi['id'][:10].upper()}", True, (0, 100, 70))
                    surf.blit(lbl, (col_rx, pending_y))
                    pending_y += 12
            cap_lbl = self._font_px.render(
                f"{len(self.unit_queue)}/{self.UNIT_QUEUE_CAP}", True,
                (200, 80, 20) if len(self.unit_queue) >= self.UNIT_QUEUE_CAP else (0, 80, 60))
            surf.blit(cap_lbl, (col_rx + col_w - cap_lbl.get_width() - 2, qy))

        # Upgrade buttons strip
        if self.upgrades:
            upy = max(qy + 30, qy + 8)
            # header
            uh = self._font_px.render("RESEARCH", True, TEAL_DIM)
            surf.blit(uh, (col_lx, upy))
            upy += 11
            full_w = col_w * 2 + BTN_PAD
            for upg in self.upgrades:
                purchased = upg["base"] in world.unit_tier
                affordable = creds >= upg["cost"]
                req = upg.get("requires")
                has_bld = (not req or any(req in pb.bid and pb.faction == player_faction
                                          for pb in world.placed_buildings.values()))
                locked = not has_bld
                urect = pygame.Rect(col_lx, upy, full_w, UPG_H)
                self._draw_upgrade_btn(surf, urect, upg, purchased, affordable and not locked, locked)
                click_zones.append((urect, "upgrade", upg["id"]))
                upy += UPG_H + BTN_PAD

        return click_zones

    def _draw_btn(self, surf, rect, name, cost, affordable, queued, locked=False, upgraded=False):
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

        if upgraded:
            t2 = self._font_px.render("T2", True, CYAN)
            surf.blit(t2, (rect.right - t2.get_width() - 3, rect.top + 3))

    def _draw_upgrade_btn(self, surf, rect, upg, purchased, affordable, locked):
        if purchased:
            bg, border_col = (10, 28, 20), CYAN
        elif locked:
            bg, border_col = (14, 10, 10), (40, 20, 20)
        elif affordable:
            bg, border_col = (16, 32, 24), TEAL
        else:
            bg, border_col = (20, 15, 12), (0, 40, 30)

        pygame.draw.rect(surf, bg, rect)
        pygame.draw.rect(surf, border_col, rect, 1)

        label = upg["name"] + ("  [ACTIVE]" if purchased else f"  §{upg['cost']}")
        col = CYAN if purchased else (TEAL if affordable else TEAL_DIM)
        if locked:
            col = (60, 40, 40)
        lbl = self._font_px.render(label, True, col)
        surf.blit(lbl, (rect.left + 4, rect.top + 4))

        desc = self._font_px.render(upg.get("desc", ""), True, (0, 120, 80))
        surf.blit(desc, (rect.left + 4, rect.top + 14))

    def _draw_queue_bar(self, surf, x, y, w, item, label):
        lbl = self._font_px.render(f"{label}: {item['id'][:10].upper()}", True, TEAL_DIM)
        surf.blit(lbl, (x, y))
        bar = pygame.Rect(x, y + 12, w, 8)
        pygame.draw.rect(surf, (20, 20, 20), bar)
        fill_w = int(bar.width * item["progress"])
        pygame.draw.rect(surf, (30, 180, 60), pygame.Rect(x, y + 12, fill_w, 8))
        pygame.draw.rect(surf, BORDER, bar, 1)

    def handle_click(self, pos, click_zones, world, player_faction):
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
                elif kind == "upgrade":
                    upg = next((u for u in self.upgrades if u["id"] == iid), None)
                    if upg:
                        ok = self.purchase_upgrade(upg, world, player_faction)
                        if ok:
                            return ("upgrade_purchased", iid)
        return None
