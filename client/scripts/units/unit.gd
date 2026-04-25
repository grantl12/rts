extends CharacterBody3D
class_name Unit

## THE DEEP STATE: Base Unit Node

@export var data: UnitResource
@export var is_soul_leader: bool = false
@export var soul_id: String = ""

# Veterancy / XP — cumulative XP thresholds to reach each rank (index = rank - 1)
const RANK_XP    := [0.0, 50.0, 150.0, 300.0, 500.0, INF]
const RANK_NAMES := ["AGENT", "FIELD AGENT", "SR. OPERATIVE", "DEPT. HEAD", "EXECUTIVE"]
# Per rank-up bonus: +8 % damage output, +8 % max vitality
const RANK_STAT_BONUS := 0.08

@onready var _status_label: Label3D = $StatusLabel
@onready var _nav_agent: NavigationAgent3D = $NavigationAgent3D

var target_position: Vector3
var target_unit: Unit = null
var target_building: Building = null
var is_selected: bool = false
var current_vitality: float
var current_bureaucracy: float
var current_supplies: float
var attack_cooldown: float = 0.0
var is_suppressed: bool = false

# Veterancy state
var current_rank: int   = 1
var current_xp: float   = 0.0
var _damage_mult: float = 1.0
var _health_mult: float = 1.0
var _passive_xp_timer: float = 0.0

var _body_material: StandardMaterial3D
var _head_material: StandardMaterial3D
var _base_color: Color
var _health_label: Label3D
var _bars_dirty: bool = false

func _ready():
	if data:
		# Apply any pre-existing veterancy rank (e.g. loaded from save)
		current_rank = clampi(data.veterancy_rank, 1, 5)
		for _r in range(1, current_rank):
			_damage_mult += RANK_STAT_BONUS
			_health_mult += RANK_STAT_BONUS

		current_vitality    = data.max_vitality * _health_mult
		current_bureaucracy = data.max_bureaucracy
		current_supplies    = data.max_supplies
		target_position     = global_position
		_build_visuals()

		if data.unit_type == "Hero" or is_soul_leader:
			is_soul_leader = true
			soul_id = data.soul_id if data.soul_id != "" else str(get_instance_id())
			apply_soul_visuals()

func _build_visuals():
	_base_color = _get_faction_color()

	# Body — slim capsule, faction colored
	var body = MeshInstance3D.new()
	var capsule = CapsuleMesh.new()
	capsule.radius = 0.22
	capsule.height = 1.1
	_body_material = StandardMaterial3D.new()
	_body_material.albedo_color = _base_color
	_body_material.emission_enabled = true
	_body_material.emission = _base_color * 0.4
	body.mesh = capsule
	body.material_override = _body_material
	body.position.y = 0.7
	add_child(body)

	# Head sphere
	var head = MeshInstance3D.new()
	var sphere = SphereMesh.new()
	sphere.radius = 0.2
	sphere.height = 0.4
	_head_material = StandardMaterial3D.new()
	_head_material.albedo_color = _base_color.lightened(0.25)
	_head_material.emission_enabled = true
	_head_material.emission = _base_color * 0.3
	head.mesh = sphere
	head.material_override = _head_material
	head.position.y = 1.5
	add_child(head)

	# Soul leader crown indicator
	if is_soul_leader:
		var crown = MeshInstance3D.new()
		var crown_mesh = CylinderMesh.new()
		crown_mesh.top_radius = 0.0
		crown_mesh.bottom_radius = 0.18
		crown_mesh.height = 0.28
		var crown_mat = StandardMaterial3D.new()
		crown_mat.albedo_color = Color(1.0, 0.85, 0.1)
		crown_mat.emission_enabled = true
		crown_mat.emission = Color(1.0, 0.75, 0.0) * 1.2
		crown_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		crown.mesh = crown_mesh
		crown.material_override = crown_mat
		crown.position.y = 1.78
		add_child(crown)

	# Base ring
	if has_node("Shadow"):
		var ring_mat = StandardMaterial3D.new()
		ring_mat.albedo_color = Color(_base_color.r, _base_color.g, _base_color.b, 0.6)
		ring_mat.emission_enabled = true
		ring_mat.emission = _base_color * 0.7
		ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		$Shadow.material = ring_mat

	# Name label
	var name_label = Label3D.new()
	name_label.text = data.unit_name
	name_label.font_size = 6
	name_label.outline_size = 3
	name_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	name_label.modulate = _base_color
	name_label.position = Vector3(0, 2.6, 0)
	add_child(name_label)

	# Health bars label (above head, below status)
	_health_label = Label3D.new()
	_health_label.font_size = 7
	_health_label.outline_size = 2
	_health_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_health_label.position = Vector3(0, 1.95, 0)
	add_child(_health_label)
	_update_bars()

func _get_faction_color() -> Color:
	match data.faction:
		"Regency":  return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)

func apply_soul_visuals():
	if _body_material:
		_body_material.emission = Color(1.0, 0.85, 0.2) * 0.9

func set_selected(value: bool):
	is_selected = value
	if not _body_material:
		return
	if value:
		_body_material.emission = Color(0.3, 1.0, 0.6) * 1.0
		_head_material.emission = Color(0.3, 1.0, 0.6) * 0.7
	else:
		_body_material.emission = _base_color * 0.4
		_head_material.emission = _base_color * 0.3
		if is_soul_leader:
			apply_soul_visuals()

