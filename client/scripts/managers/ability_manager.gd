extends Node

## THE DEEP STATE: Ability Manager
## Q — Fact Check: bureaucratic AoE that suppresses enemies in range.
## E — Call Backup: spawns two temporary reinforcement units.

const FACT_CHECK_RADIUS  := 12.0
const REINFORCE_COUNT    := 2
const REINFORCE_DURATION := 28.0

# ── Q: Fact Check ──────────────────────────────────────────────────────────────

func cast_fact_check(pos: Vector3) -> void:
	SoundManager.play("fact_check")
	var player := GameSession.player_faction
	var radius := FACT_CHECK_RADIUS
	for b in get_tree().get_nodes_in_group("relay_station"):
		if is_instance_valid(b) and b.get("faction") == player:
			radius += 8.0
	_spawn_fact_check_vfx(pos, radius)
	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node):
			continue
		if node.data.faction == player:
			continue
		if node.global_position.distance_to(pos) <= radius:
			node.apply_suppression()

func _spawn_fact_check_vfx(pos: Vector3, radius: float) -> void:
	var root := get_tree().current_scene
	var ring := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius      = radius
	mesh.bottom_radius   = radius
	mesh.height          = 0.07
	mesh.radial_segments = 40
	ring.mesh = mesh

	var mat := StandardMaterial3D.new()
	mat.albedo_color    = Color(1.0, 0.12, 0.12, 0.75)
	mat.emission_enabled = true
	mat.emission        = Color(1.0, 0.08, 0.08) * 1.8
	mat.transparency    = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode    = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode       = BaseMaterial3D.CULL_DISABLED
	ring.material_override = mat
	ring.position          = pos + Vector3(0, 0.58, 0)
	ring.scale             = Vector3(0.02, 1.0, 0.02)
	root.add_child(ring)

	var tw := ring.create_tween()
	tw.tween_property(ring, "scale", Vector3(1.0, 1.0, 1.0), 0.55)
	tw.parallel().tween_method(
		func(a: float): mat.albedo_color.a = a,
		0.75, 0.0, 0.55
	)
	tw.tween_callback(ring.queue_free)

# ── E: Call Backup ─────────────────────────────────────────────────────────────

func spawn_reinforcements(pos: Vector3, faction: String) -> void:
	SoundManager.play("reinforce")
	var res_path   := GameSession.default_unit_path(faction)
	var unit_res   := load(res_path) as UnitResource
	var unit_scene := load("res://scenes/units/unit_base.tscn") as PackedScene

	for i in REINFORCE_COUNT:
		var unit: Unit = unit_scene.instantiate()
		unit.data     = unit_res
		unit.position = pos + Vector3((i - 0.5) * 2.8, 0.0, randf_range(-1.5, 1.5))
		get_tree().current_scene.add_child(unit)
		_flash_spawn(unit)
		# Temporary reinforcement — despawns after REINFORCE_DURATION seconds
		get_tree().create_timer(REINFORCE_DURATION).timeout.connect(func():
			if is_instance_valid(unit):
				unit.queue_free()
		)

func _flash_spawn(unit: Unit) -> void:
	await get_tree().process_frame
	if not is_instance_valid(unit):
		return
	var sprite := unit.get_node_or_null("Sprite3D") as Sprite3D
	if not sprite:
		return
	sprite.modulate = Color(3.0, 2.4, 0.4)
	var tw := unit.create_tween()
	tw.tween_property(sprite, "modulate", Color.WHITE, 0.5)
