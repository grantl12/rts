extends Control

## THE DEEP STATE: System Calibration
## Satirical settings menu.

@onready var glitch_slider = $VBoxContainer/GlitchIntensity/Slider

func _on_glitch_slider_changed(value: float):
	print("GLITCH INTENSITY SET TO: ", value)
	# Update global shader parameters

func _on_apply_pressed():
	# Save to local config
	hide()

func _on_back_pressed():
	hide()
