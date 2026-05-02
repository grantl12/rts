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
    "rank_5_promotion": [
        "Executive rank achieved. Naming rights have been processed. Congratulations are contractually mandated.",
        "Elite designation confirmed. This individual is now a liability. Guard accordingly.",
        "Operative has exceeded standard performance metrics. A plaque is being considered. Probably.",
    ],
    "tape_acquired": [
        "Sensitive archival material secured. Its contents are, of course, unverified. Officially.",
        "High-value intelligence asset acquired. Do not describe its contents in writing. Or aloud.",
        "The tape is now in your custody. This is either very good or very bad. Possibly both.",
    ],
    "tape_lost": [
        "Archival material has been... misplaced. This is a routine administrative incident.",
        "Sensitive asset no longer in custody. We recommend immediate retrieval before it becomes a headline.",
        "The tape is loose. Begin not-panicking protocols.",
    ],
    "vbied_armed": [
        "Mobile explosive asset detected in civilian configuration. Do not approach. Do not park nearby.",
        "Sovereign vehicle improvisation in progress. Recommend immediate tactical repositioning.",
        "A car is no longer just a car. This is a Sovereign operational update. Good luck.",
    ],
    "cease_desist": [
        "Legal interdiction filed. Enemy personnel are now experiencing administrative difficulties.",
        "Cease and desist issued. Compliance is mandatory. Enforcement is contractual.",
        "Patriot Lawyer has deployed procedural suppression. The paperwork is real. The suffering is real.",
    ],
    "witness_radicalized": [
        "Civilian has been radicalized by Sovereign proximity. This was not in the risk model.",
        "Local witness converted to armed asset. This is why we do not leave civilians unattended.",
        "Radicalization confirmed. Recommend containment, or at minimum, distance.",
    ],
    "power_low": [
        "Power grid underpowered. Production is on hold pending infrastructure investment.",
        "Energy deficit detected. Build a substation or accept strategic paralysis.",
        "Operational capacity suspended. Power is not optional. Build more substations.",
    ],
    "unit_locked": [
        "Production prerequisite not met. The correct building must exist before this unit can be trained.",
        "This unit requires a facility that you have not yet constructed. That is the rule.",
        "Acquisition denied. The appropriate infrastructure is absent. Build it first.",
    ],
    "salvage": [
        "Wreck converted to administrative credit. Oligarchy efficiency metrics improving.",
        "Salvage operation complete. Someone else's loss is now your budget line.",
        "Asset recovery confirmed. The market finds a way.",
    ],
    "journalist_killed": [
        "Credentialed media asset neutralized. Infamy penalty has been logged. By them.",
        "A journalist has been processed. This is now international news. Congratulations.",
        "Press casualty recorded. Expect the infamy meter to have feelings about this.",
    ],
    "meat_grinder": [
        "Wagner contingent deployed. They are aware of the risks. Mostly.",
        "Five expendable assets en route. Operational efficiency through attrition.",
        "Meat Grinder activated. They volunteered. This is the official position.",
    ],
    "crowdfunding": [
        "Crowdfunding window opened. Chaos metrics are generating revenue.",
        "Viral engagement translated to operational capital. As intended.",
        "Donation surge confirmed. The algorithm is working for us today.",
    ],
    "kickback": [
        "Funds redirected from opposing interests. Administratively speaking, this never happened.",
        "Kickback processed. Their loss. Our gain. The ledger balances.",
        "Asset transfer complete. The other faction's accountant will be confused.",
    ],
    "shadow_cell": [
        "Shadow cell deployed. They are not here. You did not see this.",
        "Proxy assets activated. No attribution. No footprint. As intended.",
        "Black market reinforcements confirmed. Deniability is a feature, not a bug.",
    ],
    "agitator_active": [
        "Agitator unit in the field. Red Tape dissipation radius active.",
        "Megaphone deployed. Bureaucratic interference is being... countered.",
        "Agitator operational. Morale suppression reduced in zone. Temporarily.",
    ],
    "donor_killed": [
        "A Donor has been neutralized. This is a political incident. Update your liability waiver.",
        "High-value political asset eliminated. Nearby units are experiencing morale feedback.",
        "The Donor has been processed. Your own personnel are now suppressed. As predicted.",
    ],
    "ddos_hit": [
        "DDoS pulse delivered. Enemy systems experiencing... administrative difficulties.",
        "Target infrastructure disrupted. Their IT department will not be pleased.",
        "Digital interdiction successful. Production at target facility is offline.",
    ],
    "scotus_gavel": [
        "SCOTUS Gavel deployed. The area has been formally de-zoned. Legally.",
        "Construction zone declared inactive by executive order. This is binding. Probably.",
        "Area of operations legally cleared. Enemy building permits: denied.",
    ],
    "drone_swarm": [
        "Drone swarm launched. Four simultaneous kinetic engagements in progress.",
        "FPV assets deployed. Multiple high-value targets being re-evaluated.",
        "Swarm protocol active. This is what we call a target-rich environment.",
    ],
    "epstein_leak": [
        "The files are live. Map reveal active. Enemy income is experiencing a confidence crisis.",
        "Classified archive deployed. Everybody can see everything now. Including us.",
        "Epstein Protocol initiated. Full spectrum transparency. Temporarily.",
    ],
    "troll_surge": [
        "Troll Farm output at maximum. Capture erosion doubled. The comments section is unmanageable.",
        "Amplification surge authorized. Enemy audit progress is now a liability.",
        "The farms are operating at full influence capacity. We recommend not reading the replies.",
    ],
    "iron_dome_intercept": [
        "Intercept station online. Hostile drones are being administratively suppressed.",
        "Iron Dome active. Aerial assets in range are experiencing... difficulties.",
    ],
    "interpreter_active": [
        "Interpreter deployed. Enemy audit communications are being... mistranslated.",
        "Translation services engaged. Capture rate in area reduced by 50%.",
    ],
    "direktor_killed": [
        "The Direktor has been eliminated. His portfolio will be... redistributed.",
        "Kraznov is down. Asset recovery protocols initiated. The yacht is unaccounted for.",
        "Executive casualty confirmed. The board has been notified. Condolences are pending approval.",
    ],
    "hq_under_fire": [
        "This is fine. The structure is fine. Everything is procedurally fine.",
        "HQ integrity is... sub-optimal. Recommend not panicking. This is fine.",
        "Command post is experiencing structural feedback. This is fine.",
    ],
    "upgrade_purchased": [
        "Procurement approved. Field personnel have been notified. Probably.",
        "Equipment upgrade processed. Enhanced compliance assets inbound.",
        "Research investment confirmed. The board approves. Mostly.",
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
