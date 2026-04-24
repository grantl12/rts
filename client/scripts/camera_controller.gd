extends CharacterBody3D

## THE DEEP STATE: RTS Camera Controller
## Move with WASD, Zoom with Mouse Wheel.

@export var move_speed: float = 20.0
@export var zoom_speed: float = 2.0

@onready var camera = $Camera3D

func _physics_process(_delta):
	var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	if direction:
		velocity = direction * move_speed
	else:
		velocity.x = move_toward(velocity.x, 0, move_speed)
		velocity.z = move_toward(velocity.z, 0, move_speed)

	move_and_slide()

func _input(event):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera.position.y -= zoom_speed
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera.position.y += zoom_speed
		camera.position.y = clamp(camera.position.y, 5.0, 30.0)
