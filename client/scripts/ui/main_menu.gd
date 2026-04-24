extends Control

## THE DEEP STATE: Executive Dashboard
## The primary interface for initiating audits and accessing archives.

@onready var status_label = $StatusMargin/StatusLabel
@onready var version_label = $Footer/Version

func _ready():
	version_label.text = "Build: v0.4.4-REDACTED"
	animate_boot_sequence()

func animate_boot_sequence():
	status_label.text = "Initializing Deep State Protocols..."
	await get_tree().create_timer(1.0).timeout
	status_label.text = "Synchronizing with the Grid..."
	await get_tree().create_timer(0.5).timeout
	status_label.text = "Jurisdiction: ACTIVE"

@onready var ticker = $TickerBackground/NewsTicker

func _process(delta):
	# Scrolling ticker effect
	ticker.position.x -= 100 * delta
	if ticker.position.x < -1500:
		update_ticker_from_meta()
		ticker.position.x = 1280

func update_ticker_from_meta():
	# Placeholder for fetching latest Global Conflict headlines
	pass

func _on_new_audit_pressed():
	print("SELECTING JURISDICTION...")
	get_tree().change_scene_to_file("res://scenes/ui/faction_selection.tscn")

func _on_access_archives_pressed():
	print("ACCESSING ARCHIVES...")
	# Logic for loading saves

func _on_calibration_pressed():
	print("CALIBRATING SYSTEMS...")
	# Settings menu

func _on_redact_session_pressed():
	get_tree().quit()
