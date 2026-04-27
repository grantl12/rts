extends Node

## THE DEEP STATE: Game Session
## Persists player faction choice and per-faction defaults across scenes.

var player_faction: String = "Regency"
var enemy_faction: String = "Oligarchy"

const _RIVALS := {
	"Regency": "Oligarchy",
	"Oligarchy": "Regency",
	"Frontline": "Sovereign",
	"Sovereign": "Frontline"
}

const _DEFAULT_UNITS := {
	"Regency": "res://resources/units/park_ranger.tres",
	"Oligarchy": "res://resources/units/conscript.tres",
	"Frontline": "res://resources/units/digital_nomad.tres",
	"Sovereign": "res://resources/units/the_proxy.tres"
}

func set_player_faction(faction: String) -> void:
	player_faction = faction
	enemy_faction = _RIVALS.get(faction, "Oligarchy")

func default_unit_path(faction: String) -> String:
	return _DEFAULT_UNITS.get(faction, "res://resources/units/conscript.tres")
