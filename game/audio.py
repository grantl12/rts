"""
Procedural audio system — no WAV files required.
All sounds are synthesized at startup from sine waves and noise.
Fails silently if mixer is unavailable.
"""
import array, math, random

_RATE = 22050   # samples per second


def _buf(samples_mono):
    """Wrap a mono sample list into a pygame.mixer.Sound, handling stereo if needed."""
    try:
        import pygame
        info = pygame.mixer.get_init()
        if info is None:
            return None
        _, _, channels = info
        arr = array.array('h', samples_mono)
        if channels == 2:
            stereo = array.array('h', [0] * (len(arr) * 2))
            for i, s in enumerate(arr):
                stereo[i * 2]     = s
                stereo[i * 2 + 1] = s
            return pygame.mixer.Sound(buffer=stereo)
        return pygame.mixer.Sound(buffer=arr)
    except Exception:
        return None


def _sine_wave(freq, duration, vol=0.35, decay=False):
    n   = int(_RATE * duration)
    out = []
    for i in range(n):
        t   = i / _RATE
        env = (1 - i / n) if decay else 1.0
        out.append(int(env * vol * 32767 * math.sin(2 * math.pi * freq * t)))
    return out


def _noise(duration, vol=0.4, decay=True, low_pass=False):
    n   = int(_RATE * duration)
    out = []
    prev = 0
    for i in range(n):
        env   = (1 - i / n) ** 1.5 if decay else 1.0
        raw   = random.uniform(-1, 1)
        s     = (prev * 0.4 + raw * 0.6) if low_pass else raw   # simple LP filter
        prev  = s
        out.append(int(env * vol * 32767 * s))
    return out


def _glide(freq_start, freq_end, duration, vol=0.3, decay=False):
    n   = int(_RATE * duration)
    out = []
    for i in range(n):
        t    = i / _RATE
        pct  = i / n
        freq = freq_start + (freq_end - freq_start) * pct
        env  = (1 - pct) if decay else 1.0
        out.append(int(env * vol * 32767 * math.sin(2 * math.pi * freq * t)))
    return out


def _concat(*segs):
    out = []
    for s in segs:
        out.extend(s)
    return out


def _silence(duration):
    return [0] * int(_RATE * duration)


# ── Sound definitions ─────────────────────────────────────────────────────────

def _make_gunshot():
    return _buf(_noise(0.055, vol=0.5, decay=True))

def _make_heavy_shot():
    return _buf(_concat(
        _sine_wave(80, 0.03, vol=0.5, decay=False),
        _noise(0.09, vol=0.45, decay=True, low_pass=True),
    ))

def _make_explosion():
    return _buf(_concat(
        _sine_wave(55, 0.04, vol=0.6),
        _noise(0.45, vol=0.55, decay=True, low_pass=True),
    ))

def _make_move_order():
    return _buf(_concat(
        _sine_wave(620, 0.032, vol=0.25, decay=False),
        _silence(0.016),
        _sine_wave(820, 0.032, vol=0.25, decay=True),
    ))

def _make_capture():
    return _buf(_concat(
        _sine_wave(390, 0.07, vol=0.28, decay=False),
        _silence(0.01),
        _sine_wave(490, 0.07, vol=0.28, decay=False),
        _silence(0.01),
        _sine_wave(640, 0.12, vol=0.3, decay=True),
    ))

def _make_alert():
    seg = _concat(
        _sine_wave(1100, 0.10, vol=0.3, decay=False),
        _silence(0.04),
        _sine_wave(1100, 0.10, vol=0.3, decay=False),
        _silence(0.04),
        _sine_wave(1100, 0.10, vol=0.28, decay=True),
    )
    return _buf(seg)

def _make_spawn():
    return _buf(_glide(260, 520, 0.08, vol=0.22, decay=False))

def _make_infamy_tick():
    return _buf(_concat(
        _sine_wave(500, 0.07, vol=0.22, decay=False),
        _silence(0.01),
        _sine_wave(380, 0.07, vol=0.22, decay=False),
        _silence(0.01),
        _sine_wave(280, 0.10, vol=0.22, decay=True),
    ))

def _make_blip():
    return _buf(_sine_wave(760, 0.022, vol=0.18, decay=True))

def _make_building_lost():
    return _buf(_concat(
        _sine_wave(440, 0.07, vol=0.25),
        _noise(0.12, vol=0.3, decay=True, low_pass=True),
    ))

def _make_bus_unload():
    return _buf(_concat(
        _sine_wave(520, 0.04, vol=0.2),
        _silence(0.01),
        _sine_wave(660, 0.04, vol=0.2),
        _silence(0.01),
        _sine_wave(820, 0.06, vol=0.22, decay=True),
    ))


# ── Manager ───────────────────────────────────────────────────────────────────

class AudioManager:
    def __init__(self):
        self._sounds  = {}
        self._enabled = True
        self._combat_cooldown = 0.0   # prevents gunshot spam
        self._try_init()

    def _try_init(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=_RATE, size=-16, channels=1, buffer=256)
            self._sounds = {
                "gunshot":       _make_gunshot(),
                "heavy_shot":    _make_heavy_shot(),
                "explosion":     _make_explosion(),
                "move_order":    _make_move_order(),
                "capture":       _make_capture(),
                "alert":         _make_alert(),
                "spawn":         _make_spawn(),
                "infamy_tick":   _make_infamy_tick(),
                "blip":          _make_blip(),
                "building_lost": _make_building_lost(),
                "bus_unload":    _make_bus_unload(),
            }
            # Set volumes
            for snd in self._sounds.values():
                if snd:
                    snd.set_volume(0.6)
        except Exception:
            self._enabled = False

    def play(self, key: str):
        if not self._enabled:
            return
        snd = self._sounds.get(key)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def update(self, dt_sec: float):
        self._combat_cooldown = max(0.0, self._combat_cooldown - dt_sec)

    def play_combat(self, heavy=False):
        """Rate-limited combat sound — call when any unit fires."""
        if not self._enabled or self._combat_cooldown > 0:
            return
        self._combat_cooldown = 0.18
        self.play("heavy_shot" if heavy else "gunshot")

    def toggle_mute(self):
        self._enabled = not self._enabled
