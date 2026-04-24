extends StaticBody3D
class_name Building

## THE DEEP STATE: Base Building
## Handles health, unit production, and grid influence.

@export var building_name: String = "Structure"
@export var faction: String = "Neutral"
@export var cost: int = 100
@export var max_health: float = 500.0
@export var production_queue: Array[UnitResource] = []

var current_health: float
var is_constructed: bool = false

func _ready():
	current_health = max_health
	if is_constructed:
		apply_grid_influence()

func produce_unit(unit_data: UnitResource):
	print(building_name, " is auditing a new ", unit_data.unit_name)
	# Production timer logic would go here
	await get_tree().create_timer(5.0).timeout
	spawn_unit(unit_data)

func spawn_unit(unit_data: UnitResource):
	var unit_scene = load("res://scenes/units/unit_base.tscn")
	var unit_instance = unit_scene.instantiate()
	unit_instance.data = unit_data
	get_parent().add_child(unit_instance)
	unit_instance.global_position = global_position + Vector3(0, 0, 5)

func apply_grid_influence():
	# Buildings shift the neon grid color around them
	pass

func take_damage(amount: float):
	current_health -= amount
	if current_health <= 0:
		explode()

func explode():
	print(building_name, " has been DE-ZONED.")
	queue_free()
