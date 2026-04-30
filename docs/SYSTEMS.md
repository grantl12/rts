# THE DEEP STATE — Master Systems Reference

> Authoritative list of every implemented system with code pointers.
> Update this when a system ships. If it's not here, it's not done.

---

## Unit System
**Files:** `game/unit_entity.py`

### Unit Types (`UNIT_DEFS`)
| ID | Faction | HP | Speed | Dmg | Range | Armor | Cost |
|---|---|---|---|---|---|---|---|
| `gravy_seal` | regency | 120 | 2.8 | 14 | 4.0 | light | 200 |
| `ice_agent` | regency | 180 | 2.2 | 18 | 3.5 | medium | 350 |
| `unmarked_van` | regency | 400 | 3.0 | 20 | 4.0 | medium | 450 |
| `proxy` | sovereign | 100 | 3.5 | 22 | 5.0 | light | 280 |
| `contractor` | oligarchy | 300 | 1.8 | 30 | 5.5 | heavy | 500 |
| `drone_scout` | frontline | 80 | 5.0 | 10 | 6.0 | light | 300 |
| `drone_assault` | frontline | 200 | 3.5 | 28 | 5.5 | medium | 550 |
| `protester` | neutral | 60 | 3.2 | 0 | — | unarmored | — |

### Armor Matchup Table
Attacker armor type vs. defender armor type → damage multiplier.
Defined in `ARMOR_MOD` dict. Key examples:
- heavy vs. unarmored: 2.5×
- light vs. heavy: 0.4×
- medium vs. medium: 1.0×

### Rank System
- Ranks 1–5: AGENT → EXECUTIVE
- +5 XP per attack, +25 XP per kill
- XP threshold doubles each rank (`xp_to_next *= 1.5`)
- On rank-up: +20% HP heal, +8% stats/rank bonus applied to damage
- `Unit.RANK_NAMES` holds display strings

### Suppression
- `unit.suppress(duration)` — sets `_suppress_timer`
- While suppressed: `_do_attack()` returns immediately (no firing)
- Renders "RED TAPE" bar above unit (`unit_entity.py:draw`)

### Low-HP Panic Retreat
- Triggers at <10% HP when not already moving
- Pathfinds to nearest friendly `command` building
- `unit_entity.py:update` — panic retreat block

### States
`STATE_IDLE / STATE_MOVING / STATE_ATTACK / STATE_DEAD`

---

## Building System
**Files:** `game/building_defs.py`, `game/world.py`

### Building Entry Keys (selected)
| ID | Name | Faction | Notable Flags |
|---|---|---|---|
| `reg_hq` | Regional HQ | regency | command, production |
| `reg_pen` | Compliance Pen | regency | holding_pen, garrison=12 |
| `reg_barracks` | Processing Center | regency | production |
| `reg_propaganda` | Propaganda Tower | regency | vision, relay |
| `sov_hq` | Revolutionary HQ | sovereign | command |
| `oli_hq` | Oligarchy HQ | oligarchy | command |
| `fro_hq` | Press Bureau HQ | frontline | command, infamy_amplify |
| `medical_center` | Medical Center | neutral | capturable |

### Capture Mechanic
- Unit within 2 tiles of enemy/neutral building → `capture_progress` increments
- Enemy units near building decrement progress
- At 100: ownership changes, fires `building_captured` world event

### Garrison
- Right-click building → `order_garrison(bid, waypoints)`
- On arrival: unit added to `pb.garrison[]`, `garrisoned_in = bid`
- Garrisoned units fire from windows at `attack_range * 1.3`

### Auras (in `world._tick_income`)
- `propaganda` flag: −2 infamy/tick to player if held by player
- `medical` flag: +2 HP/tick to garrisoned units

### Income
- `passive_income` per tick from owned buildings
- `PEN_INCOME_RATE × len(pb.garrison)` for holding pens

---

## Civilian System
**Files:** `game/civilian.py`

### Types
| Type | Speed | Visual | Notes |
|---|---|---|---|
| `normie` | 1.2 | grey circle | Standard pedestrian |
| `purple_hair` | 1.2 | purple circle | Higher infamy value if killed |
| `riot_gear` | 1.2 | orange circle | Resistant to panic |
| `runner` | 4.5 | yellow diamond | HVP; has a destination |
| `kirk` | 1.2 | white circle + glow | Special; assassination catalyst |

### Runner HVPs
- 3 spawned at intro end from `KIRK_RALLY`
- Destinations in `RUNNER_DESTINATIONS`: `[(2,2), (25,3), (26,20)]`
- On arrival → world spawns enemy ambush squad + 25 infamy
- Rendered with "HVP" label

### BOLO Target
- `world._bolo_uid` set at mission start to a random civilian
- `civilian.is_bolo = True` → pulsing red crosshair render
- On pen capture of BOLO civ → `bolo_captured` world event → +§500 bonus

