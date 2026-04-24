extends Resource
class_name UnitResource

## RED TAPE & RENEGADES: Base Unit Resource
## Bridges the C&C RTS feel with FTL-style deep stats.

@export_group("Identity")
@export var unit_name: String = "Unknown Unit"
@export var unit_type: String = "Infantry"
@export var faction: String = "Neutral"

@export_group("Vitality & Bureaucracy")
@export var max_vitality: float = 100.0
@export var max_bureaucracy: float = 50.0 # Morale
@export var max_supplies: float = 20.0    # Ammo/Energy

@export_group("Combat")
@export var damage: float = 10.0
@export var attack_range: float = 15.0
@export var attack_speed: float = 1.0     # Attacks per second
@export var accuracy: float = 0.8         # 0.0 to 1.0

@export_group("The Soul (Persistence)")
@export var soul_id: String = ""          # Unique ID for Supabase
@export var veterancy_rank: int = 1
@export var map_cap_reached: bool = false
@export var metadata: Dictionary = {}      # For "Legacy Gear" and "Soul Traits"

## FTL-style System Check
func is_operational() -> bool:
	return max_vitality > 0 and max_bureaucracy > 0

func get_status_summary() -> String:
	if max_bureaucracy < 10:
		return "PANIC: SELF-AUDIT IMMINENT"
	if max_supplies <= 0:
		return "LOW RESOURCES: MELEE ONLY"
	return "OPERATIONAL"
