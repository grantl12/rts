extends Node

## THE DEEP STATE: Ability Manager
## Handles faction-specific "Superweapons" and powers.

func spawn_reinforcements(pos: Vector3, faction: String = "Regency"):
	var res_map := {
		"Regency": "res://resources/units/park_ranger.tres",
		"Oligarchy": "res://resources/units/conscript.tres",
		"Frontline": "res://resources/units/digital_nomad.tres",
		"Sovereign": "res://resources/units/conscript.tres",
	}
	var unit_res = load(res_map.get(faction, "res://resources/units/conscript.tres"))
	var unit_scene = load("res://scenes/units/unit_base.tscn")
	for i in range(3):
		var unit = unit_scene.instantiate()
		unit.data = unit_res
		unit.position = pos + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
		get_tree().current_scene.add_child(unit)

func spawn_meat_grinder(pos: Vector3, faction: String = "Oligarchy"):
	print("INITIATING THE MEAT GRINDER at ", pos)
	var conscript_res = load("res://resources/units/conscript.tres")
	var unit_scene = load("res://scenes/units/unit_base.tscn")

	for i in range(10):
		var unit = unit_scene.instantiate()
		unit.data = conscript_res
		unit.global_position = pos + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
		get_tree().current_scene.add_child(unit)

func cast_fact_check(pos: Vector3, radius: float = 15.0):
	print("INITIATING FACT CHECK AOE")
	
	# Find all units and clear suppression
	var all_units = get_tree().get_nodes_in_group("units")
	for unit in all_units:
		if unit is Unit and unit.global_position.distance_to(pos) <= radius:
			unit.is_suppressed = false
			unit.current_bureaucracy = unit.data.max_bureaucracy
			print("Unit ", unit.data.unit_name, " has been FACT CHECKED.")