### Panic
- `civilian.panic()` → 10s flee burst at 3.5 speed toward random tile
- Triggered by: ROE 5, Kirk assassination, direct damage
- Visual: red blink at 5Hz

---

## Infamy / ROE System
**Files:** `game/roe.py`, `game/world.py`

### ROE Levels
| Level | Name | Damage Mult | Ambient Infamy |
|---|---|---|---|
| 1 | RESTRAINED | 0.35× | none |
| 2 | ADMINISTRATIVE | 0.65× | none |
| 3 | STANDARD PROCEDURE | 1.00× | none |
| 4 | ESCALATED RESPONSE | 1.50× | +1/10s |
| 5 | ABSOLUTE IMMUNITY | 2.50× | +5/5s |

- ROE 5 requires Y/N confirmation overlay
- ROE 5 activates `is_butcher=True` (irreversible), +200 infamy, suppresses all enemies 8s, panics all civs

### Infamy Thresholds
| Threshold | Name | Consequence |
|---|---|---|
| 200 | SCRUTINIZED | Notification only |
| 400 | SURVEILLED | Frontline drone_scout spawns near center every 30s |
| 750 | SANCTIONED | Heavy-tier production frozen (contractor / drone_assault / unmarked_van) |

### Infamy Sources
- Civilian killed: +50 (`civilian.take_damage`)
- Civilian killed near infamy_amplify building (Press Bureau): +5 additional
- ROE 5 activation: +200
- Ambient: ROE 4 = +1/10s, ROE 5 = +5/5s

---

## Fog of War
**File:** `game/fog.py`

- Grid states: `SHROUD` (never seen) / `FOG` (seen, currently dark) / `VISION` (currently lit)
- Starts as FOG — map layout visible, enemies hidden
- Vision radii:
  - Standard unit: 10 tiles
  - `drone_scout`: 15 tiles
  - Command building: 16 tiles
  - `vision` flag building: 28 tiles
- Minimap dims FOG/SHROUD tiles

---

## AI System
**File:** `game/ai.py`

- One `AIFaction` per non-player faction
- Tick loop: produce (12s) → order units (6s) → raid pens (25s)
- Production: enqueues cheapest available unit if credits allow
- Order priority:
  1. Capture uncaptured objectives
  2. Attack nearest player unit
  3. Attack player HQ
- Raids: sends up to 3 units at player holding pens that contain civs
- Faction-aware: reads `world.player_faction`, no hardcoded strings

---

## World Events
**Produced in:** various (`world.py`, `civilian.py`, `unit_entity.py`)
**Consumed in:** `game/main.py` per-frame, then cleared

| Event key | Payload | Trigger |
|---|---|---|
| `building_captured` | `{name, old_faction, new_faction}` | Capture race complete |
| `building_destroyed` | `{name, faction}` | Building HP → 0 |
| `press_amplify` | `{building}` | Neutral killed near Press Bureau |
| `bolo_captured` | `{faction}` | BOLO civ enters player pen |
| `runner_arrived` | `{dest}` | Runner reaches destination |

---

## Post-Op Screen
**File:** `game/postop.py`

Two phases run sequentially:
1. **Allocation Screen** — detained civ count dragged into 3 silos:
   - Bio-Metric DB: +§150/unit
   - Infrastructure: +§2/sec (passive income bonus)
   - PR: −40 infamy/unit
2. **Press Briefing** — spin tree (Gaslight / Double Down / Redact); each choice has infamy/credit tradeoffs

---

## Main Menu
**File:** `game/menu.py`

- Terminal boot sequence (text scroll, flicker)
- 4 faction cards with keyboard nav (arrow keys, Enter)
- Returns selected faction string to `main.py`

---

## Notifications
**File:** `game/notifications.py`

- `NotificationManager.add(text, color)` — called from `main.py` after consuming world events
- Left-edge scrolling log, 6s lifetime, fade out over last 1s
- Max 8 visible at once; older entries scroll up

---

## UI Systems
**Files:** `game/hud.py`, `game/sidebar.py`, `game/selection.py`

### HUD (top bar)
- Credits (§) — faction color
- Clock (mission elapsed)
- ROE indicator — current level + name
- Power indicator — draw vs. capacity
- Infamy bar — color gradient with threshold ticks at 200/400/750

### Sidebar
- Minimap: faction-colored dots, camera viewport polygon, fog shading
- Left-click minimap → `cam.pan_to(gx, gy)` camera jump
- Build menu: per-faction `FACTION_BUILD_MENU` entries (structures + units)
- Single-unit info: rank stars, XP bar, state, stats
- Multi-unit info: up to 30 unit icons

### Selection
- Drag-box multi-select
- Double-click: selects all visible units of same type
- Right-click: move order (formation if multi), attack order if enemy target
- G key: garrison order for selected units
