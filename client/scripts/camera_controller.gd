extends CharacterBody3D

## THE DEEP STATE: Advanced RTS Camera Controller
## Supports WASD, Edge Scrolling, and Smooth Zoom.

@export_group("Movement")
@export var move_speed: float = 30.0
@export var edge_margin: float = 20.0 # Pixels from screen edge to trigger scroll
@export var use_edge_scroll: bool = true

@export_group("Zoom")
@export var min_zoom: float = 5.0
@export var max_zoom: float = 40.0
@export var zoom_sensitivity: float = 2.0
@export var zoom_speed: float = 10.0

@onready var camera: Camera3D = $Camera3D

var _target_zoom: float = 20.0

func _ready():
	add_to_group("rts_camera")
	rotation = Vector3.ZERO                          # clear any baked scene rotation
	camera.rotation_degrees = Vector3(-55, 0, 0)
	camera.position = Vector3(0, _target_zoom, _target_zoom * 0.75)

func _process(delta):
	_handle_movement(delta)
	_handle_zoom(delta)

func _handle_movement(delta):
	var dir = Vector3.ZERO
	
	# Keyboard Input
	if Input.is_key_pressed(KEY_W) or Input.is_action_pressed("ui_up"): dir.z -= 1
	if Input.is_key_pressed(KEY_S) or Input.is_action_pressed("ui_down"): dir.z += 1
	if Input.is_key_pressed(KEY_A) or Input.is_action_pressed("ui_left"): dir.x -= 1
	if Input.is_key_pressed(KEY_D) or Input.is_action_pressed("ui_right"): dir.x += 1
	
	# Edge Scrolling
	if use_edge_scroll:
		var mouse_pos = get_viewport().get_mouse_position()
		var screen_size = get_viewport().get_visible_rect().size
		
		if mouse_pos.x < edge_margin: dir.x -= 1
		if mouse_pos.x > screen_size.x - edge_margin: dir.x += 1
		if mouse_pos.y < edge_margin: dir.z -= 1
		if mouse_pos.y > screen_size.y - edge_margin: dir.z += 1
	
	if dir != Vector3.ZERO:
		dir = dir.normalized()
		global_position += dir * move_speed * delta

func _handle_zoom(delta):
	camera.position.y = lerp(camera.position.y, _target_zoom, zoom_speed * delta)
	# Also move Z to keep the "Look At" point somewhat centered
	camera.position.z = camera.position.y * 0.8 

func _input(event):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_target_zoom = max(min_zoom, _target_zoom - zoom_sensitivity)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_target_zoom = min(max_zoom, _target_zoom + zoom_sensitivity)
