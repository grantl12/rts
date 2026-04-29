# THE DEEP STATE — Source of Truth for Claude Sessions

> Keep this file current. Update it at the end of every meaningful session.
> Claude reads this first to avoid re-capping prior work.

---

## 🎯 Project Identity

**Engine:** Python · pygame · Isometric RTS  
**Coordinate system:** `iso.py` — TILE_W=72, TILE_H=36, WALL_H=22; 28×24 tile grid  
**Tone:** Detached, corporate, absurdly bureaucratic. Satire that earns it.  
**Working branch:** `claude/build-more-features-FEAzl`

> Note: An earlier Godot 4.4 prototype lives in `client/` and is no longer being actively developed.
> All new work goes in `game/`.

---

## 📖 Story Canon (locked)

### The Kirk Catalyst
Kirk — a prominent activist — is assassinated at a rally on **The Quad**. Every faction's presence on every map is a downstream consequence of this moment. The Regency's Deepfake monetizing his death is the mid-game reveal. The final mission destroys the servers housing the Kirk AI before the Oligarchy steals the code.

### Three-Campaign Architecture
Same maps, time-shifted POVs:

| Campaign | Faction | Vibe | Map State |
|---|---|---|---|
| **"The Administration"** | Regency | First Responders / Janitors | Pristine — your choices create the original scars |
| **"The Information War"** | Frontline | Insurgents / Observers | Scarred — arrives after Regency messed it up |
| **"The Salvage Operation"** | Oligarchy | Vultures | Shattered — picks through the ruins of both prior runs |

### Eight Factions
1. **Regency** (US/ICE) — Janitors, compliance, Administrative Credits, holding pens
2. **Frontline** (Ukraine-adj) — Information warfare, drone recording, viral funding windows
3. **Sovereign** (Iran-adj) — Chaos exploitation, VBIED, civilian shields, "Revolutionary Safehouses"
4. **Oligarchy** (Russia-adj) — Vultures, salvage, insurance payouts, "Staffing Agency" pens
5. **The Collective** (EU-adj) — International Observers; high infamy → sanctions freeze production
6. **The Syndicate** (Cartel-adj) — Black market, intercepts extraction routes, steals Compliance Buses
7. **The Tech-State** (Silicon Valley) — Kirk AI Deepfake, manages Fundraising Windows
8. **The Remnant** (Veteran-adj) — Rogue ex-Regency; Hero units to recruit or execute

### Map Evolution (3 visits per map)
- **Phase 1 Pristine** — Green, functional infrastructure, "Administrative" atmosphere
- **Phase 2 Scarred** — Barricades, scorched earth, persistent wrecks, "Managed Chaos"
- **Phase 3 Shattered** — Ruined buildings, black censor tarps, glitching UI, 60% Redaction Fog

### Post-Op Loop (meta-game, not yet built)
1. **Allocation Screen** — drag harvested civilians into Bio-Metric DB / Infrastructure / PR silos
2. **Press Briefing** — Gaslight / Double Down / Redact spin tree; redacting journalist costs +50 Infamy

---

## 🏗️ Current Code Architecture (`game/`)

### Entry Point
- `game/main.py` — pygame main loop, state machine (`STATE_PLAYING` / menus), event dispatch, `_point_in_poly` helper

### Coordinate System
- `game/iso.py` — `TILE_W=72, TILE_H=36, WALL_H=22`; `tile_to_screen(tx,ty,floor)`, `screen_to_tile(sx,sy)` transforms
- `game/camera.py` — pan/zoom; `world_to_screen(gx,gy,floor=0)`, `tile_diamond(gx,gy)` for hit testing

### World State
- `game/world.py` — `World` class: units dict, civilians dict, placed_buildings dict, credits per faction, ROE manager, AI factions
  - `place_building(bid, faction, gx, gy)` → creates `PlacedBuilding`, registers `ProductionQueue` if produces
  - `_place_map_buildings()` — loads `map_data.BUILDINGS` as neutral PlacedBuildings at mission start
  - `update(dt_ms)` — units, civilians, AI, capture logic, production queues, income tick, pen harvest
  - `enemies_of(faction)` — relation table for all 4 active factions

### Units
- `game/unit_entity.py` — `Unit` class: STATE_IDLE/MOVING/ATTACK/DEAD; `UNIT_DEFS` dict (utype→stats); ROE damage scaling
  - Stats tuple index: `[0]=hp, [1]=damage, [2]=speed, [3]=range, [4]=cost ...`
  - `order_move(waypoints)`, `order_attack(target_uid)`

### Buildings
- `game/building_defs.py` — `BUILDINGS` dict keyed by string ID; each entry has: `name, sub, category, faction, w, h, floors, cost, hp, power_draw, garrison, produces, description, palette, flags, roof_style`
  - Categories: `"base"` (faction-built) · `"civilian"` (neutral capturable) · `"garrisonable"`
  - Key flags: `"command"`, `"production"`, `"holding_pen"`, `"capturable"`, `"objective"`, `"vision"`, `"relay"`
  - `get_by_category(cat)`, `get_by_faction(faction)` helpers
  - **No duplicate keys** — `"reg_pen"` is the holding pen (garrison=12); `"reg_detention"` is the detention center

