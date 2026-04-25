extends Node

## THE DEEP STATE: Global Game Manager
## Tracks ROE levels, Infamy, and global mission state.

signal roe_level_changed(new_level: int)
signal infamy_changed(new_score: float)

enum ROELevel {
	HEARTS_AND_MINDS = 1,
	MODERATE_CONTROL = 2,
	HIGH_SUPPRESSION = 3,
	MARTIAL_LAW = 4,
	ABSOLUTE_IMMUNITY = 5
}

var current_roe: ROELevel = ROELevel.HEARTS_AND_MINDS:
	set(value):
		current_roe = value
		roe_level_changed.emit(current_roe)

var infamy_score: float = 0.0:
	set(value):
		infamy_score = value
		infamy_changed.emit(infamy_score)

func _ready():
	# Initial load from local archive or Supabase could happen here
	pass

func add_infamy(amount: float):
	infamy_score += amount
	# Logic for backend sync could be triggered here
