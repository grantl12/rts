extends Node

## THE DEEP STATE: Global Game Manager
## Tracks ROE levels, Infamy, Infamy, Infamy, and global mission state.

signal roe_level_changed(new_level: int)
signal infamy_changed(new_score: float)
signal message_logged(text: String, color: Color)
signal mission_finished(success: bool)

# Visual settings
var use_crt_shader: bool = true
var pixel_size: int = 3
var scanline_intensity: float = 0.15
var color_bleed: float = 0.001

enum ROELevel {
	HEARTS_AND_MINDS = 1,
	MODERATE_CONTROL = 2,
	HIGH_SUPPRESSION = 3,
	MARTIAL_LAW = 4,
	ABSOLUTE_IMMUNITY = 5
}

var current_roe: ROELevel = ROELevel.HEARTS_AND_MINDS:
	set(value):
		current_roe = value
		roe_level_changed.emit(current_roe)

var infamy_score: float = 0.0:
	set(value):
		infamy_score = value
		infamy_changed.emit(infamy_score)
		if infamy_score >= infamy_limit:
			_finish_mission(false, "ADMINISTRATIVE SHUTDOWN: INFAMY LIMIT EXCEEDED")

var processed_civilians: int = 0:
	set(value):
		processed_civilians = value
		if processed_civilians >= target_civilians:
			_finish_mission(true, "AUDIT COMPLETE: RECRUITMENT QUOTA MET")

# Mission Config
var target_civilians: int = 15
var infamy_limit: float = 100.0
var is_mission_active: bool = true

func _ready():
	pass

func add_infamy(amount: float):
	if not is_mission_active: return
	infamy_score += amount

func log_message(text: String, color: Color = Color.WHITE):
	message_logged.emit(text, color)

func _finish_mission(success: bool, reason: String):
	if not is_mission_active: return
	is_mission_active = false
	log_message(reason, Color.YELLOW if success else Color.RED)
	mission_finished.emit(success)
