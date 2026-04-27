extends StaticBody3D
class_name HoldingPen

## THE DEEP STATE: Voluntary Compliance Habitat
## Pre-placed capturable structure. Automatically pulls nearby Civilians
## into "managed care." Generates Administrative Credits per occupant.
## Busting a pen pays a cash bounty to the attacker and panics the survivors.
## Permanently destroyed — no respawn. Raze logged to WorldStateManager.

@export var building_name: String  = "Voluntary Compliance Habitat"
@export var initial_civs:  int     = 0
@export var max_capacity:  int     = 10
@export var income_per_civ: float  = 3.0   # funds per civ per income tick
@export var income_interval: float = 4.0
@export var bust_bounty_per_civ: float = 20.0
@export var infamy_on_bust: int    = 15
@export var capture_radius: float  = 7.0
@export var capture_speed:  float  = 16.0
@export var building_size:  Vector3 = Vector3(5, 2, 5)
@export var mesh_color:     Color   = Color(0.30, 0.24, 0.18)
@export var max_health:     float   = 180.0

var faction: String = "Neutral"
var current_health: float
var civs_held: int = 0
var _capture_progress: float = 0.0

var _mesh_mat:      StandardMaterial3D
var _ring_mat:      StandardMaterial3D
var _label:         Label3D
var _count_lbl:     Label3D
var _health_lbl:    Label3D
var _income_timer:  Timer = null
var _units_in_zone: Array[Unit] = []

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready() -> void:
	add_to_group("buildings")
	add_to_group("civ_buildings")
	add_to_group("holding_pens")
	current_health = max_health
	civs_held      = initial_civs
	_build_visuals()
	_build_capture_zone()
	_build_civ_zone()

func _build_visuals() -> void:
	var h2 := building_size.y * 0.5

	var col_shape := CollisionShape3D.new()
	var box       := BoxShape3D.new()
	box.size           = building_size
	col_shape.shape    = box
	col_shape.position = Vector3(0, h2, 0)
	add_child(col_shape)

	_mesh_mat = StandardMaterial3D.new()
	_mesh_mat.albedo_color     = mesh_color
	_mesh_mat.emission_enabled = true
	_mesh_mat.emission         = mesh_color * 0.10

	var mi   := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size            = building_size
	mi.mesh              = mesh
	mi.material_override = _mesh_mat
	mi.position          = Vector3(0, h2, 0)
	add_child(mi)

	_add_fence_posts(h2)

	var label_y := building_size.y + 1.6

	_label = Label3D.new()
	_label.text         = building_name.to_upper() + "\n[ NEUTRAL ]"
	_label.font_size    = 8
	_label.outline_size = 3
	_label.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_label.modulate     = Color(0.70, 0.62, 0.48)
	_label.position     = Vector3(0, label_y, 0)
	add_child(_label)

	_count_lbl = Label3D.new()
	_count_lbl.font_size    = 7
	_count_lbl.outline_size = 2
	_count_lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_count_lbl.modulate     = Color(0.9, 0.82, 0.55)
	_count_lbl.position     = Vector3(0, label_y - 0.8, 0)
	add_child(_count_lbl)

	_health_lbl = Label3D.new()
	_health_lbl.font_size    = 6
	_health_lbl.outline_size = 2
	_health_lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_health_lbl.modulate     = Color(0.55, 0.55, 0.55)
	_health_lbl.position     = Vector3(0, label_y - 1.5, 0)
	add_child(_health_lbl)

	_refresh_count_label()
	_refresh_health_label()

func _add_fence_posts(h2: float) -> void:
	var post_mat := StandardMaterial3D.new()
	post_mat.albedo_color     = Color(0.18, 0.14, 0.10)
	post_mat.emission_enabled = true
	post_mat.emission         = Color(0.06, 0.04, 0.02)

	var post_h := building_size.y + 0.7
	var hx     := building_size.x * 0.5 + 0.08
	var hz     := building_size.z * 0.5 + 0.08
	var cy     := post_h * 0.5

	for px in [-hx, 0.0, hx]:
		for pz in [-hz, hz]:
			_post(px, cy, pz, post_h, post_mat)
	for pz in [-hz, 0.0, hz]:
		for px in [-hx, hx]:
			if px == -hx or px == hx:
				_post(px, cy, pz, post_h, post_mat)

