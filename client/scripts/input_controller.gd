extends Node3D

## THE DEEP STATE: Player Input Controller
## Left-click to select, shift+left to add, right-click to move/attack.

var selected_units: Array[Unit] = []
var _camera: Camera3D

func _ready():
	_camera = get_parent().get_node("RTSCamera/Camera3D")

func _input(event: InputEvent):
	if not event is InputEventMouseButton or not event.pressed:
		return
	match event.button_index:
		MOUSE_BUTTON_LEFT:
			_handle_select(event.position, event.shift_pressed)
			get_viewport().set_input_as_handled()
		MOUSE_BUTTON_RIGHT:
			_handle_order(event.position)
			get_viewport().set_input_as_handled()

func _handle_select(mouse_pos: Vector2, additive: bool):
	var hit = _raycast(mouse_pos)
	if not additive:
		_deselect_all()
	if hit and hit.collider is Unit:
		_select_unit(hit.collider)

func _handle_order(mouse_pos: Vector2):
	selected_units = selected_units.filter(func(u): return is_instance_valid(u))
	if selected_units.is_empty():
		return
	var hit = _raycast(mouse_pos)
	if not hit:
		return

	if hit.collider is Unit:
		var target = hit.collider as Unit
		if target.data.faction != selected_units[0].data.faction:
			for unit in selected_units:
				unit.target_unit = target
	else:
		var dest = hit.position
		for i in selected_units.size():
			var col: int = i % 3
			var row: int = i / 3
			var offset = Vector3((col - 1) * 2.0, 0, row * 2.0)
			selected_units[i].target_unit = null
			selected_units[i].target_position = dest + offset
			print("ORDER set target_position on unit ", i, ": ", dest + offset)

func _select_unit(unit: Unit):
	if unit not in selected_units:
		selected_units.append(unit)
		unit.set_selected(true)

func _deselect_all():
	for unit in selected_units:
		if is_instance_valid(unit):
			unit.set_selected(false)
	selected_units.clear()

func _raycast(mouse_pos: Vector2) -> Dictionary:
	var from = _camera.project_ray_origin(mouse_pos)
	var to = from + _camera.project_ray_normal(mouse_pos) * 1000.0
	var query = PhysicsRayQueryParameters3D.create(from, to)
	query.collide_with_areas = false
	return get_world_3d().direct_space_state.intersect_ray(query)
