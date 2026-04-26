extends Node3D

## THE DEEP STATE: Map Base Class
## Handles world state, "Audit" mechanics, and navigation mesh setup.

@export var map_name: String = "The Quad of Compliance"
@export var faction_control: Dictionary = {
	"Regency": 25.0,
	"Oligarchy": 25.0,
	"Neutral": 50.0
}

func _ready():
	print("Loading Map: " + map_name)
	setup_neon_grid()
	call_deferred("_setup_navmesh")
	_setup_fog()

func _setup_fog() -> void:
	var fog := preload("res://scripts/managers/fog_of_war_manager.gd").new()
	add_child(fog)

# ── Campus Dressing ────────────────────────────────────────────────────────────

func setup_neon_grid() -> void:
	_setup_environment()
	_apply_building_materials()
	_add_pathways()
	_add_fountain()
	_add_trees()
	_add_lamps()

func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode      = Environment.BG_COLOR
	env.background_color     = Color(0.04, 0.04, 0.08)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color  = Color(0.14, 0.17, 0.24)
	env.ambient_light_energy = 0.65
	env.glow_enabled         = true
	env.glow_intensity       = 0.30
	env.glow_bloom           = 0.04
	env.glow_hdr_threshold   = 1.2
	if has_node("WorldEnvironment"):
		($WorldEnvironment as WorldEnvironment).environment = env