func _physics_process(delta):
	if attack_cooldown > 0:
		attack_cooldown -= delta

	if not is_suppressed and current_bureaucracy < data.max_bureaucracy:
		current_bureaucracy += delta * 2.0
		_bars_dirty = true

	# Passive XP only for player-controlled units (1 XP every 10 s)
	if data and data.faction == GameSession.player_faction:
		_passive_xp_timer -= delta
		if _passive_xp_timer <= 0.0:
			_passive_xp_timer = 10.0
			_award_xp(1.0)

	if _bars_dirty:
		_update_bars()
		_bars_dirty = false

	if target_building and is_instance_valid(target_building):
		handle_building_combat(delta)
	elif target_unit and is_instance_valid(target_unit):
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

func handle_building_combat(_delta):
	var dist = global_position.distance_to(target_building.global_position)
	if dist <= data.attack_range:
		velocity = Vector3.ZERO
		if attack_cooldown <= 0:
			_shoot_building()
	else:
		target_position = target_building.global_position
		move_to_target(_delta)

func _shoot_building():
	if current_supplies <= 0 or is_suppressed:
		return
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	target_building.take_damage(data.damage * _damage_mult * 0.75)
	_award_xp(3.0)

func shoot():
	if current_supplies <= 0 or is_suppressed:
		return
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	target_unit.take_damage(data.damage * _damage_mult * 0.5, "Bureaucracy")
	if randf() <= data.accuracy:
		target_unit.take_damage(data.damage * _damage_mult, "Vitality")
	# Kill confirmed — target freed itself
	if not is_instance_valid(target_unit):
		_award_xp(25.0)

# ── Veterancy ─────────────────────────────────────────────────────────────────

func _award_xp(amount: float) -> void:
	if data.faction != GameSession.player_faction:
		return
	current_xp += amount
	_check_rank_up()

func _check_rank_up() -> void:
	if current_rank >= 5:
		return
	if current_xp >= RANK_XP[current_rank]:
		_do_rank_up()

func _do_rank_up() -> void:
	current_rank    += 1
	_damage_mult    += RANK_STAT_BONUS
	_health_mult    += RANK_STAT_BONUS
	# Grant bonus health headroom
	var hp_bonus := data.max_vitality * RANK_STAT_BONUS
	current_vitality = minf(current_vitality + hp_bonus, data.max_vitality * _health_mult)
	_bars_dirty = true
	_show_promotion_effect()
	# Handle rapid multi-rank jumps from large XP awards
	_check_rank_up()

func _show_promotion_effect() -> void:
	if _body_material:
		_body_material.emission = Color(1.0, 0.9, 0.2) * 2.8
	_status_label.text = "▲ " + RANK_NAMES[current_rank - 1]
	_status_label.modulate = Color(1.0, 0.9, 0.2)
	AdvisorManager.speak("promotion")
	var tw := create_tween()
	tw.tween_interval(2.2)
	tw.tween_callback(func():
		if not is_instance_valid(self):
			return
		_status_label.text = ""
		if not is_selected and _body_material:
			if is_soul_leader:
				apply_soul_visuals()
			else:
				_body_material.emission = _base_color * 0.4
	)

# ── Movement ───────────────────────────────────────────────────────────────────

func move_to_target(_delta):
	if global_position.distance_to(target_position) <= 0.5:
		velocity = Vector3.ZERO
		return

	_nav_agent.target_position = target_position

	var dir: Vector3
	if not _nav_agent.is_navigation_finished():
		var next_pos := _nav_agent.get_next_path_position()
		dir = next_pos - global_position
	else:
		# Fallback: straight-line movement (before navmesh is ready)
		dir = target_position - global_position

	dir.y = 0.0
	if dir.length() > 0.05:
		velocity = dir.normalized() * 5.0
		move_and_slide()
	else:
		velocity = Vector3.ZERO

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
	_bars_dirty = true
	if current_vitality <= 0:
		die()

func _update_bars():
	if not _health_label or not data:
		return
	var vit_pct := clampf(current_vitality / (data.max_vitality * _health_mult), 0.0, 1.0)
	var bur_pct := clampf(current_bureaucracy / data.max_bureaucracy, 0.0, 1.0)
	var vn := int(round(vit_pct * 6))
	var bn := int(round(bur_pct * 6))
	_health_label.text = "█".repeat(vn) + "░".repeat(6 - vn) + "\n" + "█".repeat(bn) + "░".repeat(6 - bn)
	_health_label.modulate = Color(0.3 + vit_pct * 0.7, 0.9 * vit_pct, 0.2)

func is_in_cover() -> bool:
	return false

func apply_suppression():
	if is_suppressed:
		return
	is_suppressed = true
	if data.faction == GameSession.player_faction:
		AdvisorManager.speak("suppressed")
	_status_label.text = "█ RED TAPE █"
	_status_label.modulate = Color(1.0, 0.15, 0.15)
	if _body_material:
		_body_material.albedo_color = Color(0.35, 0.35, 0.35)
	if _head_material:
		_head_material.albedo_color = Color(0.35, 0.35, 0.35)
	await get_tree().create_timer(3.0).timeout
	is_suppressed = false
	_status_label.text = ""
	if _body_material:
		_body_material.albedo_color = _base_color
	if _head_material:
		_head_material.albedo_color = _base_color.lightened(0.25)

func die():
	if is_soul_leader:
		var hero_data := {
			"unit_type": data.unit_name,
			"faction": data.faction,
			"veterancy_rank": current_rank,
			"status": "REDACTED"
		}
		SupabaseManager.save_hero_to_cloud(hero_data)
	queue_free()
