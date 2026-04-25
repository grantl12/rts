extends Node3D

## THE DEEP STATE: Fog of War — "Data Blackout"
## Builds the fog mesh, pushes vision positions to the shader,
## and shows/hides enemy units + buildings based on player sight lines.

const VISION_RADIUS    := 28.0   # world units
const UPDATE_INTERVAL  := 0.12   # seconds between visibility ticks
const MAX_VIS_SOURCES  := 32     # must match shader array size

var _fog_mat: ShaderMaterial
var _tick_timer: float = 0.0

func _ready() -> void:
	_build_fog_mesh()

# ── Fog mesh ──────────────────────────────────────────────────────────────────

func _build_fog_mesh() -> void:
	var mesh_inst := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(200.0, 200.0)
	plane.subdivide_width  = 0
	plane.subdivide_depth  = 0
	mesh_inst.mesh = plane
	# Just above the ground surface (top face at y = 0.5) but below unit visuals
	mesh_inst.position = Vector3(0.0, 0.55, 0.0)

	_fog_mat = ShaderMaterial.new()
	_fog_mat.shader = load("res://shaders/data_blackout.gdshader")
	_fog_mat.set_shader_parameter("vis_radius",  VISION_RADIUS)
	_fog_mat.set_shader_parameter("fog_density", 0.88)
	_fog_mat.set_shader_parameter("vis_count",   0)
	mesh_inst.material_override = _fog_mat
	add_child(mesh_inst)

# ── Per-tick update ───────────────────────────────────────────────────────────

func _physics_process(delta: float) -> void:
	_tick_timer -= delta
	if _tick_timer > 0.0:
		return
	_tick_timer = UPDATE_INTERVAL
	_tick()

func _tick() -> void:
	var vis_pos := _gather_vision_sources()
	_push_shader(vis_pos)
	_update_entity_visibility(vis_pos)

func _gather_vision_sources() -> Array[Vector3]:
	var player := GameSession.player_faction
	var out: Array[Vector3] = []

	for node in get_tree().get_nodes_in_group("units"):
		if out.size() >= MAX_VIS_SOURCES:
			break
		if node is Unit and is_instance_valid(node) and node.data.faction == player:
			out.append(node.global_position)

	var scene := get_tree().current_scene
	for node in scene.get_children():
		if out.size() >= MAX_VIS_SOURCES:
			break
		if node is Building and is_instance_valid(node) and node.faction == player:
			out.append(node.global_position)

	return out

func _push_shader(vis_pos: Array[Vector3]) -> void:
	var count := mini(vis_pos.size(), MAX_VIS_SOURCES)
	var packed := PackedVector3Array()
	packed.resize(MAX_VIS_SOURCES)
	for i in MAX_VIS_SOURCES:
		packed[i] = vis_pos[i] if i < count else Vector3.ZERO
	_fog_mat.set_shader_parameter("vis_positions", packed)
	_fog_mat.set_shader_parameter("vis_count",     count)

func _update_entity_visibility(vis_pos: Array[Vector3]) -> void:
	var player := GameSession.player_faction

	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node):
			continue
		# Player units always visible; enemy units only when in sight
		node.visible = (node.data.faction == player) or _in_vision(node.global_position, vis_pos)

	var scene := get_tree().current_scene
	for node in scene.get_children():
		if not (node is Building) or not is_instance_valid(node):
			continue
		node.visible = (node.faction == player) or _in_vision(node.global_position, vis_pos)

func _in_vision(pos: Vector3, vis_pos: Array[Vector3]) -> bool:
	for vp in vis_pos:
		if pos.distance_to(vp) <= VISION_RADIUS:
			return true
	return false
