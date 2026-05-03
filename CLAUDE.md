# THE DEEP STATE — Source of Truth for Claude Sessions

> Keep this file current. Update it at the end of every meaningful session.
> Claude reads this first to avoid re-capping prior work.

---

## 🎯 Project Identity

**Engine:** Python 3 + pygame 2 (isometric RTS)
**Working branch:** `master`
**Run:** `python -m game.main` from project root (Windows: `D:\Users\grant\Documents\RTS\`)
**Resolution:** 1280×800 (RESIZABLE)

> Note: The Godot prototype (`client/`) is archived. The active game is the Python/pygame implementation in `game/`.

---

## 🗺️ Active Game Architecture

### Entry Point
`game/main.py` → `main()` → menu → slot select → **theater select** → game loop

### Core Module Map
| File | Responsibility |
|---|---|
| `game/main.py` | Game loop, intro sequence, event dispatch, draw orchestration |
| `game/world.py` | Units, buildings, civilians, AI, income, capture, events |
| `game/unit_entity.py` | Unit stats, update, combat, suppression, draw (polygon shapes) |
| `game/civilian.py` | Civilian NPC: wander, panic, runner HVP logic, pathfinding |
| `game/building_defs.py` | Full building catalog (40+ buildings across 4 factions) |
| `game/camera.py` | Iso pan/zoom; `pan_to(gx,gy)` centers on world tile |
| `game/fog.py` | Fog of war: SHROUD/FOG/VISION grid; vision tower/command building radii |
| `game/renderer.py` | Terrain, buildings, minimap (faction dots + camera viewport) |
| `game/hud.py` | Top bar (ROE/credits/clock), sidebar (minimap, building info, infamy bar) |
| `game/sidebar.py` | Build menu: structures + units, per-faction FACTION_BUILD_MENU |
| `game/selection.py` | Drag-box select, right-click orders, formation move, garrison order |
| `game/pathfinding.py` | A* on 56×44 tile grid; `find_path` + `formation_goals` |
| `game/roe.py` | ROEManager: 5 levels, damage mults, infamy accrual |
| `game/ai.py` | AIFaction: produce, order objectives, raid player pens |
| `game/menu.py` | Main menu: terminal boot animation, 4 faction cards, keyboard nav |
| `game/postop.py` | Post-op allocation screen: detained civs → 3 silos |
| `game/notifications.py` | Left-edge scrolling event log with fade |
| `game/map_data.py` | Map 1 terrain (56×44), static buildings, KIRK_RALLY — **mutated in-place on map swap** |
| `game/map_data_2.py` | Map 2 "Whipple District" terrain, buildings, incident coords |

---

## 📖 Story Canon (locked)

### The Kirk Catalyst
Kirk — a prominent activist — is assassinated at a rally on **The Quad**. Every faction's presence is a downstream consequence.

### Three-Campaign Architecture
| Campaign | Faction | Vibe |
|---|---|---|
| **"The Administration"** | Regency | First Responders / Janitors |
| **"The Information War"** | Frontline | Insurgents / Observers |
| **"The Salvage Operation"** | Oligarchy | Vultures |

### Eight Factions (4 playable)
1. **Regency** — Gravy Seals, ICE Agents, Compliance Pens, MRAP
2. **Frontline** — Drone Scouts, Drone Assault, Press Bureau (amplifies player infamy)
3. **Sovereign** — Proxy, Contractor, VBIED
4. **Oligarchy** — Contractor, Salvage Yard, "Staffing Agency" pens

---

## 🏗️ Current Implemented Systems

### Unit System (`unit_entity.py`)
- 8 unit types with distinct polygon shapes per type
- Armor type matchup table (light/medium/heavy/unarmored → damage mults)
- Rank system 1–5: XP gain per attack, 20% HP heal on rank-up, +8% stats/rank
- Suppression: `suppress(duration)` → RED TAPE bar above unit, blocks attacks
- ROE damage multiplier applied to all Regency attacks
- States: idle / moving / attacking / dead

### Building System (`building_defs.py`, `world.py`)
- 40+ buildings: Regency, Frontline, Sovereign, Oligarchy, civilian/neutral
- Capture mechanic: unit proximity race to 100 progress, fires `building_captured` event
- Garrison: units enter buildings via right-click + `order_garrison()`; fire from windows
- Auras implemented: propaganda tower (−2 infamy/tick), medical center (+2 HP/tick)
- Income: passive_income per tick + PEN_INCOME_RATE × civs_held
- Vision towers: `vision` flag → 28-tile fog radius; command buildings → 16r

### Civilian System (`civilian.py`)
- 4 types: normie, purple_hair, riot_gear, runner (HVP)
- Civilians panic when ROE 5 or Kirk is shot
- A* pathfinding in `_wander_logic` (routes around buildings)
- **Runner HVPs**: 3 spawned at intro end from KIRK_RALLY to RUNNER_DESTINATIONS
  - On arrival at destination → enemy ambush squad spawns (+25 infamy)
  - Rendered as yellow diamond + "HVP" label

### Infamy System (`roe.py`, `world.py`)
- **SCRUTINIZED (200):** notification only
- **SURVEILLED (400):** Frontline drone_scout spawns near map center every 30s
- **SANCTIONED (750):** heavy-tier production frozen (contractor/drone_assault/unmarked_van)
- **Frontline Press Bureau** (infamy_amplify flag): +5 infamy per neutral killed within 12 tiles
- Propaganda Tower: −2 infamy/tick if held by player
- Infamy bar: tier markers + color-coded threshold ticks in HUD

### ROE System
- Levels 1–5: RESTRAINED (0.35×) → ABSOLUTE IMMUNITY (2.5×)
- **ROE 5 requires Y/N confirmation overlay** before activating
- ROE 5: is_butcher=true, +200 infamy, suppresses all enemies 8s, panics all civs
- Ambient infamy: ROE 4 = +1/10s, ROE 5 = +5/5s

### Fog of War (`fog.py`)
- Starts as FOG (map layout visible, enemies hidden)
- VISION sources: units (10r, drone_scout 15r), command buildings (16r), vision towers (28r)
- Minimap shows fog state with dimming

### AI (`ai.py`)
- Per-faction AIFaction tick: produce → order → raid
- Priorities: capture objectives → attack nearest player unit → attack player HQ
- Uses world.player_faction (no hardcoded "regency")
- Raids specifically target player holding pens with civs

### Win/Loss
- `world.game_over`: GAME_OVER_DEFEAT (player HQ gone) / GAME_OVER_VICTORY (enemy HQ gone)
- Either state triggers post-op debrief screen then exits

### Post-Op Screen (`postop.py`)
- Shows: mission time, infamy, detained civ count
- 3 silos: Bio-Metric DB (+§150/unit), Infrastructure (+2§/sec), PR (−40 infamy)
- Click +/− to allocate; FILE REPORT closes

### Notifications (`notifications.py`)
- NotificationManager: left-edge scrolling log, 6s lifetime, fade out
- Triggered by: building captured/lost/destroyed, unit deployed, structure ready,
  infamy thresholds (SCRUTINIZED/SURVEILLED/SANCTIONED), press bureau recording

### World Events (`world.events`)
- `building_captured` — name, old faction, new faction
- `building_destroyed` — name, faction
- `press_amplify` — building name
- Consumed each frame by main.py, then cleared

### UI Improvements
- **Info bar**: single-unit shows rank stars + XP bar + state + stats; multi-unit shows 30 icons
- **Help overlay**: H or ? toggles full keybinding reference (5 sections)
- **Minimap**: faction-colored unit dots + buildings + camera viewport polygon + fog shading
- **Minimap click**: left-click minimap → camera jumps to tile (uses `cam.pan_to()`)
- **Capture bars**: yellow progress bar floats above being-captured buildings
- **HUD infamy bar**: threshold tick marks at 200/400/750 with color labels

### Build Menu (`sidebar.py`)
All 4 factions have `FACTION_BUILD_MENU` entries:
- Regency: 8 structures, 8 units (gravy_seal, ice_agent, ice_agent_tac, proud_perimeter, unmarked_van, mrap, compliance_bus, patriot_lawyer)
- Frontline: 2 structures, 7 units (proxy, drone_scout, drone_assault, drone_operator, journalist, agitator, news_van)
- Sovereign: 2 structures, 2 units (proxy, contractor)
- Oligarchy: 3 structures, 3 units (contractor, gravy_seal, wagner)

**Unit prereq system**: Units can only be queued if the player owns a building with that unit in its `produces` list. Buttons show `LOCKED` when prereq or power is missing. Queues stall (no progress) when `world.power_balance < 0`. Completed units spawn adjacent to their producing building, not at a hardcoded tile.

**Structures**: Cannot be queued when `power_balance < 0` unless the building has the `power` flag (power substations are always buildable).

### New unit types (latest session)
| Unit | Faction | Role | Special |
|---|---|---|---|
| `wagner` | oligarchy | §60 cannon fodder | Triangle shape, high turnover |
| `journalist` | frontline | §250 support | 0 dmg; killing grants +30 infamy; doubles capture speed in 5r |
| `agitator` | frontline | §200 support | Megaphone aura: burns suppress timer 2× for nearby allies |
| `proud_perimeter` | regency | §380 melee tank | Intercepts suppression from nearby allies (takes 50% of it) |

### New buildings (latest session)
| Building | Faction | Effect |
|---|---|---|
| `olig_troll` | oligarchy | "Troll Farm" — erodes enemy capture progress in 10r passively |

### Q/E abilities are faction-specific
- **Regency**: Q = Red Tape Burst (suppress burst, 20s), E = Stimulus Drop (2 gravy seals, §200, 45s)
- **Frontline**: Q = Crowdfunding Surge (+§300, 30s), E = Drone Overwatch (area suppress 8r, 40s)
- **Oligarchy**: Q = Meat Grinder (5 wagners, §100, 35s), E = Kickback (steal §150 from nearest enemy, 50s)
- **Sovereign**: Q = Black Market (+§250, 25s), E = Shadow Cell (2 proxies, §150, 45s)

### `building_defs.py` — `produces` field (canonical)
| Building | Produces |
|---|---|
| `reg_barracks` | gravy_seal, ice_agent, ice_agent_tac, proud_perimeter, patriot_lawyer |
| `reg_depot` | unmarked_van, mrap, compliance_bus |
| `fl_drone` | drone_scout, drone_assault, drone_operator |
| `fl_press` | proxy, news_van, journalist, agitator |
| `sov_safehouse` | proxy |
| `sov_cache` | proxy, vbied |
| `olig_hq` | contractor, gravy_seal, wagner |
| `olig_troll` | (none — passive aura building) |

---

## 🗺️ Maps

### Map 1 — "The Quad" (`game/map_data.py`)
56×44 tile isometric grid
**KIRK_RALLY:** (14.0, 12.0) — map center
**Enemy base:** (3, 2) — reg_hq + reg_barracks pre-placed
**Player HQ placed:** (46, 37) at intro end; starters spawn (43, 38)
**Runner destinations:** hardcoded in `game/civilian.py` RUNNER_DESTINATIONS

### Map 2 — "Whipple District" (`game/map_data_2.py`)
56×44 tile isometric grid (same dimensions — required for pathfinding W/H)
**Incident point (KIRK_RALLY):** (29.0, 16.5) — Aurora Ave compliance check
**SUV crash target:** (29.0, 13.0) — lurches north into civic plaza
**Player HQ placed:** (30, 36) at intro end; starters spawn (28, 37)
**Enemy spawn:** 3 proxies at (50, 3) — northeast staging
**Runner destinations:** (52,2), (2,42), (52,40)
**Win condition:** NG arrival timer at T=300s spawns reinforcements at (42,11) + triggers GAME_OVER_VICTORY
**Key buildings:** Whipple Federal Bldg (40,1), ICE Field Office (47,1), NG Armory (40,10), Federal Courthouse (27,1)

### Map swap mechanism
`_run_mission()` mutates `game.map_data` **in place** so renderer.py and pathfinding.py (which bind TERRAIN at import time) see new data:
- `_MAP_MOD.TERRAIN[:] = new_terrain` — list in-place
- `_MAP_MOD.BUILDINGS[:] = new_buildings` — list in-place
- `_MAP_MOD.BTYPE_COLORS.clear(); .update(...)` — dict in-place
- `_MAP_MOD.KIRK_RALLY = new_val` + `global KIRK_RALLY; KIRK_RALLY = new_val` — tuple reassign
- `world = World(..., map_module=_active_map)` — World reads KIRK_RALLY from map_module

---

## 🚧 Pending / Next Up

### Implemented (prior sessions)
- [x] Hall of Heroes, Tape MacGuffin, Witness War, VBIED AI, campaign save slots (3-slot JSON)
- [x] Thermal menu background, legibility pass, unit spawn prereq system
- [x] Wagner, Journalist, Agitator, Proud Perimeter units; Troll Farm building
- [x] Faction-specific Q/E/R abilities (all 4 factions)
- [x] Faction research upgrades (2 per faction in UNIT_UPGRADES)
- [x] Minimap vehicle dots, hero name in info bar, aura rings (units + buildings)
- [x] Iron Dome interception notification, MISSION COMPLETE/FAILED splash

### Implemented this session (2026-05-02)
- [x] **Whipple District map** (`map_data_2.py`) — 56×44 urban grid, 17 pre-placed buildings, Aurora Ave road network
- [x] **Theater select screen** (`_pick_theater()`) — shown after slot select, [1]/[2]/arrow keys
- [x] **District intro state machine** — d_approach → d_check → d_shot → d_crash → d_panic → end
  - ICE officer typewriter dialogue during d_check
  - Animated SUV ellipse crashes north toward `INCIDENT_SUV_CRASH_TARGET` during d_crash
  - Permanent wreck placed at crash position; civilians in 12r panic
  - Overlay text: "AURORA AVE — 09:14 LOCAL" / "SHOTS FIRED — NARRATIVE CONTAINMENT ACTIVE"
- [x] **NG arrival timer** — 300s countdown; spawns 3 gravy seals + MRAP at NG Armory → GAME_OVER_VICTORY
- [x] **Map-aware labels** — incident marker says "COMPLIANCE CHECK" / "AURORA AVE — INCIDENT" on district
- [x] **Runner destinations** pulled from `_active_map.RUNNER_DESTINATIONS` (not hardcoded import)

### Next up
- [ ] Faction renames (backlog): Oligarchy → Direktorate — deferred, keep internal keys
- [ ] Visual upgrade tiers — 3 sprite tiers per unit, swap on rank-up — needs asset pipeline
- [ ] Wrecks persistent across sessions — currently lost on mission exit
- [x] District AI tuning — `map_data` / `map_data_2` define `AI_*` spawn and interval multipliers; `AIFaction` + frontline/regency district behavior
- [x] NG arrival — `advisor.trigger("ng_arrival_district")` + `AI_NG_*` spawns; Whipple copy in `advisor.py`

---

## 🛠️ Conventions

- **No comments** unless WHY is non-obvious
- **Building auras** → implement in `world._tick_income()`
- **World events** → append to `world.events`, consume in main.py per-frame
- **New notification** → `notifs.add(text, color)` in main.py update section
- **New building** → one entry in `building_defs.BUILDINGS`, add to `FACTION_BUILD_MENU` in sidebar.py
- **New unit type** → add to `UNIT_DEFS` + `Unit._SHAPES` in unit_entity.py
- **Camera centering** → `cam.pan_to(gx, gy)`
- **Pathfinding** → `find_path((sx,sy), (gx,gy), world.blocked_tiles())`