func _post(px: float, py: float, pz: float, h: float, mat: StandardMaterial3D) -> void:
	var pm    := MeshInstance3D.new()
	var pmesh := BoxMesh.new()
	pmesh.size           = Vector3(0.16, h, 0.16)
	pm.mesh              = pmesh
	pm.material_override = mat
	pm.position          = Vector3(px, py, pz)
	add_child(pm)

func _build_capture_zone() -> void:
	var area  := Area3D.new()
	var shape := CollisionShape3D.new()
	var cyl   := CylinderShape3D.new()
	cyl.radius  = capture_radius
	cyl.height  = 6.0
	shape.shape = cyl
	area.add_child(shape)
	area.body_entered.connect(_on_body_entered)
	area.body_exited.connect(_on_body_exited)
	add_child(area)

	_ring_mat = StandardMaterial3D.new()
	_ring_mat.albedo_color    = Color(0.55, 0.42, 0.28, 0.25)
	_ring_mat.emission_enabled = true
	_ring_mat.emission        = Color(0.35, 0.22, 0.08) * 0.15
	_ring_mat.transparency    = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ring_mat.shading_mode    = BaseMaterial3D.SHADING_MODE_UNSHADED

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

func _build_civ_zone() -> void:
	var area  := Area3D.new()
	var shape := CollisionShape3D.new()
	var cyl   := CylinderShape3D.new()
	cyl.radius  = capture_radius * 0.65
	cyl.height  = 5.0
	shape.shape = cyl
	area.add_child(shape)
	area.body_entered.connect(_on_civ_zone_entered)
	add_child(area)

# ── Capture (units) ────────────────────────────────────────────────────────────

func _on_body_entered(body: Node3D) -> void:
	if body is Unit:
		_units_in_zone.append(body as Unit)

func _on_body_exited(body: Node3D) -> void:
	if body is Unit:
		_units_in_zone.erase(body as Unit)

func _on_civ_zone_entered(body: Node3D) -> void:
	if body is Civilian and civs_held < max_capacity:
		civs_held += 1
		body.get_captured()
		_refresh_count_label()
		if faction != "Neutral" and is_instance_valid(_income_timer):
			pass  # timer already running, it reads civs_held live

func _process(delta: float) -> void:
	_units_in_zone = _units_in_zone.filter(func(u): return is_instance_valid(u))

	var counts: Dictionary = {}
	for unit in _units_in_zone:
		var f := unit.data.faction
		counts[f] = counts.get(f, 0) + 1

	var strongest   := ""
	var strongest_n := 0
	var contested   := false
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

func _do_capture(new_faction: String) -> void:
	faction = new_faction
	_update_visuals()
	_restart_income_timer()
	if new_faction == GameSession.player_faction:
		AdvisorManager.speak("capture")
		SoundManager.play("capture")

# ── Visuals ────────────────────────────────────────────────────────────────────

func _update_visuals() -> void:
	var col := _faction_color(faction)
	if faction == "Neutral":
		_mesh_mat.albedo_color = mesh_color
		_mesh_mat.emission     = mesh_color * 0.10
		_label.text    = building_name.to_upper() + "\n[ NEUTRAL ]"
		_label.modulate = Color(0.70, 0.62, 0.48)
		_ring_mat.albedo_color = Color(0.55, 0.42, 0.28, 0.25)
		_ring_mat.emission     = Color(0.35, 0.22, 0.08) * 0.15
	else:
		_mesh_mat.albedo_color = mesh_color.lerp(col, 0.22)
		_mesh_mat.emission     = col * 0.22
		_label.text    = building_name.to_upper() + "\n[ " + faction.to_upper() + " ]"
		_label.modulate = col
		_ring_mat.albedo_color = Color(col.r, col.g, col.b, 0.28)
		_ring_mat.emission     = col * 0.16

