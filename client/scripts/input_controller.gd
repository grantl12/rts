extends Node3D

## THE DEEP STATE: Player Input Controller
## Left-click / drag to select, right-click to move/attack buildings+units.
## Q = Fact Check, E = Call Backup, B = Build menu.

var selected_units: Array[Unit] = []
var _camera: Camera3D

var _drag_start: Vector2 = Vector2.ZERO
var _is_dragging: bool = false
const DRAG_THRESHOLD := 6.0

# Build placement state
var _placing: bool = false
var _place_res_path: String = ""
var _ghost: MeshInstance3D = null

func _ready():
	add_to_group("input_controller")
	_camera = get_parent().get_node("RTSCamera/Camera3D")

func _input(event: InputEvent):
	if event is InputEventMouseButton:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				if event.pressed:
					if _placing:
						_confirm_placement(event.position)
						get_viewport().set_input_as_handled()
					else:
						_drag_start = event.position
						_is_dragging = false
				else:
					if not _placing:
						if _is_dragging:
							_handle_box_select(event.position)
							_get_hud().hide_drag_box()
							_is_dragging = false
						else:
							_handle_select(event.position, event.shift_pressed)
					get_viewport().set_input_as_handled()
			MOUSE_BUTTON_RIGHT:
				if event.pressed:
					if _placing:
						cancel_placement()
					else:
						_handle_order(event.position)
					get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion:
		if _placing:
			_update_ghost(event.position)
		elif Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			if not _is_dragging and event.position.distance_to(_drag_start) > DRAG_THRESHOLD:
				_is_dragging = true
			if _is_dragging:
				_get_hud().update_drag_box(_drag_start, event.position)
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_Q: _cast_ability(true)
			KEY_E: _cast_ability(false)
			KEY_B:
				if _placing:
					cancel_placement()
				else:
					_get_hud().show_build_menu()
			KEY_ESCAPE:
				if _placing:
					cancel_placement()
				else:
					_get_hud().hide_build_menu()

func _handle_select(mouse_pos: Vector2, additive: bool):
	var hit := _raycast(mouse_pos)
	if not additive:
		_deselect_all()
	if not hit:
		_get_hud().deselect_building()
		_notify_hud()
		return
	if hit.collider is Unit and hit.collider.visible:
		_get_hud().deselect_building()
		_select_unit(hit.collider)
	elif hit.collider is Building and hit.collider.visible:
		_deselect_all()
		_get_hud().select_building(hit.collider as Building)
		return
	elif hit.collider is CivBuilding and hit.collider.visible:
		_deselect_all()
		_get_hud().select_civ_building(hit.collider as CivBuilding)
		return
	elif hit.collider is HoldingPen and hit.collider.visible:
		_deselect_all()
		_get_hud().select_holding_pen(hit.collider as HoldingPen)
		return
	elif hit.collider is CivilianCar and hit.collider.visible:
		_deselect_all()
		_get_hud().select_vehicle(hit.collider as CivilianCar)
		return
	_notify_hud()

func _handle_box_select(mouse_end: Vector2):
	var select_rect := Rect2(_drag_start, mouse_end - _drag_start).abs()
	_deselect_all()
	_get_hud().deselect_building()
	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node):
			continue
		if node.data.faction != GameSession.player_faction:
			continue
		var screen_pos := _camera.unproject_position(node.global_position)
		if select_rect.has_point(screen_pos):
			_select_unit(node)
	_notify_hud()

func _handle_order(mouse_pos: Vector2):
	selected_units = selected_units.filter(func(u): return is_instance_valid(u))
	if selected_units.is_empty():
		return
	var hit := _raycast(mouse_pos)
	if not hit:
		return
	if hit.collider is Unit and hit.collider.visible:
		var target := hit.collider as Unit
		if target.data.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_unit = target
				unit.target_building = null
	elif hit.collider is Building and hit.collider.visible:
		var building := hit.collider as Building
		if building.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_building = building
				unit.target_unit = null
	elif hit.collider is CivBuilding and hit.collider.visible:
		var cb := hit.collider as CivBuilding
		if cb.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_building = cb
				unit.target_unit = null
	elif hit.collider is HoldingPen and hit.collider.visible:
		var pen := hit.collider as HoldingPen
		if pen.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_building = pen
				unit.target_unit = null
	else:
		var dest := hit.position
		for i in selected_units.size():
			var col: int = i % 3
			var row: int = i / 3
			var offset := Vector3((col - 1) * 2.0, 0, row * 2.0)
			selected_units[i].target_unit = null
			selected_units[i].target_building = null
			selected_units[i].target_position = dest + offset

