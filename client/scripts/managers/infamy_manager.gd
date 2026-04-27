extends Node

## THE DEEP STATE: Infamy Manager
## Global reputation damage tracker. High infamy triggers Frontline
## surveillance, press briefings, and eventually International Sanctions.

signal infamy_changed(new_value: int)

const MAX_INFAMY          := 1000
const THRESHOLD_SANCTIONS   := 750   # Collective freezes high-tier production
const THRESHOLD_SURVEILLANCE := 400  # Frontline drones start appearing
const THRESHOLD_PRESS        := 200  # Press briefing mandatory on next post-op

var infamy: int = 0

func add_infamy(amount: int, source: String = "") -> void:
	infamy = mini(infamy + amount, MAX_INFAMY)
	infamy_changed.emit(infamy)
	if source != "":
		print("[INFAMY] +%d (%s) → %d / %d  [ %s ]" % [amount, source, infamy, MAX_INFAMY, get_tier()])

func reduce_infamy(amount: int) -> void:
	infamy = maxi(infamy - amount, 0)
	infamy_changed.emit(infamy)

func reset() -> void:
	infamy = 0
	infamy_changed.emit(0)

func get_tier() -> String:
	if infamy >= THRESHOLD_SANCTIONS:    return "SANCTIONED"
	if infamy >= THRESHOLD_SURVEILLANCE: return "SURVEILLED"
	if infamy >= THRESHOLD_PRESS:        return "SCRUTINIZED"
	return "CONTAINED"

func is_sanctioned() -> bool:
	return infamy >= THRESHOLD_SANCTIONS

func is_surveilled() -> bool:
	return infamy >= THRESHOLD_SURVEILLANCE
