extends Node3D

## THE DEEP STATE: Player Input Controller
## Left-click to select units/buildings, right-click to move/attack.
## Q = Fact Check, E = Call Backup.

var selected_units: Array[Unit] = []
var _camera: Camera3D

func _ready():
	_camera = get_parent().get_node("RTSCamera/Camera3D")

func _input(event: InputEvent):
	if event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				_handle_select(event.position, event.shift_pressed)
				get_viewport().set_input_as_handled()
			MOUSE_BUTTON_RIGHT:
				_handle_order(event.position)
				get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_Q: _cast_ability(true)
			KEY_E: _cast_ability(false)

func _handle_select(mouse_pos: Vector2, additive: bool):
	var hit := _raycast(mouse_pos)
	if not additive:
		_deselect_all()
	if not hit:
		_get_hud().deselect_building()
		_notify_hud()
		return
	if hit.collider is Unit:
		_get_hud().deselect_building()
		_select_unit(hit.collider)
	elif hit.collider is Building:
		_deselect_all()
		_get_hud().select_building(hit.collider as Building)
		return
	_notify_hud()

func _handle_order(mouse_pos: Vector2):
	selected_units = selected_units.filter(func(u): return is_instance_valid(u))
	if selected_units.is_empty():
		return
	var hit := _raycast(mouse_pos)
	if not hit:
		return
	if hit.collider is Unit:
		var target := hit.collider as Unit
		if target.data.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_unit = target
	else:
		var dest := hit.position
		for i in selected_units.size():
			var col: int = i % 3
			var row: int = i / 3
			var offset := Vector3((col - 1) * 2.0, 0, row * 2.0)
			selected_units[i].target_unit = null
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