func _cast_ability(is_q: bool):
	var hud := _get_hud()
	if not hud:
		return
	var world_pos := _get_screen_center_world()
	if world_pos == Vector3.ZERO:
		return
	if is_q:
		hud.try_q(world_pos)
	else:
		hud.try_e(world_pos)

func _get_screen_center_world() -> Vector3:
	var center := get_viewport().get_visible_rect().size / 2.0
	var hit := _raycast(center)
	return hit.position if hit else Vector3.ZERO

func _select_unit(unit: Unit):
	if unit not in selected_units:
		selected_units.append(unit)
		unit.set_selected(true)

func _deselect_all():
	for unit in selected_units:
		if is_instance_valid(unit):
			unit.set_selected(false)
	selected_units.clear()

func _notify_hud():
	_get_hud().update_selection(selected_units)

func _get_hud() -> Node:
	return get_tree().get_first_node_in_group("hud")

func _raycast(mouse_pos: Vector2) -> Dictionary:
	var from := _camera.project_ray_origin(mouse_pos)
	var to := from + _camera.project_ray_normal(mouse_pos) * 1000.0
	var query := PhysicsRayQueryParameters3D.create(from, to)
	query.collide_with_areas = false
	return get_world_3d().direct_space_state.intersect_ray(query)

# ── Build Placement ────────────────────────────────────────────────────────────

func start_placement(res_path: String) -> void:
	cancel_placement()
	_place_res_path = res_path
	_placing = true
	_ghost = _make_ghost()
	get_tree().current_scene.add_child(_ghost)

func cancel_placement() -> void:
	_placing = false
	_place_res_path = ""
	if is_instance_valid(_ghost):
		_ghost.queue_free()
	_ghost = null

func _update_ghost(mouse_pos: Vector2) -> void:
	if not is_instance_valid(_ghost):
		return
	var hit := _raycast(mouse_pos)
	if hit:
		_ghost.global_position = Vector3(hit.position.x, 3.0, hit.position.z)
		_ghost.visible = true
	else:
		_ghost.visible = false

func _confirm_placement(mouse_pos: Vector2) -> void:
	var hit := _raycast(mouse_pos)
	if not hit:
		return
	var place_pos := Vector3(hit.position.x, 0.5, hit.position.z)

	var bres: BuildingResource = load(_place_res_path) as BuildingResource
	if not bres:
		cancel_placement()
		return

	var faction := GameSession.player_faction
	if not ResourceManager.spend_funds(faction, bres.cost):
		AdvisorManager.speak("insufficient_funds")
		return

	if bres.extra_group == "holding_pen":
		var pen := HoldingPen.new()
		pen.position = place_pos
		get_tree().current_scene.add_child(pen)
		pen.set_owned_by(faction)
		cancel_placement()
		return

	var building: Building = (load("res://scenes/buildings/building_base.tscn") as PackedScene).instantiate()
	building.building_name  = bres.building_name
	building.faction        = faction
	building.max_health     = bres.max_health
	building.produce_time   = bres.produce_time
	building.extra_group    = bres.extra_group
	building.passive_income = bres.passive_income
	building.effect_type    = bres.effect_type
	building.effect_radius  = bres.effect_radius
	building.effect_interval = bres.effect_interval
	building.is_constructed = true
	if bres.produces_units:
		if bres.producible_unit_path_override != "":
			building.producible_unit_path = bres.producible_unit_path_override
		else:
			building.producible_unit_path = GameSession.default_unit_path(faction)
	building.position = place_pos
	get_tree().current_scene.add_child(building)

	cancel_placement()

func _make_ghost() -> MeshInstance3D:
	var mi   := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(8, 5, 8)
	mi.mesh   = mesh
	var mat := StandardMaterial3D.new()
	var col := _player_faction_color()
	mat.albedo_color = Color(col.r, col.g, col.b, 0.35)
	mat.emission_enabled = true
	mat.emission = col * 0.3
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	return mi

func _player_faction_color() -> Color:
	match GameSession.player_faction:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)
