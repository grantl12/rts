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
var target_building = null
var is_selected: bool = false
var current_vitality: float
var current_bureaucracy: float
var current_supplies: float
var attack_cooldown: float = 0.0
var is_suppressed: bool = false
var tethered_units: Array[Unit] = []

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

# ── Sprite Generation — C&C 1995 style, 16×24 canvas ─────────────────────────

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

func _sprite_colors() -> Dictionary:
	var c := _base_color
	return {
		"c":  c,
		"cd": c.darkened(0.40),
		"cl": c.lightened(0.25),
		"sk": Color(0.88, 0.72, 0.56),
		"dk": Color(0.08, 0.08, 0.10),
		"gn": Color(0.32, 0.34, 0.38),
		"gl": Color(0.55, 0.57, 0.60),
		"wh": Color(0.92, 0.92, 0.95),
		"gd": Color(1.00, 0.82, 0.18),
		"cy": Color(0.10, 0.80, 1.00),
	}

func _generate_sprite() -> ImageTexture:
	var img := Image.create(16, 24, false, Image.FORMAT_RGBA8)
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
	_outline(img)
	return ImageTexture.create_from_image(img)

func _outline(img: Image) -> void:
	var snap := img.duplicate()
	var w := img.get_width(); var h := img.get_height()
	var ol := Color(0.06, 0.06, 0.08, 1.0)
	for y in h:
		for x in w:
			if snap.get_pixel(x, y).a > 0.1:
				continue
			for dy2 in range(-1, 2):
				for dx2 in range(-1, 2):
					var nx := x + dx2; var ny := y + dy2
					if nx >= 0 and nx < w and ny >= 0 and ny < h:
						if snap.get_pixel(nx, ny).a > 0.5:
							img.set_pixel(x, y, ol)

# Shared base: torso, arms, legs — head drawn per unit
func _draw_base(img: Image, p: Dictionary) -> void:
	_px_rect(img, 4, 7, 8, 6, p.c)
	_px_rect(img, 5, 8, 6, 3, p.cd)   # chest shadow
	_px_rect(img, 2, 7, 2, 5, p.c)    # left arm
	_px_rect(img, 12, 7, 2, 5, p.c)   # right arm
	_px_h_line(img, 13, 3, 12, p.dk)  # belt
	_px_rect(img, 4, 14, 3, 6, p.cd)  # left leg
	_px_rect(img, 9, 14, 3, 6, p.cd)  # right leg
	_px_rect(img, 3, 20, 4, 3, p.dk)  # left boot
	_px_rect(img, 9, 20, 4, 3, p.dk)  # right boot

