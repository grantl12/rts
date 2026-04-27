extends Node

## THE DEEP STATE: Advisor Manager
## "The Auditor" — faction-specific reactive commentary.
## Rate-limited per event type so lines don't spam.

signal advisor_spoke(text: String)

const _COOLDOWN := 25.0

const _LINES := {
	"Regency": {
		"briefing":           "Greetings, Citizen-Officer. Secure the Quad. Ensure the Official Memory is properly installed. Do not mind the protestors — they have already been audited.",
		"capture":            "Excellent. The narrative has been stabilized. Jurisdiction acknowledged.",
		"suppressed":         "Unit compromised by Red Tape. Bureaucratic intervention required immediately.",
		"hq_attack":          "PRIORITY ALERT: Our base of operations is under assault. This is highly irregular.",
		"promotion":          "Field promotion confirmed. Enhanced operational parameters have been logged and approved.",
		"insufficient_funds": "Insufficient budget. Allocate additional resources before proceeding.",
		"dispersal":          "Director, the subjects are dispersing. Secure the habitats before they reach the perimeter. Every uncollected asset is a liability.",
		"quota_met":          "Detention quota achieved. Fifty subjects secured for re-education. The official record will reflect your efficiency.",
		"absolute_immunity":  "Absolute Immunity is now in effect. All prior constraints have been administratively dissolved. This is not reversible. Do not expect the cameras to come back on.",
		"victory":            "Mission accomplished. The Quad has been audited. Your performance has been noted in the official record.",
		"defeat":             "The jurisdiction has been compromised. A full audit of your decisions will be conducted.",
	},
	"Oligarchy": {
		"briefing":           "Deploy your assets. Control the narrative. The opposition will be processed and liquidated.",
		"capture":            "Resource secured. Shareholders are satisfied. Continue extraction.",
		"suppressed":         "Unit experiencing compliance failure. This is unacceptable. Unacceptable.",
		"hq_attack":          "OUR ASSETS ARE UNDER ATTACK. Protect the investment at all costs.",
		"promotion":          "Promotion approved. Raise their performance bonus by two percent. Loyalty rewarded.",
		"insufficient_funds": "Insufficient capital. The markets will not support this acquisition.",
		"dispersal":          "The inventory is walking away. Round them up — each loose subject is lost revenue.",
		"quota_met":          "Fifty units processed. Staffing quotas filled. The contracts are satisfied.",
		"absolute_immunity":  "Absolute Immunity authorized. Liability exposure is now the board's problem. You have full sanction. Do not leave witnesses.",
		"victory":            "Outstanding. Another market captured. The consolidation continues on schedule.",
		"defeat":             "Assets liquidated. Begin restructuring protocols. Find someone to blame.",
	},
	"Frontline": {
		"briefing":           "They're trying to bronze him, guys. We need to leak the raw footage and reclaim the Quad. The algorithm is watching.",
		"capture":            "Audit the Audit! The truth is uploading. Keep pushing — the grid is shifting!",
		"suppressed":         "Signal jammed! Red Tape in the feed. Reroute through a secondary node!",
		"hq_attack":          "They're hitting our servers! Distribute the load! Get everyone online!",
		"promotion":          "Level up! That unit just hit a new thread. The community is rallying around them.",
		"insufficient_funds": "Not enough in the crowdfund. We need more contributions before we can deploy.",
		"dispersal":          "They're running! The crowd is breaking apart — this is exactly what they wanted to record. Stay on them!",
		"quota_met":          "Fifty witnesses secured. Every one of them is a testimony waiting to happen. Hold those habitats.",
		"absolute_immunity":  "They just went dark. Full blackout. Whatever happens now, it will never trend — because the feed is dead. This is the unrecorded chapter.",
		"victory":            "The glitch is spreading. The grid is ours. His redaction is our greatest asset. For the Cloud!",
		"defeat":             "We've been 404'd. Regroup. The broadcast will continue from a new location.",
	},
	"Sovereign": {
		"briefing":           "The Quad is sovereign territory. We do not recognize their jurisdiction. Move.",
		"capture":            "Zone secured. Their laws do not apply here. Hold the line.",
		"suppressed":         "Bureaucratic countermeasure deployed against our unit. We operate outside their system.",
		"hq_attack":          "They dare intrude on sovereign ground. Make them regret every step.",
		"promotion":          "Veteran recognized. The zone remembers its own. They answer to no one but the cause.",
		"insufficient_funds": "Resources are thin. The zone provides what it can. Wait.",
		"dispersal":          "The people are moving. Let them scatter — then collect what remains. The zone is patient.",
		"quota_met":          "Fifty secured. The zone acknowledges the bounty. Do not let the enemy take what we have built.",
		"absolute_immunity":  "The zone has no rules. It never did. This is just the rest of the world catching up. Do what must be done.",
		"victory":            "The border holds. Their institutions are illusions. We remain.",
		"defeat":             "The zone has been compromised. Relocate. The sovereign claim is never surrendered.",
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
