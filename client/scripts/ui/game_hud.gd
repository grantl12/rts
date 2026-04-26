extends CanvasLayer

## THE DEEP STATE: In-Game HUD

# Top-right tactical minimap.
class _Minimap extends Control:
	const _WORLD := 100.0

	func _draw() -> void:
		var sz := size
		draw_rect(Rect2(Vector2.ZERO, sz), Color(0.03, 0.04, 0.08))

		for body in get_tree().get_nodes_in_group("cover"):
			if not is_instance_valid(body): continue
			var p := _w2m(body.global_position, sz)
			draw_rect(Rect2(p - Vector2(3, 1), Vector2(6, 2)), Color(0.30, 0.28, 0.26))

		for ap in get_tree().get_nodes_in_group("audit_points"):
			if not is_instance_valid(ap): continue
			var p   := _w2m(ap.global_position, sz)
			var col := _fc(ap.controlling_faction)
			draw_circle(p, 5.0, col.darkened(0.4))
			draw_arc(p, 5.5, 0.0, TAU, 22, col, 1.5)

		for b in get_tree().get_nodes_in_group("buildings"):
			if not is_instance_valid(b): continue
			var p := _w2m(b.global_position, sz)
			draw_rect(Rect2(p - Vector2(4, 4), Vector2(8, 8)), _fc(b.faction))

		for u in get_tree().get_nodes_in_group("units"):
			if not is_instance_valid(u) or not u.visible: continue
			if not u.get("data"): continue
			var p := _w2m(u.global_position, sz)
			draw_circle(p, 2.0, _fc(u.data.faction))

		var cams := get_tree().get_nodes_in_group("rts_camera")
		if cams.size() > 0:
			var p := _w2m(cams[0].global_position, sz)
			var r := Rect2(p - Vector2(13, 9), Vector2(26, 18))
			draw_rect(r, Color(1, 1, 1, 0.10), true)
			draw_rect(r, Color(1, 1, 1, 0.40), false, 1.0)

		draw_rect(Rect2(Vector2.ZERO, sz), Color(0.22, 0.25, 0.32), false, 1.5)

	func _w2m(world: Vector3, sz: Vector2) -> Vector2:
		return Vector2(
			(world.x + _WORLD * 0.5) / _WORLD * sz.x,
			(world.z + _WORLD * 0.5) / _WORLD * sz.y
		)

	func _fc(faction: String) -> Color:
		match faction:
			"Regency":   return Color(0.2, 0.5, 1.0)
			"Oligarchy": return Color(1.0, 0.2, 0.2)
			"Frontline": return Color(0.3, 1.0, 0.35)
			"Sovereign": return Color(0.8, 0.3, 1.0)
		return Color(0.5, 0.5, 0.5)

# Drag-selection box drawn on top of all other HUD elements.
class _SelectionBox extends Control:
	var _from := Vector2.ZERO
	var _to   := Vector2.ZERO

	func set_rect(from: Vector2, to: Vector2) -> void:
		_from = from
		_to   = to
		queue_redraw()

	func _draw() -> void:
		var r := Rect2(_from, _to - _from).abs()
		draw_rect(r, Color(0.35, 0.75, 1.0, 0.10), true)
		draw_rect(r, Color(0.35, 0.75, 1.0, 0.80), false, 1.5)

const Q_COOLDOWN_MAX := 15.0
const E_COOLDOWN_MAX := 30.0

const BARRACKS_RES := "res://resources/buildings/barracks.tres"

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
var _build_menu: Control
var _game_over_panel: Control
var _sel_box: _SelectionBox
var _advisor_label: Label
var _advisor_tween: Tween = null
var _minimap: _Minimap = null

