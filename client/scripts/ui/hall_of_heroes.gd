extends Control

## THE HALL OF HEROES (War Room)
## Displays fallen soul leaders fetched from Supabase.
## Accessible from the main menu via "Access Archives".

var _list_container: VBoxContainer
var _status_label: Label

func _ready():
	_build_ui()
	SupabaseManager.heroes_loaded.connect(_on_heroes_loaded)
	SupabaseManager.fetch_heroes_from_cloud()
	_status_label.text = "RETRIEVING RECORDS FROM THE CLOUD..."

func _build_ui():
	# Dark background
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.03, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	# Header
	var header := Label.new()
	header.text = "THE HALL OF HEROES"
	header.set_anchors_preset(Control.PRESET_TOP_WIDE)
	header.position = Vector2(0, 28)
	header.size = Vector2(0, 40)
	header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	header.add_theme_font_size_override("font_size", 28)
	header.add_theme_color_override("font_color", Color(0.2, 0.55, 1.0))
	add_child(header)

	var sub := Label.new()
	sub.text = "REDACTED PERSONNEL // CLASSIFIED RECORD"
	sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	sub.position = Vector2(0, 70)
	sub.size = Vector2(0, 24)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_font_size_override("font_size", 11)
	sub.add_theme_color_override("font_color", Color(0.45, 0.55, 0.65))
	add_child(sub)

	# Status / loading label
	_status_label = Label.new()
	_status_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_status_label.position = Vector2(0, 100)
	_status_label.size = Vector2(0, 24)
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.add_theme_font_size_override("font_size", 10)
	_status_label.add_theme_color_override("font_color", Color(0.5, 0.7, 0.5))
	add_child(_status_label)

	# Scrollable hero list
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_top    = 130
	scroll.offset_bottom = -60
	scroll.offset_left   = 40
	scroll.offset_right  = -40
	add_child(scroll)

	_list_container = VBoxContainer.new()
	_list_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list_container.add_theme_constant_override("separation", 8)
	scroll.add_child(_list_container)

	# Back button
	var back := Button.new()
	back.text = "[ RETURN TO EXECUTIVE DASHBOARD ]"
	back.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	back.offset_top    = -50
	back.offset_bottom = -10
	back.offset_left   = 200
	back.offset_right  = -200
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn"))
	add_child(back)

func _on_heroes_loaded(heroes: Array) -> void:
	# Clear previous entries
	for child in _list_container.get_children():
		child.queue_free()

	if heroes.is_empty():
		_status_label.text = "NO CASUALTIES RECORDED // DATA PENDING"
		return

	_status_label.text = str(heroes.size()) + " FALLEN AGENT(S) ON RECORD"

	for hero in heroes:
		_list_container.add_child(_make_hero_card(hero))

func _make_hero_card(hero: Dictionary) -> Control:
	var faction: String = hero.get("faction", "Unknown")
	var col := _faction_color(faction)

	var card := ColorRect.new()
	card.color = Color(col.r * 0.1, col.g * 0.1, col.b * 0.15, 0.9)
	card.custom_minimum_size = Vector2(0, 66)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Faction accent stripe on the left
	var stripe := ColorRect.new()
	stripe.color = col
	stripe.size = Vector2(4, 66)
	card.add_child(stripe)

	# Name + details
	var lbl := Label.new()
	lbl.position = Vector2(16, 8)
	lbl.size = Vector2(800, 50)
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", Color(0.88, 0.88, 0.88))

	var rank: int  = hero.get("veterancy_rank", 1)
	var status: String = hero.get("status", "REDACTED")
	var name_str: String = hero.get("unit_type", "UNKNOWN AGENT")
	lbl.text = (
		"[ " + name_str.to_upper() + " ]   " + faction.to_upper() +
		"\nVETERANCY RANK: " + str(rank) + "   STATUS: " + status.to_upper()
	)
	card.add_child(lbl)

	return card

func _faction_color(faction: String) -> Color:
	match faction:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.5, 0.5, 0.5)