func _make_mat(albedo: Color, emit: Color = Color.BLACK, emit_str: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	if emit_str > 0.0:
		m.emission_enabled = true
		m.emission = emit * emit_str
	return m

func _add_mesh_box(pos: Vector3, size: Vector3, mat: Material) -> void:
	var mi   := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size            = size
	mi.mesh              = mesh
	mi.material_override = mat
	mi.position          = pos
	add_child(mi)

func _add_mesh_cylinder(pos: Vector3, top_r: float, bot_r: float, h: float, segs: int, mat: Material) -> void:
	var mi   := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius      = top_r
	mesh.bottom_radius   = bot_r
	mesh.height          = h
	mesh.radial_segments = segs
	mi.mesh              = mesh
	mi.material_override = mat
	mi.position          = pos
	add_child(mi)

func _apply_building_materials() -> void:
	var concrete := _make_mat(Color(0.48, 0.46, 0.43))
	var windows  := _make_mat(Color(0.12, 0.14, 0.20), Color(0.15, 0.55, 0.9), 0.35)

	for wing_name in ["WestWing", "EastWing"]:
		if not has_node(wing_name):
			continue
		(get_node(wing_name) as CSGBox3D).material = concrete
		var x_sign := -1.0 if wing_name == "WestWing" else 1.0
		# Thin overlay plane to fake a window band at mid-height
		_add_mesh_box(Vector3(x_sign * 38.0, 5.5, 0.0), Vector3(0.05, 2.0, 40.0), windows)

func _add_pathways() -> void:
	var stone := _make_mat(Color(0.36, 0.34, 0.31))
	var plaza := _make_mat(Color(0.30, 0.29, 0.27))

	_add_mesh_box(Vector3(0, 0.52, 0),   Vector3(9, 0.06, 100), stone)   # N-S thoroughfare
	_add_mesh_box(Vector3(0, 0.52, 0),   Vector3(100, 0.06, 9), stone)   # E-W cross path
	_add_mesh_box(Vector3(0, 0.56, 0),   Vector3(22, 0.06, 22), plaza)   # central quad square
	_add_mesh_box(Vector3(0, 0.54, -28), Vector3(16, 0.05, 14), plaza)   # north apron
	_add_mesh_box(Vector3(0, 0.54, 28),  Vector3(16, 0.05, 14), plaza)   # south apron

func _add_fountain() -> void:
	var stone := _make_mat(Color(0.32, 0.30, 0.28))
	var water := _make_mat(Color(0.12, 0.48, 0.72, 0.75), Color(0.20, 0.70, 1.0), 0.55)

	_add_mesh_cylinder(Vector3(0, 0.80, 0), 3.0, 3.2, 0.55, 32, stone)  # basin ring
	_add_mesh_cylinder(Vector3(0, 0.82, 0), 2.6, 2.6, 0.06, 32, water)  # water surface
	_add_mesh_cylinder(Vector3(0, 1.20, 0), 0.10, 0.14, 1.20, 12, stone) # column
	_add_mesh_cylinder(Vector3(0, 1.88, 0), 0.22, 0.10, 0.16, 12, stone) # cap

func _add_trees() -> void:
	var trunk_mat  := _make_mat(Color(0.28, 0.19, 0.11))
	var canopy_mat := _make_mat(Color(0.15, 0.30, 0.13), Color(0.10, 0.25, 0.09), 0.12)

	var positions: Array[Vector3] = [
		Vector3( 12, 0, -22), Vector3(-12, 0, -22),
		Vector3( 12, 0,  -8), Vector3(-12, 0,  -8),
		Vector3( 12, 0,   8), Vector3(-12, 0,   8),
		Vector3( 12, 0,  22), Vector3(-12, 0,  22),
		Vector3( 10, 0, -33), Vector3(-10, 0, -33),
		Vector3( 10, 0,  33), Vector3(-10, 0,  33),
	]
	for p in positions:
		_add_tree(p, trunk_mat, canopy_mat)

func _add_tree(pos: Vector3, trunk_mat: Material, canopy_mat: Material) -> void:
	_add_mesh_cylinder(pos + Vector3(0, 1.2, 0), 0.11, 0.17, 2.4, 8, trunk_mat)
	var mi   := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 1.7
	mesh.height = 3.0
	mi.mesh              = mesh
	mi.material_override = canopy_mat
	mi.position          = pos + Vector3(0, 3.8, 0)
	add_child(mi)

func _add_lamps() -> void:
	var pole_mat  := _make_mat(Color(0.58, 0.56, 0.52))
	var globe_mat := _make_mat(Color(0.96, 0.92, 0.78), Color(1.0, 0.90, 0.65), 1.6)

	var positions: Array[Vector3] = [
		Vector3( 5.5, 0, -36), Vector3(-5.5, 0, -36),
		Vector3( 5.5, 0, -14), Vector3(-5.5, 0, -14),
		Vector3( 5.5, 0,  14), Vector3(-5.5, 0,  14),
		Vector3( 5.5, 0,  36), Vector3(-5.5, 0,  36),
	]
	for p in positions:
		_add_lamp(p, pole_mat, globe_mat)

func _add_lamp(pos: Vector3, pole_mat: Material, globe_mat: Material) -> void:
	_add_mesh_cylinder(pos + Vector3(0, 2.1, 0), 0.05, 0.09, 4.2, 6, pole_mat)
	var mi   := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 0.26
	mi.mesh              = mesh
	mi.material_override = globe_mat
	mi.position          = pos + Vector3(0, 4.45, 0)
	add_child(mi)

# ── Navigation ─────────────────────────────────────────────────────────────────

func _setup_navmesh() -> void:
	var nav_region := NavigationRegion3D.new()
	var nav_mesh   := NavigationMesh.new()
	# STATIC_COLLIDERS so CSGBox3D buildings register as obstacles
	nav_mesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	nav_mesh.geometry_collision_mask = 1
	nav_mesh.agent_height    = 2.0
	nav_mesh.agent_radius    = 0.4
	nav_mesh.agent_max_climb = 0.3
	nav_mesh.agent_max_slope = 25.0
	nav_mesh.cell_size       = 0.35
	nav_mesh.region_min_size = 2.0
	nav_region.navigation_mesh = nav_mesh
	add_child(nav_region)
	await get_tree().process_frame
	nav_region.bake_navigation_mesh(false)
	print("Navigation mesh baked for: " + map_name)

# ── Capture Logic ──────────────────────────────────────────────────────────────

func on_point_captured(point_name: String, faction: String):
	print("Point " + point_name + " AUDITED by " + faction)
	if faction == GameSession.player_faction:
		AdvisorManager.speak("capture")
	if faction in faction_control:
		faction_control[faction] = minf(faction_control[faction] + 10.0, 100.0)
	if "Neutral" in faction_control:
		faction_control["Neutral"] = maxf(faction_control["Neutral"] - 10.0, 0.0)
	update_grid_visuals()

func update_grid_visuals():
	pass
