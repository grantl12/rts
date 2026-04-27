extends CharacterBody3D
class_name Civilian

## THE DEEP STATE: Civilian NPC
## Wanders the map. Sucked into Holding Pens by their capture zones.
## Freed on pen destruction — panics and scatters.

enum CivType { NORMIE, PURPLE_HAIR, RIOT_GEAR, RUNNER }

@export var wander_radius: float = 10.0
@export var wander_speed:  float = 1.1
@export var civ_type: CivType = CivType.NORMIE

const RUNNER_SPEED := 5.4

var is_runner:          bool    = false
var runner_destination: Vector3 = Vector3.ZERO

var _home:     Vector3
var _target:   Vector3
var _sprite:   Sprite3D
var _lbl:      Label3D
var _captured: bool = false

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready() -> void:
	add_to_group("civilians")
	_home   = global_position
	_target = global_position
	if is_runner:
		civ_type = CivType.RUNNER
	elif civ_type == CivType.NORMIE:
		var r := randf()
		if r < 0.25:
			civ_type = CivType.PURPLE_HAIR
		elif r < 0.40:
			civ_type = CivType.RIOT_GEAR
	_build_visuals()
	if is_runner:
		_lbl.text     = "HVP"
		_lbl.modulate = Color(1.0, 0.4, 0.1, 1.0)
		_target = runner_destination
	else:
		_schedule_wander()

func _build_visuals() -> void:
	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.22
	cap.height = 0.85
	col.shape    = cap
	col.position = Vector3(0, 0.5, 0)
	add_child(col)

	_sprite = Sprite3D.new()
	_sprite.pixel_size  = 0.032
	_sprite.billboard   = BaseMaterial3D.BILLBOARD_ENABLED
	_sprite.fixed_size  = false
	_sprite.position    = Vector3(0, 1.0, 0)
	_sprite.texture     = _generate_sprite()
	add_child(_sprite)

	_lbl = Label3D.new()
	_lbl.text         = "HVP" if civ_type == CivType.RUNNER else "CIV"
	_lbl.font_size    = 4
	_lbl.outline_size = 1
	_lbl.billboard    = BaseMaterial3D.BILLBOARD_ENABLED
	_lbl.modulate     = Color(0.85, 0.82, 0.72, 0.65)
	_lbl.position     = Vector3(0, 1.5, 0)
	add_child(_lbl)

# ── Wander AI ─────────────────────────────────────────────────────────────────

func _schedule_wander() -> void:
	await get_tree().create_timer(randf_range(2.0, 5.5)).timeout
	if not is_instance_valid(self) or _captured:
		return
	var angle := randf() * TAU
	var dist  := randf_range(2.0, wander_radius)
	_target = _home + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
	_schedule_wander()

func _physics_process(_delta: float) -> void:
	if _captured:
		return
	var dir := _target - global_position
	dir.y = 0.0
	if dir.length_squared() < 0.3:
		if is_runner:
			is_runner     = false
			wander_radius = 5.0
			_home         = global_position
			_sprite.modulate = Color(0.6, 0.55, 0.55)
			_schedule_wander()
		return
	var spd := RUNNER_SPEED if is_runner else wander_speed
	velocity   = dir.normalized() * spd
	velocity.y = 0.0
	move_and_slide()

# ── Capture / panic ────────────────────────────────────────────────────────────

func get_captured() -> void:
	_captured = true
	queue_free()

func panic() -> void:
	wander_speed = 3.8
	_sprite.modulate = Color(2.0, 1.2, 0.5)
	var angle  := randf() * TAU
	_target    = global_position + Vector3(cos(angle) * wander_radius, 0.0, sin(angle) * wander_radius)
	_home      = global_position
	_captured  = false
	_schedule_wander()

func expand_wander(new_radius: float) -> void:
	if is_runner:
		return
	wander_radius = new_radius
	var angle := randf() * TAU
	var dist  := randf_range(wander_radius * 0.4, wander_radius)
	_target   = _home + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)

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

