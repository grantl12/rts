# 👁️ PROJECT: THE DEEP STATE
> "In a post-truth world, the only thing more dangerous than a leak is an audit."

**The Deep State** is a satirical real-time strategy (RTS) game built on Godot 4.4 and Supabase. It blends the squad-based tactical depth of *Company of Heroes* with the internal resource management of *FTL*, all wrapped in a bureaucratic, "Terminal OS" aesthetic.

---

## 🏛️ THE CORE PILLARS

### 1. The Audit & Roundup
Civilians are not just background dressing—they are your primary "resource." Instead of mining gold, you are "Vetting" and "Tethering" civilian groups to escort them to **Processing Centers**. Your success depends on how efficiently you can manage human flow without triggering a total collapse of public order.

### 2. Dynamic Rules of Engagement (ROE)
Control your squads with a global ROE Slider:
*   **Level 1 (Hearts & Minds):** Non-lethal suppression. High bureaucratic overhead, slow processing, but low **Infamy**.
*   **Level 5 (Absolute Immunity):** Administrative erasure. High lethality, rapid mission completion, but maximum **Infamy**.

### 3. Infamy & Persistence
Your actions have permanent consequences. Your **Infamy Score** is stored in the Supabase backend and affects:
*   **World State:** Visual rubble, smoke, and "Data Blackout" fog on future maps.
*   **Funding:** Higher Infamy triggers budget cuts and "Audits of the Auditor."
*   **Civilian Behavior:** (See below).

---

## 👥 THE "ANTAGONISTIC CIVILIAN" AI
The civilian population is a dynamic, reactive force that evolves based on your **Infamy Score**. They are not passive victims; they are the terrain you must navigate.

### Passive State (Low Infamy)
*   **Compliance:** Civilians follow "Tether" commands easily.
*   **Obstruction:** They may block paths or loiter, requiring non-lethal "Red Tape" suppression to move.

### Reactive State (Medium Infamy)
*   **Panic:** Crowds scatter or stampede, potentially damaging your own squads or blocking line-of-sight.
*   **Recording:** Civilians pull out "Mobile Devices" (visualized as small glowing rectangles). Being caught on camera during Level 5 ROE actions generates massive Infamy spikes.

### Antagonistic State (High Infamy)
*   **Insurgency:** Civilians have a chance to flip into "Insurgent" units. They don't have uniforms, making them hard to distinguish from the crowd until they attack.
*   **Asymmetric Sabotage:** Civilians will actively sabotage "Audit Points" or provide "Proxies" with intel, revealing your squad positions through the Fog of War.
*   **The "Human Shield" Logic:** Enemy AI (The Proxy) will intentionally cluster near civilian groups, forcing you to choose between slow, high-risk non-lethal play or a high-Infamy "Erasure" event.

---

## 🛠️ TECH STACK
*   **Engine:** Godot 4.4 (C# / GDScript)
*   **Backend:** Supabase (PostgreSQL, Auth, Real-time Ticker)
*   **UI:** 16-bit glitch-box aesthetics / Terminal OS
*   **Audio:** Faction-specific "Gilded Epaulets" orchestral & industrial synth-pop

---

## 📂 PROJECT STRUCTURE
*   `/client`: Godot 4.4 project files.
*   `/backend`: Supabase Edge Functions and database schemas.
*   `/docs`: Detailed design manifestos and unit rosters.
*   `/assets`: Lo-fi 3D assets and 2D billboards.

---
*UNCLASSIFIED // FOR AUDITOR EYES ONLY*
