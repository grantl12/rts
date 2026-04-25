# 🎨 THE DEEP STATE: UNIT SPRITE SPECIFICATION
> Lo-fi 3D world + 2D Pixelated Billboards.

## 📐 TECHNICAL SPECS
*   **Resolution:** 32x32 or 48x48 per frame.
*   **Filter:** Nearest Neighbor (No blurring).
*   **Alpha:** 1-bit transparency (hard edges).
*   **Style:** Chunky pixels, limited color palette per faction.

## 👥 FACTION VISUAL CUES

| Unit | Faction | Key Visuals | Palette |
| :--- | :--- | :--- | :--- |
| **Park Ranger** | **Regency** | Wide-brim hat, clipboard, non-lethal "Audit Wand." | Blues, Tans, Greys |
| **MAGA Patriot** | **Regency** | Tactical vest, red cap, "Stimulus Drop" flare. | Red, White, Blue, Camo |
| **Proxy** | **Sovereign** | Hooded, goggles, glowing "Sabotage Kit." | Purples, Dark Greys, Neon |
| **Contractor** | **Oligarchy** | Slick corporate armor, monocle-HUD, heavy rifle. | Reds, Blacks, Gold |
| **Civilian** | **Neutral** | Casual wear, glowing "Mobile Device" (recording). | Greys, Muted Browns |

## 🎞️ ANIMATION STATES (Atlas Layout)
Since we use `Sprite3D` billboards, we need a simple horizontal or vertical atlas:
1.  **IDLE:** (2-4 frames) Slight breathing/shifting.
2.  **MOVE:** (4-6 frames) High-energy lo-fi run.
3.  **AUDIT/ATTACK:** (4 frames) Action frame (e.g., raising clipboard or rifle).
4.  **PANIC (Suppressed):** (2 frames) Glitching/shaking.
5.  **RECORDING:** (Civilians only) Raising phone, glowing red screen.

## 💾 GODOT IMPLEMENTATION
1.  Drop PNG into `/assets/sprites/units/`.
2.  Assign to `sprite_texture` on the `UnitResource` (.tres).
3.  Set `sprite_scale` (Default 1.0).
4.  The `Unit.gd` script handles the billboard physics and selection glow automatically.
