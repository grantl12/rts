# 📑 PROJECT: THE DEEP STATE
## **MANIFESTO & DESIGN ARCHITECTURE (APRIL 2026)**

### **1. CORE GAMEPLAY MECHANIC: THE AUDIT & ROUNDUP**
* **The Mission:** Civilians are the primary "resource." Players must "Vet" and "Tether" civilian groups and escort them to **Processing Centers**.
* **Dynamic ROE (Rules of Engagement):**
    * **Level 1 (Hearts & Minds):** Non-lethal gear. High suppression, slow processing, low Infamy.
    * **Level 5 (Absolute Immunity):** Total administrative erasure. High lethality, rapid mission completion, maximum Infamy.
* **Infamy Persistence:** Casualties and ROE choices are stored in **Supabase**. High Infamy makes future missions harder, turning civilians into insurgents and triggering funding cuts.

### **2. FACTION & SUB-SECT ROSTER**
| Pillar | Sub-Sect | Focus |
| :--- | :--- | :--- |
| **The Regency** | **The Shield (Israel-adj)** | Iron Dome defense, Merkava-adj mobility. |
| **The Regency** | **The MAGA (Patriot)** | Gravy Seals, Stimulus Drops, high-energy synth themes. |
| **Sovereign Union** | **The Proxy (Iran-adj)** | Martyr Drones, Tunnel Networks, asymmetric sabotage. |
| **The Oligarchy** | **The Contractor** | The Meat Grinder, brute-force attrition, private mercs. |

### **3. SONIC IDENTITY (AUDIO CUES)**
* **Main Theme ("Gilded Epaulets"):** Ominous orchestral, militaristic percussion.
* **The "Patriot" Mission:** High-energy, "over-the-top" synth-pop/rally vibes.
* **The "Proxy" Mission:** Distorted Middle Eastern strings (Oud/Saz) mixed with industrial glitch.
* **The "Frontline" Mission:** 150 BPM Glitch-Hop/Breakbeat (Crowdfunding Chaos).

### **4. MAIN MENU & UI DESIGN**
* **"Terminal OS" Aesthetic:** Desktop icons, classified file folders, and a level 5 clearance dashboard.
* **Live Satellite Feed:** The background is a live Godot render of the **University Quad** map.
    * *Visual Polish:* The zoom/pan focus changes based on menu hover.
    * *World State:* The map visuals (smoke, rubble, grid) reflect the player's **Infamy Score** pulled from the backend.

### **5. DATA PERSISTENCE (SUPABASE SCHEMA)**
* `player_meta`: Stores `infamy_score` and `global_reputation`.
* `veteran_roster`: Stores surviving Rank 3 squads (Stats: Kills, Missions, "ROE Tendency").
* `mission_logs`: Stores "Legacy Flags" (e.g., *Did the player destroy the Evidence in Mission 1?*).

---

### **How to add the songs to Git:**
Since the audio is generated here, you’ll want to:
1.  **Download** the 30s clips from our chat.
2.  **Move them** into your repo under `/assets/audio/music/`.
3.  **Rename them** following the faction logic:
    * `maga_rally_synth.wav`
    * `proxy_iran_theme.wav`
    * `deep_state_main.wav`

---

### **Engineering Checklist for when you get to your desk:**
* [ ] **Rename the Tracks:** Name them `maga_rally.wav`, `proxy_iran.wav`, etc., so they’re ready for the Godot `AudioStreamPlayer`.
* [ ] **Update the Repo:** Commit the new `.md` file with the message: `"Initial tech spec for ROE and Infamy persistence logic."`
* [ ] **Test the "Stuff":** See if you can get that **Squad Leader** node to move while carrying the **Civilian Tether** logic.