func _generate_sprite() -> ImageTexture:
	var img := Image.create(16, 24, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	match civ_type:
		CivType.PURPLE_HAIR: _draw_purple_hair(img)
		CivType.RIOT_GEAR:   _draw_riot_gear(img)
		CivType.RUNNER:      _draw_runner(img)
		_:                   _draw_normie(img)
	_outline(img)
	return ImageTexture.create_from_image(img)

func _draw_civ_base(img: Image, shirt: Color, shirt_d: Color, pants: Color) -> void:
	var dk := Color(0.08, 0.08, 0.10)
	_px_rect(img, 4, 7, 8, 6, shirt)
	_px_rect(img, 5, 8, 6, 2, shirt_d)
	_px_rect(img, 3, 7, 1, 5, shirt)   # slim arms (thinner than military)
	_px_rect(img, 12, 7, 1, 5, shirt)
	_px_h_line(img, 13, 4, 11, dk)
	_px_rect(img, 4, 14, 3, 6, pants)
	_px_rect(img, 9, 14, 3, 6, pants)
	_px_rect(img, 3, 20, 4, 2, dk)
	_px_rect(img, 9, 20, 4, 2, dk)

# Normie — brown hair, grey shirt, blue jeans
func _draw_normie(img: Image) -> void:
	var sk  := Color(0.88, 0.72, 0.56)
	var dk  := Color(0.08, 0.08, 0.10)
	var br  := Color(0.38, 0.24, 0.12)
	var gy  := Color(0.55, 0.57, 0.60)
	var gyd := Color(0.38, 0.40, 0.43)
	var bl  := Color(0.22, 0.32, 0.55)
	_draw_civ_base(img, gy, gyd, bl)
	_px_rect(img, 5, 0, 6, 3, br)     # hair
	_px_rect(img, 5, 3, 6, 4, sk)     # face (y=3-6)
	_px(img, 6, 4, dk); _px(img, 9, 4, dk)

# Purple Hair — spiky, protest sign. Law enforcement threat level: elevated.
func _draw_purple_hair(img: Image) -> void:
	var sk  := Color(0.88, 0.72, 0.56)
	var dk  := Color(0.08, 0.08, 0.10)
	var pu  := Color(0.70, 0.20, 0.95)
	var gy  := Color(0.55, 0.57, 0.60)
	var gyd := Color(0.38, 0.40, 0.43)
	var bl  := Color(0.22, 0.32, 0.55)
	var wh  := Color(0.92, 0.92, 0.95)
	_draw_civ_base(img, gy, gyd, bl)
	# spiky purple hair — wide and unmistakable
	_px(img, 4, 0, pu); _px(img, 7, 0, pu); _px(img, 10, 0, pu)
	_px_rect(img, 4, 1, 8, 2, pu)
	# face
	_px_rect(img, 5, 3, 6, 4, sk)
	_px(img, 6, 4, dk); _px(img, 9, 4, dk)
	# protest sign held left — white board with red/blue text lines
	_px_rect(img, 0, 7, 3, 6, wh)
	_px_h_line(img, 8, 0, 2, Color(0.9, 0.1, 0.1))
	_px_h_line(img, 10, 0, 2, Color(0.1, 0.5, 0.9))

# Riot Gear — traffic cone helmet, trash can lid shield. Self-taught tactician.
func _draw_riot_gear(img: Image) -> void:
	var sk  := Color(0.88, 0.72, 0.56)
	var dk  := Color(0.08, 0.08, 0.10)
	var br  := Color(0.38, 0.24, 0.12)
	var gy  := Color(0.55, 0.57, 0.60)
	var gyd := Color(0.38, 0.40, 0.43)
	var bl  := Color(0.22, 0.32, 0.55)
	var or_ := Color(1.00, 0.45, 0.05)
	var ord := Color(0.75, 0.30, 0.02)
	_draw_civ_base(img, gy, gyd, bl)
	# face drawn first so cone renders over it
	_px_rect(img, 5, 4, 6, 3, sk)
	_px(img, 6, 5, dk); _px(img, 9, 5, dk)
	# hair peeking under cone brim
	_px(img, 4, 3, br); _px(img, 5, 3, br)
	_px(img, 10, 3, br); _px(img, 11, 3, br)
	# traffic cone (drawn last, wins at y=3)
	_px(img, 8, 0, or_)
	_px_h_line(img, 1, 7, 8, or_)
	_px_h_line(img, 2, 6, 9, or_)
	_px_h_line(img, 3, 5, 10, ord)    # cone base
	# trash can lid shield on left arm
	_px_rect(img, 0, 8, 3, 5, gy)
	_px(img, 1, 9, gyd); _px(img, 1, 11, gyd)

# Runner (HVP) — dark hoodie, bright frightened eyes, fleeing
func _draw_runner(img: Image) -> void:
	var dk  := Color(0.08, 0.08, 0.10)
	var rd  := Color(1.00, 0.22, 0.08)
	var rdd := Color(0.75, 0.12, 0.04)
	var bl  := Color(0.22, 0.32, 0.55)
	var yw  := Color(1.00, 0.85, 0.10)
	_draw_civ_base(img, rd, rdd, bl)
	# dark hoodie
	_px(img, 8, 0, dk)
	_px_h_line(img, 1, 7, 8, dk)
	_px_h_line(img, 2, 6, 9, dk)
	_px_rect(img, 4, 3, 8, 3, dk)     # hood base + face void
	# wide frightened yellow eyes
	_px(img, 5, 5, yw); _px(img, 6, 5, yw)
	_px(img, 9, 5, yw); _px(img, 10, 5, yw)
	_px_h_line(img, 6, 5, 10, dk)     # collar
