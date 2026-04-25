extends CanvasLayer

## THE DEEP STATE: In-Game HUD

const Q_COOLDOWN_MAX := 15.0
const E_COOLDOWN_MAX := 30.0

var _q_cooldown: float = 0.0
var _e_cooldown: float = 0.0
var _selected_units: Array = []
var _selected_building: Building = null

var _funds_label: Label
var _q_label: Label
var _e_label: Label
var _selection_panel: Control
var _selection_label: Label
var _building_panel: Control
var _building_label: Label
var _produce_btn: Button
var _game_over_panel: Control

func _ready():
	add_to_group("hud")
	process_mode = PROCESS_MODE_ALWAYS
	_build_ui()
	ResourceManager.resources_changed.connect(_on_resources_changed)
	_sync_faction_label()

func _sync_faction_label():
	var faction := GameSession.player_faction
	var funds := ResourceManager.faction_funds.get(faction, 0)
	_funds_label.text = faction.to_upper() + " // INTELLIGENCE BUDGET: $" + str(funds)
	_funds_label.add_theme_color_override("font_color", _faction_color(faction))

func _build_ui():
	var top := _panel(true)
	add_child(top)
	_funds_label = Label.new()
	_funds_label.position = Vector2(14, 8)
	top.add_child(_funds_label)

	var bot := _panel(false)
	add_child(bot)

	var q_slot := _ability_slot(bot, Vector2(8, 6), Color(0.04, 0.08, 0.2))
	_q_label = q_slot.get_child(0) as Label
	_q_label.text = "[Q]\nFACT\nCHECK"
	_q_label.add_theme_color_override("font_color", Color(0.4, 0.9, 1.0))

	var e_slot := _ability_slot(bot, Vector2(72, 6), Color(0.2, 0.04, 0.04))
	_e_label = e_slot.get_child(0) as Label
	_e_label.text = "[E]\nCALL\nBACKUP"
	_e_label.add_theme_color_override("font_color", Color(1.0, 0.55, 0.2))

	# Unit selection panel (bottom-left)
	_selection_panel = ColorRect.new()
	(_selection_panel as ColorRect).color = Color(0.02, 0.02, 0.08, 0.88)
	_selection_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_selection_panel.position = Vector2(8, -150)
	_selection_panel.custom_minimum_size = Vector2(210, 90)
	_selection_panel.size = Vector2(210, 90)
	_selection_panel.visible = false
	add_child(_selection_panel)

	_selection_label = Label.new()
	_selection_label.position = Vector2(10, 8)
	_selection_label.size = Vector2(190, 74)
	_selection_label.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
	_selection_panel.add_child(_selection_label)

	# Building selection panel (bottom-right)
	_building_panel = ColorRect.new()
	(_building_panel as ColorRect).color = Color(0.02, 0.04, 0.02, 0.9)
	_building_panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_building_panel.position = Vector2(-230, -160)
	_building_panel.custom_minimum_size = Vector2(220, 100)
	_building_panel.size = Vector2(220, 100)
	_building_panel.visible = false
	add_child(_building_panel)

	_building_label = Label.new()
	_building_label.position = Vector2(10, 8)
	_building_label.size = Vector2(200, 52)
	_building_label.add_theme_color_override("font_color", Color(0.8, 0.9, 0.8))
	_building_panel.add_child(_building_label)

	_produce_btn = Button.new()
	_produce_btn.text = "[ PRODUCE UNIT — $50 ]"
	_produce_btn.position = Vector2(10, 66)
	_produce_btn.size = Vector2(200, 26)
	_produce_btn.pressed.connect(_on_produce_pressed)
	_building_panel.add_child(_produce_btn)

	# Game-over overlay (full screen, always on top)
	_game_over_panel = ColorRect.new()
	(_game_over_panel as ColorRect).color = Color(0.0, 0.0, 0.0, 0.88)
	_game_over_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_game_over_panel.visible = false
	add_child(_game_over_panel)

	var result_lbl := Label.new()
	result_lbl.name = "ResultLabel"
	result_lbl.set_anchors_preset(Control.PRESET_CENTER)
	result_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	result_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	result_lbl.position = Vector2(-200, -60)
	result_lbl.size = Vector2(400, 80)
	result_lbl.add_theme_font_size_override("font_size", 22)
	_game_over_panel.add_child(result_lbl)

	var back_btn := Button.new()
	back_btn.text = "RETURN TO MENU"
	back_btn.set_anchors_preset(Control.PRESET_CENTER)
	back_btn.position = Vector2(-90, 40)
	back_btn.size = Vector2(180, 36)
	back_btn.pressed.connect(func():
		get_tree().paused = false
		get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
	)
	_game_over_panel.add_child(back_btn)

func _panel(top: bool) -> ColorRect:
	var r := ColorRect.new()
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
	var slot := ColorRect.new()
	slot.color = bg
	slot.position = pos
	slot.size = Vector2(56, 44)
	parent.add_child(slot)
	var lbl := Label.new()
	lbl.position = Vector2(0, 2)
	lbl.size = Vector2(56, 40)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.add_theme_font_size_override("font_size", 9)
	slot.add_child(lbl)
	return slot

func _faction_color(faction: String) -> Color:
	match faction:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.7, 0.7, 0.7)

func _process(delta: float):
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

func _on_resources_changed(faction: String, amount: int):
	if faction == GameSession.player_faction:
		_funds_label.text = faction.to_upper() + " // INTELLIGENCE BUDGET: $" + str(amount)

func update_selection(units: Array):
	_selected_units = units.filter(func(u): return is_instance_valid(u))
	_selection_panel.visible = not _selected_units.is_empty()
	if not _selected_units.is_empty():
		_selected_building = null
		_building_panel.visible = false
	_refresh_selection()

func select_building(building: Building):
	_selected_building = building
	_selected_units.clear()
	_selection_panel.visible = false
	_building_panel.visible = true
	_refresh_building_panel()

func deselect_building():
	_selected_building = null
	_building_panel.visible = false

func _refresh_building_panel():
	if not is_instance_valid(_selected_building):
		_building_panel.visible = false
		return
	var b := _selected_building
	var hp_pct := clampf(b.current_health / b.max_health, 0.0, 1.0)
	_building_label.text = (
		"[ " + b.building_name.to_upper() + " ]\n" +
		"INTEGRITY  " + _bar(hp_pct) + "\n" +
		("PRODUCING..." if b._is_producing else "STANDBY")
	)
	_produce_btn.visible = (b.faction == GameSession.player_faction)
	_produce_btn.disabled = b._is_producing

func _on_produce_pressed():
	if is_instance_valid(_selected_building):
		_selected_building.request_produce()
		_refresh_building_panel()

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

func show_game_over(won: bool):
	_game_over_panel.visible = true
	var lbl := _game_over_panel.get_node("ResultLabel") as Label
	if won:
		lbl.text = "MISSION ACCOMPLISHED\n\nObjective secured. The jurisdiction holds."
		lbl.add_theme_color_override("font_color", Color(0.2, 1.0, 0.45))
	else:
		lbl.text = "JURISDICTION LOST\n\nThe opposition prevailed."
		lbl.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
	get_tree().paused = true

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
	AbilityManager.spawn_reinforcements(world_pos, GameSession.player_faction)
	return true