# Park Ranger — wide patrol hat (12px brim), long sniper rifle to frame edge
func _draw_park_ranger(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px_rect(img, 5, 0, 6, 3, p.cd)   # hat crown
	_px_h_line(img, 3, 2, 13, p.cd)   # brim — 12px wide
	_px_h_line(img, 3, 5, 10, p.dk)   # hat band
	_px_rect(img, 5, 4, 6, 3, p.sk)   # face (y=4-6)
	_px(img, 6, 5, p.dk); _px(img, 9, 5, p.dk)
	_px_rect(img, 13, 8, 3, 3, p.gn)  # rifle receiver
	_px_h_line(img, 9, 11, 15, p.gn)  # long barrel
	_px(img, 14, 7, p.gl)             # scope glint

# Conscript — wide dome helmet (8px), cyan visor, AK-47 with curved mag
func _draw_conscript(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px_h_line(img, 1, 5, 10, p.c)    # dome top arc
	_px_rect(img, 4, 2, 8, 3, p.c)    # dome body (8px wide)
	_px_h_line(img, 3, 4, 11, p.dk)   # visor band
	_px_h_line(img, 3, 5, 10, p.cy)   # visor glow
	_px_rect(img, 5, 5, 6, 2, p.cd)   # neck guard (y=5-6)
	_px_rect(img, 12, 9, 3, 3, p.gn)  # AK receiver
	_px_h_line(img, 10, 11, 15, p.gn) # barrel to frame edge
	_px_rect(img, 13, 12, 2, 2, p.gn) # curved magazine

# Digital Nomad — pointed hoodie, twin glowing eyes, data backpack
func _draw_digital_nomad(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px(img, 8, 0, p.c)               # hood tip
	_px_h_line(img, 1, 7, 8, p.c)
	_px_h_line(img, 2, 6, 9, p.c)
	_px_rect(img, 4, 3, 8, 3, p.c)    # hood base
	_px_rect(img, 5, 2, 6, 4, p.dk)   # dark face void
	_px(img, 5, 4, p.cy); _px(img, 6, 4, p.cy)
	_px(img, 9, 4, p.cy); _px(img, 10, 4, p.cy)
	_px_h_line(img, 6, 5, 10, p.c)    # collar (y=6)
	_px_rect(img, 1, 7, 2, 6, p.cd)   # data backpack
	_px(img, 1, 9, p.cy)              # indicator light

# The Proxy — tall crown + 12px fedora brim (fixed), trenchcoat hem, briefcase
func _draw_the_proxy(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px_rect(img, 5, 0, 6, 4, p.c)    # fedora crown (4px tall, y=0-3)
	_px_h_line(img, 4, 2, 13, p.c)    # brim — 12px wide (y=4, below crown)
	_px_h_line(img, 4, 5, 10, p.cd)   # hat band on brim
	_px_h_line(img, 5, 4, 11, p.cd)   # brim underside shadow
	_px_rect(img, 5, 5, 6, 2, p.sk)   # face (y=5-6)
	_px(img, 6, 6, p.dk); _px(img, 9, 6, p.dk)
	_px_rect(img, 3, 11, 10, 3, p.c)  # trenchcoat hem
	_px_rect(img, 13, 9, 3, 4, p.gn)  # briefcase
	_px_h_line(img, 8, 13, 15, p.gd)  # handle
	_px(img, 14, 9, p.wh)             # latch

# Gravy Seal — 12px box helmet with HUD, extra-bulky torso, assault rifle
func _draw_gravy_seal(img: Image, p: Dictionary) -> void:
	_px_rect(img, 3, 7, 10, 7, p.c)   # wide chest plate
	_px_rect(img, 4, 9, 8, 3, p.cd)   # armor ribbing
	_px_rect(img, 1, 7, 2, 6, p.c)    # thick left arm
	_px_rect(img, 13, 7, 2, 5, p.c)   # right arm
	_px_h_line(img, 14, 2, 13, p.dk)  # belt
	_px_rect(img, 3, 15, 4, 5, p.cd); _px_rect(img, 9, 15, 4, 5, p.cd)
	_px_rect(img, 2, 20, 5, 3, p.dk); _px_rect(img, 9, 20, 5, 3, p.dk)
	_px_rect(img, 2, 0, 12, 7, p.c)   # box helmet — 12px wide, 7px tall (y=0-6)
	_px_h_line(img, 3, 2, 13, p.dk)   # visor slit
	_px_h_line(img, 3, 3, 12, Color(1.0, 0.5, 0.08, 0.9))  # HUD orange
	_px(img, 13, 0, p.cd)             # NVG mount
	_px_h_line(img, 9, 13, 15, p.gn)
	_px_rect(img, 13, 8, 2, 4, p.gn)
	_px(img, 14, 12, p.gn)            # magazine

# The Martyr — wide halo (8px), keffiyeh wrap, raised fist, gold cross emblem
func _draw_the_martyr(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px_h_line(img, 0, 4, 11, p.gd)   # halo top arc (8px wide)
	_px(img, 3, 1, p.gd); _px(img, 12, 1, p.gd)
	_px_rect(img, 5, 1, 6, 5, p.sk)   # face
	_px(img, 4, 2, p.c); _px(img, 11, 2, p.c)
	_px(img, 4, 3, p.c); _px(img, 11, 3, p.c)
	_px(img, 4, 5, p.c); _px(img, 11, 5, p.c)
	_px_h_line(img, 6, 4, 11, p.c)    # keffiyeh lower wrap (y=6)
	_px(img, 6, 3, p.dk); _px(img, 9, 3, p.dk)
	_px(img, 8, 8, p.gd)
	_px_h_line(img, 9, 7, 9, p.gd)    # gold cross
	_px(img, 8, 10, p.gd)
	_px_rect(img, 0, 2, 2, 5, p.c)    # raised left arm
	_px(img, 0, 1, p.sk); _px(img, 1, 1, p.sk)    # fist

func _draw_generic(img: Image, p: Dictionary) -> void:
	_draw_base(img, p)
	_px_h_line(img, 1, 5, 10, p.c)    # dome top
	_px_rect(img, 4, 2, 8, 4, p.c)    # dome body
	_px_rect(img, 5, 5, 6, 2, p.sk)   # face (y=5-6)
	_px(img, 6, 6, p.dk); _px(img, 9, 6, p.dk)

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
	var dmg := data.damage * _damage_mult * 0.75
	if data.faction == GameSession.player_faction:
		dmg *= ROEManager.get_damage_mult()
	target_building.take_damage(dmg)
	_award_xp(3.0)

func shoot():
	if current_supplies <= 0 or is_suppressed:
		return
	attack_cooldown = 1.0 / data.attack_speed
	current_supplies -= 1.0
	if data.faction == GameSession.player_faction:
		SoundManager.play_shoot()
	var roe_mult := ROEManager.get_damage_mult() if data.faction == GameSession.player_faction else 1.0
	target_unit.take_damage(data.damage * _damage_mult * 0.5 * roe_mult, "Bureaucracy", global_position)
	if randf() <= data.accuracy:
		target_unit.take_damage(data.damage * _damage_mult * roe_mult, "Vitality", global_position)
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
	SoundManager.play("promotion")
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

func move_to_target(_delta: float) -> void:
	if global_position.distance_to(target_position) <= 0.5:
		velocity = Vector3.ZERO
		return
	var dir := target_position - global_position
	dir.y = 0.0
	if dir.length() > 0.05:
		velocity = dir.normalized() * 5.0
		move_and_slide()
	else:
		velocity = Vector3.ZERO

# ── Damage & Status ────────────────────────────────────────────────────────────

func take_damage(amount: float, type: String = "Vitality", from_pos: Vector3 = Vector3.ZERO):
	var final_amount := amount
	if type == "Vitality" and from_pos != Vector3.ZERO and is_in_cover(from_pos):
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

func is_in_cover(from_pos: Vector3) -> bool:
	var space := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(from_pos, global_position + Vector3(0, 0.8, 0))
	query.collide_with_areas = false
	var hit := space.intersect_ray(query)
	return hit and (hit["collider"] as Node).is_in_group("cover")

func apply_suppression():
	if is_suppressed:
		return
	is_suppressed = true
	if data.faction == GameSession.player_faction:
		AdvisorManager.speak("suppressed")
	_status_label.text     = "█ RED TAPE █"
	_status_label.modulate = Color(1.0, 0.15, 0.15)
	if data.faction == GameSession.player_faction:
		SoundManager.play("suppressed")
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
	for t in tethered_units:
		if is_instance_valid(t) and t.has_method("untether"):
			t.untether()
	tethered_units.clear()
	
	if is_soul_leader:
		var hero_data := {
			"unit_type":      data.unit_name,
			"faction":        data.faction,
			"veterancy_rank": current_rank,
			"status":         "REDACTED"
		}
		SupabaseManager.save_hero_to_cloud(hero_data)
	queue_free()

func tether_civilians(radius: float = 5.0):
	if not is_soul_leader: return # Only squad leaders can tether
	
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsShapeQueryParameters3D.new()
	var sphere = SphereShape3D.new()
	sphere.radius = radius
	query.shape = sphere
	query.transform = global_transform
	
	var results = space_state.intersect_shape(query)
	for res in results:
		var obj = res.collider
		if obj.has_method("tether_to") and obj.current_state == 0:
			obj.tether_to(self)
			tethered_units.append(obj)
			if ROEManager.current_roe >= 3:
				InfamyManager.add_infamy(5, "forced_tether")
