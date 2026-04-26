extends Resource
class_name BuildingResource

@export_group("Identity")
@export var building_name: String = "Structure"
@export var description: String = ""

@export_group("Economy")
@export var cost: int = 200
@export var build_time: float = 0.0

@export_group("Stats")
@export var max_health: float = 300.0

@export_group("Production")
@export var produce_time: float = 5.0
