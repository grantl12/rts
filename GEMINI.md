# THE DEEP STATE: Project Status & Roadmap

## 🎯 Current Vision
A satirical RTS built on Godot 4.4 and Supabase. The game blends the weighted squad combat of *Company of Heroes* with the internal system depth of *FTL*, set in a "Post-Truth" world where "Auditing" is the primary weapon.

---

## 🏗️ Architectural Progress

### 1. Core Systems (The Logic)
- **Unit "Soul" System:** Persistence logic for veteran units, tracking Vitality, Bureaucracy (Morale), and Supplies (Ammo/Resources).
- **Combat & Suppression:** Directional damage and "Red Tape" suppression mechanics that disable unit fire.
- **Audit Points:** A "Strength of Numbers" capture system that shifts the map's narrative and global color.
- **Ability Manager:** Functional "Superweapons" including the **Meat Grinder** (Oligarchy mob spawn) and **Fact Check** (AOE suppression clear).
- **Global Conflict Manager:** Meta-manager tracking theater control and updating satirical news headlines.

### 2. Theaters & Maps (The World)
- **Theater 1 (The Quad):** Greyboxed "Incident" site with a central Memorial Audit point.
- **Theater 2 (The Wall):** Functional "Audit Station" logic and **Analog Zone** shader for anti-grid areas.
- **Theater 3 (The Ziggurat):** "Server Migration" mechanic (units physically carrying Data Cores).
- **Theater 4 (The Suburbs):** "Property Value" aura logic for building-based buffs/debuffs.

### 3. Interface (The UX)
- **Executive Dashboard:** Boot sequence, satirical News Ticker, and navigation.
- **Jurisdiction Selection:** Faction choosing flow (Regency, Oligarchy, Frontline, Sovereign).
- **RTS Camera:** Functional pan/zoom controller for the "Omniscient Auditor."

---

## 🛰️ Integration Status
- **Supabase Bridge:** `SupabaseManager.gd` is set up for REST API calls.
- **Local Persistence:** `ArchiveManager.gd` handles local "Audit Log" saves.
- **Shader Library:** `neon_grid.gdshader` (World overlay) and `analog_zone.gdshader` (Dead zones).

---

## 🚀 Potential Next Steps

### Phase 1: Tactical Polish
- [ ] **Selection UI:** Implement the 16-bit glitch boxes for selecting squads.
- [ ] **Unit Visuals:** Create unique sprites for the 4 core factions (Park Ranger vs. Conscript).
- [ ] **Statue Shader:** A mesh-deformation shader for the "Martyr's Statue" that glitches based on narrative control.

### Phase 2: Strategic Depth
- [ ] **Executive Board:** The meta-progression screen to spend "Legacy Points" on global buffs.
- [ ] **Suppression UI:** Visual "Red Tape" bars above suppressed units.
- [ ] **Fog of War:** A "Data Blackout" fog system that only clears in areas with high grid control.

### Phase 3: The Narrative Layer
- [ ] **Advisor VO/Text:** Implement the "Bureaucratic Calm" vs "Total Panic" mission briefings.
- [ ] **Narrative Events:** Scripted mid-mission "Leaks" that change objectives dynamically.

### Phase 4: Cloud Connectivity
- [ ] **Supabase Auth:** Real login/signup for the Hall of Heroes.
- [ ] **Real-time Global Ticker:** Syncing the Main Menu ticker with the *actual* global database stats from all players.

---

## 📝 Developer Notes
- **Tone Mandate:** Keep it detached, corporate, and absurdly bureaucratic.
- **Asset Strategy:** Lo-fi 3D with 2D billboards. Priority is systems and "vibes" over high-fidelity meshes.
- **The "Mirror" Loop:** Every map must be playable and narratively distinct from at least two opposing sides.
