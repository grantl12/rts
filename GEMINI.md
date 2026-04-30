# THE DEEP STATE: Project Status & Roadmap

## 🎯 Current Vision
A satirical isometric RTS built in **Python + pygame**. The game blends the weighted squad combat of *Company of Heroes* with the internal system depth of *FTL*, set in a "Post-Truth" world where "Auditing" is the primary weapon.

> Note: An earlier Godot 4.4 prototype exists in `client/` and is no longer being developed. All active code lives in `game/`.

---

## 🏗️ Architectural Progress

### 1. Core Systems (Implemented)
- **Isometric Renderer:** `game/renderer.py` — per-building palettes (top/wall_l/wall_r/accent/window), floor-height projection, `TILE_W=72 TILE_H=36 WALL_H=22`
- **A\* Pathfinding:** `game/pathfinding.py` — diagonal movement, formation spreading via `formation_goals(center, n)`
- **Unit Soul System:** `game/unit_entity.py` — `UNIT_DEFS` dict, STATE_IDLE/MOVING/ATTACK/DEAD, ROE damage scaling
- **Combat:** Auto-acquire nearest enemy at idle; attack range check; damage applied via ROE multiplier
- **Dynamic ROE (Rules of Engagement):** `game/roe.py` — 5 levels RESTRAINED→ABSOLUTE IMMUNITY; damage mults `[0.35, 0.65, 1.00, 1.50, 2.50]`; ambient infamy ticks; ROE 5 is irreversible (`is_butcher`)
- **Infamy System:** `ROEManager.infamy` — thresholds 200/400/750; killing civilians = +50 infamy
- **Civilian NPCs:** `game/civilian.py` — types NORMIE/PURPLE_HAIR/RIOT_GEAR/RUNNER/KIRK; wander, panic, capture by holding pens
- **Population Harvest:** `game/world.py` — pens auto-suck civs within 3.0 tiles; `PEN_INCOME_RATE=5 §/sec/occupant`
- **AI Factions:** `game/ai.py` — Sovereign + Oligarchy run production (12s), orders (6s), raids (25s) ticks
- **Fog of War:** `game/fog.py` — "Data Blackout" tile visibility system
- **Building Catalog:** `game/building_defs.py` — full catalog: Regency (9) · Frontline (3) · Sovereign (2) · Oligarchy (2) · Civilian (6) · Garrisonable (4)
- **Capture System:** Majority-faction rule; progress bar 0–100; contested buildings revert slowly
- **Production Queues:** `ProductionQueue` per factory; 8s per unit; auto-spawns at building exit tile
- **Camera:** `game/camera.py` — pan/zoom, `world_to_screen()`, `tile_diamond()` for click-hit-testing

### 2. The Quad — Current Map
- **`game/map_data.py`:** 28×24 terrain grid (VOID/GROUND/PATH/PLAZA/GRASS)
- **UVU campus layout** — Fulton Library · Engineering Center · Sorensen Center · Woodbury Business · Losee Center · Admin Building · Clock Tower · North Parking
- **KIRK_RALLY = (13.5, 12.0)** — plaza center where assassination occurred
- 25 civilians spawned at rally point with scatter on mission start
- Enemy AI (Sovereign + Oligarchy) spawn at tiles (5,5)

### 3. Interface (Implemented)
- **HUD:** `game/hud.py` — credits, infamy score, ROE name/color indicator
- **Sidebar:** `game/sidebar.py` — selected building/unit info, production queue display
- **Drag-box Selection:** `game/selection.py` — multi-unit select

---

## 🚀 Next Steps

### Phase 1: Tactical Polish
- [ ] **Selection UI:** 16-bit glitch selection boxes around selected units
- [ ] **Unit Visuals:** Distinct shapes/colors per unit type (Gravy Seal vs. ICE Agent vs. Proxy vs. Drone)
- [ ] **Suppression UI:** "Red Tape" bars above suppressed units
- [ ] **ROE Confirmation Dialog:** Second-click authorization before ROE 4→5 ("Absolute Immunity")

### Phase 2: Strategic Depth
- [ ] **Infamy Consequences:** SURVEILLED (≥400) spawns Frontline observer unit; SANCTIONED (≥750) freezes high-tier production
- [ ] **Runner HVP Sub-objectives:** 3 fast RUNNER civilians flee to fixed zones, trigger enemy ambush squads
- [ ] **Compliance Bus:** 30-seat escort unit, 3× credit multiplier on extraction to base
- [ ] **Executive Board:** Post-op meta-progression screen to spend Legacy Points on global buffs

### Phase 3: The Narrative Layer
- [ ] **Press Briefing UI:** Post-op spin tree (Gaslight / Double Down / Redact)
- [ ] **Post-op Allocation Screen:** Drag harvested civs into Bio-Metric DB / Infrastructure / PR silos
- [ ] **Narrative Events:** Scripted mid-mission "Leaks" that change objectives dynamically
- [ ] **Map Phase System:** `map_phase` int on world; visual scarring variants between campaign visits (Pristine → Scarred → Shattered)

### Phase 4: Vehicles & Advanced Units
- [ ] **Vehicle System:** `Vehicle` base class — Idle/Moving/Wrecked states; VBIED for Sovereign
- [ ] **BOLO Mechanic:** Per-mission FEMA-style target plate; ALPR Scanner unit scans civilian vehicles
- [ ] **Civilian NavMesh:** Route civilians around buildings instead of clipping through tiles
- [ ] **Multi-campaign Saves:** Regency / Frontline / Oligarchy slot selection; persistent world state between runs

---

## 📝 Developer Notes
- **Tone Mandate:** Keep it detached, corporate, and absurdly bureaucratic.
- **No Godot references** — `client/` is archived. All new features go in `game/`.
- **Building catalog:** Add new buildings to `game/building_defs.py` `BUILDINGS` dict only — no duplicate keys.
- **Infamy events:** `world.roe_manager.add_infamy(amount)` — always positive int.
- **Pathfinding:** `find_path(start_tuple, goal_tuple, blocked_set)` returns list of `(gx,gy)` tuples.
- **The "Mirror" Loop:** Every map must be playable and narratively distinct from at least two opposing factions.
