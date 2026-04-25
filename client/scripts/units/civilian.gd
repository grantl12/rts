extends Unit
class_name Civilian

## THE DEEP STATE: Civilian Unit Logic
## Reacts to Infamy and ROE. Can be tethered by Auditor squads.

enum CivilianState { IDLE, TETHERED, PANIC, INSURGENCY, PROCESSED }

var current_state: CivilianState = CivilianState.IDLE
var tether_leader: Unit = null
var recording_active: bool = false # Mobile device "recording" state

func _ready():
	super._ready()
	_base_color = Color(0.8, 0.8, 0.8) # Civilians are grey by default
	if _body_material:
		_body_material.albedo_color = _base_color

func _physics_process(delta):
	match current_state:
		CivilianState.TETHERED:
			_handle_tether_logic(delta)
		CivilianState.PANIC:
			_handle_panic_logic(delta)
		CivilianState.IDLE:
			_handle_idle_behavior(delta)
		CivilianState.INSURGENCY:
			# Behave like an enemy unit
			super._physics_process(delta)

	_check_infamy_reactions()

func _handle_tether_logic(_delta):
	if is_instance_valid(tether_leader):
		# Follow at a slight offset
		target_position = tether_leader.global_position + Vector3(randf_range(-2, 2), 0, randf_range(2, 4))
		move_to_target(_delta)
	else:
		current_state = CivilianState.IDLE

func _handle_panic_logic(_delta):
	# Run away from any combat or high-lethality zones
	# To be implemented: flee logic
	move_to_target(_delta)

func _handle_idle_behavior(_delta):
	# Occasional loitering or recording
	if GameManager.current_roe >= GameManager.ROELevel.HIGH_SUPPRESSION:
		if randf() < 0.001:
			_start_recording()

func _start_recording():
	if recording_active or current_state == CivilianState.INSURGENCY: return
	recording_active = true
	_status_label.text = "[ REC ]"
	_status_label.modulate = Color(1, 0, 0)
	# Logic for Infamy spike if ROE 5 actions happen nearby
	
func _check_infamy_reactions():
	# Chance to flip to Insurgency based on Infamy
	if current_state == CivilianState.IDLE and GameManager.infamy_score > 50.0:
		if randf() < 0.0001: # Small tick chance
			become_insurgent()

func become_insurgent():
	current_state = CivilianState.INSURGENCY
	_base_color = Color(1.0, 0.5, 0.0) # Orange/Rust for insurgents
	if _body_material:
		_body_material.albedo_color = _base_color
	_status_label.text = "!!! INSURGENT !!!"
	GameManager.log_message("CIVILIAN FLIPPED: INSURGENT DETECTED", Color(1.0, 0.2, 0.2))
	# Logic to switch faction to Proxy/Sovereign

func tether_to(leader: Unit):
	if current_state == CivilianState.INSURGENCY: return
	tether_leader = leader
	current_state = CivilianState.TETHERED
	_status_label.text = "TETHERED"
	_status_label.modulate = Color(0.2, 0.8, 1.0)

func untether():
	tether_leader = null
	current_state = CivilianState.IDLE
	_status_label.text = ""
