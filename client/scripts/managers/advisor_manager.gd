extends Node

## THE DEEP STATE: Advisor Manager
## "The Auditor" — faction-specific reactive commentary.
## Rate-limited per event type so lines don't spam.

signal advisor_spoke(text: String)

const _COOLDOWN := 25.0

const _LINES := {
	"Regency": {
		"briefing":    "Greetings, Citizen-Officer. Secure the Quad. Ensure the Official Memory is properly installed. Do not mind the protestors — they have already been audited.",
		"capture":     "Excellent. The narrative has been stabilized. Jurisdiction acknowledged.",
		"suppressed":  "Unit compromised by Red Tape. Bureaucratic intervention required immediately.",
		"hq_attack":   "PRIORITY ALERT: Our base of operations is under assault. This is highly irregular.",
		"promotion":   "Field promotion confirmed. Enhanced operational parameters have been logged and approved.",
		"victory":     "Mission accomplished. The Quad has been audited. Your performance has been noted in the official record.",
		"defeat":      "The jurisdiction has been compromised. A full audit of your decisions will be conducted.",
	},
	"Oligarchy": {
		"briefing":    "Deploy your assets. Control the narrative. The opposition will be processed and liquidated.",
		"capture":     "Resource secured. Shareholders are satisfied. Continue extraction.",
		"suppressed":  "Unit experiencing compliance failure. This is unacceptable. Unacceptable.",
		"hq_attack":   "OUR ASSETS ARE UNDER ATTACK. Protect the investment at all costs.",
		"promotion":   "Promotion approved. Raise their performance bonus by two percent. Loyalty rewarded.",
		"victory":     "Outstanding. Another market captured. The consolidation continues on schedule.",
		"defeat":      "Assets liquidated. Begin restructuring protocols. Find someone to blame.",
	},
	"Frontline": {
		"briefing":    "They're trying to bronze him, guys. We need to leak the raw footage and reclaim the Quad. The algorithm is watching.",
		"capture":     "Audit the Audit! The truth is uploading. Keep pushing — the grid is shifting!",
		"suppressed":  "Signal jammed! Red Tape in the feed. Reroute through a secondary node!",
		"hq_attack":   "They're hitting our servers! Distribute the load! Get everyone online!",
		"promotion":   "Level up! That unit just hit a new thread. The community is rallying around them.",
		"victory":     "The glitch is spreading. The grid is ours. His redaction is our greatest asset. For the Cloud!",
		"defeat":      "We've been 404'd. Regroup. The broadcast will continue from a new location.",
	},
	"Sovereign": {
		"briefing":    "The Quad is sovereign territory. We do not recognize their jurisdiction. Move.",
		"capture":     "Zone secured. Their laws do not apply here. Hold the line.",
		"suppressed":  "Bureaucratic countermeasure deployed against our unit. We operate outside their system.",
		"hq_attack":   "They dare intrude on sovereign ground. Make them regret every step.",
		"promotion":   "Veteran recognized. The zone remembers its own. They answer to no one but the cause.",
		"victory":     "The border holds. Their institutions are illusions. We remain.",
		"defeat":      "The zone has been compromised. Relocate. The sovereign claim is never surrendered.",
	},
}

var _last_event_times: Dictionary = {}

func speak(event: String) -> void:
	var now := Time.get_unix_time_from_system()
	if now < _last_event_times.get(event, 0.0) + _COOLDOWN:
		return
	_last_event_times[event] = now

	var faction := GameSession.player_faction
	var faction_lines: Dictionary = _LINES.get(faction, _LINES["Regency"])
	var line: String = faction_lines.get(event, "")
	if line.is_empty():
		return
	advisor_spoke.emit(line)
