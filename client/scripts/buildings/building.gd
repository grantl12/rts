extends StaticBody3D
class_name Building

## THE DEEP STATE: Base Building

signal building_destroyed(building_name: String, faction: String)

@export var building_name: String = "Structure"
@export var faction: String = "Neutral"
@export var cost: int = 100
@export var max_health: float = 500.0
@export var producible_unit_path: String = ""
@export var produce_time: float = 5.0
@export var extra_group: String = ""
@export var passive_income: int = 0
@export var effect_type: String = ""
@export var effect_radius: float = 0.0
@export var effect_interval: float = 0.0

const UNIT_PRODUCTION_COST := 50

var current_health: float
var is_constructed: bool = false
var _is_producing: bool = false
var _produce_time_remaining: float = 0.0
var _hq_warned: bool = false

func _ready():
	add_to_group("buildings")
	current_health = max_health
	if extra_group != "":
		add_to_group(extra_group)
	_apply_faction_visuals()
	if is_constructed:
		apply_grid_influence()
		if passive_income > 0:
			_start_timer(3.0, _on_income_tick)
		if effect_interval > 0.0 and effect_type != "":
			_start_timer(effect_interval, _on_effect_tick)

func _process(delta: float) -> void:
	if _is_producing and _produce_time_remaining > 0.0:
		_produce_time_remaining -= delta

func _start_timer(interval: float, callback: Callable) -> void:
	var t := Timer.new()
	t.wait_time = interval
	t.autostart = true
	t.timeout.connect(callback)
	add_child(t)

func _on_income_tick() -> void:
	ResourceManager.add_funds(faction, passive_income)

func _on_effect_tick() -> void:
	match effect_type:
		"heal_allies":
			for node in get_tree().get_nodes_in_group("units"):
				if not (node is Unit) or not is_instance_valid(node):
					continue
				if node.data.faction != faction:
					continue
				if global_position.distance_to(node.global_position) <= effect_radius:
					var cap := node.data.max_vitality * node._health_mult
					node.current_vitality = minf(node.current_vitality + 15.0, cap)
					node._bars_dirty = true
		"suppress_enemies":
			for node in get_tree().get_nodes_in_group("units"):
				if not (node is Unit) or not is_instance_valid(node):
					continue
				if node.data.faction == faction:
					continue
				if global_position.distance_to(node.global_position) <= effect_radius:
					node.apply_suppression()

func _apply_faction_visuals():
	var col := _faction_color()
	var csg = get_node_or_null("MeshInstance3D")
	if csg is CSGBox3D:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = col.darkened(0.45)
		mat.emission_enabled = true
		mat.emission = col * 0.35
		csg.material = mat

	var lbl := Label3D.new()
	lbl.text = building_name.to_upper()
	lbl.font_size = 9
	lbl.outline_size = 3
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.modulate = col
	lbl.position = Vector3(0, 6.8, 0)
	add_child(lbl)

func _faction_color() -> Color:
	match faction:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)

func get_producible_unit() -> UnitResource:
	if producible_unit_path.is_empty():
		return null
	return load(producible_unit_path) as UnitResource

func request_produce() -> bool:
	if _is_producing:
		return false
	var unit_data := get_producible_unit()
	if not unit_data:
		return false
	if not ResourceManager.spend_funds(faction, UNIT_PRODUCTION_COST):
		return false
	produce_unit(unit_data)
	return true

func produce_unit(unit_data: UnitResource):
	_is_producing = true
	print(building_name, " is producing: ", unit_data.unit_name)
	_produce_time_remaining = produce_time
	await get_tree().create_timer(produce_time).timeout
	_produce_time_remaining = 0.0
	spawn_unit(unit_data)
	_is_producing = false

func spawn_unit(unit_data: UnitResource):
	var unit: Unit = (load("res://scenes/units/unit_base.tscn") as PackedScene).instantiate()
	# Duplicate so we can set faction without touching the shared resource.
	var data := unit_data.duplicate() as UnitResource
	data.faction = faction
	unit.data = data
	get_tree().current_scene.add_child(unit)
	unit.global_position = global_position + Vector3(randf_range(-3.0, 3.0), 0.0, 5.0)

func apply_grid_influence():
	pass

func take_damage(amount: float):
	current_health -= amount
	if not _hq_warned and current_health < max_health * 0.5 and faction == GameSession.player_faction:
		_hq_warned = true
		AdvisorManager.speak("hq_attack")
		SoundManager.play("hq_alert")
	if current_health <= 0:
		explode()

func explode():
	print(building_name, " has been DE-ZONED.")
	building_destroyed.emit(building_name, faction)
	queue_free()
