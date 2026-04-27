extends HSlider

## THE DEEP STATE: ROE Control Slider (legacy — superseded by HUD buttons)

func _ready():
	min_value = 1
	max_value = 5
	step = 1
	value = ROEManager.current_roe
	value_changed.connect(_on_value_changed)
	ROEManager.roe_changed.connect(_on_roe_external_change)

func _on_value_changed(new_value: float):
	ROEManager.set_roe(int(new_value))

func _on_roe_external_change(new_level: int):
	if value != new_level:
		value = new_level
