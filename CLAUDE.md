# THE DEEP STATE — Source of Truth for Claude Sessions

> Keep this file current. Update it at the end of every meaningful session.
> Claude reads this first to avoid re-capping prior work.

---

## 🎯 Project Identity

**Engine:** Godot 4.4 · Forward Plus renderer · GDScript  
**Backend:** Supabase (REST + Realtime)  
**Tone:** Detached, corporate, absurdly bureaucratic. Satire that earns it.  
**Working branch:** `claude/build-more-features-FEAzl`

---

## 📖 Story Canon (locked)

### The Kirk Catalyst
Kirk — a prominent activist — is assassinated at a rally on **The Quad**. Every faction's presence on every map is a downstream consequence of this moment. The Regency's Deepfake monetizing his death is the mid-game reveal. The final mission destroys the servers housing the Kirk AI before the Oligarchy steals the code.

### Three-Campaign Architecture
Same maps, time-shifted POVs, shared world state via Supabase:

| Campaign | Faction | Vibe | Map State |
|---|---|---|---|
| **"The Administration"** | Regency | First Responders / Janitors | Pristine — your choices create the original scars |
| **"The Information War"** | Frontline | Insurgents / Observers | Scarred — arrives after Regency messed it up |
| **"The Salvage Operation"** | Oligarchy | Vultures | Shattered — picks through the ruins of both prior runs |

Playing Regency first → Russia campaign loads your exact wreck coordinates ("Ghost of the Player"). Playing Russia first → randomized chaos seed.

### Eight Factions
1. **Regency** (US/ICE) — Janitors, compliance, Administrative Credits, holding pens
2. **Frontline** (Ukraine-adj) — Information warfare, drone recording, viral funding windows
3. **Sovereign** (Iran-adj) — Chaos exploitation, VBIED, civilian shields, "Revolutionary Safehouses"
4. **Oligarchy** (Russia-adj) — Vultures, salvage, insurance payouts, "Staffing Agency" pens
5. **The Collective** (EU-adj) — International Observers; high infamy → sanctions freeze production
6. **The Syndicate** (Cartel-adj) — Black market, intercepts extraction routes, steals Compliance Buses
7. **The Tech-State** (Silicon Valley) — Kirk AI Deepfake, manages Fundraising Windows, throttles UI at low data points
8. **The Remnant** (Veteran-adj) — Rogue ex-Regency; Hero units to recruit or execute

### Map Evolution (3 visits per map)
- **Phase 1 Pristine** — Green, functional infrastructure, "Administrative" atmosphere
- **Phase 2 Scarred** — Barricades, scorched earth, persistent wrecks, "Managed Chaos"
- **Phase 3 Shattered** — Ruined buildings, black censor tarps, glitching UI, 60% Redaction Fog

### Post-Op Loop (meta-game, not yet built)
1. **Allocation Screen** — drag harvested civilians into Bio-Metric DB / Infrastructure / PR silos
2. **Press Briefing** — Gaslight / Double Down / Redact spin tree; redacting journalist costs +50 Infamy

### Vehicle Systems (planned)
- BOLO target per mission (FEMA/IPAWS flavor, anonymous federal aesthetic)
- ALPR Scouts scan plates; wrong audit → "Civil Rights Litigation" 30s freeze
- Sovereign VBIED paranoia — any civilian car could be a Sleeper
- Compliance Bus (30-seat escort objective, 3× credit multiplier)
- Wrecks persistent; Oligarchy can salvage them for scrap (removes cover)
- Vehicle flavor text on click: "Driving to a job that was automated six months ago."

---

## 🏗️ Current Code Architecture

### Autoloads (project.godot)
```
GameSession        — player/enemy faction, default unit paths
AdvisorManager     — faction-flavored VO lines, advisor_spoke signal
SupabaseManager    — REST helper (SUPABASE_URL, SUPABASE_KEY constants), hero upload/fetch
ResourceManager    — faction_funds dict, add_funds/spend_funds, resources_changed signal
AbilityManager     — Fact Check (Q) + Call Backup (E) abilities; relay station radius bonus
SoundManager       — play(key) dispatcher
InfamyManager      — global infamy int (0–1000), add/reduce/reset, get_tier(), infamy_changed signal
WorldStateManager  — Supabase world_state table R/W; record_raze/record_wreck; begin_mission/commit_state
```

### Key Scripts

#### Units
- `scripts/units/unit.gd` — core unit; `target_building` is **untyped** (var, not Building) to support duck-typed attacks on CivBuilding/HoldingPen
- `scripts/units/civilian.gd` — wandering CharacterBody3D; `get_captured()` / `panic()` for pen bust

#### Buildings
- `scripts/buildings/building.gd` — faction-owned placeable; BuildingResource-driven; produces units, passive income, AoE effects
- `scripts/buildings/civ_building.gd` — pre-placed neutral; capturable; buff types: income/supply/xp/morale; `_collapse()` fires InfamyManager +25 + WorldStateManager.record_raze
- `scripts/buildings/holding_pen.gd` — capturable; inner zone sucks in Civilian nodes; income = civs_held × rate; bust pays bounty, panics freed civs, fires InfamyManager +15

