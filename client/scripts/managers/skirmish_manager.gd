extends Node

## THE DEEP STATE: Skirmish Spawner
## Initializes the map with starting bases and units.

@export var player_faction: String = "Regency"
@export var enemy_faction: String = "Oligarchy"

func _ready():
	setup_skirmish()

func setup_skirmish():
	# Spawn Regency Base (North)
	spawn_base(Vector3(0, 0, -40), "Regency")
	
	# Spawn Oligarchy Base (South)
	spawn_base(Vector3(0, 0, 40), "Oligarchy")
	
	# Initial Squads
	spawn_initial_squad(Vector3(-10, 0, -30), "Regency", "res://resources/units/park_ranger.tres")
	spawn_initial_squad(Vector3(10, 0, 30), "Oligarchy", "res://resources/units/conscript.tres")

func spawn_base(pos: Vector3, faction: String):
	var base_scene = load("res://scenes/buildings/building_base.tscn")
	var base = base_scene.instantiate()
	base.building_name = faction + " HQ"
	base.faction = faction
	base.is_constructed = true
	get_tree().current_scene.add_child.call_deferred(base)
	base.global_position = pos

func spawn_initial_squad(pos: Vector3, faction: String, res_path: String):
	var unit_res = load(res_path)
	for i in range(3):
		var unit_scene = load("res://scenes/units/unit_base.tscn")
		var unit = unit_scene.instantiate()
		unit.data = unit_res
		# Set the first unit as the Soul Leader
		if i == 0: unit.is_soul_leader = true
		
		get_tree().current_scene.add_child.call_deferred(unit)
		unit.global_position = pos + Vector3(i * 2, 0, 0)
