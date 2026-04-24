extends CharacterBody3D
class_name Unit

## THE DEEP STATE: Base Unit Node
## Handles 3D movement, combat state, and FTL-style systems.

@export var data: UnitResource
@export var is_soul_leader: bool = false
@export var soul_id: String = ""

@onready var navigation_agent: NavigationAgent3D = $NavigationAgent3D
@onready var _status_label: Label3D = $StatusLabel

var target_position: Vector3
var target_unit: Unit = null
var is_selected: bool = false
var current_vitality: float
var current_bureaucracy: float
var current_supplies: float
var attack_cooldown: float = 0.0
var is_suppressed: bool = false
var _base_modulate: Color = Color(1, 1, 1)

func _ready():
	if data:
		current_vitality = data.max_vitality
		current_bureaucracy = data.max_bureaucracy
		current_supplies = data.max_supplies
		target_position = global_position
		
		if data.unit_type == "Hero" or is_soul_leader:
			is_soul_leader = true
			soul_id = data.soul_id if data.soul_id != "" else str(get_instance_id())
			apply_soul_visuals()

func apply_soul_visuals():
	_base_modulate = Color(1.5, 1.5, 1.5)
	if has_node("Sprite3D"):
		$Sprite3D.modulate = _base_modulate

func set_selected(value: bool):
	is_selected = value
	if has_node("Sprite3D"):
		$Sprite3D.modulate = Color(0.4, 1.0, 0.6) if value else _base_modulate

func _physics_process(delta):
	if attack_cooldown > 0:
		attack_cooldown -= delta
	
	# Suppression Recovery
	if !is_suppressed and current_bureaucracy < data.max_bureaucracy:
		current_bureaucracy += delta * 2.0 

	if target_unit and is_instance_valid(target_unit):
		handle_combat(delta)
	elif global_position.distance_to(target_position) > 0.5:
		move_to_target(delta)

func handle_combat(_delta):
	var dist = global_position.distance_to(target_unit.global_position)
	if dist <= data.attack_range:
		velocity = Vector3.ZERO
		if attack_cooldown <= 0:
			shoot()
	else:
		target_position = target_unit.global_position
		move_to_target(_delta)

func shoot():
	if current_supplies <= 0 or is_suppressed:
		return
		
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	
	target_unit.take_damage(data.damage * 0.5, "Bureaucracy")
	
	if randf() <= data.accuracy:
		target_unit.take_damage(data.damage, "Vitality")
	
	print(data.unit_name + " Fired at " + target_unit.data.unit_name)

func move_to_target(_delta):
	navigation_agent.target_position = target_position
	if navigation_agent.is_navigation_finished():
		return
	var next_pos = navigation_agent.get_next_path_position()
	velocity = (next_pos - global_position).normalized() * 5.0
	move_and_slide()

func take_damage(amount: float, type: String = "Vitality"):
	var final_amount = amount
	
	if type == "Vitality" and is_in_cover():
		final_amount *= 0.5
		
	if type == "Vitality":
		current_vitality -= final_amount
	elif type == "Bureaucracy":
		current_bureaucracy -= final_amount
		if current_bureaucracy < (data.max_bureaucracy * 0.3):
			apply_suppression()
	
	if current_vitality <= 0:
		die()

func is_in_cover() -> bool:
	return false 

func apply_suppression():
	if is_suppressed: return
	is_suppressed = true
	_status_label.text = "█ RED TAPE █"
	_status_label.modulate = Color(1.0, 0.15, 0.15)
	print(data.unit_name + " IS SUPPRESSED: Bureaucracy failure.")
	await get_tree().create_timer(3.0).timeout
	is_suppressed = false
	_status_label.text = ""

func die():
	if is_soul_leader:
		print("CRITICAL LOSS: The Soul of the squad (", data.unit_name, ") has been REDACTED.")
		var hero_data = {
			"unit_type": data.unit_name,
			"veterancy_rank": data.veterancy_rank,
			"status": "REDACTED"
		}
		SupabaseManager.save_hero_to_cloud(hero_data)
	else:
		print(data.unit_name + " has been discarded.")
	queue_free()

