extends Node

## THE DEEP STATE: World State Manager
## Persists map scars to Supabase between sessions and campaigns.
## "Ghost of the Player" — every burned bus, every razed building, every
## wreck coordinate is saved so other campaigns inherit the consequences.
##
## Supabase table required:
##   world_state (
##     map_id          text PRIMARY KEY,
##     razed_buildings jsonb,
##     wreck_positions jsonb,
##     infamy_score    integer,
##     updated_at      text
##   )

signal state_loaded(state: Dictionary)

var _current_map: String = ""
var _razed_buildings: Array[String] = []
var _wreck_positions: Array[Dictionary] = []

# ── Mission lifecycle ──────────────────────────────────────────────────────────

func begin_mission(map_id: String) -> void:
	_current_map     = map_id
	_razed_buildings = []
	_wreck_positions = []
	_fetch_state(map_id)

func commit_state() -> void:
	if _current_map.is_empty():
		return
	var payload := {
		"map_id":          _current_map,
		"razed_buildings": _razed_buildings,
		"wreck_positions": _wreck_positions,
		"infamy_score":    InfamyManager.infamy,
		"updated_at":      Time.get_datetime_string_from_system(),
	}
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(func(_r, _c, _h, _b): http.queue_free())
	var headers := [
		"Content-Type: application/json",
		"apikey: "        + SupabaseManager.SUPABASE_KEY,
		"Authorization: Bearer " + SupabaseManager.SUPABASE_KEY,
		"Prefer: resolution=merge-duplicates",
	]
	http.request(
		SupabaseManager.SUPABASE_URL + "/rest/v1/world_state",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(payload)
	)

# ── Record events during a mission ────────────────────────────────────────────

func record_raze(building_node_name: String) -> void:
	if not _razed_buildings.has(building_node_name):
		_razed_buildings.append(building_node_name)

func record_wreck(asset_id: String, world_pos: Vector3) -> void:
	_wreck_positions.append({
		"asset_id": asset_id,
		"x": snappedf(world_pos.x, 0.1),
		"y": snappedf(world_pos.y, 0.1),
		"z": snappedf(world_pos.z, 0.1),
	})

# ── Accessors for map-load logic ───────────────────────────────────────────────

func get_razed() -> Array[String]:
	return _razed_buildings

func get_wrecks() -> Array[Dictionary]:
	return _wreck_positions

func was_razed(building_node_name: String) -> bool:
	return _razed_buildings.has(building_node_name)

# ── Supabase I/O ───────────────────────────────────────────────────────────────

func _fetch_state(map_id: String) -> void:
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_state_response.bind(http))
	var url := SupabaseManager.SUPABASE_URL + \
		"/rest/v1/world_state?map_id=eq." + map_id + "&select=*&limit=1"
	var headers := [
		"Content-Type: application/json",
		"apikey: "        + SupabaseManager.SUPABASE_KEY,
		"Authorization: Bearer " + SupabaseManager.SUPABASE_KEY,
	]
	var err := http.request(url, headers, HTTPClient.METHOD_GET)
	if err != OK:
		state_loaded.emit({})

func _on_state_response(
		_result: int, _code: int, _headers: PackedStringArray,
		body: PackedByteArray, http: HTTPRequest) -> void:
	http.queue_free()
	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK \
			or not (json.data is Array) \
			or json.data.is_empty():
		state_loaded.emit({})
		return
	var row: Dictionary = json.data[0]
	_razed_buildings = Array(row.get("razed_buildings", []))
	_wreck_positions  = Array(row.get("wreck_positions", []))
	if row.has("infamy_score"):
		InfamyManager.infamy = int(row["infamy_score"])
		InfamyManager.infamy_changed.emit(InfamyManager.infamy)
	state_loaded.emit(row)
