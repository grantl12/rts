extends Resource
class_name BuildingResource

@export_group("Identity")
@export var building_name: String = "Structure"
@export var description: String = ""
@export var extra_group: String = ""

@export_group("Economy")
@export var cost: int = 200
@export var passive_income: int = 0

@export_group("Stats")
@export var max_health: float = 300.0

@export_group("Production")
@export var produces_units: bool = false
@export var producible_unit_path_override: String = ""
@export var produce_time: float = 5.0

@export_group("Area Effect")
@export var effect_type: String = ""
@export var effect_radius: float = 0.0
@export var effect_interval: float = 0.0
