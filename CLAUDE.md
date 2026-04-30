# THE DEEP STATE — Source of Truth for Claude Sessions

> Keep this file current. Update it at the end of every meaningful session.
> Claude reads this first to avoid re-capping prior work.

---

## 🎯 Project Identity

**Engine:** Python 3 + pygame 2 (isometric RTS)
**Working branch:** `master`
**Run:** `python -m game.main` from `/home/user/rts/`
**Resolution:** 1280×800 (RESIZABLE)

> Note: The Godot prototype (`client/`) is archived. The active game is the Python/pygame implementation in `game/`.

---

## 🗺️ Active Game Architecture

### Entry Point
`game/main.py` → `main()` → menu → game loop

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
| `game/pathfinding.py` | A* on 28×24 tile grid; `find_path` + `formation_goals` |
| `game/roe.py` | ROEManager: 5 levels, damage mults, infamy accrual |
| `game/ai.py` | AIFaction: produce, order objectives, raid player pens |
| `game/menu.py` | Main menu: terminal boot animation, 4 faction cards, keyboard nav |
| `game/postop.py` | Post-op allocation screen: detained civs → 3 silos |
| `game/notifications.py` | Left-edge scrolling event log with fade |
| `game/map_data.py` | Map terrain grid (28×24), static buildings, KIRK_RALLY coords |

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
- Regency: 8 structures, 3 units
- Frontline: 2 structures, 3 units
- Sovereign: 2 structures, 2 units
- Oligarchy: 2 structures, 2 units

---

## 🗺️ Map — "The Quad"

28×24 tile isometric grid
**KIRK_RALLY:** map center (~14, 12)
**Enemy base:** (3, 2) — reg_hq + reg_barracks (pre-placed for enemy faction)
**Player spawn:** (13, 19) — starter squad after intro

**Pre-placed neutral buildings** (from map_data.BUILDINGS → world._place_map_buildings):
- Campus Café, Student Library, Medical Center, Delta/Sigma Houses, Audit Points, etc.

---

## 🚧 Pending / Next Up

### Near-term gameplay
- [ ] Double-click unit to select all of that type visible on screen
- [ ] Unit kill grant extra XP (currently only attack XP, not kill XP)
- [ ] Press briefing mini-game after post-op (Gaslight/Double Down/Redact spin tree)
- [ ] BOLO mechanic — per-mission civilian target, ALPR Scout unit
- [ ] Compliance Bus — 30-seat escort objective, 3× credit multiplier

### Vehicle Systems (planned)
- Vehicle_Base: Idle/Audited/Moving/Wrecked states
- Sovereign VBIED — civilian car paranoia mechanic
- Wrecks persistent; Oligarchy can salvage them

### Architecture
- [ ] Multiple map phases (map_phase: pristine/scarred/shattered visual variants)
- [ ] Main menu satellite thermal view background
- [ ] Supabase world_state persistence (razed buildings, wreck positions)

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
