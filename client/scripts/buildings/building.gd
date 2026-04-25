extends StaticBody3D
class_name Building

## THE DEEP STATE: Base Building
## Handles health, production, grid influence, and destruction signalling.

signal building_destroyed(building_name: String, faction: String)

@export var building_name: String = "Structure"
@export var faction: String = "Neutral"
@export var cost: int = 100
@export var max_health: float = 500.0
@export var producible_unit_path: String = ""

const UNIT_PRODUCTION_COST := 50

var current_health: float
var is_constructed: bool = false
var _is_producing: bool = false
var _hq_warned: bool = false

func _ready():
	current_health = max_health
	_apply_faction_visuals()
	if is_constructed:
		apply_grid_influence()

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
	await get_tree().create_timer(5.0).timeout
	spawn_unit(unit_data)
	_is_producing = false

func spawn_unit(unit_data: UnitResource):
	var unit: Unit = (load("res://scenes/units/unit_base.tscn") as PackedScene).instantiate()
	unit.data = unit_data
	get_tree().current_scene.add_child(unit)
	unit.global_position = global_position + Vector3(randf_range(-3.0, 3.0), 0.0, 5.0)

func apply_grid_influence():
	pass

func take_damage(amount: float):
	current_health -= amount
	if not _hq_warned and current_health < max_health * 0.5 and faction == GameSession.player_faction:
		_hq_warned = true
		AdvisorManager.speak("hq_attack")
	if current_health <= 0:
		explode()

func explode():
	print(building_name, " has been DE-ZONED.")
	building_destroyed.emit(building_name, faction)
	queue_free()
