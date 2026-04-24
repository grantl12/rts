extends CharacterBody3D
class_name Unit

## THE DEEP STATE: Base Unit Node

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

var _body_material: StandardMaterial3D
var _base_color: Color

func _ready():
	if data:
		current_vitality = data.max_vitality
		current_bureaucracy = data.max_bureaucracy
		current_supplies = data.max_supplies
		target_position = global_position
		_build_visuals()

		if data.unit_type == "Hero" or is_soul_leader:
			is_soul_leader = true
			soul_id = data.soul_id if data.soul_id != "" else str(get_instance_id())
			apply_soul_visuals()

func _build_visuals():
	_base_color = _get_faction_color()

	# Body capsule mesh — faction colored with soft emission
	var body = MeshInstance3D.new()
	var capsule = CapsuleMesh.new()
	capsule.radius = 0.35
	capsule.height = 1.4
	_body_material = StandardMaterial3D.new()
	_body_material.albedo_color = _base_color
	_body_material.emission_enabled = true
	_body_material.emission = _base_color * 0.5
	body.mesh = capsule
	body.material_override = _body_material
	add_child(body)
	body.position.y = 0.9

	# Colored base ring (replaces the transparent shadow)
	if has_node("Shadow"):
		var ring_mat = StandardMaterial3D.new()
		ring_mat.albedo_color = Color(_base_color.r, _base_color.g, _base_color.b, 0.7)
		ring_mat.emission_enabled = true
		ring_mat.emission = _base_color * 0.8
		ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		$Shadow.material = ring_mat

	# Unit name label floating above
	var name_label = Label3D.new()
	name_label.text = data.unit_name
	name_label.font_size = 6
	name_label.outline_size = 3
	name_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	name_label.modulate = _base_color
	name_label.position = Vector3(0, 2.6, 0)
	add_child(name_label)

func _get_faction_color() -> Color:
	match data.faction:
		"Regency":  return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)

func apply_soul_visuals():
	if _body_material:
		_body_material.emission = Color(1.0, 0.85, 0.2) * 0.8  # Gold soul glow

func set_selected(value: bool):
	is_selected = value
	if not _body_material:
		return
	if value:
		_body_material.emission = Color(0.3, 1.0, 0.6) * 1.0
	else:
		_body_material.emission = _base_color * 0.5
		if is_soul_leader:
			apply_soul_visuals()

func _physics_process(delta):
	if attack_cooldown > 0:
		attack_cooldown -= delta

	if not is_suppressed and current_bureaucracy < data.max_bureaucracy:
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

func move_to_target(_delta):
	var dir = Vector3(target_position.x - global_position.x, 0, target_position.z - global_position.z)
	if dir.length() > 0.1:
		velocity = dir.normalized() * 5.0
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
	if is_suppressed:
		return
	is_suppressed = true
	_status_label.text = "█ RED TAPE █"
	_status_label.modulate = Color(1.0, 0.15, 0.15)
	if _body_material:
		_body_material.albedo_color = Color(0.4, 0.4, 0.4)
	await get_tree().create_timer(3.0).timeout
	is_suppressed = false
	_status_label.text = ""
	if _body_material:
		_body_material.albedo_color = _base_color

func die():
	if is_soul_leader:
		var hero_data = {
			"unit_type": data.unit_name,
			"veterancy_rank": data.veterancy_rank,
			"status": "REDACTED"
		}
		SupabaseManager.save_hero_to_cloud(hero_data)
	queue_free()
