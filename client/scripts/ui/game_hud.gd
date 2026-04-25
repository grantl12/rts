extends CanvasLayer

## THE DEEP STATE: In-Game HUD
## Features a Mission Control Ticker and Terminal UI.

const Q_COOLDOWN_MAX := 15.0
const E_COOLDOWN_MAX := 30.0

var player_faction: String = "Regency"
var _q_cooldown: float = 0.0
var _e_cooldown: float = 0.0
var _selected_units: Array = []

var _funds_label: Label
var _q_label: Label
var _e_label: Label
var _selection_panel: Control
var _selection_label: Label

# Ticker variables
var _ticker_label: Label
var _ticker_text: String = "--- SYSTEM READY --- STANDBY FOR AUDIT ---"
var _ticker_speed: float = 80.0 # Pixels per second

func _ready():
	add_to_group("hud")
	_build_ui()
	ResourceManager.resources_changed.connect(_on_resources_changed)
	GameManager.message_logged.connect(_on_message_logged)

func _build_ui():
	var top = _panel(true)
	add_child(top)
	
	_funds_label = Label.new()
	_funds_label.position = Vector2(14, 8)
	_funds_label.add_theme_color_override("font_color", Color(0.2, 0.5, 1.0))
	_funds_label.text = "REGENCY // INTELLIGENCE BUDGET: $500"
	top.add_child(_funds_label)

	# Ticker setup inside top panel
	var ticker_container = Control.new()
	ticker_container.clip_contents = true
	ticker_container.size = Vector2(600, 36)
	ticker_container.position = Vector2(400, 0) # Middle-right of top bar
	top.add_child(ticker_container)
	
	_ticker_label = Label.new()
	_ticker_label.text = _ticker_text
	_ticker_label.add_theme_color_override("font_color", Color(0.4, 0.9, 1.0))
	_ticker_label.position = Vector2(600, 8) # Start off-screen right
	ticker_container.add_child(_ticker_label)

	var bot = _panel(false)
	add_child(bot)

	var q_slot = _ability_slot(bot, Vector2(8, 6), Color(0.04, 0.08, 0.2))
	_q_label = q_slot.get_child(0) as Label
	_q_label.text = "[Q]\nFACT\nCHECK"
	_q_label.add_theme_color_override("font_color", Color(0.4, 0.9, 1.0))

	var e_slot = _ability_slot(bot, Vector2(72, 6), Color(0.2, 0.04, 0.04))
	_e_label = e_slot.get_child(0) as Label
	_e_label.text = "[E]\nCALL\nBACKUP"
	_e_label.add_theme_color_override("font_color", Color(1.0, 0.55, 0.2))

	_selection_panel = ColorRect.new()
	(_selection_panel as ColorRect).color = Color(0.02, 0.02, 0.08, 0.88)
	_selection_panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_selection_panel.position = Vector2(8, 44)
	_selection_panel.custom_minimum_size = Vector2(210, 0)
	_selection_panel.size = Vector2(210, 90)
	_selection_panel.visible = false
	add_child(_selection_panel)

	_selection_label = Label.new()
	_selection_label.position = Vector2(10, 8)
	_selection_label.size = Vector2(190, 74)
	_selection_label.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
	_selection_panel.add_child(_selection_label)

func _panel(top: bool) -> ColorRect:
	var r = ColorRect.new()
	r.color = Color(0.02, 0.02, 0.08, 0.88)
	if top:
		r.set_anchors_preset(Control.PRESET_TOP_WIDE)
		r.size.y = 36
	else:
		r.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
		r.size.y = 56
		r.offset_top = -56
	return r

func _ability_slot(parent: Control, pos: Vector2, bg: Color) -> ColorRect:
	var slot = ColorRect.new()
	slot.color = bg
	slot.position = pos
	slot.size = Vector2(56, 44)
	parent.add_child(slot)
	var lbl = Label.new()
	lbl.position = Vector2(0, 2)
	lbl.size = Vector2(56, 40)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.add_theme_font_size_override("font_size", 9)
	slot.add_child(lbl)
	return slot

func _process(delta):
	if _q_cooldown > 0:
		_q_cooldown -= delta
		_q_label.text = "[Q] FACT\nCHECK\n%.0fs" % _q_cooldown
	else:
		_q_label.text = "[Q]\nFACT\nCHECK"
	if _e_cooldown > 0:
		_e_cooldown -= delta
		_e_label.text = "[E] CALL\nBACKUP\n%.0fs" % _e_cooldown
	else:
		_e_label.text = "[E]\nCALL\nBACKUP"
	if _selection_panel.visible and not _selected_units.is_empty():
		_refresh_selection()
	
	_process_ticker(delta)

func _process_ticker(delta):
	if not _ticker_label: return
	_ticker_label.position.x -= _ticker_speed * delta
	if _ticker_label.position.x < -_ticker_label.size.x:
		_ticker_label.position.x = 600 # Wrap around

func _on_message_logged(text: String, color: Color):
	_ticker_text = "--- " + text.to_upper() + " --- STANDBY --- " + _ticker_text
	_ticker_label.text = _ticker_text
	_ticker_label.add_theme_color_override("font_color", color)
	# Reset position for priority read
	_ticker_label.position.x = 600

func _on_resources_changed(faction: String, amount: int):
	if faction == player_faction:
		_funds_label.text = faction.to_upper() + " // INTELLIGENCE BUDGET: $" + str(amount)
		GameManager.log_message("BUDGET UPDATED: $" + str(amount), Color(0.2, 0.5, 1.0))

func update_selection(units: Array):
	_selected_units = units.filter(func(u): return is_instance_valid(u))
	_selection_panel.visible = not _selected_units.is_empty()
	_refresh_selection()

func _refresh_selection():
	_selected_units = _selected_units.filter(func(u): return is_instance_valid(u))
	if _selected_units.is_empty():
		_selection_panel.visible = false
		return
	if _selected_units.size() == 1:
		var u = _selected_units[0]
		_selection_label.text = (
			"[ " + u.data.unit_name.to_upper() + " ]\n" +
			"VIT  " + _bar(u.current_vitality / u.data.max_vitality) + "\n" +
			"MORL " + _bar(u.current_bureaucracy / u.data.max_bureaucracy) +
			("\n!! RED TAPE ACTIVE !!" if u.is_suppressed else "")
		)
	else:
		_selection_label.text = "[ " + str(_selected_units.size()) + " UNITS SELECTED ]"

func _bar(pct: float) -> String:
	var n := int(round(clampf(pct, 0.0, 1.0) * 8))
	return "█".repeat(n) + "░".repeat(8 - n)

func try_q(world_pos: Vector3) -> bool:
	if _q_cooldown > 0:
		return false
	_q_cooldown = Q_COOLDOWN_MAX
	AbilityManager.cast_fact_check(world_pos)
	return true

func try_e(world_pos: Vector3) -> bool:
	if _e_cooldown > 0:
		return false
	_e_cooldown = E_COOLDOWN_MAX
	AbilityManager.spawn_reinforcements(world_pos, player_faction)
	return true
