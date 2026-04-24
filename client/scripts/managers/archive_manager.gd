extends Node

## THE DEEP STATE: Archive Manager
## Handles local and cloud (Supabase) save data.

const SAVE_PATH = "user://audit_log.save"

func archive_current_state(player_profile: Dictionary, heroes: Array):
	print("ARCHIVING AUDIT LOG...")
	var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	var data = {
		"profile": player_profile,
		"heroes": heroes,
		"timestamp": Time.get_datetime_dict_from_system()
	}
	file.store_var(data)
	file.close()

func load_archive() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}
	
	var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
	var data = file.get_var()
	file.close()
	return data
