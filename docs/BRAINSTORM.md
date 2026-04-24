# THE DEEP STATE: Brainstorm & Design Overflow
## Running doc for ideas that haven't been formally specced yet.
## Pull from here when building out MAPS.md, UNITS.md, or feature tickets.

---

## CORE DESIGN DECISIONS (LOCKED)

### The "Audit" Language — KEEP IT
Every faction calls capturing territory an "Audit" because the entire game world speaks sanitized bureaucratic euphemism. This isn't one faction's spin — it's the shared doublespeak everyone is trapped inside. Changing it would break the satirical coherence.

- A unit doesn't die — it gets **Redacted**
- A conscript doesn't die — it gets **Discarded**
- Morale = **Bureaucracy**
- Ammo = **Supplies**
- Suppression = **Red Tape**
- Capturing territory = **Auditing**

The faction-specific flavor comes from the **capture completion text**, not the mechanic name. Frontline captures a point and it says "LIBERATED (FOOTAGE LEAKED)." The word Audit describes the act. The result is where their voice lives.

### Mirror-Map Architecture
Regency always "wins" their campaign. Their victory state IS the opposing faction's starting conditions. The map geometry never changes — only time of day, objectives, and narrative layer.

### Tone Mandate
Detached. Corporate. Absurdly bureaucratic. The Advisor sounds like a GPS crossed with an HR rep. The game should feel like it knows your history but never explains why.

---

## NEW UNITS & SUBFACTIONS

### THE REGENCY
| Unit | Role | Special Ability | Notes |
|---|---|---|---|
| Park Ranger | Core infantry (scalpel) | Thermal Scope — high accuracy, drains Supplies | Already in codebase |
| Gravy Seal | Elite drop unit | Stimulus Drop — calls in backup squad | Already in codebase |
| The Proud Perimeter | Melee, shield wall | "Stand Back & Stand By" — absorbs suppression for nearby units | Proud Boys analog. Street fighters, close range only |
| The Patriot Lawyer | Ranged support | "Cease & Desist" — freezes single enemy unit in Red Tape | Briefcase as weapon. Never shoots. |
| The Donor | Passive aura | Bureaucracy aura for nearby units. Cannot fight. | Extremely fragile. Golf shirt. Politically untouchable — killing one triggers a morale penalty for YOUR units. |
| Chief Auditor | Hero/promotion | Promoted Park Ranger. Federal Grant income +2%, unlocks Tactical Segway. | Hall of Heroes promotion path |

### THE OLIGARCHY
| Unit | Role | Special Ability | Notes |
|---|---|---|---|
| Conscript | Core infantry (meat) | "Adrenaline" buff on squadmate death | Already in codebase |
| PMC Contractor | Elite mercenary | Kickback — siphons resources from nearby enemy structures | Already in codebase |
| Wagner Unit | Expendable swarm | "Expendable Asset" — arrives in waves of 15, costs nearly nothing | Even worse Meat Grinder. Morale immune. |
| The Troll Farm | Structure unit | Passively erodes enemy Audit Points at range. Untargetable behind other buildings. | Most annoying unit in the game. No combat stats. |
| The Oligarch | Hero unit | Massive resource aura. One-hit kill. Has a yacht. | Yacht = docked structure/mobile HQ prop. Not a vehicle. |

### THE FRONTLINE
| Unit | Role | Special Ability | Notes |
|---|---|---|---|
| Digital Nomad | Core infantry | Crowdfunding — chaos events generate bonus resources | Already in codebase |
| FPV Drone Operator | Ranged/artillery | Deploys one-use FPV drone — massive single-target damage, drone destroyed on impact | Operator stays in rear with a tablet. Drone is a projectile. NO flight model needed. Ukraine's actual doctrine. |
| The Journalist | Support | Accelerates Audit Point capture in radius. Arresting one = huge Frontline morale penalty. | The unit everyone's afraid to shoot. Killing one is a war crime (mechanically). |
| The Hacktivist | Structure/support | "DDoS" — disables enemy Audit Station for 45 seconds | Never leaves base. Pizza boxes are environmental props near spawn. |
| The Agitator | Psychological ops | Reduces enemy Bureaucracy in radius. Can "flip" neutral civilian units. | No weapon. Megaphone only. |

### THE SOVEREIGN UNION
| Unit | Role | Special Ability | Notes |
|---|---|---|---|
| The Proxy | Core infantry | Black Market supply lines — less reliable but untrackable | Already in codebase |
| The Settler | Builder | "Outpost Declaration" — plants flag that converts nearby neutral terrain | Extremely fast construction. Extremely controversial. |
| Iron Dome Turret | Defense structure | Intercepts incoming projectiles in radius | Structure unit, not infantry. Counters FPV Drone Operator. |
| The Interpreter | Support | Slows enemy Audit Point capture speed by "translating" their communications | Strange support unit. No weapon. Earpiece visible. |

