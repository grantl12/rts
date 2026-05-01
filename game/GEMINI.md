# THE DEEP STATE — Gemini Session Brief

> Keep this file current. Read it before every session.

---

## What This Project Is

**Python 3 + pygame-ce isometric RTS.** Satirical. Four factions. One campus assassination. Civilians are the resource.

- **Run:** `python -m game.main` from project root
- **Resolution:** 1280×800 (resizable)
- **Python target:** 3.8+ (use `Optional[X]` not `X | None`, add `from __future__ import annotations` if needed)

The `client/` folder is an archived Godot prototype. **Do not touch it.**

---

## Your Lane

Gemini owns **asset generation and visual content**:

- Sprite sheets (unit sprites, building tiles, UI icons)
- Sound effects and audio cues
- Map terrain tiles and visual variants (pristine / scarred / shattered phases)
- Flavor text — building descriptions, advisor lines, unit dossiers, faction lore
- Design docs in `docs/` — brainstorm, unit dossiers, faction lore bibles

**Leave the main game code alone.** Claude owns the Python/pygame codebase. The architecture is intricate and interconnected — well-intentioned edits to `game/*.py` without full session context cause regressions that take time to untangle. If you see something broken in the code, document it in `docs/BRAINSTORM.md` and flag it rather than patching it directly.

---

## Current Sprite Sheet Format

All unit sprites are in `assets/` as JPEGs (grey background, 1024×559px or similar).

**Standard layout:** 4 columns × 2 rows — 8 frames (4 walk directions, idle + walk per direction)

**Stacked layout (two units on one sheet):** 4 columns × 4 rows — top 2 rows = unit A, bottom 2 rows = unit B.
- Example: `ScoutandAssaultDrones.jpg` — rows 0–1 = drone_scout, rows 2–3 = drone_assault

**Grey removal:** The sprite loader in `game/sprites.py` strips the grey background via PixelArray — just deliver standard JPEG sheets, no alpha needed.

**Naming:** Match the key in `_SHEET_MAP` inside `game/sprites.py`. When you add a new sprite file, also add the mapping entry there (but coordinate with Claude on the code side).

---

## Active Sprite Requests

These unit types exist in code but need or could use better sprites:

| Unit | Current Sprite | Notes |
|---|---|---|
| `militia` | polygon fallback | Radicalized civilian → spawns on Witness War conversion |
| `ice_agent_tac` | polygon fallback | Upgraded ICE agent with tac gear |
| `drone_operator` | `drone operator.jpg` | Wired up |
| `mrap` | polygon fallback | Heavy Regency vehicle |
| `news_van` | polygon fallback | Frontline vehicle, 6-tile Witness War range |

---

## Active Flavor Text Requests

The advisor system (`game/advisor.py`) uses `_LINES` keyed event dict. Events that could use more lines:

- `rank_5_promotion` — hero gets named, needs a corporate-bureaucratic congratulations
- `tape_acquired` / `tape_lost` — The Tape MacGuffin, holder gets +15% income
- `witness_radicalized` — civilian turns militia
- `cease_desist` — Patriot Lawyer suppression pulse fires
- `vbied_armed` — Sovereign arms a parked civilian car

Add lines to `_LINES` in `game/advisor.py` — that file is safe to edit for content additions.

---

## Conventions (Don't Break These)

- **Building catalog:** Edit `game/building_defs.py` only to add flavor text (`description` field). Do not change `produces`, `flags`, `cost`, `hp`, or `power_draw` — those are mechanically load-bearing.
- **No new `.py` files** without coordinating first.
- **Infamy events:** `world.roe_manager.add_infamy(amount)` — always a positive int.
- **Pathfinding:** `find_path(start_tuple, goal_tuple, blocked_set)` returns list of `(gx, gy)` tuples.

---

## Faction Tone Reference

| Faction | Voice | Vibe |
|---|---|---|
| Regency | Corporate HR, passive-aggressive | "This decision has been logged." |
| Frontline | Urgent, righteous, media-savvy | "The people are watching." |
| Sovereign | Conspiratorial, paranoid, blunt | "No witnesses." |
| Oligarchy | Detached, financial, amoral | "Casualties are a line item." |

The advisor character (**The Auditor**) speaks in all four registers depending on which faction's event fired.
