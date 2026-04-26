extends StaticBody3D
class_name CivBuilding

## THE DEEP STATE: Civilian / Neutral Building
## Pre-placed on the map. Factions capture by moving units into the zone.
## Providing a passive buff while held. Permanently destroyed if razed.

@export var building_name: String = "Civic Structure"
@export var buff_type: String = "income"    # "income" | "supply" | "xp" | "morale"
@export var capture_radius: float = 7.0
@export var capture_speed: float = 18.0
@export var building_size: Vector3 = Vector3(6, 5, 6)
@export var mesh_color: Color = Color(0.68, 0.64, 0.57)   # sandstone default
@export var label_color: Color = Color(0.70, 0.68, 0.62)
@export var max_health: float = 300.0

var faction: String = "Neutral"
var current_health: float
var _capture_progress: float = 0.0

var _mesh_mat:     StandardMaterial3D
var _ring_mat:     StandardMaterial3D
var _label:        Label3D
var _progress_lbl: Label3D
var _health_lbl:   Label3D
var _buff_timer:   Timer = null
var _units_in_zone: Array[Unit] = []

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready() -> void:
	add_to_group("buildings")
	add_to_group("civ_buildings")
	current_health = max_health
	_build_visuals()
	_build_capture_zone()

func _build_visuals() -> void:
	var h2 := building_size.y * 0.5

	var col_shape := CollisionShape3D.new()
	var box       := BoxShape3D.new()
	box.size           = building_size
	col_shape.shape    = box
	col_shape.position = Vector3(0, h2, 0)
	add_child(col_shape)

	_mesh_mat = StandardMaterial3D.new()
	_mesh_mat.albedo_color    = mesh_color
	_mesh_mat.emission_enabled = true
	_mesh_mat.emission        = mesh_color * 0.18

	var mi   := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size            = building_size
	mi.mesh              = mesh
	mi.material_override = _mesh_mat
	mi.position          = Vector3(0, h2, 0)
	add_child(mi)

	var label_y := building_size.y + 1.6
	_label = Label3D.new()
	_label.text         = building_name.to_upper() + "\n[ NEUTRAL ]"
	_label.font_size    = 8
	_label.outline_size = 3
	_label.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_label.modulate     = label_color
	_label.position     = Vector3(0, label_y, 0)
	add_child(_label)

	_progress_lbl = Label3D.new()
	_progress_lbl.font_size    = 7
	_progress_lbl.outline_size = 2
	_progress_lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_progress_lbl.position     = Vector3(0, label_y - 0.7, 0)
	add_child(_progress_lbl)

	_health_lbl = Label3D.new()
	_health_lbl.font_size    = 6
	_health_lbl.outline_size = 2
	_health_lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_health_lbl.modulate     = Color(0.55, 0.55, 0.55)
	_health_lbl.position     = Vector3(0, label_y - 1.4, 0)
	add_child(_health_lbl)
	_refresh_health_label()

func _build_capture_zone() -> void:
	var area  := Area3D.new()
	var shape := CollisionShape3D.new()
	var cyl   := CylinderShape3D.new()
	cyl.radius = capture_radius
	cyl.height = 6.0
	shape.shape = cyl
	area.add_child(shape)
	area.body_entered.connect(_on_body_entered)
	area.body_exited.connect(_on_body_exited)
	add_child(area)

	_ring_mat = StandardMaterial3D.new()
	_ring_mat.albedo_color = Color(0.5, 0.5, 0.5, 0.28)
	_ring_mat.emission_enabled = true
	_ring_mat.emission      = Color(0.3, 0.3, 0.3) * 0.18
	_ring_mat.transparency  = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ring_mat.shading_mode  = BaseMaterial3D.SHADING_MODE_UNSHADED

	var ring      := MeshInstance3D.new()
	var ring_mesh := CylinderMesh.new()
	ring_mesh.top_radius      = capture_radius
	ring_mesh.bottom_radius   = capture_radius
	ring_mesh.height          = 0.05
	ring_mesh.radial_segments = 36
	ring.mesh              = ring_mesh
	ring.material_override = _ring_mat
	ring.position.y        = -0.44
	add_child(ring)

# ── Capture ────────────────────────────────────────────────────────────────────

func _on_body_entered(body: Node3D) -> void:
	if body is Unit:
		_units_in_zone.append(body as Unit)

func _on_body_exited(body: Node3D) -> void:
	if body is Unit:
		_units_in_zone.erase(body as Unit)

func _process(delta: float) -> void:
	_units_in_zone = _units_in_zone.filter(func(u): return is_instance_valid(u))

	var counts: Dictionary = {}
	for unit in _units_in_zone:
		var f := unit.data.faction
		counts[f] = counts.get(f, 0) + 1

	var strongest := ""
	var strongest_n := 0
	var contested := false
	for f in counts:
		if counts[f] > strongest_n:
			strongest_n = counts[f]
			strongest   = f
	for f in counts:
		if f != strongest and counts[f] > 0:
			contested = true
			break

	if strongest != "" and strongest != faction:
		var rate := capture_speed * strongest_n * (0.2 if contested else 1.0)
		_capture_progress += rate * delta
		if _capture_progress >= 100.0:
			_capture_progress = 0.0
			_do_capture(strongest)
	elif strongest == faction:
		_capture_progress = maxf(_capture_progress - capture_speed * 0.4 * delta, 0.0)

	_refresh_progress_label(strongest, contested)

