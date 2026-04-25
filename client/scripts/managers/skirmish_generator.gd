extends Node

## THE DEEP STATE: Procedural Skirmish Generator
## Places bases, audit points, and civilian clusters based on map size.

@export var map_size: float = 200.0
@export var audit_point_count: int = 5
@export var civilian_cluster_count: int = 4
@export var civilians_per_cluster: int = 5

@export_group("Factions")
@export var player_faction: String = "Regency"
@export var enemy_faction: String = "Oligarchy"

func _ready():
	generate_mission()

func generate_mission():
	randomize()
	print("GENERATING AUDIT MISSION: [", player_faction, " VS ", enemy_faction, "]")
	
	# 1. Spawn Bases at opposite ends
	var player_base_pos = Vector3(0, 1, -(map_size / 2) + 20)
	var enemy_base_pos = Vector3(0, 1, (map_size / 2) - 20)
	
	spawn_base(player_base_pos, player_faction, true)
	spawn_base(enemy_base_pos, enemy_faction, false)
	
	# 2. Spawn Processing Center for Player (near base)
	spawn_processing_center(player_base_pos + Vector3(15, 0, 10))
	
	# 3. Spawn Random Audit Points in the middle zone
	for i in range(audit_point_count):
		var pos = Vector3(
			randf_range(-map_size/2.5, map_size/2.5),
			1,
			randf_range(-map_size/3.0, map_size/3.0)
		)
		spawn_audit_point(pos, "ZONE_" + str(i))
	
	# 4. Spawn Civilian Clusters (The Mission Targets)
	for i in range(civilian_cluster_count):
		var cluster_pos = Vector3(
			randf_range(-map_size/2.2, map_size/2.2),
			1,
			randf_range(-map_size/4.0, map_size/4.0)
		)
		spawn_civilian_cluster(cluster_pos)

func spawn_base(pos: Vector3, faction: String, is_player: bool):
	var base_scene = load("res://scenes/buildings/building_base.tscn")
	var base = base_scene.instantiate()
	base.building_name = faction + " HQ"
	base.faction = faction
	base.is_constructed = true
	base.position = pos
	get_tree().current_scene.add_child.call_deferred(base)
	
	# Spawn initial defense squad
	var unit_path = "res://resources/units/park_ranger.tres" if is_player else "res://resources/units/conscript.tres"
	spawn_squad(pos + Vector3(0, 0, 10 if is_player else -10), faction, unit_path)

func spawn_processing_center(pos: Vector3):
	var pc_scene = load("res://scenes/buildings/processing_center.tscn")
	# If scene doesn't exist, we'd need to create it or instantiate via script
	# For now, let's assume we use a script-based instantiation if tscn is missing
	var pc = Node3D.new()
	pc.set_script(load("res://scripts/buildings/processing_center.gd"))
	pc.position = pos
	get_tree().current_scene.add_child.call_deferred(pc)

func spawn_audit_point(pos: Vector3, ap_name: String):
	var ap_scene = load("res://scenes/maps/audit_point.tscn")
	# Falling back to script if scene is missing
	var ap = Area3D.new()
	ap.set_script(load("res://scripts/maps/audit_point.gd"))
	ap.position = pos
	# Area3D needs a collision shape to work with audit_point.gd
	var col = CollisionShape3D.new()
	var sphere = SphereShape3D.new()
	sphere.radius = 10.0
	col.shape = sphere
	ap.add_child(col)
	
	get_tree().current_scene.add_child.call_deferred(ap)

func spawn_civilian_cluster(pos: Vector3):
	var civ_res = load("res://resources/units/civilian.tres")
	for i in range(civilians_per_cluster):
		var civ_pos = pos + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
		var civ_scene = load("res://scenes/units/unit_base.tscn") # Use unit_base
		var civ = civ_scene.instantiate()
		civ.set_script(load("res://scripts/units/civilian.gd"))
		civ.data = civ_res
		civ.position = civ_pos
		get_tree().current_scene.add_child.call_deferred(civ)

func spawn_squad(pos: Vector3, _faction: String, res_path: String):
	var unit_res = load(res_path)
	for i in range(3):
		var unit_scene = load("res://scenes/units/unit_base.tscn")
		var unit = unit_scene.instantiate()
		unit.data = unit_res
		if i == 0: unit.is_soul_leader = true
		unit.position = pos + Vector3(i * 2, 0, 0)
		get_tree().current_scene.add_child.call_deferred(unit)
