extends Node

## THE DEEP STATE: Global Conflict Manager
## Tracks the meta-state of all Theaters.

signal grid_shifted(theater_name, new_faction)

var theater_control = {
	"The Quad": "Neutral",
	"The Border Wall": "Neutral",
	"The Ziggurat": "Neutral",
	"The Suburbs": "Neutral"
}

func update_theater_control(theater: String, faction: String):
	theater_control[theater] = faction
	grid_shifted.emit(theater, faction)
	update_propaganda(theater, faction)

func update_propaganda(theater: String, faction: String):
	var headlines = {
		"The Quad": {
			"Regency": "STATUE STABILIZED: ORDER RESTORED TO UNIVERSITY PLAZA",
			"Frontline": "GLITCH IN THE SYSTEM: RAW FOOTAGE VIRAL ON THE QUAD"
		},
		"The Border Wall": {
			"Regency": "BUREAUCRATIC PERIMETER SECURE: DATA FLOW OPTIMIZED",
			"Sovereign": "WALL BREACHED: ANALOG ANALYSTS CLAIM 'FREEDOM AT LAST'"
		}
	}
	
	if headlines.has(theater) and headlines[theater].has(faction):
		# Push to the News Ticker
		print("GLOBAL HEADLINE: ", headlines[theater][faction])
