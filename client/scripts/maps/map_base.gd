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

func setup_neon_grid():
	pass

func _setup_navmesh() -> void:
	var nav_region := NavigationRegion3D.new()
	var nav_mesh := NavigationMesh.new()
	nav_mesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_MESH_INSTANCES
	nav_mesh.agent_height = 2.0
	nav_mesh.agent_radius = 0.5
	nav_mesh.cell_size = 0.3
	nav_mesh.region_min_size = 2.0
	nav_region.navigation_mesh = nav_mesh
	add_child(nav_region)
	await get_tree().process_frame
	nav_region.bake_navigation_mesh(false)
	print("Navigation mesh baked for: " + map_name)

func on_point_captured(point_name: String, faction: String):
	print("Point " + point_name + " AUDITED by " + faction)
	if faction in faction_control:
		faction_control[faction] = minf(faction_control[faction] + 10.0, 100.0)
	if "Neutral" in faction_control:
		faction_control["Neutral"] = maxf(faction_control["Neutral"] - 10.0, 0.0)
	update_grid_visuals()

func update_grid_visuals():
	pass
