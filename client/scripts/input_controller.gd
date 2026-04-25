extends Node3D

## THE DEEP STATE: Player Input Controller
## Left-click to select, shift+left to add, right-click to move/attack.
## Q = Fact Check (AOE de-suppress), E = Call Backup (spawn reinforcements).

var selected_units: Array[Unit] = []
var _camera: Camera3D

func _ready():
	_camera = get_parent().get_node("RTSCamera/Camera3D")

func _input(event: InputEvent):
	if event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				if event.is_pressed():
					_start_marquee_select(event.position)
				elif event.is_released():
					_end_marquee_select(event.position, event.shift_pressed)
				get_viewport().set_input_as_handled()
			MOUSE_BUTTON_RIGHT:
				_handle_order(event.position)
				get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_Q: _cast_ability(true)
			KEY_E: _cast_ability(false)

func _handle_select(mouse_pos: Vector2, additive: bool):
	var hit = _raycast(mouse_pos)
	if not additive:
		_deselect_all()
	if hit and hit.collider is Unit:
		_select_unit(hit.collider)
	_notify_hud()

func _start_marquee_select(start_pos: Vector2):
	# Store the starting position for marquee selection
	pass # Logic will be in _end_marquee_select

func _end_marquee_select(end_pos: Vector2, additive: bool):
	var selection_rect = Rect2(start_pos.min_v(end_pos), (start_pos - end_pos).abs())
	
	# Deselect existing units if not additive
	if not additive:
		_deselect_all()
		
	# Get all units in the scene and check if they are within the selection rect
	var all_units = get_tree().get_nodes_in_group("units") # Assuming units are in a group
	for unit_node in all_units:
		if unit_node is Unit:
			var unit = unit_node as Unit
			# Convert unit's screen position to viewport coordinates
			var screen_pos = _camera.unproject_position(unit.global_position)
			if selection_rect.has_point(screen_pos):
				_select_unit(unit)
	_notify_hud()
