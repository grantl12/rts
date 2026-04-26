extends CharacterBody3D
class_name Unit

## THE DEEP STATE: Base Unit Node

@export var data: UnitResource
@export var is_soul_leader: bool = false
@export var soul_id: String = ""

const RANK_XP    := [0.0, 50.0, 150.0, 300.0, 500.0, INF]
const RANK_NAMES := ["AGENT", "FIELD AGENT", "SR. OPERATIVE", "DEPT. HEAD", "EXECUTIVE"]
const RANK_STAT_BONUS := 0.08

@onready var _status_label: Label3D = $StatusLabel
@onready var _nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var _sprite: Sprite3D = $Sprite3D

var target_position: Vector3
var target_unit: Unit = null
var target_building: Building = null
var is_selected: bool = false
var current_vitality: float
var current_bureaucracy: float
var current_supplies: float
var attack_cooldown: float = 0.0
var is_suppressed: bool = false

var current_rank: int   = 1
var current_xp: float   = 0.0
var _damage_mult: float = 1.0
var _health_mult: float = 1.0
var _passive_xp_timer: float = 0.0

var _base_color: Color
var _health_label: Label3D = null
var _bars_dirty: bool = false

func _ready():
	if data:
		current_rank = clampi(data.veterancy_rank, 1, 5)
		for _r in range(1, current_rank):
			_damage_mult += RANK_STAT_BONUS
			_health_mult += RANK_STAT_BONUS

		current_vitality    = data.max_vitality * _health_mult
		current_bureaucracy = data.max_bureaucracy
		current_supplies    = data.max_supplies
		target_position     = global_position
		_build_visuals()

		if data.unit_type == "Hero" or is_soul_leader:
			is_soul_leader = true
			soul_id = data.soul_id if data.soul_id != "" else str(get_instance_id())
			apply_soul_visuals()

# ── Visuals ────────────────────────────────────────────────────────────────────

func _build_visuals() -> void:
	_base_color = _get_faction_color()

	_sprite.pixel_size = 0.038
	_sprite.billboard  = BaseMaterial3D.BILLBOARD_ENABLED
	_sprite.fixed_size = false
	_sprite.texture    = _generate_sprite()
	_sprite.modulate   = Color.WHITE

	if has_node("Shadow"):
		var ring_mat := StandardMaterial3D.new()
		ring_mat.albedo_color     = Color(_base_color.r, _base_color.g, _base_color.b, 0.6)
		ring_mat.emission_enabled = true
		ring_mat.emission         = _base_color * 0.7
		ring_mat.transparency     = BaseMaterial3D.TRANSPARENCY_ALPHA
		$Shadow.material          = ring_mat

	if is_soul_leader:
		var crown      := MeshInstance3D.new()
		var crown_mesh := CylinderMesh.new()
		crown_mesh.top_radius    = 0.0
		crown_mesh.bottom_radius = 0.18
		crown_mesh.height        = 0.28
		var crown_mat := StandardMaterial3D.new()
		crown_mat.albedo_color    = Color(1.0, 0.85, 0.1)
		crown_mat.emission_enabled = true
		crown_mat.emission        = Color(1.0, 0.75, 0.0) * 1.2
		crown_mat.shading_mode    = BaseMaterial3D.SHADING_MODE_UNSHADED
		crown.mesh                = crown_mesh
		crown.material_override   = crown_mat
		crown.position.y          = 1.9
		add_child(crown)

	var name_label := Label3D.new()
	name_label.text         = data.unit_name
	name_label.font_size    = 6
	name_label.outline_size = 3
	name_label.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	name_label.modulate     = _base_color
	name_label.position     = Vector3(0, 2.6, 0)
	add_child(name_label)

	_health_label              = Label3D.new()
	_health_label.font_size    = 7
	_health_label.outline_size = 2
	_health_label.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_health_label.position     = Vector3(0, 2.1, 0)
	add_child(_health_label)
	_update_bars()

func _get_faction_color() -> Color:
	match data.faction:
		"Regency":   return Color(0.2, 0.5, 1.0)
		"Oligarchy": return Color(1.0, 0.2, 0.2)
		"Frontline": return Color(0.3, 1.0, 0.35)
		"Sovereign": return Color(0.8, 0.3, 1.0)
	return Color(0.6, 0.6, 0.6)