func _ready():
	add_to_group("hud")
	process_mode = PROCESS_MODE_ALWAYS
	_build_ui()
	ResourceManager.resources_changed.connect(_on_resources_changed)
	AdvisorManager.advisor_spoke.connect(_show_advisor_line)
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
	_selection_panel.position = Vector2(8, -185)
	_selection_panel.custom_minimum_size = Vector2(220, 125)
	_selection_panel.size = Vector2(220, 125)
	_selection_panel.visible = false
	add_child(_selection_panel)

	_selection_label = Label.new()
	_selection_label.position = Vector2(10, 8)
	_selection_label.size = Vector2(200, 110)
	_selection_label.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
	_selection_panel.add_child(_selection_label)

	# Building selection panel (bottom-right of center)
	_building_panel = ColorRect.new()
	(_building_panel as ColorRect).color = Color(0.02, 0.04, 0.02, 0.9)
	_building_panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_building_panel.position = Vector2(-460, -175)
	_building_panel.custom_minimum_size = Vector2(220, 115)
	_building_panel.size = Vector2(220, 115)
	_building_panel.visible = false
	add_child(_building_panel)

	_building_label = Label.new()
	_building_label.position = Vector2(10, 8)
	_building_label.size = Vector2(200, 64)
	_building_label.add_theme_color_override("font_color", Color(0.8, 0.9, 0.8))
	_building_panel.add_child(_building_label)

	_produce_btn = Button.new()
	_produce_btn.text = "[ PRODUCE UNIT — $50 ]"
	_produce_btn.position = Vector2(10, 80)
	_produce_btn.size = Vector2(200, 26)
	_produce_btn.pressed.connect(_on_produce_pressed)
	_building_panel.add_child(_produce_btn)

	# Build menu (bottom-right, beside building panel)
	_build_menu = ColorRect.new()
	(_build_menu as ColorRect).color = Color(0.02, 0.02, 0.06, 0.92)
	_build_menu.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_build_menu.position = Vector2(-230, -175)
	_build_menu.custom_minimum_size = Vector2(218, 115)
	_build_menu.size = Vector2(218, 115)
	_build_menu.visible = false
	add_child(_build_menu)

	var bm_title := Label.new()
	bm_title.text = "[ CONSTRUCT ]"
	bm_title.add_theme_font_size_override("font_size", 9)
	bm_title.add_theme_color_override("font_color", Color(0.5, 0.8, 0.5))
	bm_title.position = Vector2(10, 6)
	_build_menu.add_child(bm_title)

	var barracks_btn := Button.new()
	barracks_btn.text = "BARRACKS — $150\nProduces units (4s)"
	barracks_btn.position = Vector2(10, 26)
	barracks_btn.size = Vector2(198, 36)
	barracks_btn.pressed.connect(func(): _on_build_selected(BARRACKS_RES))
	_build_menu.add_child(barracks_btn)

	var cancel_btn := Button.new()
	cancel_btn.text = "[ CANCEL ]"
	cancel_btn.position = Vector2(10, 70)
	cancel_btn.size = Vector2(198, 26)
	cancel_btn.pressed.connect(func(): hide_build_menu())
	_build_menu.add_child(cancel_btn)

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

	# Advisor ticker — above ability bar
	_advisor_label = Label.new()
	_advisor_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_advisor_label.offset_top = -100
	_advisor_label.offset_bottom = -60
	_advisor_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_advisor_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_advisor_label.add_theme_font_size_override("font_size", 11)
	_advisor_label.add_theme_color_override("font_color", Color(0.75, 0.92, 1.0))
	_advisor_label.modulate.a = 0.0
	add_child(_advisor_label)

	# Minimap — top-right corner, below the top bar
	var mm_bg := ColorRect.new()
	mm_bg.color = Color(0.02, 0.02, 0.06, 0.90)
	mm_bg.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	mm_bg.position = Vector2(-158, 40)
	mm_bg.size     = Vector2(152, 158)
	add_child(mm_bg)

	var mm_lbl := Label.new()
	mm_lbl.text = "[ SURVEILLANCE ]"
	mm_lbl.add_theme_font_size_override("font_size", 7)
	mm_lbl.add_theme_color_override("font_color", Color(0.4, 0.6, 0.8))
	mm_lbl.position = Vector2(4, 2)
	mm_bg.add_child(mm_lbl)

	_minimap = _Minimap.new()
	_minimap.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_minimap.position = Vector2(-155, 53)
	_minimap.size     = Vector2(146, 140)
	_minimap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_minimap)

	# Drag-selection box — drawn last so it's always on top
	_sel_box = _SelectionBox.new()
	_sel_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	_sel_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sel_box.visible = false
	add_child(_sel_box)

