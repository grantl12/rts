extends Node

## THE DEEP STATE: Resource Manager
## Tracks Faction economy and grid stability.

signal resources_changed(faction, amount)

var faction_funds = {
	"Regency": 500,
	"Oligarchy": 500,
	"Frontline": 200,
	"Sovereign": 300
}

func _ready():
	# Passive income timer
	var timer = Timer.new()
	timer.wait_time = 2.0
	timer.autostart = true
	timer.timeout.connect(_on_income_tick)
	add_child(timer)

func _on_income_tick():
	for faction in faction_funds:
		# Income is boosted by capturing Audit Points (logic to be connected)
		add_funds(faction, 10)

func add_funds(faction: String, amount: int):
	faction_funds[faction] += amount
	resources_changed.emit(faction, faction_funds[faction])

func spend_funds(faction: String, amount: int) -> bool:
	if faction_funds[faction] >= amount:
		faction_funds[faction] -= amount
		resources_changed.emit(faction, faction_funds[faction])
		return true
	return false