### Civilians
- `game/civilian.py` — `Civilian` class; types: `NORMIE / PURPLE_HAIR / RIOT_GEAR / RUNNER / KIRK`
  - `panic()` → 10s flee burst; `take_damage()` → big infamy hit on death
  - World pens auto-capture nearby civs at range 3.0 tiles

### AI
- `game/ai.py` — `AIFaction` class; timers for production (12s), orders (6s), raids (25s)
  - `_do_production()` — picks random factory, enqueues cheapest unit if credits allow
  - `_do_orders()` — priority: 1) uncaptured objectives 2) attack player units 3) attack player HQ
  - `_do_raids()` — targets player holding pens with up to 3 units

### ROE / Infamy
- `game/roe.py` — `ROEManager`; 5 levels (RESTRAINED→ABSOLUTE IMMUNITY)
  - Damage multipliers: `[0.35, 0.65, 1.00, 1.50, 2.50]`
  - ROE 5 is irreversible (`is_butcher = True`); panics all civs, halves enemy unit stats
  - Ambient infamy: ROE 4 = +1/10s, ROE 5 = +5/5s
  - Thresholds: 200 SCRUTINIZED / 400 SURVEILLED / 750 SANCTIONED

### Map Data
- `game/map_data.py` — 28×24 terrain grid (VOID/GROUND/PATH/PLAZA/GRASS); `BUILDINGS` list of pre-placed map structures; `KIRK_RALLY=(13.5,12.0)`
  - UVU campus buildings: Fulton Library (intel) · Engineering Center (tech) · Sorensen (command) · Woodbury Business (resource) · Losee Center (barracks) · Admin · Clock Tower (sensor) · North Parking (depot)

### Rendering
- `game/renderer.py` — isometric tile + building renderer; per-building palette (top/wall_l/wall_r/accent/window)
- `game/fog.py` — fog of war ("Data Blackout"); tile visibility array
- `game/hud.py` — top-bar HUD: credits, infamy, ROE indicator
- `game/sidebar.py` — right-panel sidebar; building/unit info, production queue display

### Input / Selection
- `game/selection.py` — drag-box multi-select; `SelectionManager`
- `game/pathfinding.py` — A* with diagonal movement; `find_path(start, goal, blocked)`; `formation_goals(center, n)` for squad spreading

---

## 🗺️ The Quad — Current Map State

**Terrain:** 28×24 grid, UVU campus layout  
**KIRK_RALLY:** (13.5, 12.0) — center plaza where assassination occurred  
**Pre-placed buildings:** 8 map structures loaded as neutral at mission start  
**Civilians:** 25 spawned at KIRK_RALLY with ±4 tile scatter at `World.__init__`  
**AI factions:** Sovereign + Oligarchy (both run production + order ticks)  
**Player faction:** Regency (starts with 5000 credits)

---

## 🚧 Pending / Next Up

### Bug fixes (done this session)
- [x] `civilian.py`: added `KIRK = "kirk"` constant (NameError fix)
- [x] `building_defs.py`: renamed duplicate `"reg_pen"` to `"reg_detention"`
- [x] `world.py`: removed corrupted duplicate lines at end of `_place_map_buildings`; added `unit_queues` registration for map buildings that produce
- [x] `ai.py`: completed `_do_orders` case 2 (attack player units / HQ fallback)

### Near-term gameplay
- [ ] Selection UI — 16-bit glitch selection boxes around selected units
- [ ] Unit visuals — distinct sprites/shapes per faction (Gravy Seal vs. Conscript vs. Proxy)
- [ ] Infamy consequences — SURVEILLED (≥400) spawns Frontline observer unit; SANCTIONED (≥750) freezes high-tier production
- [ ] Suppression UI — "Red Tape" bar above suppressed units
- [ ] ROE confirmation dialog — require second click at ROE 4→5 to prevent accidents
- [ ] Compliance Bus — 30-seat escort unit, 3× credit multiplier on extraction to base

### Narrative / campaign
- [ ] Runner HVP sub-objectives (3 fast civilians flee to fixed map zones, triggering ambushes)
- [ ] Press Briefing UI (post-op spin tree: Gaslight / Double Down / Redact)
- [ ] Post-op allocation screen (detained civs → Bio-Metric DB / Infrastructure / PR silos)
- [ ] Map Phase system — `map_phase` int; visual scarring on tiles/buildings between visits

### Architecture
- [ ] Civilian `NavigationAgent` equivalent — path around buildings instead of clipping through
- [ ] Vehicle system — `Vehicle` class with Idle/Moving/Wrecked states; VBIED for Sovereign
- [ ] BOLO mechanic — per-mission target plate; ALPR Scanner unit scans vehicles
- [ ] Multi-campaign save state (Regency / Frontline / Oligarchy slot selection)

---

## 🛠️ Conventions

- **All game code in `game/`** — `client/` is the retired Godot prototype, do not modify
- **Building catalog** — one key in `game/building_defs.py` `BUILDINGS` dict; no duplicate keys
- **Infamy events** → `world.roe_manager.add_infamy(amount)` — always pass a positive int
- **Pathfinding** → `find_path(start_tuple, goal_tuple, blocked_set)` — returns list of (gx,gy) tuples
- **Comments** — only the WHY, never the WHAT. No multi-line blocks.
- **Satire tone** — corporate detachment. "Voluntary Compliance Habitat", not "Prison".