func _do_capture(new_faction: String) -> void:
	faction = new_faction
	_update_visuals()
	_restart_buff_timer()
	if new_faction == GameSession.player_faction:
		AdvisorManager.speak("capture")
		SoundManager.play("capture")

# ── Visuals ────────────────────────────────────────────────────────────────────

func _update_visuals() -> void:
	var col := _faction_color(faction)
	if faction == "Neutral":
		_mesh_mat.albedo_color = mesh_color
		_mesh_mat.emission     = mesh_color * 0.18
		_label.text    = building_name.to_upper() + "\n[ NEUTRAL ]"
		_label.modulate = label_color
		_ring_mat.albedo_color = Color(0.5, 0.5, 0.5, 0.28)
		_ring_mat.emission     = Color(0.3, 0.3, 0.3) * 0.18
	else:
		_mesh_mat.albedo_color = mesh_color.lerp(col, 0.30)
		_mesh_mat.emission     = col * 0.30
		_label.text    = building_name.to_upper() + "\n[ " + faction.to_upper() + " ]"
		_label.modulate = col
		_ring_mat.albedo_color = Color(col.r, col.g, col.b, 0.30)
		_ring_mat.emission     = col * 0.22

func _refresh_progress_label(strongest: String, contested: bool) -> void:
	if contested:
		_progress_lbl.text    = "[ CONTESTED ]"
		_progress_lbl.modulate = Color(1.0, 0.80, 0.2)
	elif strongest != "" and strongest != faction:
		var n := int(round(_capture_progress / 100.0 * 8.0))
		_progress_lbl.text    = "▶ " + "█".repeat(n) + "░".repeat(8 - n)
		_progress_lbl.modulate = _faction_color(strongest)
	else:
		_progress_lbl.text = ""

func _refresh_health_label() -> void:
	var pct := clampf(current_health / max_health, 0.0, 1.0)
	var n   := int(round(pct * 6))
	_health_lbl.text    = "█".repeat(n) + "░".repeat(6 - n)
	_health_lbl.modulate = Color(0.3 + pct * 0.5, pct * 0.7, 0.15)

# ── Damage & Destruction ───────────────────────────────────────────────────────

func take_damage(amount: float) -> void:
	current_health -= amount
	_refresh_health_label()
	if current_health <= 0.0:
		_collapse()
		return
	# Brief damage flash
	var original := _mesh_mat.albedo_color
	_mesh_mat.albedo_color = Color(1.0, 0.25, 0.15)
	await get_tree().create_timer(0.07).timeout
	if is_instance_valid(self):
		_mesh_mat.albedo_color = original

func _collapse() -> void:
	if is_instance_valid(_buff_timer):
		_buff_timer.queue_free()
	InfamyManager.add_infamy(25, "civilian_structure_razed")
	WorldStateManager.record_raze(name)
	WorldStateManager.record_wreck("civ_building", global_position)
	# Spawn simple debris
	for i in 6:
		var d    := MeshInstance3D.new()
		var dm   := BoxMesh.new()
		dm.size  = Vector3(randf_range(0.3, 1.1), randf_range(0.3, 1.1), randf_range(0.3, 1.1))
		d.mesh   = dm
		var dmat := StandardMaterial3D.new()
		dmat.albedo_color = mesh_color.darkened(randf_range(0.0, 0.35))
		dmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		d.material_override = dmat
		d.global_position = global_position + Vector3(
			randf_range(-2.5, 2.5), randf_range(0.5, building_size.y),
			randf_range(-2.5, 2.5)
		)
		get_tree().current_scene.add_child(d)
		var tw := d.create_tween()
		tw.tween_property(dmat, "albedo_color:a", 0.0, 1.8)
		tw.tween_callback(d.queue_free)
	queue_free()

# ── Buff timers ────────────────────────────────────────────────────────────────

func _restart_buff_timer() -> void:
	if is_instance_valid(_buff_timer):
		_buff_timer.queue_free()
	_buff_timer = null
	if faction == "Neutral":
		return

	_buff_timer = Timer.new()
	match buff_type:
		"income":
			_buff_timer.wait_time = 2.0
			_buff_timer.timeout.connect(func(): ResourceManager.add_funds(faction, 6))
		"supply":
			_buff_timer.wait_time = 3.0
			_buff_timer.timeout.connect(_tick_supply)
		"xp":
			_buff_timer.wait_time = 8.0
			_buff_timer.timeout.connect(_tick_xp)
		"morale":
			_buff_timer.wait_time = 4.0
			_buff_timer.timeout.connect(_tick_morale)
	_buff_timer.autostart = true
	add_child(_buff_timer)

func _tick_supply() -> void:
	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node): continue
		if node.data.faction != faction: continue
		if global_position.distance_to(node.global_position) <= 16.0:
			node.current_supplies = minf(node.current_supplies + 5.0, node.data.max_supplies)

func _tick_xp() -> void:
	if faction != GameSession.player_faction:
		return
	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node): continue
		if node.data.faction != faction: continue
		if global_position.distance_to(node.global_position) <= 18.0:
			node._award_xp(3.0)

func _tick_morale() -> void:
	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node): continue
		if node.data.faction != faction: continue
		if global_position.distance_to(node.global_position) <= 14.0:
			node.current_bureaucracy = minf(
				node.current_bureaucracy + 8.0,
				node.data.max_bureaucracy
			)
			node._bars_dirty = true

func _faction_color(f: String) -> Color:
	match f:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)
