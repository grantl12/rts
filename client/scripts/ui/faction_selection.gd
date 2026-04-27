extends Control

## THE DEEP STATE: Faction Selection
## Choose your jurisdiction and starting narrative.

func _on_faction_selected(faction_name: String):
	GameSession.set_player_faction(faction_name)
	get_tree().change_scene_to_file("res://scenes/maps/the_quad.tscn")

func _on_back_pressed():
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
