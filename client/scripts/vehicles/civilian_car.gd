extends CharacterBody3D
class_name CivilianCar

## THE DEEP STATE: Civilian Vehicle
## Drives preset loops around The Quad. Clickable for flavor text.
## During ROE 5: panics. When an HVP boards: escapes to a secondary locale.
## Wrecked cars become permanent cover obstacles.

const DRIVE_SPEED  := 7.0
const ESCAPE_SPEED := 15.0
const WRECK_HEALTH := 80.0

const FLAVOR_TEXTS: Array[String] = [
	"Driving to a job that was automated six months ago.",
	"Registration: expired. Insurance: lapsed. Threat level: unclassified.",
	"Civilian asset in transit. Destination: irrelevant.",
	"Plate: unregistered. Status: not yet.",
	"Vehicle occupant last audited: never.",
	"Nothing to declare. Nothing to hide. Probably.",
	"Emissions: over limit. Owner: unaware. Day: going fine.",
	"GPS says: turn left. GPS always says turn left.",
	"Heading somewhere. Unclear where. Not our problem.",
	"Outstanding parking violations: 3. Outstanding warrants: unknown.",
]

var waypoints: Array[Vector3] = []
var _wp_idx:   int   = 0
var _health:   float = WRECK_HEALTH
var _wrecked:  bool  = false
var _escaping: bool  = false
var _panicking: bool = false

var _escape_dest:      Vector3  = Vector3.ZERO
var _runner_passenger: Civilian = null

var _body_mat: StandardMaterial3D
var _flavor:   String = ""

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready() -> void:
	add_to_group("civilian_vehicles")
	_flavor = FLAVOR_TEXTS[randi() % FLAVOR_TEXTS.size()]
	_build_visuals()
	if not waypoints.is_empty():
		global_position   = waypoints[_wp_idx]
		global_position.y = 0.5

func _build_visuals() -> void:
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size     = Vector3(2.0, 1.0, 4.2)
	col.shape    = box
	col.position = Vector3(0, 0.55, 0)
	add_child(col)

	_body_mat             = StandardMaterial3D.new()
	_body_mat.albedo_color = _rand_color()

	var body      := MeshInstance3D.new()
	var body_mesh := BoxMesh.new()
	body_mesh.size        = Vector3(1.9, 0.78, 4.0)
	body.mesh             = body_mesh
	body.material_override = _body_mat
	body.position          = Vector3(0, 0.54, 0)
	add_child(body)

	var roof_mat           := StandardMaterial3D.new()
	roof_mat.albedo_color   = _body_mat.albedo_color.darkened(0.28)
	var roof      := MeshInstance3D.new()
	var roof_mesh := BoxMesh.new()
	roof_mesh.size        = Vector3(1.6, 0.48, 2.0)
	roof.mesh             = roof_mesh
	roof.material_override = roof_mat
	roof.position          = Vector3(0, 1.21, -0.22)
	add_child(roof)

	var wheel_mat             := StandardMaterial3D.new()
	wheel_mat.albedo_color     = Color(0.08, 0.08, 0.08)
	for wx: float in [-1.05, 1.05]:
		for wz: float in [-1.28, 1.28]:
			var wheel      := MeshInstance3D.new()
			var wheel_mesh := CylinderMesh.new()
			wheel_mesh.top_radius    = 0.29
			wheel_mesh.bottom_radius = 0.29
			wheel_mesh.height        = 0.22
			wheel.mesh             = wheel_mesh
			wheel.material_override = wheel_mat
			wheel.position          = Vector3(wx, 0.29, wz)
			wheel.rotation_degrees  = Vector3(0, 0, 90)
			add_child(wheel)

# ── Movement ───────────────────────────────────────────────────────────────────

func _physics_process(_delta: float) -> void:
	if _wrecked or waypoints.is_empty() and not _escaping:
		return

	var target: Vector3
	var spd:    float

	if _escaping:
		target = _escape_dest
		spd    = ESCAPE_SPEED
		if global_position.distance_to(target) < 2.5:
			_finish_escape()
			return
	else:
		target = waypoints[_wp_idx]
		spd    = ESCAPE_SPEED if _panicking else DRIVE_SPEED
		if global_position.distance_to(target) < 2.0:
			_wp_idx = (_wp_idx + 1) % waypoints.size()
			return

	var dir := target - global_position
	dir.y = 0.0
	if dir.length_squared() < 0.05:
		return
	velocity   = dir.normalized() * spd
	velocity.y = 0.0
	move_and_slide()
	var look_tgt := global_position + dir.normalized()
	look_at(Vector3(look_tgt.x, global_position.y, look_tgt.z), Vector3.UP)

# ── Runner boarding / escape ───────────────────────────────────────────────────

func pick_up_runner(civ: Civilian, escape_dest: Vector3) -> void:
	_runner_passenger      = civ
	civ._captured          = true          # freeze without deleting
	civ.global_position    = Vector3(0, -50, 0)  # stash underground (avoid pen zones)
	_escape_dest           = escape_dest
	_escaping              = true
	_panicking             = false

func _finish_escape() -> void:
	_escaping = false
	if is_instance_valid(_runner_passenger):
		_runner_passenger.global_position = global_position + Vector3(2.0, 0.0, 0.0)
		_runner_passenger._captured       = false
		_runner_passenger.is_runner       = false
		_runner_passenger.wander_radius   = 6.0
		_runner_passenger._home           = _runner_passenger.global_position
		_runner_passenger._schedule_wander()
		_runner_passenger = null
	if not waypoints.is_empty():
		_wp_idx = 0

# ── Damage & wreck ─────────────────────────────────────────────────────────────

func take_damage(amount: float) -> void:
	if _wrecked:
		return
	_health -= amount
	if _health <= 0.0:
		_wreck()

func _wreck() -> void:
	_wrecked                    = true
	_body_mat.albedo_color       = Color(0.20, 0.15, 0.11)
	_body_mat.emission_enabled   = true
	_body_mat.emission           = Color(1.0, 0.28, 0.0) * 0.65
	velocity                     = Vector3.ZERO
	if is_instance_valid(_runner_passenger):
		_runner_passenger.global_position = global_position + Vector3(1.5, 0.0, 1.5)
		_runner_passenger._captured       = false
		_runner_passenger.is_runner       = false
		_runner_passenger.wander_radius   = 6.0
		_runner_passenger._home           = _runner_passenger.global_position
		_runner_passenger._schedule_wander()
		_runner_passenger = null
	add_to_group("cover")
	WorldStateManager.record_wreck("civilian_car", global_position)
	InfamyManager.add_infamy(5, "vehicle_wrecked")

# ── Panic (ROE 5) ──────────────────────────────────────────────────────────────

func panic() -> void:
	if _wrecked or _escaping:
		return
	_panicking = true
	waypoints  = [
		Vector3(randf_range(-36.0, 36.0), 0.5, randf_range(-44.0, 44.0)),
		global_position,
	]
	_wp_idx = 0

# ── Public API ─────────────────────────────────────────────────────────────────

func get_flavor() -> String:
	return _flavor

func _rand_color() -> Color:
	var palette: Array[Color] = [
		Color(0.70, 0.70, 0.70),
		Color(0.16, 0.16, 0.16),
		Color(0.60, 0.14, 0.12),
		Color(0.14, 0.26, 0.52),
		Color(0.63, 0.58, 0.46),
		Color(0.24, 0.40, 0.21),
		Color(0.52, 0.44, 0.22),
	]
	return palette[randi() % palette.size()]
