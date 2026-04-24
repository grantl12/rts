extends Control

## THE HALL OF HEROES (War Room)
## The FTL-style "Between Mission" screen for meta-progression.

@onready var hero_list = $VBoxContainer/HeroList
@onready var legacy_points_label = $Header/LegacyPoints

var surviving_heroes = []

func _ready():
	# This would be populated from Supabase in the future
	update_ui()

func update_ui():
	# Placeholder for UI population
	pass

func _on_promote_button_pressed(hero_id):
	# "Promote to Executive Board" logic
	# Deducts Legacy Points, grants global buff
	pass

func _on_retire_button_pressed(hero_id):
	# "Retired to Hall of Heroes"
	# Removes from active roster, saves to DB
	pass
