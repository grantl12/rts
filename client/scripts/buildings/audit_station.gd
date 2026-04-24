extends Building
class_name AuditStation

## THE DEEP STATE: Audit Station
## Regency specific building for processing "Digital Nomads".

@export var processing_rate: float = 5.0
var processed_metadata_count: int = 0

func _on_unit_entered(unit: Unit):
	if faction == "Regency" and unit.data.faction == "Frontline":
		print("AUDITING METADATA FOR: ", unit.data.unit_name)
		process_unit(unit)

func process_unit(unit: Unit):
	# Drains Bureaucracy from the unit to "Index" them
	unit.take_damage(processing_rate, "Bureaucracy")
	processed_metadata_count += 1
	ResourceManager.add_funds("Regency", 5)