### NEUTRAL / CIVILIAN UNITS
| Unit | Behavior | Notes |
|---|---|---|
| The Resident | Shoots anyone entering their yard. Cannot be killed. | Chicago map specific. Armed escalation per wave. |
| The Journalist | Neutral until arrested | Appears on multiple maps. Mechanically protected. |
| The Donor | Regency-aligned aura unit | Not a combatant. Buff radius. |
| The Protester | Frontline-adjacent civilian | Can be processed (Regency), supplied (Frontline), or ignored (everyone else). |

---

## SUPERWEAPONS (FULL LIST)

| Name | Faction | Effect |
|---|---|---|
| The SCOTUS Gavel | Regency | De-Zones an area — no enemy building/rebuilding for set duration |
| The Stimulus Drop | Regency | Drops cash + a Gravy Seal squad from a helicopter |
| The Epstein File Leak | Sovereign / Oligarchy | Global info blackout — reveals full map, disables enemy Hero units and income for 45 seconds |
| The Fact Check | Support (any) | AOE clears suppression, debunks Stealth, weakens Viral bonuses |
| The Meat Grinder | Oligarchy | Instant mob of 10 Conscripts at target location |
| The Platform Ban | Regency | Removes a Frontline unit's "Journalist" protection temporarily. They can now be targeted. |
| The Drone Swarm | Frontline | 5 simultaneous FPV drones launched at random enemy structures |
| The Troll Surge | Oligarchy | Troll Farm efficiency doubled for 60 seconds. Audit erosion goes critical. |

---

## CULTURAL REFERENCE CHECKLIST
*Things that must be in the game somewhere*

- [ ] "Stand Back and Stand By" — Proud Perimeter ability name
- [ ] "Epstein didn't kill himself" — Easter egg / loading screen tip
- [ ] "Do your own research" — Sovereign Unit briefing line
- [ ] "This is fine" — Advisor line when your HQ is on fire
- [ ] "Let's Go Brandon" — Regency unit cheer on capture (audio)
- [ ] "Slava Ukraini" — Frontline unit cheer on capture (audio)
- [ ] Pizza references everywhere in the Comet Ping Pong map
- [ ] The yacht exists as a prop. It is not explained.
- [ ] The golf cart. Always the golf cart.
- [ ] "The Algorithm" — referenced by Frontline as a deity
- [ ] Jan 6 footage — loadscreen static on Regency campaign
- [ ] A loading screen tip that just says "REDACTED"

---

## BACKLOG FEATURES (PRIORITY ORDER)

### P1 — Needed for playable skirmish
- [x] Input controller (selection + orders)
- [ ] Suppression UI (Red Tape bars above units)
- [ ] Wire Meat Grinder to actually spawn units
- [ ] NavigationRegion3D baked into The Quad (pathfinding currently line-of-sight only)
- [ ] Basic resource HUD (show current Supplies/Bureaucracy for selected unit)

### P2 — Needed for first demo
- [ ] Unique sprites per faction (Park Ranger vs Conscript at minimum)
- [ ] 16-bit glitch selection box UI
- [ ] Faction selection → map load flow (currently stubs)
- [ ] Audit Point progress bar visible in world
- [ ] Win/loss condition detection + end screen

### P3 — Needed for campaign
- [ ] Mirror-map transition cinematics (Regency win → Frontline briefing)
- [ ] Advisor VO system (text-based first, audio later)
- [ ] Narrative Events / mid-mission "Leaks"
- [ ] Hall of Heroes promotion flow

### P4 — Replayability
- [ ] **Skirmish Mode + Procedural Map Generator**
  - Biome palette system (Urban, Federal, Suburban, Island, Underground)
  - Audit Point placement algorithm (always odd count, one central "Memorial")
  - Faction base placement (opposing corners, balanced)
  - Narrative Seed cards (randomize advisor tone + flavor text)
- [ ] Skirmish-specific unit unlocks separate from campaign progression

### P5 — Cloud / Live
- [ ] Supabase Auth (Hall of Heroes login)
- [ ] Real-time global conflict ticker (main menu syncs with DB)
- [ ] Cross-player narrative events ("The Quad has been held by Regency for 72 hours globally")

### P6 — Scope Expansions (v2, do not architect around)
- [ ] Water as traversable terrain
- [ ] Actual aircraft units (helicopters, planes)
- [ ] The Oligarch's Yacht as a mobile naval HQ
- [ ] Multiplayer (currently single-player vs AI assumed)

---

## OPEN QUESTIONS

1. **Base builder scope:** How much construction does the player do mid-mission vs. pre-mission? C&C-style (build during) or StarCraft-style (army composition before deployment)?
2. **AI faction behavior:** Does the AI play mechanically or does it play "in character" (Oligarchy AI always goes for resource siphon first, Frontline AI always goes for Audit Points)?
3. **Campaign linearity:** Does the player pick a faction at the start and run their full campaign, or is it mission-by-mission with faction switching?
4. **The Martyr (Charlie Kirk):** Is he a unit? A map prop? Both? In the Regency campaign he's a narrative asset. In the Frontline campaign he's a martyr symbol. Does the player ever control him?
