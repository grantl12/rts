extends Node

## THE DEEP STATE: Supabase Manager
## The bridge between the Neon Grid and the Cloud DB.

const SUPABASE_URL = "https://hyipcvepncxliiokqgpt.supabase.co"
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5aXBjdmVwbmN4bGlpb2txZ3B0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwNDU3MTcsImV4cCI6MjA5MjYyMTcxN30.lHqUFveKlUJalKyHjqhLlBRYVsa4WPNts6umgyOUe0o"

func save_hero_to_cloud(hero_data: Dictionary):
	print("UPLOADING SOUL TO THE HALL OF HEROES...")
	var http = HTTPRequest.new()
	add_child(http)
	
	var url = SUPABASE_URL + "/rest/v1/hero_units"
	var headers = [
		"Content-Type: application/json",
		"apikey: " + SUPABASE_KEY,
		"Authorization: Bearer " + SUPABASE_KEY
	]
	
	var body = JSON.stringify(hero_data)
	http.request(url, headers, HTTPClient.METHOD_POST, body)

func sync_global_conflict(theater_data: Dictionary):
	print("SYNCHRONIZING GLOBAL CONFLICT...")
	# Logic to update the global_conflict_stats table
	pass
