extends Building
class_name SuburbanHouse

## THE DEEP STATE: Suburban House
## Generates a "Property Value" aura based on faction control.

@export var property_value_radius: float = 20.0
@export var current_equity: float = 100.0

func _process(_delta):
	apply_property_aura()

func apply_property_aura():
	var units = get_tree().get_nodes_in_group("units")
	for unit in units:
		if unit.global_position.distance_to(global_position) < property_value_radius:
			if unit.data.faction == faction:
				unit.current_bureaucracy += 1.0 # Buff allies
			else:
				unit.take_damage(0.5, "Bureaucracy") # "Red Tape" the interlopers

func _on_captured(new_faction: String):
	faction = new_faction
	print("HOA NOTICE: Property has been AUDITED by ", new_faction)
