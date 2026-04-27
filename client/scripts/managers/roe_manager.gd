extends Node

## THE DEEP STATE: Rules of Engagement Manager
## Five tiers of operational constraint. Escalating damage, escalating Infamy.
## Absolute Immunity (ROE 5) is irreversible — the cameras go off and stay off.

signal roe_changed(level: int)

const ROE_NAMES: Array[String] = [
	"RESTRAINED",
	"CONTROLLED",
	"STANDARD",
	"ESCALATED",
	"ABSOLUTE IMMUNITY",
]

const DAMAGE_MULTS: Array[float]  = [0.35, 0.65, 1.00, 1.50, 2.50]
const ROE_COLORS:  Array[Color]   = [
	Color(0.30, 0.85, 0.35),   # 1 green
	Color(0.30, 0.82, 0.95),   # 2 cyan
	Color(0.82, 0.82, 0.82),   # 3 gray
	Color(1.00, 0.65, 0.10),   # 4 amber
	Color(1.00, 0.15, 0.10),   # 5 red
]

const INFAMY_ON_ACTIVATION := 200
const AMBIENT_INTERVALS: Array[float] = [0.0, 0.0, 0.0, 10.0, 5.0]
const AMBIENT_AMOUNTS:   Array[int]   = [0,   0,   0,    1,   5]

var current_roe: int  = 3
var is_butcher:  bool = false

var _ambient_timer: float = 0.0

# ── Public API ─────────────────────────────────────────────────────────────────

func set_roe(level: int) -> void:
	level = clampi(level, 1, 5)
	if level == current_roe:
		return
	current_roe    = level
	_ambient_timer = 0.0
	roe_changed.emit(current_roe)
	if level == 5:
		_activate_absolute_immunity()

func get_name() -> String:
	return ROE_NAMES[current_roe - 1]

func get_color() -> Color:
	return ROE_COLORS[current_roe - 1]

func get_damage_mult() -> float:
	return DAMAGE_MULTS[current_roe - 1]

# ── Process — ambient infamy at high ROE ───────────────────────────────────────

func _process(delta: float) -> void:
	var interval := AMBIENT_INTERVALS[current_roe - 1]
	if interval <= 0.0:
		return
	_ambient_timer += delta
	if _ambient_timer >= interval:
		_ambient_timer = 0.0
		InfamyManager.add_infamy(AMBIENT_AMOUNTS[current_roe - 1], "roe_%d_ambient" % current_roe)

# ── Absolute Immunity activation ───────────────────────────────────────────────

func _activate_absolute_immunity() -> void:
	is_butcher = true
	InfamyManager.add_infamy(INFAMY_ON_ACTIVATION, "absolute_immunity_activated")
	SoundManager.play("absolute_immunity")
	AdvisorManager.speak("absolute_immunity")

	for node in get_tree().get_nodes_in_group("civilians"):
		if node is Civilian and is_instance_valid(node):
			node.panic()

	for node in get_tree().get_nodes_in_group("units"):
		if not (node is Unit) or not is_instance_valid(node): continue
		if node.data.faction != GameSession.player_faction:
			node.apply_suppression()
