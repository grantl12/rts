extends Area3D
class_name AuditPoint

## THE DEEP STATE: Capture Point
## Units within this area "Audit" the sector to their faction.

signal captured(faction_name)

@export var point_name: String = "Central Plaza"
@export var capture_speed: float = 10.0
@export var total_audit_required: float = 100.0

var current_audit_value: float = 0.0
var controlling_faction: String = "Neutral"
var units_in_area: Array[Unit] = []

func _ready():
	area_entered.connect(_on_unit_entered)
	area_exited.connect(_on_unit_exited)

func _process(delta):
	if units_in_area.size() > 0:
		process_audit(delta)

func process_audit(delta):
	# Calculate faction strengths in the area
	var strengths = {"Regency": 0, "Oligarchy": 0, "Frontline": 0, "Sovereign": 0}
	for unit in units_in_area:
		strengths[unit.data.faction] += 1
	
	# Find the strongest faction
	var strongest_faction = ""
	var max_strength = 0
	for faction in strengths:
		if strengths[faction] > max_strength:
			max_strength = strengths[faction]
			strongest_faction = faction
	
	# If contested (multiple factions), audit slows or stops
	var is_contested = false
	for faction in strengths:
		if faction != strongest_faction and strengths[faction] > 0:
			is_contested = true
			break
			
	if strongest_faction != "" and strongest_faction != controlling_faction:
		var multiplier = 1.0 if !is_contested else 0.2 # Massive slowdown if contested
		current_audit_value += capture_speed * max_strength * multiplier * delta
		
		if current_audit_value >= total_audit_required:
			controlling_faction = strongest_faction
			current_audit_value = total_audit_required
			captured.emit(controlling_faction)
			print("NARRATIVE UPDATED: " + point_name + " is now " + _get_faction_flavor(controlling_faction))
	elif strongest_faction == controlling_faction and current_audit_value < total_audit_required:
		# "Reinforcing" the narrative
		current_audit_value += capture_speed * delta


func _get_faction_flavor(faction: String) -> String:
	match faction:
		"Regency": return "SECURED FOR PUBLIC SAFETY"
		"Oligarchy": return "ACQUIRED FOR PRIVATE EQUITY"
		"Frontline": return "LIBERATED (FOOTAGE LEAKED)"
		"Sovereign": return "RECLAIMED BY THE SOUL"
	return "AUDITED"

func _on_unit_entered(area):
	var unit = area.get_parent()
	if unit is Unit:
		units_in_area.append(unit)

func _on_unit_exited(area):
	var unit = area.get_parent()
	if unit is Unit:
		units_in_area.erase(unit)
