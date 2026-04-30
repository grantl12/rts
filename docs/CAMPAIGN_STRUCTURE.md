# THE DEEP STATE — Campaign Structure & Save State

---

## The Core Conceit

Three campaigns. Same maps. Different times, different factions, different information.

The Regency plays the maps first — pristine, well-lit, full bureaucratic authority. Their choices create the scars. The Frontline arrives second into the damage the Regency caused. The Oligarchy picks through what's left of both.

Every player choice in Campaign 1 becomes environmental fact in Campaign 2. Campaign 2's outcomes shape Campaign 3's starting conditions. The maps are not reused — they're *revisited*.

---

## Campaign Breakdown

### Campaign 1: "The Administration" — Regency
**Tone:** First Responders. Janitors. We are here to help.
**Map state:** Pristine. Green grass, functioning infrastructure, full civilian population.
**Objectives:** Capture narrative control points, detain protesters, neutralize Kirk incident.
**Hidden consequence:** Your ROE choices and infamy score are written into the save state. High ROE / high infamy → more rubble, more hostile civilians, and more Frontline presence in Campaign 2.

### Campaign 2: "The Information War" — Frontline
**Tone:** Insurgents and observers. Document everything.
**Map state:** Scarred. The Regency's barricades are still up. Wrecks. Reduced civilian count.
**Objectives:** Document Regency atrocities, fund drones through viral footage, expose the Kirk deepfake.
**Reads from:** Regency save — which buildings are damaged, how many civilians were detained, ROE history.
**Hidden consequence:** Frontline's information control score affects how much of the Kirk deepfake the Oligarchy inherits in Campaign 3.

### Campaign 3: "The Salvage Operation" — Oligarchy
**Tone:** Vultures. Insurance adjusters. Nothing personal.
**Map state:** Shattered. 60% Redaction Fog. Black censor tarps on rubble. Glitched HUD elements.
**Objectives:** Recover the Kirk AI code before Tech-State locks it down. Salvage wreck fields. Extract value from the ruin.
**Reads from:** Both prior saves — wreck positions, building destruction state, which narrative assets were captured.

---

## Save State Schema

One save slot per faction. Stored as JSON in `saves/` (not yet implemented).

```json
{
  "faction": "regency",
  "campaign_complete": true,
  "missions": {
    "the_quad": {
      "roe_peak": 4,
      "infamy_final": 312,
      "civilians_detained": 18,
      "civilians_killed": 2,
      "buildings_destroyed": ["student_library"],
      "bolo_captured": true,
      "runners_stopped": 1,
      "mission_time_sec": 847
    }
  }
}
```

### What carries forward

| Save field | Campaign 2 effect | Campaign 3 effect |
|---|---|---|
| `roe_peak` ≥ 4 | +15% starting Frontline units | Oligarchy gets "Documented Atrocity" credit bonus |
| `infamy_final` > 400 | Map starts in Scarred phase | Map starts in Shattered phase |
| `civilians_detained` | Subtracted from civilian pool available to Frontline | Fewer salvageable assets |
| `buildings_destroyed` | Those buildings are rubble — no capture possible | Wreck markers at those positions |
| `bolo_captured` | Frontline gets intel on BOLO's identity | Oligarchy can sell BOLO data for credits |
| `runners_stopped` | Fewer Frontline ambush reinforcements | Fewer salvage-spawn locations |

---

## Map Phase System

Each theater has 3 visual phases. The active phase for a given campaign is determined by the prior save state.

| Phase | Name | Visuals | Fog |
|---|---|---|---|
| 0 | Pristine | Green terrain, no damage, full building set | Standard FOG start |
| 1 | Scarred | Concrete barricades, scorched tiles, wreck markers, dim palette | FOG + some SHROUD patches |
| 2 | Shattered | Rubble terrain, black censor tarps, 60% SHROUD start, glitch UI | Heavy SHROUD, reduced vision |

Phase is set on `World.__init__` via `map_phase` int. Renderer reads it for terrain palette and wreck overlays.

*Implementation: see `docs/MAP_EVOLUTION.md` for full visual spec.*

---

## Mission Flow

```
Main Menu (faction select)
    ↓
Mission Briefing (The Auditor voiceover)
    ↓
Game Loop
    ↓ (win or loss)
Post-Op: Allocation Screen
    ↓
Post-Op: Press Briefing
    ↓
Save state written to saves/{faction}.json
    ↓
Next mission unlock / Campaign complete screen
```

---

## Save Slot UI (not yet designed)

Three slots on main menu: one per faction. Each shows:
- Faction name + icon
- Last mission completed
- Infamy score
- "NEW GAME" or "CONTINUE" action

Choosing a faction with a save and starting "The Information War" or "The Salvage Operation" requires the prior faction's save to exist. If it doesn't: the Frontline and Oligarchy campaigns start with no inherited state (neutral map conditions).

---

## The Kirk AI Thread

Running across all three campaigns:

- **Campaign 1 (Regency):** Kirk is assassinated. Tech-State begins training Kirk AI on the footage. Player is unaware.
- **Campaign 2 (Frontline):** Mid-game reveal — the Kirk deepfake is live, being used for fundraising by Tech-State. Final mission: expose or protect the servers.
- **Campaign 3 (Oligarchy):** The Kirk AI code is the MacGuffin. Race to extract it before Tech-State locks it. Final mission destroys (or copies) the servers.

The Kirk AI outcome in Campaign 2 affects what the Oligarchy finds in Campaign 3:
- Frontline exposed the deepfake → servers are partially destroyed, lower yield but easier mission
- Frontline failed / didn't expose → servers intact, higher yield but defended by Tech-State units
