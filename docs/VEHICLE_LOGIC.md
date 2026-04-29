# 🚗 TECHNICAL BRIEF: CIVILIAN VEHICLE SYSTEMS
**Project:** *The Deep State* **Core Function:** Tactical Obstacles, Economic Nodes, and "Visual Scarring"

## 🏗️ 1. THE "GRIDLOCK" ARCHITECTURE
Maps are populated with randomized civilian vehicles (Sedans, SUVs, Buses, Vans).
 * **Dynamic Pathfinding:** Vehicles are not static; they create a "Navigation Maze."
 * **The Audit Requirement:** For the **Regency**, vehicles act as roadblocks. You must "Audit" a car to make it pull over or move, slowing down your advance.
 * **The "Plow" Mechanic:** Heavy units (**Oligarchy** or **Merkava-adj** tanks) can shove or crush cars to clear paths, but this spikes **Property Damage** penalties and Infamy.

## 🚔 2. FEDERAL ALPR & THE "IPAWS" OVERLAY
Using a generic, high-level **FEMA/Department of Compliance** interface for vehicle tracking.
 * **The "BOLO" (Be On The Look Out):** Every mission features a "High-Value Target" vehicle identified by an anonymous government feed.
 * **The Scan:** Regency **ALPR Scouts** (blacked-out SUVs) scan plates in real-time using a grainy, green-tinted HUD.
 * **The Objective:** Correctly identifying and "Auditing" the target vehicle grants a massive **Political Capital** boost.
 * **The Satire:** Auditing the *wrong* civilian vehicle triggers a "Civil Rights Litigation" cooldown, freezing your administrative budget for 30 seconds.

## 💣 3. THE "SLEEPER" VEHICLE (Proxy Tactics)
Civilian cars are the primary weapon of the **Sovereign Union**.
 * **VBIED Potential:** Any civilian vehicle can be a "Sleeper." If the Proxy player "hacks" a car, it becomes a **Vehicle-Borne IED**.
 * **The Paranoia:** The Regency player never knows if the SUV in the Toll Bridge gridlock is just a "Commuter" or a "Kamikaze" until it starts moving toward their units.

## 📈 4. VEHICLE PERSISTENCE (Visual Scarring)
Vehicles are the primary indicator of how "hot" a zone has become over multiple visits.
 * **Persistence State:** While functional cars may despawn, **Destroyed Wrecks** are permanent.
 * **The Catwalk of Carnage:** By Visit 3 of the **University Quad**, the main roads should be impassable due to the scorched remains of cars from Visit 1.
 * **Cover Utility:** Wrecks provide **75% Cover** but can be "Salvaged" by the **Oligarchy** for scrap metal, physically removing the cover from the map to deny it to the enemy.

## 🚌 5. THE "COMPLIANCE BUS" (Mobile Harvest)
Vehicles act as the "Transport Layer" for your civilian extraction.
 * **The Bus:** A high-capacity, windowless transport that holds up to 30 civilians.
 * **The Escort:** Players must protect the bus as it moves toward the **Extraction Zone**.
 * **The Multiplier:** Successfully extracting a bus provides a **3x Bonus** to "Administrative Credits" compared to walking civilians out on foot.

## 🛠️ ENGINEERING TO-DO LIST
 1. **[CODE]** Implement Vehicle_Base.gd with states: Idle, Audited, Moving, Wrecked.
 2. **[UI]** Create a cold, federal-style HUD for the BOLO target (Plate #, Make, Model).
 3. **[FX]** Design the "Crush" animation/mesh-swap for when tanks drive over sedans.
 4. **[NAV]** Ensure the **NavigationServer3D** updates dynamically as vehicles are destroyed or moved.

### **The "Noodle" on Vehicle Satire:**
 * **Vehicle Flavor Text:** When you click a car, it shows the "Commuter's Reason for Travel."
   * *Example:* "Going to a meeting about 'Compliance Efficiencies'."
   * *Example:* "Driving to a job that was automated six months ago."
 * **The "Redacted" Plate:** In high-Infamy zones, some cars have black bars over their license plates, making them invisible to ALPR scans.
