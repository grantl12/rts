"""
Event notification system — scrolling text log on left edge of screen.
"""
import pygame

DARK   = (6, 13, 10)
TEAL   = (0, 255, 204)
ORANGE = (255, 102, 0)
RED    = (220, 40, 30)
GREEN  = (40, 200, 80)
WHITE  = (200, 200, 200)

LIFETIME = 6.0   # seconds before a notification fades out
MAX_SHOWN = 8


class NotificationManager:
    def __init__(self):
        self._queue = []  # [(text, color, age)]
        self._font  = None

    def _load_font(self):
        if not self._font:
            self._font = pygame.font.SysFont("couriernew", 9)

    def add(self, text: str, color=None):
        if color is None:
            color = TEAL
        self._queue.append([text, color, 0.0])
        if len(self._queue) > 24:
            self._queue.pop(0)

    def update(self, dt_sec):
        for entry in self._queue:
            entry[2] += dt_sec
        self._queue = [e for e in self._queue if e[2] < LIFETIME]

    def draw(self, surf, x=8, bottom_y=None):
        self._load_font()
        if bottom_y is None:
            bottom_y = surf.get_height() - 52

        visible = [e for e in self._queue if e[2] < LIFETIME][-MAX_SHOWN:]
        line_h = 13
        y = bottom_y - len(visible) * line_h

        for text, color, age in visible:
            alpha = max(0, min(255, int(255 * (1.0 - age / LIFETIME) * 2)))
            col = tuple(int(c * alpha / 255) for c in color)
            lbl = self._font.render(f"▸ {text}", True, col)
            surf.blit(lbl, (x, y))
            y += line_h