func apply_soul_visuals() -> void:
	if _sprite:
		_sprite.modulate = Color(2.0, 1.7, 0.5)

func set_selected(value: bool) -> void:
	is_selected = value
	if not _sprite:
		return
	if value:
		_sprite.modulate = Color(0.6, 2.0, 1.2)
	else:
		_sprite.modulate = Color.WHITE
		if is_soul_leader:
			apply_soul_visuals()

# ── Sprite Generation ──────────────────────────────────────────────────────────

func _px(img: Image, x: int, y: int, c: Color) -> void:
	if x >= 0 and x < img.get_width() and y >= 0 and y < img.get_height():
		img.set_pixel(x, y, c)

func _px_rect(img: Image, x: int, y: int, w: int, h: int, c: Color) -> void:
	for dy in h:
		for dx in w:
			_px(img, x + dx, y + dy, c)

func _px_h_line(img: Image, y: int, x1: int, x2: int, c: Color) -> void:
	for x in range(x1, x2 + 1):
		_px(img, x, y, c)

func _px_v_line(img: Image, x: int, y1: int, y2: int, c: Color) -> void:
	for y in range(y1, y2 + 1):
		_px(img, x, y, c)

func _sprite_colors() -> Dictionary:
	var c := _base_color
	return {
		"c":  c,
		"cd": c.darkened(0.35),
		"cl": c.lightened(0.30),
		"sk": Color(0.90, 0.74, 0.58),
		"dk": Color(0.10, 0.10, 0.13),
		"gn": Color(0.38, 0.40, 0.46),
		"gl": Color(0.58, 0.60, 0.65),
		"wh": Color(0.92, 0.92, 0.95),
		"gd": Color(1.00, 0.82, 0.18),
		"rd": Color(0.80, 0.15, 0.15),
	}