func _refresh_count_label() -> void:
	var filled := "▓".repeat(civs_held)
	var empty  := "░".repeat(max_capacity - civs_held)
	_count_lbl.text = "OCCUPANCY [ %d/%d ]  %s%s" % [civs_held, max_capacity, filled, empty]

func _refresh_health_label() -> void:
	var pct := clampf(current_health / max_health, 0.0, 1.0)
	var n   := int(round(pct * 6))
	_health_lbl.text    = "█".repeat(n) + "░".repeat(6 - n)
	_health_lbl.modulate = Color(0.3 + pct * 0.5, pct * 0.7, 0.15)

func set_owned_by(f: String) -> void:
	faction = f
	_update_visuals()
	_restart_income_timer()

# ── Income ─────────────────────────────────────────────────────────────────────

func _restart_income_timer() -> void:
	if is_instance_valid(_income_timer):
		_income_timer.queue_free()
	_income_timer = null
	if faction == "Neutral":
		return
	_income_timer = Timer.new()
	_income_timer.wait_time = income_interval
	_income_timer.autostart = true
	_income_timer.timeout.connect(func():
		if civs_held > 0:
			ResourceManager.add_funds(faction, int(civs_held * income_per_civ))
	)
	add_child(_income_timer)

# ── Damage & destruction ───────────────────────────────────────────────────────

func take_damage(amount: float) -> void:
	current_health -= amount
	_refresh_health_label()
	if current_health <= 0.0:
		_collapse()
		return
	var original := _mesh_mat.albedo_color
	_mesh_mat.albedo_color = Color(1.0, 0.25, 0.15)
	await get_tree().create_timer(0.07).timeout
	if is_instance_valid(self):
		_mesh_mat.albedo_color = original

func _collapse() -> void:
	if is_instance_valid(_income_timer):
		_income_timer.queue_free()

	InfamyManager.add_infamy(infamy_on_bust, "pen_busted")
	WorldStateManager.record_raze(name)
	WorldStateManager.record_wreck("holding_pen", global_position)

	# Pay bust bounty to nearest hostile faction
	var bounty := int(civs_held * bust_bounty_per_civ)
	if bounty > 0:
		var nearby: Dictionary = {}
		for node in get_tree().get_nodes_in_group("units"):
			if not (node is Unit) or not is_instance_valid(node): continue
			if node.data.faction == faction: continue
			if global_position.distance_to(node.global_position) <= capture_radius + 5.0:
				var f := node.data.faction
				nearby[f] = nearby.get(f, 0) + 1
		var best_f := ""
		var best_n := 0
		for f in nearby:
			if nearby[f] > best_n:
				best_n = nearby[f]
				best_f = f
		if best_f != "":
			ResourceManager.add_funds(best_f, bounty)

	# Free and panic survivors
	for i in mini(civs_held, 5):
		var civ := Civilian.new()
		civ.global_position = global_position + Vector3(
			randf_range(-2.5, 2.5), 0.5, randf_range(-2.5, 2.5)
		)
		get_tree().current_scene.add_child(civ)
		civ.call_deferred("panic")

	# Debris fade
	for i in 5:
		var d    := MeshInstance3D.new()
		var dm   := BoxMesh.new()
		dm.size  = Vector3(randf_range(0.3, 0.9), randf_range(0.2, 0.7), randf_range(0.3, 0.9))
		d.mesh   = dm
		var dmat := StandardMaterial3D.new()
		dmat.albedo_color = mesh_color.darkened(randf_range(0.0, 0.4))
		dmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		d.material_override = dmat
		d.global_position = global_position + Vector3(
			randf_range(-2.0, 2.0), randf_range(0.3, building_size.y),
			randf_range(-2.0, 2.0)
		)
		get_tree().current_scene.add_child(d)
		var tw := d.create_tween()
		tw.tween_property(dmat, "albedo_color:a", 0.0, 1.5)
		tw.tween_callback(d.queue_free)

	queue_free()

func _faction_color(f: String) -> Color:
	match f:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)