func update_drag_box(from: Vector2, to: Vector2) -> void:
	_sel_box.visible = true
	_sel_box.set_rect(from, to)

func hide_drag_box() -> void:
	_sel_box.visible = false

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
	if _minimap:
		_minimap.queue_redraw()
	if _selection_panel.visible and not _selected_units.is_empty():
		_refresh_selection()
	if _building_panel.visible and is_instance_valid(_selected_building):
		_refresh_building_panel()

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

	var status_line: String
	if b._is_producing:
		status_line = "PRODUCING... %.0fs" % maxf(b._produce_time_remaining, 0.0)
	else:
		status_line = "STANDBY"

	_building_label.text = (
		"[ " + b.building_name.to_upper() + " ]\n" +
		"INTEGRITY  " + _bar(hp_pct) + "\n" +
		status_line
	)
	_produce_btn.visible = (b.faction == GameSession.player_faction and not b.producible_unit_path.is_empty())
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
		var u := _selected_units[0]
		var vit_pct  := u.current_vitality / (u.data.max_vitality * u._health_mult)
		var bur_pct  := u.current_bureaucracy / u.data.max_bureaucracy
		var xp_prev  := Unit.RANK_XP[u.current_rank - 1]
		var xp_next  := Unit.RANK_XP[u.current_rank]
		var xp_pct   := 1.0 if u.current_rank >= 5 else \
						clampf((u.current_xp - xp_prev) / (xp_next - xp_prev), 0.0, 1.0)
		_selection_label.text = (
			"[ " + u.data.unit_name.to_upper() + " ]\n" +
			"VIT  " + _bar(vit_pct) + "\n" +
			"MORL " + _bar(bur_pct) + "\n" +
			"RANK " + Unit.RANK_NAMES[u.current_rank - 1] + "\n" +
			"XP   " + _bar(xp_pct) +
			("\n!! RED TAPE ACTIVE !!" if u.is_suppressed else "")
		)
	else:
		_selection_label.text = "[ " + str(_selected_units.size()) + " UNITS SELECTED ]"

func _bar(pct: float) -> String:
	var n := int(round(clampf(pct, 0.0, 1.0) * 8))
	return "█".repeat(n) + "░".repeat(8 - n)

func show_build_menu() -> void:
	_build_menu.visible = true

func hide_build_menu() -> void:
	_build_menu.visible = false
	var ic := get_tree().get_first_node_in_group("input_controller")
	if ic and ic.has_method("cancel_placement"):
		ic.cancel_placement()

func _on_build_selected(res_path: String) -> void:
	hide_build_menu()
	var ic := get_tree().get_first_node_in_group("input_controller")
	if ic and ic.has_method("start_placement"):
		ic.start_placement(res_path)

func show_game_over(won: bool):
	AdvisorManager.speak("victory" if won else "defeat")
	_game_over_panel.visible = true
	var lbl := _game_over_panel.get_node("ResultLabel") as Label
	if won:
		lbl.text = "MISSION ACCOMPLISHED\n\nObjective secured. The jurisdiction holds."
		lbl.add_theme_color_override("font_color", Color(0.2, 1.0, 0.45))
	else:
		lbl.text = "JURISDICTION LOST\n\nThe opposition prevailed."
		lbl.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
	get_tree().paused = true

func _show_advisor_line(text: String) -> void:
	if _advisor_tween:
		_advisor_tween.kill()
	_advisor_label.text = "[ THE AUDITOR ]  " + text
	_advisor_label.modulate.a = 0.0
	_advisor_tween = create_tween()
	_advisor_tween.tween_property(_advisor_label, "modulate:a", 1.0, 0.25)
	_advisor_tween.tween_interval(5.0)
	_advisor_tween.tween_property(_advisor_label, "modulate:a", 0.0, 0.6)

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
