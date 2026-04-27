extends Node

## THE DEEP STATE: Sound Manager
## All audio is synthesised at startup — no external files needed.
## Sounds are thematic: bureaucratic stamps, radio crackle, ascending chimes.

const RATE := 22050

var _shoot_throttle: float = -99.0

func _ready() -> void:
	_build("shoot",              _gen_shoot())
	_build("capture",            _gen_capture())
	_build("suppressed",         _gen_suppressed())
	_build("promotion",          _gen_promotion())
	_build("fact_check",         _gen_fact_check())
	_build("reinforce",          _gen_reinforce())
	_build("hq_alert",           _gen_hq_alert())
	_build("ui_click",           _gen_ui_click())
	_build("absolute_immunity",  _gen_absolute_immunity())

func _build(id: String, wav: AudioStreamWAV) -> void:
	var p       := AudioStreamPlayer.new()
	p.name      = id
	p.stream    = wav
	if id == "shoot":
		p.max_polyphony = 4
	add_child(p)

# Public API ───────────────────────────────────────────────────────────────────

func play(id: String, volume_db: float = 0.0) -> void:
	var p := get_node_or_null(id) as AudioStreamPlayer
	if p:
		p.volume_db = volume_db
		p.play()

func play_shoot() -> void:
	# Throttle so a volley of units doesn't spam identical sounds
	var now := Time.get_unix_time_from_system()
	if now < _shoot_throttle + 0.18:
		return
	_shoot_throttle = now
	play("shoot")

# WAV helpers ──────────────────────────────────────────────────────────────────

func _make_wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		var s := int(clampf(samples[i], -1.0, 1.0) * 32767.0)
		data[i * 2]     = s & 0xFF
		data[i * 2 + 1] = (s >> 8) & 0xFF
	var wav        := AudioStreamWAV.new()
	wav.format     = AudioStreamWAV.FORMAT_16_BIT
	wav.mix_rate   = RATE
	wav.stereo     = false
	wav.data       = data
	return wav

func _sine(t: float, freq: float) -> float:
	return sin(TAU * freq * t)

# Sound definitions ────────────────────────────────────────────────────────────

func _gen_shoot() -> AudioStreamWAV:
	# Short suppressed-crack: descending sine + noise tail
	var n := int(RATE * 0.065)
	var s := PackedFloat32Array(); s.resize(n)
	for i in n:
		var t   := float(i) / RATE
		var env := exp(-t * 48.0)
		s[i] = (_sine(t, 240.0) * 0.65 + randf_range(-1.0, 1.0) * 0.35) * env
	return _make_wav(s)

func _gen_capture() -> AudioStreamWAV:
	# Three ascending tones — C5, E5, G5
	var freqs     := [523.0, 659.0, 784.0]
	var note_n    := int(RATE * 0.10)
	var s := PackedFloat32Array(); s.resize(note_n * freqs.size() + int(RATE * 0.08))
	for ni in freqs.size():
		var off := ni * note_n
		for i in note_n:
			var t   := float(i) / RATE
			var env := exp(-t * 4.5)
			s[off + i] += _sine(t, freqs[ni]) * env * 0.75
	return _make_wav(s)

func _gen_suppressed() -> AudioStreamWAV:
	# Descending buzz + noise — bureaucratic interference
	var n := int(RATE * 0.32)
	var s := PackedFloat32Array(); s.resize(n)
	for i in n:
		var t    := float(i) / RATE
		var env  := exp(-t * 3.8)
		var freq := 290.0 - 190.0 * (t / 0.32)
		s[i] = (_sine(t, freq) * 0.55 + randf_range(-1.0, 1.0) * 0.45) * env
	return _make_wav(s)

func _gen_promotion() -> AudioStreamWAV:
	# Four-note ascending arpeggio — C5 E5 G5 C6
	var freqs  := [523.0, 659.0, 784.0, 1047.0]
	var note_n := int(RATE * 0.10)
	var tail_n := int(RATE * 0.18)
	var s := PackedFloat32Array(); s.resize(note_n * freqs.size() + tail_n)
	for ni in freqs.size():
		var off := ni * note_n
		for i in note_n + (tail_n if ni == freqs.size() - 1 else 0):
			var t   := float(i) / RATE
			var env := exp(-t * 3.5)
			s[off + i] += _sine(t, freqs[ni]) * env * 0.7
	return _make_wav(s)

func _gen_fact_check() -> AudioStreamWAV:
	# Bureaucratic stamp: low thump then static burst
	var thump_n := int(RATE * 0.11)
	var gap_n   := int(RATE * 0.05)
	var burst_n := int(RATE * 0.14)
	var s := PackedFloat32Array(); s.resize(thump_n + gap_n + burst_n)
	for i in thump_n:
		var t := float(i) / RATE
		s[i] = _sine(t, 72.0) * exp(-t * 28.0) * 0.9
	for i in burst_n:
		var t := float(i) / RATE
		s[thump_n + gap_n + i] = randf_range(-1.0, 1.0) * exp(-t * 18.0) * 0.65
	return _make_wav(s)

func _gen_reinforce() -> AudioStreamWAV:
	# Radio-static sweep ascending — signal locking on
	var n := int(RATE * 0.48)
	var s := PackedFloat32Array(); s.resize(n)
	for i in n:
		var t    := float(i) / RATE
		var env  := minf(t * 10.0, 1.0) * (1.0 - t / 0.48)
		var freq := 160.0 + 440.0 * (t / 0.48)
		s[i] = (_sine(t, freq) * 0.60 + randf_range(-1.0, 1.0) * 0.40) * env
	return _make_wav(s)

func _gen_hq_alert() -> AudioStreamWAV:
	# Two-tone alarm — alternating 440 / 554 Hz
	var n   := int(RATE * 0.60)
	var seg := int(RATE * 0.15)
	var s   := PackedFloat32Array(); s.resize(n)
	var freqs := [440.0, 554.0]
	for i in n:
		var t   := float(i) / RATE
		var f   := freqs[(i / seg) % 2]
		var env := 0.85 + 0.15 * sin(TAU * 7.0 * t)
		s[i] = _sine(t, f) * env * 0.82
	return _make_wav(s)

func _gen_ui_click() -> AudioStreamWAV:
	# Crisp tick — 900 Hz, 30 ms
	var n := int(RATE * 0.030)
	var s := PackedFloat32Array(); s.resize(n)
	for i in n:
		var t := float(i) / RATE
		s[i] = _sine(t, 900.0) * exp(-t * 85.0) * 0.72
	return _make_wav(s)

func _gen_absolute_immunity() -> AudioStreamWAV:
	# Deep sub-bass drone swelling into distorted harmonics — irreversible, ominous
	var n := int(RATE * 1.4)
	var s := PackedFloat32Array(); s.resize(n)
	for i in n:
		var t   := float(i) / RATE
		var env := minf(t * 2.5, 1.0) * (0.7 + 0.3 * sin(TAU * 0.6 * t))
		s[i] = clampf(
			(_sine(t, 55.0) * 0.55 +
			 _sine(t, 110.0) * 0.25 +
			 _sine(t, 220.0) * 0.15 +
			 randf_range(-1.0, 1.0) * 0.12) * env,
			-1.0, 1.0)
	return _make_wav(s)
