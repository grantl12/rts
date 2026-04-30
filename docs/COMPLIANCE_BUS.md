# THE COMPLIANCE BUS — Feature Design Spec

> "Voluntary Relocation Assistance Program. Boarding is encouraged."

---

## Concept

The Compliance Bus is a high-value escort unit that transforms the mid-game from firefight to logistics puzzle. It carries civilians from the field to your Compliance Pen / HQ, bypassing the proximity auto-capture mechanic and delivering a 3× credit multiplier on every successfully transported civilian.

The satire: it is a school bus. It says "SAFE HARBOR EXPRESS" on the side. It has a smiley face decal.

---

## Mechanical Role

Standard holding pens auto-capture civilians within 3 tiles — slow, passive, and easily raided. The Compliance Bus lets you:
- Actively drive into high-civilian zones (center plaza, campus grounds)
- Board up to 30 civilians rapidly
- Drive the load back to your pen / HQ for a lump-sum payout
- Extract BOLO targets intentionally rather than waiting for them to wander in

This is the primary mechanism for the **Compliance Score** mid-campaign metric — how many civilians were "processed" vs. lost to enemy factions or infamy events.

---

## Stats

| Attribute | Value | Notes |
|---|---|---|
| Capacity | 30 civilians | Hard cap |
| Speed | 2.5 tiles/sec | Slower when full (2.0) |
| HP | 350 | Heavy — survives a raid |
| Armor | medium | Vulnerable to contractors |
| Cost | 800 § | Production: reg_barracks or depot |
| Credit multiplier | 3× per delivered civ | vs. 1× for pen auto-capture |
| Infamy on death (with civs aboard) | +75 | "Administrative Incident" |

---

## Boarding Logic

- Bus enters **LOADING** state when player right-clicks it onto a tile
- Any civilian within 2.5 tiles per tick is auto-boarded (removed from world, added to `bus.passengers`)
- BOLO target boards like any other civilian but is flagged in the bus manifest
- Player can also manually click a civilian then shift-click the bus to priority-board
- When full OR player right-clicks the bus to a pen/HQ: enters **TRANSIT** state

---

## Delivery

- Bus must reach a friendly pen or HQ tile to unload
- On unload: each passenger pays `PEN_INCOME_RATE × 3` as a lump sum
- BOLO passenger: triggers `bolo_captured` event + §500 bonus as normal
- Bus returns to IDLE after unloading; passengers are now "detained" (count toward post-op)

---

## Enemy Interaction

- Enemy AI `_do_raids()` will specifically target buses in TRANSIT state with ≥10 passengers (high-value)
- Sovereign VBIED can detonate next to a bus — civilian panic, bus takes AoE damage
- If bus HP → 0 while passengers aboard: passengers scatter (panic flee), no credit payout, +75 infamy
- Frontline Press Bureau: records a "Administrative Vehicle Incident" if bus is destroyed near their buildings (+10 infamy/surviving passenger)

---

## Rendering

- Wide flat rectangle shape (already in `Unit._SHAPES` as `unmarked_van` — needs its own entry)
- Faction color + "COMPLIANCE BUS" label when selected
- Passenger count badge: small number rendered above the bus (e.g. "12/30")
- LOADING state: yellow highlight + boarding animation (civilians visually shrink into bus)
- TRANSIT state: green stripe along side

---

## Implementation Notes

### New unit type
Add to `UNIT_DEFS` in `unit_entity.py`:
```python
"compliance_bus": (350, 2.5, 0, 0.0, 0.0, "medium", "regency", 800),
```

### New class or subclass
The bus needs passenger state that a standard `Unit` doesn't have. Options:
1. Subclass `Unit` with `ComplianceBus(Unit)` — cleanest
2. Add `passengers` list + `bus_state` to base `Unit`, gated by `utype == "compliance_bus"` — simpler, less clean

Recommend option 1 since the boarding/delivery logic is substantial.

### New bus states
`BUS_IDLE / BUS_LOADING / BUS_TRANSIT / BUS_UNLOADING`
These coexist with base unit states — bus is always `STATE_IDLE` or `STATE_MOVING` at the unit layer; bus_state is a layer above.

### World integration
- `world.update()`: scan for civs near buses in LOADING state each tick
- `world._unload_bus(bus, pen)`: credit payout + transfer passengers to pen garrison count
- `world.events.append(("bus_unloaded", {...}))` for notification log

### Add to sidebar
Add `compliance_bus` to `FACTION_BUILD_MENU["regency"]` units section.

---

## Satirical Details (flavor, not mechanics)

- The bus plays a jingle on boarding ("Thank you for your Voluntary Compliance!")
- At ROE 5: the bus plays the jingle 20% faster
- The "Safe Harbor Express" decal is visible on the side in the unit render
- At SANCTIONED infamy tier: bus production is not frozen (it's non-lethal infrastructure)
