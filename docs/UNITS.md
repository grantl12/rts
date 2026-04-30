# THE DEEP STATE — Unit Design

---

## Implemented Unit System

Current Python/pygame implementation. All values from `game/unit_entity.py:UNIT_DEFS`.

### Active Unit Roster

| ID | Faction | HP | Speed | Dmg | Range | Armor | Cost |
|---|---|---|---|---|---|---|---|
| `gravy_seal` | Regency | 120 | 2.8 | 14 | 4.0 | light | 200 |
| `ice_agent` | Regency | 180 | 2.2 | 18 | 3.5 | medium | 350 |
| `unmarked_van` | Regency | 400 | 3.0 | 20 | 4.0 | medium | 450 |
| `proxy` | Sovereign | 100 | 3.5 | 22 | 5.0 | light | 280 |
| `contractor` | Oligarchy | 300 | 1.8 | 30 | 5.5 | heavy | 500 |
| `drone_scout` | Frontline | 80 | 5.0 | 10 | 6.0 | light | 300 |
| `drone_assault` | Frontline | 200 | 3.5 | 28 | 5.5 | medium | 550 |
| `protester` | neutral | 60 | 3.2 | 0 | — | unarmored | — |

### Armor Matchup Table

| Attacker \ Defender | unarmored | light | medium | heavy |
|---|---|---|---|---|
| **light** | 1.5× | 1.0× | 0.7× | 0.4× |
| **medium** | 2.0× | 1.2× | 1.0× | 0.6× |
| **heavy** | 2.5× | 1.5× | 1.2× | 1.0× |

### Rank System (Implemented)

| Rank | Name | XP to next |
|---|---|---|
| 1 | AGENT | 100 |
| 2 | FIELD AGENT | 150 |
| 3 | SR. OPERATIVE | 225 |
| 4 | DEPT. HEAD | 337 |
| 5 | EXECUTIVE | — |

- +5 XP per attack landed, +25 XP per kill
- On rank-up: +20% HP heal, +8% damage bonus per rank
- Max rank 5 — no further XP accumulates

### Suppression (Implemented)

Called via `unit.suppress(duration)`. Sets `_suppress_timer` — unit cannot fire while suppressed. Renders "RED TAPE" progress bar above unit. Triggered by ROE 5 activation (all enemies suppressed 8s) and unit abilities.

### Low-HP Panic Retreat (Implemented)

At <10% HP: unit pathfinds to nearest friendly `command` building and retreats. Does not require orders.

---

## Design Intent — Unimplemented Systems

The following are design targets, not yet in code.

### The "Soul" System
Every unit has one Leader. If the Leader dies:
- Unit loses "Soul" — cannot gain XP for the rest of the mission
- Can still fight, but no rank progression

Planned implementation: `unit.has_soul = True` flag, cleared on leader death. Leader is the first unit of its type deployed in a given squad group.

### Morale / Bureaucracy
A second resource beneath HP. If Bureaucracy hits zero, unit "Self-Audits" (flees map permanently). Sources of Bureaucracy loss:
- Nearby friendly unit deaths
- ROE escalation events
- Propaganda Tower out of range for 60s+

Sources of Bureaucracy restoration:
- Rank-up
- Medical Center aura
- Advisor voice line events

*Not yet implemented. Placeholder: suppression covers the behavioral surface for now.*

### Supplies / Ammo
Third resource. When empty: unit reverts to melee range (range = 1.0), damage halved. Restocked by:
- Returning to friendly Barracks
- Compliance Bus depot variant (future)

*Not yet implemented.*

### The Hall of Heroes
Units that hit Rank 5 can be "Retired" between missions:
- Retired to **Hall of Heroes** → permanent global buff for that faction (+2% income, etc.)
- Retired to **Executive Board** → one-time powerful mission ability unlocked

*Not yet implemented. Requires campaign save state (see `docs/CAMPAIGN_STRUCTURE.md`).*

---

## Faction Unit Philosophy

### Regency — The Scalpel
*"Over-equipped, under-supervised, doing their job."*

Gravy Seals are the core infantry — light armor, decent range, cheap enough to field in numbers. ICE Agents are the heavy option within the light-tier. Unmarked Van is the Regency's "kill truck" — high HP, wide shape, area threat.

Planned: **Compliance Bus** (30-seat escort, 3× credit multiplier on civilian delivery — see `docs/COMPLIANCE_BUS.md`).

### Sovereign — The Chaos Agent
*"Proxy, contractor, and a car full of ideology."*

Proxy is fast, hits hard, dies easy. Sovereign's power comes from disruption, not sustained fire. Planned VBIED: a civilian car that detonates, causing area panic + damage. High infamy, high shock value.

### Oligarchy — The Grinder
*"You aren't a person. You're a buffer."*

Contractor is the tankiest unit in the game. Slow, expensive, unkillable in a fair fight. Oligarchy's economy is designed around absorbing losses and billing for them — see `docs/FACTION_ECONOMY.md`.

### Frontline — The Eye
*"If it's not filmed, it didn't happen."*

Drone Scout is the fastest unit with the largest vision radius (15 tiles). Drone Assault is a serious combat platform. Frontline's strength is information and timing — they see everything, then strike when the infamy camera is pointed elsewhere.

---

## Adding a New Unit Type

1. Add entry to `UNIT_DEFS` in `game/unit_entity.py`
2. Add polygon to `Unit._SHAPES`
3. Add to `FACTION_BUILD_MENU` in `game/sidebar.py`
4. Add to `FACTION_COLORS` if new faction
5. Add to AI production list in `game/ai.py:_do_production()` if AI-spawnable
