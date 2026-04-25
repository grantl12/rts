extends HSlider

## THE DEEP STATE: ROE Control Slider
## Updates the global GameManager state.

func _ready():
	min_value = 1
	max_value = 5
	step = 1
	value = GameManager.current_roe
	value_changed.connect(_on_value_changed)
	
	GameManager.roe_level_changed.connect(_on_roe_external_change)

func _on_value_changed(new_value: float):
	var level = int(new_value)
	GameManager.current_roe = level as GameManager.ROELevel
	
	# Visual/Audio feedback for ROE change
	_play_roe_glitch_effect(level)

func _on_roe_external_change(new_level: int):
	if value != new_level:
		value = new_level

func _play_roe_glitch_effect(level: int):
	match level:
		5:
			modulate = Color(1.0, 0.2, 0.2) # High alert red
			print("AUDIT STATUS: ABSOLUTE IMMUNITY ACTIVE")
		1:
			modulate = Color(0.4, 1.0, 0.6) # Hearts and Minds green
			print("AUDIT STATUS: HEARTS AND MINDS PROTOCOL")
		_:
			modulate = Color(1.0, 1.0, 1.0)
