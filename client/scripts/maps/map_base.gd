extends Node3D

## THE DEEP STATE: Map Base Class
## Handles the "Neon Grid" world-state and "Audit" mechanics.

@export var map_name: String = "The Quad of Compliance"
@export var faction_control: Dictionary = {
	"Regency": 25.0,
	"Oligarchy": 25.0,
	"Neutral": 50.0
}

func _ready():
	print("Loading Map: " + map_name)
	setup_neon_grid()

func setup_neon_grid():
	# In a real scene, this would update the shader uniforms
	# for all surfaces using neon_grid.gdshader
	pass

func on_point_captured(point_name: String, faction: String):
	print("Point " + point_name + " has been AUDITED by " + faction)
	# Shift global control percentages
	if faction == "Regency":
		faction_control["Regency"] += 10.0
		faction_control["Neutral"] -= 10.0
	elif faction == "Oligarchy":
		faction_control["Oligarchy"] += 10.0
		faction_control["Neutral"] -= 10.0
	
	update_grid_visuals()

func update_grid_visuals():
	# This would update the Shader uniforms
	pass
