extends CharacterBody3D
class_name Civilian

## THE DEEP STATE: Civilian NPC
## Wanders the map. Sucked into Holding Pens by their capture zones.
## Freed on pen destruction — panics and scatters.

@export var wander_radius: float = 10.0
@export var wander_speed:  float = 1.1

var _home:     Vector3
var _target:   Vector3
var _mesh_mat: StandardMaterial3D
var _captured: bool = false

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready() -> void:
	add_to_group("civilians")
	_home   = global_position
	_target = global_position
	_build_visuals()
	_schedule_wander()

func _build_visuals() -> void:
	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.22
	cap.height = 0.85
	col.shape    = cap
	col.position = Vector3(0, 0.5, 0)
	add_child(col)

	_mesh_mat = StandardMaterial3D.new()
	_mesh_mat.albedo_color = Color(0.72, 0.69, 0.63)

	var mi   := MeshInstance3D.new()
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.20
	mesh.height = 0.80
	mi.mesh              = mesh
	mi.material_override = _mesh_mat
	mi.position          = Vector3(0, 0.5, 0)
	add_child(mi)

	var lbl := Label3D.new()
	lbl.text         = "CIV"
	lbl.font_size    = 4
	lbl.outline_size = 1
	lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.modulate     = Color(0.85, 0.82, 0.72, 0.65)
	lbl.position     = Vector3(0, 1.12, 0)
	add_child(lbl)

# ── Wander AI ─────────────────────────────────────────────────────────────────

func _schedule_wander() -> void:
	await get_tree().create_timer(randf_range(2.0, 5.5)).timeout
	if not is_instance_valid(self) or _captured:
		return
	var angle := randf() * TAU
	var dist  := randf_range(2.0, wander_radius)
	_target = _home + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
	_schedule_wander()

func _physics_process(_delta: float) -> void:
	if _captured:
		return
	var dir := _target - global_position
	dir.y = 0.0
	if dir.length_squared() < 0.3:
		return
	velocity   = dir.normalized() * wander_speed
	velocity.y = 0.0
	move_and_slide()

# ── Capture / panic ────────────────────────────────────────────────────────────

func get_captured() -> void:
	_captured = true
	queue_free()

func panic() -> void:
	wander_speed = 3.8
	_mesh_mat.albedo_color = Color(1.0, 0.55, 0.2)
	var angle  := randf() * TAU
	_target    = global_position + Vector3(cos(angle) * wander_radius, 0.0, sin(angle) * wander_radius)
	_home      = global_position
	_captured  = false
	_schedule_wander()