#### Managers
- `scripts/managers/infamy_manager.gd` — thresholds: 200 SCRUTINIZED / 400 SURVEILLED / 750 SANCTIONED
- `scripts/managers/world_state_manager.gd` — `begin_mission(map_id)` called from SkirmishManager._ready(); `commit_state()` called on game-over (TODO: wire up)
- `scripts/managers/skirmish_manager.gd` — spawns HQ + squads, AI tick, win/loss detection, calls WorldStateManager.begin_mission("the_quad")

#### UI
- `scripts/ui/game_hud.gd` — top bar: funds (left) + infamy bar (right, color-shifts red); bottom panels: unit selection, building panel, civ/pen panel (shared slot, mutually exclusive)
- `scripts/input_controller.gd` — handles Unit/Building/CivBuilding/HoldingPen clicks; B key = build menu; ESC = cancel

### Building Catalog Pattern
New building = one `.tres` file in `resources/buildings/`. The `_BUILD_CATALOG` array in `game_hud.gd` auto-generates the build menu — no other code changes needed.

Current catalog: Barracks · Watchtower · Supply Depot · Relay Station · Propaganda Tower · Field Hospital · Black Site · Fortification

#### BuildingResource fields
```gdscript
building_name, description, extra_group, cost, passive_income, max_health,
produces_units, producible_unit_path_override, produce_time,
effect_type, effect_radius, effect_interval
```

#### Extra groups wired up
- `"vision_tower"` → FogOfWarManager gives 48.0 radius (vs 28.0 default)
- `"relay_station"` → AbilityManager adds +8 Fact Check AoE per station
- `"cover"` → (planned) unit damage reduction when behind

### Fog of War
- `shaders/data_blackout.gdshader` — per-source `vis_radii[32]` array (not single uniform)
- `scripts/managers/fog_of_war_manager.gd` — pushes both `vis_positions` and `vis_radii` packed arrays

### Supabase Tables (live)
- `hero_units` — soul leader persistence (unit_type, faction, veterancy_rank, status)
- `world_state` — map persistence (map_id PK, razed_buildings jsonb, wreck_positions jsonb, infamy_score, updated_at)
  - **Required:** `map_id text PRIMARY KEY` with `resolution=merge-duplicates` Prefer header

---

## 🗺️ The Quad — Current Scene State

`scenes/maps/the_quad.tscn`

**Neutral capturable buildings (CivBuilding, 250 HP):**
- Campus Café (income) · Student Library (xp) · Medical Center (supply)

**Greek / Dorm houses (CivBuilding, 300 HP, brick-red, gold labels):**
- Δ Delta House (-22, z:-12) morale · Φ Phi House (+22, z:-12) xp
- Β Beta House (-22, z:+12) income · Σ Sigma House (+22, z:+12) supply

**Holding Pens (HoldingPen, 180 HP, 3–4 initial civs):**
- Voluntary Compliance Habitat (-8, z:-10) · Civic Realignment Suite (+8, z:+14)

**Civilians:** 6 wandering CharacterBody3D NPCs scattered across the central Quad area

**Audit Points:** THE QUAD (center) · NORTH PLAZA (z:-28) · SOUTH STEPS (z:+28)

**Spawn positions:** Player HQ (z:-40) / Enemy HQ (z:+40)

---

## 🚧 Pending / Next Up

### Immediate
- [ ] Wire `WorldStateManager.commit_state()` into game-over flow (skirmish_manager._on_building_destroyed)
- [ ] ROE system — global enum ROE 1–5; ROE 5 cuts music, sets `is_butcher` flag, max infamy event
- [ ] Infamy consequences — SURVEILLED tier spawns Frontline drone unit near player; SANCTIONED freezes high-tier unit production
- [ ] Post-op allocation screen (civilians → silo drag UI)
- [ ] `Civilian.gd` patrol behavior needs NavigationAgent3D or navmesh to avoid clipping through buildings

### Near-term
- [ ] Compliance Bus — high-capacity escort unit (30 civs), 3× credit multiplier on extraction
- [ ] Vehicle_Base.gd — Idle/Audited/Moving/Wrecked state machine; persistent wrecks as cover
- [ ] BOLO mechanic — per-mission FEMA target plate; ALPR Scout unit
- [ ] Map Phase system — `map_phase: int` on MapBase; visual scarring shader variants
- [ ] Press Briefing UI (post-op spin tree)

### Architecture
- [ ] Supabase world_state table creation (SQL in docs/ TBD)
- [ ] `commit_state()` call on mission end
- [ ] Multi-campaign save slot selection

---

## 🛠️ Conventions

- **No typed `Building` on `target_building`** — keep it `var` for duck-typed attacks
- **New neutral buildings** → extend `CivBuilding` or `HoldingPen`; add to the_quad.tscn directly
- **New faction buildings** → one `.tres` + one row in `_BUILD_CATALOG`
- **Infamy events** → always `InfamyManager.add_infamy(amount, "source_string")`
- **World scars** → always `WorldStateManager.record_raze(name)` + `record_wreck(asset_id, pos)` in `_collapse()`
- **Comments** — only the WHY, never the WHAT. No multi-line blocks.
- **Satire tone** — corporate detachment. Names like "Voluntary Compliance Habitat", not "Prison".
