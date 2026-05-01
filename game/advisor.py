"""Advisor System — in-universe HR/GPS voice for The Deep State."""
import math, random, pygame

_LINES = {
    "building_captured_player": [
        "Asset acquisition confirmed. Narrative zone secured.",
        "Location processed. Filing with the appropriate department.",
        "Excellent initiative, Citizen-Officer. This will reflect well in your review.",
    ],
    "building_captured_enemy": [
        "Location... reassigned. This was not in the operational brief.",
        "Territory shift detected. Recommend immediate remediation.",
        "That asset is now in unauthorized hands. Update your insurance.",
    ],
    "scrutinized": [
        "Visibility index elevated. Recommend measured discretion.",
        "You are being observed. This is normal. Carry on.",
        "Oversight protocols active. Nothing to worry about. Probably.",
    ],
    "surveilled": [
        "Aerial observation units deployed. Please behave accordingly.",
        "Frontline assets are monitoring your performance metrics.",
        "Drone coverage initiated. Limiting collateral damage is... advisable.",
    ],
    "sanctioned": [
        "Heavy production suspended. Compliance protocols engaged. This is temporary.",
        "Administrative freeze applied to high-value asset lines. Budget accordingly.",
        "Certain production lines are... inadvisable at this time. Work with what you have.",
    ],
    "runner_arrived": [
        "HVP reached alternate narrative node. Consequence protocols now active.",
        "High-value asset reached destination. Enemy reinforcements en route. Per procedure.",
        "Runner extraction confirmed. This development was anticipated. Mostly.",
    ],
    "deepfake_live": [
        "Synthetic Kirk instance now live. Engagement: optimal. Authenticity: irrelevant.",
        "AI reconstruction of Kirk broadcasting on all platforms. The narrative is flexible.",
        "Deepfake deployment confirmed. The official memory is now being installed.",
    ],
    "bolo_captured_player": [
        "BOLO target secured. Administrative bonus processed. Good work, Citizen-Officer.",
        "Target asset acquired. Bonus credits issued. Efficiency noted in your file.",
    ],
    "bolo_captured_enemy": [
        "BOLO target acquired by opposing faction. This is a suboptimal outcome.",
        "Target asset lost to competing interests. Adjust your priorities.",
    ],
    "bus_unloaded": [
        "Compliance transport processed. Administrative efficiencies recorded.",
        "Asset delivery confirmed. Credits posted to your discretionary account.",
        "Bus unloaded. Detainees are now in the system. Welcome to the database.",
    ],
    "roe_5": [
        "Rules of Engagement fully suspended. This decision has been logged. Somewhere.",
        "Absolute Immunity authorized. All incidents will be reviewed internally. By us.",
        "Escalation protocol maximum engaged. Consequences are pending audit.",
    ],
    "building_destroyed": [
        "Structural asset decommissioned. Paperwork is being filed.",
        "Location destroyed. Environmental impact assessment to follow.",
        "That building is no longer a building. Update the map accordingly.",
    ],
    "vbied_explode": [
        "Sovereign vehicle IED detonated. This was not in the risk assessment.",
        "Explosive device event logged. Recommend increasing personal safety protocols.",
        "Unscheduled demolition detected. Assessing casualties... please hold.",
    ],
    "infamy_scrutinized": [
        "Public perception index is trending unfavorably. Recommend optics review.",
    ],
    "infamy_surveilled": [
        "Media presence escalating. Frontline observation assets are active.",
    ],
    "infamy_sanctioned": [
        "Administrative sanctions applied. Certain capabilities are now restricted.",
    ],
}


class AdvisorSystem:
    DISPLAY_DURATION = 5.5
    FADE_IN  = 0.3
    FADE_OUT = 1.0

    def __init__(self):
        self._queue   = []
        self._current = None
        self._timer   = 0.0
        self._font    = None

    def trigger(self, event_key: str):
        lines = _LINES.get(event_key)
        if not lines:
            return
        msg = random.choice(lines)
        if msg != self._current and msg not in self._queue:
            self._queue.append(msg)
        if self._current is None:
            self._advance()

    def _advance(self):
        if self._queue:
            self._current = self._queue.pop(0)
            self._timer   = self.DISPLAY_DURATION
        else:
            self._current = None
            self._timer   = 0.0

    def update(self, dt_sec):
        if self._current is None:
            return
        self._timer -= dt_sec
        if self._timer <= 0:
            self._advance()

    def draw(self, surf, sw, sh):
        if not self._current:
            return
        if self._font is None:
            self._font        = pygame.font.SysFont("couriernew", 13, bold=True)
            self._font_prefix = pygame.font.SysFont("couriernew", 11, bold=True)

        if self._timer > self.DISPLAY_DURATION - self.FADE_IN:
            alpha = int(255 * (self.DISPLAY_DURATION - self._timer) / self.FADE_IN)
        elif self._timer < self.FADE_OUT:
            alpha = int(255 * self._timer / self.FADE_OUT)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        from game.hud import TOPBAR_H, SIDEBAR_W
        bar_h = 32
        y     = TOPBAR_H + 6
        w     = sw - SIDEBAR_W - 20

        # Solid dark panel — fully opaque so text is always readable
        panel = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        panel.fill((2, 14, 10, min(235, int(alpha * 0.95))))
        surf.blit(panel, (8, y))
        # Teal left accent bar
        accent = pygame.Surface((3, bar_h), pygame.SRCALPHA)
        accent.fill((0, 220, 160, alpha))
        surf.blit(accent, (8, y))
        pygame.draw.rect(surf, (0, 60, 45), (8, y, w, bar_h), 1)

        glitch = int(math.sin(pygame.time.get_ticks() * 0.04) * 1)
        ty = y + bar_h // 2 - self._font.get_height() // 2

        prefix = self._font_prefix.render("// AUDITOR :", True, (0, 210, 150))
        prefix.set_alpha(alpha)
        surf.blit(prefix, (16 + glitch, ty + 2))

        body = self._font.render(self._current, True, (230, 255, 230))
        body.set_alpha(alpha)
        surf.blit(body, (16 + prefix.get_width() + 8 + glitch, ty))
