extends Building
class_name ProcessingCenter

## THE DEEP STATE: Processing Center
## Civilians are delivered here to be "Vetted" and "Tethered" into the system.

@export var processing_radius: float = 6.0
@onready var _process_timer: Timer = Timer.new()
@onready var _status_label: Label3D = Label3D.new()

var processed_count: int = 0

func _ready():
	super._ready()
	_setup_processing_zone()
	
	# Status Label setup
	_status_label.text = "PROCESSING: 0"
	_status_label.font_size = 14
	_status_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_status_label.position = Vector3(0, 5, 0)
	_status_label.modulate = Color(0.2, 1.0, 0.4)
	add_child(_status_label)

func _setup_processing_zone():
	var area = Area3D.new()
	var collision = CollisionShape3D.new()
	var sphere = SphereShape3D.new()
	sphere.radius = processing_radius
	collision.shape = sphere
	area.add_child(collision)
	add_child(area)
	
	area.body_entered.connect(_on_body_entered)

func _on_body_entered(body):
	if body is Civilian and body.current_state == Civilian.CivilianState.TETHERED:
		_process_civilian(body)
	elif body is Unit and body.tethered_units.size() > 0:
		# Process all units tethered to this squad leader
		var to_process = body.tethered_units.duplicate()
		for civ in to_process:
			if is_instance_valid(civ):
				_process_civilian(civ)
		body.tethered_units.clear()

func _process_civilian(civ: Civilian):
	if civ.current_state == Civilian.CivilianState.PROCESSED: return
	
	civ.current_state = Civilian.CivilianState.PROCESSED
	processed_count += 1
	GameManager.processed_civilians += 1
	
	# Reward logic
	var credit_reward = 50
	ResourceManager.add_resource("AuditCredits", credit_reward)
	GameManager.log_message("CITIZEN VETTED: +50 CREDITS", Color(0.2, 1.0, 0.4))
	
	# ROE Impact
	if GameManager.current_roe == GameManager.ROELevel.HEARTS_AND_MINDS:
		GameManager.infamy_score -= 1.0 # Successful non-lethal processing reduces Infamy
	
	# Visual Feedback
	_status_label.text = "PROCESSING: " + str(processed_count)
	_show_processing_popup(civ.global_position)
	
	# "Delete" the civilian from the world (they are inside the system now)
	civ.queue_free()

func _show_processing_popup(pos: Vector3):
	var popup = Label3D.new()
	popup.text = "VETTED [+50]"
	popup.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	popup.position = pos + Vector3(0, 2, 0)
	popup.modulate = Color(0, 1, 0)
	get_tree().current_scene.add_child(popup)
	
	# Simple float up and fade
	var tween = create_tween()
	tween.tween_property(popup, "position:y", pos.y + 4.0, 1.0)
	tween.parallel().tween_property(popup, "modulate:a", 0.0, 1.0)
	tween.tween_callback(popup.queue_free)
