extends Area3D
class_name AuditPoint

## THE DEEP STATE: Capture Point & Sabotage Target

signal captured(faction_name)

@export var point_name: String = "Central Plaza"
@export var capture_speed: float = 10.0
@export var sabotage_speed: float = 5.0
@export var total_audit_required: float = 100.0

var current_audit_value: float = 0.0
var controlling_faction: String = "Neutral"
var units_in_area: Array[Node3D] = []

var _ring_material: StandardMaterial3D
var _point_label: Label3D
var _progress_label: Label3D

func _ready():
	add_to_group("audit_points")
	_build_visuals()
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_update_visual()

func _build_visuals():
	# Ground ring
	_ring_material = StandardMaterial3D.new()
	_ring_material.albedo_color = Color(0.5, 0.5, 0.5, 0.35)
	_ring_material.emission_enabled = true
	_ring_material.emission = Color(0.5, 0.5, 0.5) * 0.25
	_ring_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ring_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

	var ring = MeshInstance3D.new()
	var ring_mesh = CylinderMesh.new()
	ring_mesh.top_radius = 8.0
	ring_mesh.bottom_radius = 8.0
	ring_mesh.height = 0.06
	ring_mesh.radial_segments = 48
	ring.mesh = ring_mesh
	ring.material_override = _ring_material
	ring.position.y = -0.45
	add_child(ring)

	_point_label = Label3D.new()
	_point_label.text = point_name.to_upper() + "\n[ NEUTRAL ]"
	_point_label.font_size = 10
	_point_label.outline_size = 3
	_point_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_point_label.position = Vector3(0, 3.2, 0)
	_point_label.modulate = Color(0.7, 0.7, 0.7)
	add_child(_point_label)

	_progress_label = Label3D.new()
	_progress_label.font_size = 8
	_progress_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_progress_label.position = Vector3(0, 2.6, 0)
	add_child(_progress_label)

func _process(delta):
	if units_in_area.size() > 0:
		_process_audit(delta)

func _process_audit(delta):
	units_in_area = units_in_area.filter(func(u): return is_instance_valid(u))

	var strengths := {"Regency": 0, "Oligarchy": 0, "Frontline": 0, "Sovereign": 0, "Insurgent": 0}
	for body in units_in_area:
		if body is Civilian:
			var civ = body as Civilian
			if civ.current_state == Civilian.CivilianState.INSURGENCY:
				strengths["Insurgent"] += 2
		elif body is Unit:
			var u = body as Unit
			strengths[u.data.faction] += 1

	# Sabotage Logic
	if controlling_faction != "Neutral":
		var enemy_strength = 0
		for f in strengths:
			if f != controlling_faction and strengths[f] > 0:
				enemy_strength += strengths[f]
		
		if enemy_strength > 0:
			current_audit_value -= sabotage_speed * enemy_strength * delta
			if current_audit_value <= 0:
				GameManager.log_message("ZONE LOST: " + point_name.to_upper() + " SABOTAGED", Color(1, 0.4, 0))
				controlling_faction = "Neutral"
				current_audit_value = 0
				_point_label.text = point_name.to_upper() + "\n[ NEUTRAL ]"
			_update_visual()
			return

	var strongest := ""
	var max_str := 0
	for faction in strengths:
		if faction != "Insurgent" and strengths[faction] > max_str:
			max_str = strengths[faction]
			strongest = faction

	var contested := false
	for faction in strengths:
		if faction != "Insurgent" and faction != strongest and strengths[faction] > 0:
			contested = true
			break

	if strongest != "" and strongest != controlling_faction:
		var mult := 0.2 if contested else 1.0
		current_audit_value += capture_speed * max_str * mult * delta
		if current_audit_value >= total_audit_required:
			controlling_faction = strongest
			current_audit_value = total_audit_required
			captured.emit(controlling_faction)
			_point_label.text = point_name.to_upper() + "\n[ " + controlling_faction.to_upper() + " ]"
			_point_label.modulate = _faction_color(controlling_faction)
			GameManager.log_message("ZONE AUDITED: " + point_name.to_upper(), _faction_color(controlling_faction))
	elif strongest == controlling_faction and current_audit_value < total_audit_required:
		current_audit_value += capture_speed * delta

	_update_visual()

func _update_visual():
	var pct := current_audit_value / total_audit_required
	var col := _faction_color(controlling_faction)
	_ring_material.albedo_color = Color(col.r, col.g, col.b, 0.35)
	_ring_material.emission = col * (0.2 + pct * 0.5)
	var n := int(round(pct * 10))
	_progress_label.text = "█".repeat(n) + "░".repeat(10 - n)
	_progress_label.modulate = col

func _faction_color(faction: String) -> Color:
	match faction:
		"Regency":  return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.5, 0.5, 0.5)

func _on_body_entered(body: Node3D):
	if body is Unit or body is Civilian:
		units_in_area.append(body)

func _on_body_exited(body: Node3D):
	if body is Unit or body is Civilian:
		units_in_area.erase(body)