func _generate_sprite() -> ImageTexture:
	var img := Image.create(32, 48, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var p := _sprite_colors()
	match data.unit_name:
		"Park Ranger":   _draw_park_ranger(img, p)
		"Conscript":     _draw_conscript(img, p)
		"Digital Nomad": _draw_digital_nomad(img, p)
		"The Proxy":     _draw_the_proxy(img, p)
		"Gravy Seal":    _draw_gravy_seal(img, p)
		"The Martyr":    _draw_the_martyr(img, p)
		_:               _draw_generic(img, p)
	return ImageTexture.create_from_image(img)

# Park Ranger — lean build, wide-brim hat, long sniper rifle pointing right
func _draw_park_ranger(img: Image, p: Dictionary) -> void:
	_px_rect(img, 11, 2, 10, 5, p.cd)           # hat crown
	_px_rect(img, 4,  6, 24, 2, p.cd)           # hat brim
	_px_h_line(img, 7, 11, 20, p.dk)            # hat band
	_px_rect(img, 12, 8,  8, 5, p.sk)           # face
	_px(img, 13, 10, p.dk); _px(img, 18, 10, p.dk)
	_px(img, 15, 12, p.dk); _px(img, 16, 12, p.dk)
	_px_rect(img, 14, 13, 4, 2, p.sk)           # neck
	_px_rect(img, 12, 15, 8, 9, p.c)            # lean torso
	_px_rect(img, 9,  15, 3, 9, p.c)            # left arm
	_px_rect(img, 20, 15, 3, 5, p.c)            # right arm (holds rifle)
	_px_rect(img, 19, 19, 2, 3, p.gn)           # rifle stock
	_px_h_line(img, 20, 20, 30, p.gn)           # barrel top
	_px_h_line(img, 21, 20, 30, p.gl)           # barrel bottom (lighter)
	_px_rect(img, 20, 22, 4,  2, p.gn)          # breech block
	_px_h_line(img, 24, 12, 19, p.dk)           # belt
	_px_rect(img, 12, 25, 3, 3, p.cd)           # left hip
	_px_rect(img, 17, 25, 3, 3, p.cd)           # right hip
	_px_rect(img, 12, 28, 3, 11, p.cd)          # left leg
	_px_rect(img, 17, 28, 3, 11, p.cd)          # right leg
	_px_rect(img, 11, 39, 5,  3, p.dk)          # left boot
	_px_rect(img, 16, 39, 5,  3, p.dk)          # right boot

# Conscript — dome helmet with cyan visor, stocky build, compact SMG
func _draw_conscript(img: Image, p: Dictionary) -> void:
	_px_rect(img, 12, 3,  8, 1, p.c)            # helmet top
	_px_rect(img, 10, 4, 12, 2, p.c)
	_px_rect(img, 9,  6, 14, 3, p.c)
	_px_rect(img, 9,  7, 14, 2, p.dk)           # visor band
	_px(img, 12, 8, Color(0.1, 0.8, 1.0)); _px(img, 13, 8, Color(0.1, 0.8, 1.0))
	_px(img, 16, 8, Color(0.1, 0.8, 1.0)); _px(img, 17, 8, Color(0.1, 0.8, 1.0))
	_px(img, 20, 8, Color(0.1, 0.8, 1.0)); _px(img, 21, 8, Color(0.1, 0.8, 1.0))
	_px_rect(img, 11, 9, 10, 2, p.cd)           # neck guard
	_px_rect(img, 9, 11, 14, 11, p.c)           # stocky torso
	_px_rect(img, 11, 12, 10, 4, p.cd)          # chest plate
	_px_v_line(img, 16, 12, 15, p.c)            # centre seam
	_px_rect(img, 6, 11, 4, 9, p.c)             # left arm
	_px_rect(img, 22, 11, 4, 6, p.c)            # right arm
	_px_rect(img, 22, 17, 8, 3, p.gn)           # SMG body
	_px_h_line(img, 17, 25, 30, p.gn)           # barrel
	_px_rect(img, 24, 20, 2, 4, p.gn)           # magazine
	_px_h_line(img, 22, 9, 22, p.dk)            # belt
	_px_rect(img, 9,  23, 5, 3, p.cd)           # left hip
	_px_rect(img, 18, 23, 5, 3, p.cd)           # right hip
	_px_rect(img, 10, 26, 4, 10, p.cd)          # left leg
	_px_rect(img, 18, 26, 4, 10, p.cd)          # right leg
	_px_rect(img, 9,  36, 6,  4, p.dk)          # left boot
	_px_rect(img, 17, 36, 6,  4, p.dk)          # right boot

# Digital Nomad — pointed hoodie, backpack bump, glowing laptop screen
func _draw_digital_nomad(img: Image, p: Dictionary) -> void:
	_px_rect(img, 14, 1,  4, 2, p.c)            # hood tip
	_px_rect(img, 12, 3,  8, 2, p.c)
	_px_rect(img, 10, 5, 12, 3, p.c)
	_px_rect(img, 9,  8, 14, 2, p.c)            # hood lower
	_px_rect(img, 11, 5, 10, 5, p.dk)           # dark face cavity
	_px(img, 13, 7, Color(0.15, 0.95, 1.0)); _px(img, 14, 7, Color(0.15, 0.95, 1.0))
	_px(img, 17, 7, Color(0.15, 0.95, 1.0)); _px(img, 18, 7, Color(0.15, 0.95, 1.0))
	_px_rect(img, 13, 10, 6, 2, p.c)            # collar
	_px_rect(img, 11, 12, 10, 10, p.c)          # hoodie torso
	_px_rect(img, 7,  12, 4,  9, p.cd)          # backpack
	_px_rect(img, 7,  16, 4,  2, p.dk)          # backpack strap
	_px_rect(img, 9,  12, 3,  9, p.c)           # left arm
	_px_rect(img, 21, 12, 3,  7, p.c)           # right arm
	_px_rect(img, 21, 19, 8,  6, p.dk)          # laptop case
	_px_rect(img, 22, 20, 6,  4, Color(0.05, 0.55, 1.0, 0.9))  # screen glow
	_px_h_line(img, 25, 21, 28, p.gn)           # keyboard row
	_px_h_line(img, 22, 11, 20, p.dk)           # waist
	_px_rect(img, 12, 23, 3, 12, p.cd)          # left leg
	_px_rect(img, 17, 23, 3, 12, p.cd)          # right leg
	_px_rect(img, 11, 35, 5,  4, p.wh)          # left sneaker
	_px_rect(img, 16, 35, 5,  4, p.wh)          # right sneaker
	_px_h_line(img, 38, 11, 15, Color(0.3, 0.3, 0.3))
	_px_h_line(img, 38, 16, 20, Color(0.3, 0.3, 0.3))

# The Proxy — wide fedora, flaring trenchcoat, gold-clasped briefcase
func _draw_the_proxy(img: Image, p: Dictionary) -> void:
	_px_rect(img, 11, 2, 10, 5, p.c)            # fedora crown
	_px_h_line(img, 3, 12, 20, p.cd)            # crease
	_px_rect(img, 4,  6, 24, 2, p.c)            # brim
	_px_h_line(img, 7, 11, 20, p.cd)            # under-brim shadow
	_px_rect(img, 12, 8,  8, 5, p.sk)           # face
	_px(img, 13, 10, p.dk); _px(img, 18, 10, p.dk)
	_px(img, 15, 12, p.dk); _px(img, 16, 12, p.dk)
	_px_rect(img, 12, 13, 3, 5, p.c)            # left lapel
	_px_rect(img, 17, 13, 3, 5, p.c)            # right lapel
	_px_rect(img, 14, 13, 4, 10, p.cd)          # tie / shirt centre
	_px_rect(img, 10, 13, 12, 12, p.c)          # upper coat
	_px_rect(img, 9,  25, 14,  6, p.c)          # mid coat (wider)
	_px_rect(img, 7,  31, 18,  9, p.c)          # lower flare
	_px_h_line(img, 25, 9, 22, p.dk)            # belt
	_px(img, 15, 25, p.gd); _px(img, 16, 25, p.gd)  # buckle
	_px_rect(img, 8,  13, 3, 12, p.c)           # left arm
	_px_rect(img, 21, 13, 3, 10, p.c)           # right arm
	_px_rect(img, 21, 23, 8,  6, p.cd)          # briefcase body
	_px_rect(img, 22, 24, 6,  4, p.gn)          # case face
	_px_h_line(img, 25, 22, 28, p.dk)           # latch
	_px(img, 25, 23, p.gd); _px(img, 26, 23, p.gd)  # handle
	_px_rect(img, 11, 40, 5,  4, p.dk)          # left shoe
	_px_rect(img, 16, 40, 5,  4, p.dk)          # right shoe

# Gravy Seal — box tactical helmet, heavy armour plates, assault rifle
func _draw_gravy_seal(img: Image, p: Dictionary) -> void:
	_px_rect(img, 9,  2, 14, 9, p.c)            # box helmet
	_px_rect(img, 9,  7, 14, 3, p.dk)           # visor band
	_px_rect(img, 10, 8, 12, 1, Color(1.0, 0.50, 0.08, 0.9))  # HUD glow
	_px_rect(img, 20, 1,  2, 4, p.cd)           # antenna/NVG mount
	_px_rect(img, 11, 11, 10, 2, p.cd)          # neck piece
	_px_rect(img, 8,  13, 16, 12, p.c)          # heavy torso
	_px_v_line(img, 16, 13, 24, p.cd)           # chest seam
	_px_h_line(img, 18, 8, 23, p.cd)            # plate division
	_px_rect(img, 4,  13, 5, 11, p.c)           # left arm (thick)
	_px_rect(img, 23, 13, 5,  5, p.c)           # right arm
	_px_rect(img, 23, 18, 3,  3, p.gn)          # pistol grip
	_px_rect(img, 25, 14, 8,  3, p.gn)          # receiver
	_px_h_line(img, 14, 25, 31, p.gl)           # barrel top
	_px_h_line(img, 15, 25, 31, p.gn)           # barrel
	_px_rect(img, 26, 17, 3,  3, p.gn)          # magazine
	_px_h_line(img, 25, 8, 23, p.dk)            # belt
	_px_rect(img, 7,  26, 6,  4, p.cd)          # left hip armour
	_px_rect(img, 19, 26, 6,  4, p.cd)          # right hip armour
	_px_rect(img, 8,  30, 5,  9, p.cd)          # left leg
	_px_rect(img, 19, 30, 5,  9, p.cd)          # right leg
	_px_rect(img, 7,  39, 7,  4, p.dk)          # left boot
	_px_rect(img, 18, 39, 7,  4, p.dk)          # right boot

# The Martyr — gold halo, raised fist, star emblem, fierce expression
func _draw_the_martyr(img: Image, p: Dictionary) -> void:
	_px_h_line(img, 1, 11, 20, p.gd)            # halo top
	_px(img, 10, 2, p.gd); _px(img, 21, 2, p.gd)
	_px(img, 10, 3, p.gd); _px(img, 21, 3, p.gd)
	_px_h_line(img, 4, 11, 20, p.gd)            # halo bottom
	_px_rect(img, 12, 5, 8, 7, p.sk)            # head
	_px(img, 13, 7, p.dk); _px(img, 14, 7, p.dk)   # left eye
	_px(img, 17, 7, p.dk); _px(img, 18, 7, p.dk)   # right eye
	_px(img, 13, 6, p.dk); _px(img, 18, 6, p.dk)   # brow furrow
	_px(img, 15, 10, p.dk); _px(img, 16, 10, p.dk) # set jaw
	_px_rect(img, 14, 12, 4, 2, p.sk)           # neck
	_px_rect(img, 11, 14, 10, 10, p.c)          # torso
	_px(img, 16, 17, p.gd)                      # star emblem
	_px(img, 15, 18, p.gd); _px(img, 16, 18, p.gd); _px(img, 17, 18, p.gd)
	_px(img, 14, 19, p.gd); _px(img, 16, 19, p.gd); _px(img, 18, 19, p.gd)
	_px(img, 15, 20, p.gd); _px(img, 16, 20, p.gd); _px(img, 17, 20, p.gd)
	_px_rect(img, 9,  14, 3,  6, p.c)           # left upper arm
	_px_rect(img, 7,  10, 3,  5, p.c)           # left forearm (raised)
	_px_rect(img, 6,   7, 4,  4, p.sk)          # fist
	_px_rect(img, 6,   7, 4,  1, p.dk)          # knuckles
	_px_rect(img, 21, 14, 3,  9, p.c)           # right arm
	_px_h_line(img, 24, 11, 23, p.dk)           # waist
	_px_rect(img, 11, 25, 10, 12, p.cd)         # trousers
	_px_rect(img, 10, 37, 5,  5, p.dk)          # left boot
	_px_rect(img, 17, 37, 5,  5, p.dk)          # right boot

func _draw_generic(img: Image, p: Dictionary) -> void:
	_px_rect(img, 12, 4,  8,  8, p.c)
	_px_rect(img, 11, 12, 10, 10, p.c)
	_px_rect(img, 8,  12, 3,   8, p.c)
	_px_rect(img, 21, 12, 3,   8, p.c)
	_px_rect(img, 12, 22, 4,  12, p.cd)
	_px_rect(img, 16, 22, 4,  12, p.cd)

# ── Physics ────────────────────────────────────────────────────────────────────

func _physics_process(delta):
	if attack_cooldown > 0:
		attack_cooldown -= delta

	if not is_suppressed and current_bureaucracy < data.max_bureaucracy:
		current_bureaucracy += delta * 2.0
		_bars_dirty = true

	if data and data.faction == GameSession.player_faction:
		_passive_xp_timer -= delta
		if _passive_xp_timer <= 0.0:
			_passive_xp_timer = 10.0
			_award_xp(1.0)

	if _bars_dirty:
		_update_bars()
		_bars_dirty = false

	if target_building and is_instance_valid(target_building):
		handle_building_combat(delta)
	elif target_unit and is_instance_valid(target_unit):
		handle_combat(delta)
	elif global_position.distance_to(target_position) > 0.5:
		move_to_target(delta)

func handle_combat(_delta):
	var dist = global_position.distance_to(target_unit.global_position)
	if dist <= data.attack_range:
		velocity = Vector3.ZERO
		if attack_cooldown <= 0:
			shoot()
	else:
		target_position = target_unit.global_position
		move_to_target(_delta)

func handle_building_combat(_delta):
	var dist = global_position.distance_to(target_building.global_position)
	if dist <= data.attack_range:
		velocity = Vector3.ZERO
		if attack_cooldown <= 0:
			_shoot_building()
	else:
		target_position = target_building.global_position
		move_to_target(_delta)

func _shoot_building():
	if current_supplies <= 0 or is_suppressed:
		return
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	target_building.take_damage(data.damage * _damage_mult * 0.75)
	_award_xp(3.0)

func shoot():
	if current_supplies <= 0 or is_suppressed:
		return
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	target_unit.take_damage(data.damage * _damage_mult * 0.5, "Bureaucracy")
	if randf() <= data.accuracy:
		target_unit.take_damage(data.damage * _damage_mult, "Vitality")
	if not is_instance_valid(target_unit):
		_award_xp(25.0)

# ── Veterancy ──────────────────────────────────────────────────────────────────

func _award_xp(amount: float) -> void:
	if data.faction != GameSession.player_faction:
		return
	current_xp += amount
	_check_rank_up()

func _check_rank_up() -> void:
	if current_rank >= 5:
		return
	if current_xp >= RANK_XP[current_rank]:
		_do_rank_up()

func _do_rank_up() -> void:
	current_rank  += 1
	_damage_mult  += RANK_STAT_BONUS
	_health_mult  += RANK_STAT_BONUS
	var hp_bonus := data.max_vitality * RANK_STAT_BONUS
	current_vitality = minf(current_vitality + hp_bonus, data.max_vitality * _health_mult)
	_bars_dirty = true
	_show_promotion_effect()
	_check_rank_up()

func _show_promotion_effect() -> void:
	if _sprite:
		_sprite.modulate = Color(3.0, 2.5, 0.5)
	_status_label.text     = "▲ " + RANK_NAMES[current_rank - 1]
	_status_label.modulate = Color(1.0, 0.9, 0.2)
	AdvisorManager.speak("promotion")
	var tw := create_tween()
	tw.tween_interval(2.2)
	tw.tween_callback(func():
		if not is_instance_valid(self):
			return
		_status_label.text = ""
		if _sprite:
			_sprite.modulate = Color.WHITE
			if is_soul_leader:
				apply_soul_visuals()
	)

# ── Movement ───────────────────────────────────────────────────────────────────

func move_to_target(_delta):
	if global_position.distance_to(target_position) <= 0.5:
		velocity = Vector3.ZERO
		return

	_nav_agent.target_position = target_position

	var dir: Vector3
	if not _nav_agent.is_navigation_finished():
		var next_pos := _nav_agent.get_next_path_position()
		dir = next_pos - global_position
	else:
		dir = target_position - global_position

	dir.y = 0.0
	if dir.length() > 0.05:
		velocity = dir.normalized() * 5.0
		move_and_slide()
	else:
		velocity = Vector3.ZERO

# ── Damage & Status ────────────────────────────────────────────────────────────

func take_damage(amount: float, type: String = "Vitality"):
	var final_amount = amount
	if type == "Vitality" and is_in_cover():
		final_amount *= 0.5
	if type == "Vitality":
		current_vitality -= final_amount
	elif type == "Bureaucracy":
		current_bureaucracy -= final_amount
		if current_bureaucracy < (data.max_bureaucracy * 0.3):
			apply_suppression()
	_bars_dirty = true
	if current_vitality <= 0:
		die()

func _update_bars():
	if not _health_label or not data:
		return
	var vit_pct := clampf(current_vitality / (data.max_vitality * _health_mult), 0.0, 1.0)
	var bur_pct := clampf(current_bureaucracy / data.max_bureaucracy, 0.0, 1.0)
	var vn := int(round(vit_pct * 6))
	var bn := int(round(bur_pct * 6))
	_health_label.text     = "█".repeat(vn) + "░".repeat(6 - vn) + "\n" + "█".repeat(bn) + "░".repeat(6 - bn)
	_health_label.modulate = Color(0.3 + vit_pct * 0.7, 0.9 * vit_pct, 0.2)

func is_in_cover() -> bool:
	return false

func apply_suppression():
	if is_suppressed:
		return
	is_suppressed = true
	if data.faction == GameSession.player_faction:
		AdvisorManager.speak("suppressed")
	_status_label.text     = "█ RED TAPE █"
	_status_label.modulate = Color(1.0, 0.15, 0.15)
	if _sprite:
		_sprite.modulate = Color(0.4, 0.4, 0.4)
	await get_tree().create_timer(3.0).timeout
	is_suppressed = false
	_status_label.text = ""
	if _sprite:
		_sprite.modulate = Color.WHITE
		if is_soul_leader:
			apply_soul_visuals()

func die():
	if is_soul_leader:
		var hero_data := {
			"unit_type":      data.unit_name,
			"faction":        data.faction,
			"veterancy_rank": current_rank,
			"status":         "REDACTED"
		}
		SupabaseManager.save_hero_to_cloud(hero_data)
	queue_free()
