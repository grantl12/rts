extends Control

## THE DEEP STATE: Executive Dashboard

@onready var status_label = $StatusMargin/StatusLabel
@onready var version_label = $Footer/Version
@onready var ticker = $TickerBackground/NewsTicker
@onready var background = $Background
@onready var header = $Header
@onready var bgm = $BGM

@onready var pixelation_rect: ColorRect = $PostProcess/Pixelation # Reference to the shader layer

var _glitch_timer: float = 2.0

func _ready():
	version_label.text = "Build: v0.4.4-REDACTED"
	_apply_grid_shader()
	animate_boot_sequence()
	
	# Ensure BGM loops
	if bgm:
		bgm.finished.connect(func(): bgm.play())

func _apply_grid_shader():
	var shader = load("res://shaders/neon_grid_2d.gdshader")
	if shader:
		var mat = ShaderMaterial.new()
		mat.shader = shader
		background.material = mat

func animate_boot_sequence():
	status_label.text = "Initializing Deep State Protocols..."
	await get_tree().create_timer(1.0).timeout
	status_label.text = "Synchronizing with the Grid..."
	await get_tree().create_timer(0.5).timeout
	status_label.text = "Jurisdiction: ACTIVE"

func _process(delta):
	# Scrolling ticker
	ticker.position.x -= 100 * delta
	if ticker.position.x < -1500:
		update_ticker_from_meta()
		ticker.position.x = 1280

	# Glitch effect on header
	_glitch_timer -= delta
	if _glitch_timer <= 0:
		_glitch_timer = randf_range(3.0, 7.0)
		_trigger_glitch()

	# Update CRT shader visibility based on GameManager setting
	if pixelation_rect:
		pixelation_rect.visible = GameManager.use_crt_shader

func _trigger_glitch():
	var original_text = header.text
	var glitch_chars = ["▓", "░", "█", "▒", "■"]

	# Flash corrupt text
	header.modulate = Color(0.0, 1.0, 0.8)
	header.text = "T█E DE█P █TATE"
	header.position.x = randf_range(-4, 4)
	await get_tree().create_timer(0.06).timeout

	header.text = "THE DEEP STATE"
	header.position.x = randf_range(-2, 2)
	await get_tree().create_timer(0.04).timeout

	header.text = original_text
	header.position.x = 0
	header.modulate = Color(1, 1, 1)

func update_ticker_from_meta():
	pass

func _on_new_audit_pressed():
	get_tree().change_scene_to_file("res://scenes/ui/faction_selection.tscn")

func _on_access_archives_pressed():
	get_tree().change_scene_to_file("res://scenes/ui/hall_of_heroes.tscn")

func _on_calibration_pressed():
	pass

func _on_redact_session_pressed():
	get_tree().quit()
