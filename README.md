# THE DEEP STATE
> "In a post-truth world, the only thing more dangerous than a leak is an audit."

Satirical isometric RTS. You play as one of four factions fighting over a university campus after a politically inconvenient assassination. Civilians are the resource. The truth is negotiable.

Built in **Python 3 + pygame**. No game engine. No editor. No excuses.

---

## Install & Run

### Requirements
- **Python 3.8 or newer** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** (comes with Python)

### Step 1 — Get the code

If you have Git:
```bash
git clone https://github.com/grantl12/rts.git
cd rts
```

Or download the ZIP from GitHub → **Code → Download ZIP**, then unzip it somewhere and open a terminal in that folder.

### Step 2 — Install dependencies

```bash
pip install pygame-ce
```

> If that doesn't work, try `pip3 install pygame-ce` or `python -m pip install pygame-ce`

### Step 3 — Run

```bash
python -m game.main
```

> If that doesn't work, try `python3 -m game.main`

The window opens at **1280×800** (resizable). Run from the project root folder (the one that contains the `game/` directory).

### Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'pygame'` | Run `pip install pygame-ce` again |
| `ModuleNotFoundError: No module named 'game'` | Make sure you're in the project root, not inside `game/` |
| Black screen / crash on launch | Make sure you have Python 3.8+ (`python --version`) |
| Missing sprite assets | The `assets/` folder must be present next to `game/` — check it's not empty |

---

## Controls

| Input | Action |
|---|---|
| **WASD** / Arrow keys | Pan camera |
| **Mouse wheel** | Zoom |
| **Left click** | Select unit or building |
| **Double-click unit** | Select all of that type on screen |
| **Drag** | Box select multiple units |
| **Right click** | Move / attack order |
| **Q / E** | Unit ability |
| **1–5** | Set Rules of Engagement level |
| **B** | Open build menu |
| **G** | Garrison selected units into nearest building |
| **H** or **?** | Help overlay (full keybindings) |
| **F** | Toggle fog of war |
| **Tab** | Cycle through selected units |
| **Esc** | Deselect / cancel placement |

---

## What's in the Game

| System | Notes |
|---|---|
| Isometric renderer | Per-faction building palettes, floor height, fog of war |
| 4 playable factions | Regency, Frontline, Sovereign, Oligarchy — each with unique units + buildings |
| Unit combat | 14 unit types, armor matchups, rank 1–5, XP gain, hero name on rank-5 |
| Rules of Engagement | 5 ROE levels; ROE 5 requires confirmation; affects damage + infamy |
| Infamy system | SCRUTINIZED / SURVEILLED / SANCTIONED — escalating consequences |
| Civilian AI | Wander, panic, Witness War conversion states, Runner HVPs |
| Witness War | Civilians convert faction allegiance based on proximity — Empowered / Radicalized / Assetized |
| Building system | Capture, garrison, window fire, power grid, prereq-gated production |
| The Tape | Spawnable MacGuffin — holder faction gets +15% income |
| Compliance Bus | Auto-boards civilians, 3× credit payout on delivery |
| VBIED | Sovereign arms parked civilian cars every 50–90s |
| Fog of war | SHROUD / FOG / VISION tile grid; vision towers, command buildings |
| AI factions | Each AI faction runs produce → objectives → raid loops |
| Save system | 3-slot campaign saves, carry-over credits/infamy/hall of heroes |
| Hall of Heroes | Rank-5 units get procedural hero names, persist across missions |
| Post-op screen | Allocate detained civilians into 3 silos for meta-progression bonuses |
| Executive Board | Campaign meta layer — Legacy Point upgrades, hall of heroes display |

---

## Factions

| Faction | Role | Vibe |
|---|---|---|
| **Regency** | Campaign 1. You are the first responders / janitors. | ICE agents, compliance pens, bureaucratic suppression |
| **Frontline** | Campaign 2. Information warfare. | Drones, press bureau, viral funding, Witness War manipulation |
| **Sovereign** | Campaign 3 / AI antagonist. | Proxies, VBIEDs, chaos exploitation |
| **Oligarchy** | Campaign 3 alt. Vultures. | Contractors, salvage yards, insurance fraud |

---

## Project Layout

```
game/           Active game code (Python + pygame)
assets/         Sprite sheets, audio
docs/           Design documents
save/           Save slot files (auto-created)
client/         Archived Godot prototype — ignore this
```

---

## Docs (for contributors)

| File | Contents |
|---|---|
| `CLAUDE.md` | Source of truth — architecture, conventions, active task list |
| `game/GEMINI.md` | Gemini's scope and what to stay away from |
| `docs/SYSTEMS.md` | Every implemented system with code pointers |
| `docs/UNITS.md` | Unit design, faction roles, armor system |
| `docs/FACTION_DESIGNS.md` | Canonical faction designs v3 — the bible |
| `docs/CAMPAIGN_STRUCTURE.md` | Three-campaign architecture and save state design |
| `docs/BRAINSTORM.md` | Ideas overflow — pull from here when building features |
