extends Node

## THE DEEP STATE: Supabase Manager
## The bridge between the Neon Grid and the Cloud DB.

signal heroes_loaded(heroes: Array)

const SUPABASE_URL = "https://hyipcvepncxliiokqgpt.supabase.co"
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5aXBjdmVwbmN4bGlpb2txZ3B0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwNDU3MTcsImV4cCI6MjA5MjYyMTcxN30.lHqUFveKlUJalKyHjqhLlBRYVsa4WPNts6umgyOUe0o"

func save_hero_to_cloud(hero_data: Dictionary):
	print("UPLOADING SOUL TO THE HALL OF HEROES...")
	var http := HTTPRequest.new()
	add_child(http)
	var url := SUPABASE_URL + "/rest/v1/hero_units"
	var headers := [
		"Content-Type: application/json",
		"apikey: " + SUPABASE_KEY,
		"Authorization: Bearer " + SUPABASE_KEY,
		"Prefer: return=minimal"
	]
	http.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(hero_data))

func fetch_heroes_from_cloud() -> void:
	print("FETCHING HALL OF HEROES...")
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_heroes_response.bind(http))
	var url := SUPABASE_URL + "/rest/v1/hero_units?select=*&order=created_at.desc&limit=30"
	var headers := [
		"Content-Type: application/json",
		"apikey: " + SUPABASE_KEY,
		"Authorization: Bearer " + SUPABASE_KEY
	]
	var err := http.request(url, headers, HTTPClient.METHOD_GET)
	if err != OK:
		heroes_loaded.emit([])

func _on_heroes_response(result: int, _code: int, _headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
	http.queue_free()
	if result != HTTPRequest.RESULT_SUCCESS:
		heroes_loaded.emit([])
		return
	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		heroes_loaded.emit([])
		return
	heroes_loaded.emit(json.data if json.data is Array else [])

func sync_global_conflict(_theater_data: Dictionary):
	pass
