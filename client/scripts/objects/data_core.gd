extends Node3D
class_name DataCore

## THE DEEP STATE: Data Core
## Must be carried by a unit to a Migration Zone.

var carrier: Unit = null

func _process(_delta):
	if carrier:
		global_position = carrier.global_position + Vector3(0, 2, 0)
		# Slow down the carrier
		carrier.velocity *= 0.6 

func attach_to(unit: Unit):
	carrier = unit
	print("DATA CORE SECURED by ", unit.data.unit_name)

func detach():
	carrier = null
