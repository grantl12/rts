# THE DEEP STATE
> "In a post-truth world, the only thing more dangerous than a leak is an audit."

Satirical isometric RTS. You are the Regency. Your job is containment. The civilians are the resource. The press is the enemy.

Built in **Python 3 + pygame 2**. No engine, no editor, no excuses.

---

## Run

```bash
pip install pygame
python -m game.main
```

Resolution: 1280×800 (resizable). From the project root.

> Note: A Godot 4.4 prototype lives in `client/` — it is archived. All active development is in `game/`.

---

## What's Implemented

| System | Status |
|---|---|
| Isometric renderer (terrain, buildings, per-faction palettes) | ✅ |
| A* pathfinding with formation spreading | ✅ |
| 8 unit types, armor matchup table, rank 1–5 w/ XP | ✅ |
| Suppression ("Red Tape" bar), low-HP panic retreat | ✅ |
| ROE levels 1–5, damage mults, ROE 5 confirmation dialog | ✅ |
| Infamy system: SCRUTINIZED / SURVEILLED / SANCTIONED | ✅ |
| Civilian AI: wander, panic, A* around buildings | ✅ |
| Runner HVPs: 3 per map, destinations trigger enemy ambush | ✅ |
| BOLO target: one civilian marked per mission, bonus on capture | ✅ |
| Building capture, garrison, window fire | ✅ |
| Building auras: propaganda tower (−infamy), medical (+HP) | ✅ |
| Power system, power draw tracking | ✅ |
| Fog of war (SHROUD/FOG/VISION), minimap with fog shading | ✅ |
| AI factions: produce → order objectives → raid pens | ✅ |
| Win/loss detection (HQ destruction) | ✅ |
| Main menu: terminal boot animation, faction card select | ✅ |
| Post-op screen: detained civ allocation to 3 silos | ✅ |
| Press briefing: Gaslight / Double Down / Redact spin tree | ✅ |
| Notification log (left edge, fade) | ✅ |
| Double-click type-select, drag-box multi-select | ✅ |
| Unit abilities (Q/E keys), ability HUD | ✅ |
| Help overlay (H / ?) | ✅ |
| Compliance Bus | ⬜ |
| Vehicle system (VBIED, wrecks, salvage) | ⬜ |
| Map phase system (pristine / scarred / shattered) | ⬜ |
| Campaign save state (3 faction slots) | ⬜ |

---

## Factions

| Faction | Role | Economy |
|---|---|---|
| **Regency** | Player (Campaign 1). ICE / bureaucratic compliance. | Administrative Credits |
| **Frontline** | Player (Campaign 2). Information warfare, drones, viral funding. | Fundraising Windows |
| **Oligarchy** | Player (Campaign 3). Salvage, conscription, insurance payouts. | Staffing Agency pens |
| **Sovereign** | AI antagonist. Chaos exploitation, proxy units, VBIED. | Revolutionary Safehouses |

The Collective, Syndicate, Tech-State, and Remnant are ambient/event factions — not yet playable.

---

## Controls

| Key | Action |
|---|---|
| WASD / Arrow keys | Pan camera |
| Mouse wheel | Zoom |
| Left click | Select unit |
| Double-click unit | Select all of that type on screen |
| Drag | Box select |
| Right click | Move / attack order |
| Q / E | Unit ability |
| 1–5 | ROE level |
| B | Build mode |
| H / ? | Help overlay |
| F | Fog of war toggle |
| G | Garrison selected units |
| Tab | Cycle selected units |
| Esc | Deselect / cancel |

---

## Docs

| Doc | Contents |
|---|---|
| `CLAUDE.md` | Session source of truth — architecture, conventions, pending work |
| `docs/SYSTEMS.md` | Master reference: every implemented system with code pointers |
| `docs/UNITS.md` | Unit design, faction roles, armor system |
| `docs/FACTION_ECONOMY.md` | How each faction interacts with the civilian population |
| `docs/MAPS.md` | Theater list and design status |
| `docs/MAP_EVOLUTION.md` | Map phase system design (pristine/scarred/shattered) |
| `docs/COMPLIANCE_BUS.md` | Compliance Bus feature spec |
| `docs/CAMPAIGN_STRUCTURE.md` | Three-campaign architecture, save state, progression |
| `docs/VEHICLE_LOGIC.md` | Vehicle system design (ALPR, VBIED, wrecks) |
| `docs/STORYBOARD.md` | Mission storyboards per campaign |
| `docs/ADVISOR.md` | In-game advisor (The Auditor) scripts |
| `docs/BRAINSTORM.md` | Running ideas overflow — pull from here when building features |
