extends Node

## THE DEEP STATE: Skirmish Manager
## Spawns starting forces, wires win detection, and runs the enemy AI tick.
## Mission 01 "The Redacted Rally": detain 50 civilians before they disperse.

# ── Constants ──────────────────────────────────────────────────────────────────

const UNIT_PRODUCTION_COST := 50
const AI_PRODUCE_INTERVAL  := 15.0
const AI_ORDER_INTERVAL    :=  6.0
const AI_PEN_RAID_INTERVAL := 32.0   # how often enemy targets a player pen

const DETENTION_QUOTA   := 50
const CIVILIAN_COUNT    := 75        # spawn extra — some will escape
const DISPERSAL_INTERVAL := 45.0    # seconds between dispersal stages
const DISPERSAL_RADII   := [10.0, 18.0, 28.0, 42.0]   # 4 escalating stages

const RUNNER_AMBUSH_RADIUS     := 18.0   # player unit proximity that triggers enemy spawn
const RUNNER_AMBUSH_SQUAD_SIZE :=  4     # enemies per ambush

# Three HVPs scatter immediately — each to a distinct corner of the map
const _RUNNER_DEFS := [
	{"codename": "SUBJECT ALPHA",   "dest": Vector3(-42.0, 0.5, -14.0), "escape_dest": Vector3(-3.0,  0.5, -46.0)},
	{"codename": "SUBJECT BRAVO",   "dest": Vector3( 42.0, 0.5,  12.0), "escape_dest": Vector3(-28.0, 0.5,   4.0)},
	{"codename": "SUBJECT CHARLIE", "dest": Vector3(  2.0, 0.5,  44.0), "escape_dest": Vector3( 28.0, 0.5, -32.0)},
]

# Preset car routes that stay clear of all buildings.
# WestWing blocks x∈[-44,-32] z∈[-21,21]; EastWing blocks x∈[32,44] same z.
# CivBuildings cluster in x∈[-25,25] z∈[-25,25] — routes thread around them.
const _CAR_ROUTES: Array = [
	[Vector3(-30,0.5,-44), Vector3(30,0.5,-44), Vector3(30,0.5,-26), Vector3(-30,0.5,-26)],
	[Vector3( 30,0.5, 44), Vector3(-30,0.5,44), Vector3(-30,0.5, 26), Vector3( 30,0.5, 26)],
	[Vector3(-30,0.5,  6), Vector3(30,0.5,  6), Vector3( 30,0.5, -6), Vector3(-30,0.5, -6)],
]

# ── State ──────────────────────────────────────────────────────────────────────

var player_hq: Building = null
var enemy_hq:  Building = null

var _ai_produce_timer:   float = AI_PRODUCE_INTERVAL
var _ai_order_timer:     float = AI_ORDER_INTERVAL
var _ai_pen_raid_timer:  float = AI_PEN_RAID_INTERVAL

var _dispersal_stage:    int   = 0
var _dispersal_timer:    float = DISPERSAL_INTERVAL
var _objective_met:      bool  = false
var _last_detained:      int   = -1

var _runners: Array = []          # [{codename, dest, civ, ambush_triggered, resolved}]
var _runner_check_timer: float = 0.0

# ── Setup ──────────────────────────────────────────────────────────────────────

func _ready():
	WorldStateManager.begin_mission("the_quad")
	setup_skirmish()

func setup_skirmish():
	var player := GameSession.player_faction
	var enemy  := GameSession.enemy_faction

	player_hq = _spawn_base(Vector3(0, 0.5, -40), player)
	enemy_hq  = _spawn_base(Vector3(0, 0.5,  40), enemy)

	_spawn_squad(Vector3(0, 1, -28), player, GameSession.default_unit_path(player))
	_spawn_squad(Vector3(0, 1,  28), enemy,  GameSession.default_unit_path(enemy))

	call_deferred("_connect_audit_points")
	call_deferred("_play_briefing")
	call_deferred("_spawn_mission_civilians")

func _play_briefing() -> void:
	AdvisorManager.speak("briefing")
	if is_instance_valid(player_hq):
		var hud := get_tree().get_first_node_in_group("hud")
		if hud:
			hud.select_building(player_hq)

func _connect_audit_points():
	var map = get_parent()
	for node in get_tree().current_scene.get_children():
		if node is AuditPoint:
			if not node.captured.is_connected(map.on_point_captured):
				node.captured.connect(map.on_point_captured)

# ── Spawning ───────────────────────────────────────────────────────────────────

func _spawn_base(pos: Vector3, faction: String) -> Building:
	var base: Building = (load("res://scenes/buildings/building_base.tscn") as PackedScene).instantiate()
	base.building_name = faction + " HQ"
	base.faction       = faction
	base.is_constructed = true
	base.producible_unit_path = GameSession.default_unit_path(faction)
	base.position = pos
	base.building_destroyed.connect(_on_building_destroyed)
	get_tree().current_scene.add_child.call_deferred(base)
	return base

func _spawn_squad(pos: Vector3, faction: String, res_path: String):
	var unit_res: UnitResource = load(res_path)
	for i in range(3):
		var unit: Unit = (load("res://scenes/units/unit_base.tscn") as PackedScene).instantiate()
		unit.data = unit_res
		if i == 0:
			unit.is_soul_leader = true
		unit.position = pos + Vector3((i - 1) * 2.0, 0, 0)
		get_tree().current_scene.add_child.call_deferred(unit)

func _spawn_mission_civilians() -> void:
	var center := Vector3(0.0, 0.5, -2.0)
	var initial_radius := 7.0
	for i in CIVILIAN_COUNT:
		var civ := Civilian.new()
		var angle := randf() * TAU
		var dist  := randf_range(0.5, initial_radius)
		civ.position = center + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
		get_tree().current_scene.add_child(civ)
	_spawn_runners(center)
	_spawn_civilian_vehicles()

func _spawn_civilian_vehicles() -> void:
	# Two cars per route, each starting mid-route so they're spread around the map
	for route_idx in _CAR_ROUTES.size():
		var route: Array = _CAR_ROUTES[route_idx]
		for offset in [0, 2]:
			var car := CivilianCar.new()
			car.waypoints.assign(route)
			car._wp_idx   = offset % route.size()
			get_tree().current_scene.add_child(car)

func _spawn_runners(center: Vector3) -> void:
	for def in _RUNNER_DEFS:
		var civ := Civilian.new()
		# Runners start in the crowd but immediately peel off
		civ.position           = center + Vector3(randf_range(-2.5, 2.5), 0.0, randf_range(-2.5, 2.5))
		civ.is_runner          = true
		civ.runner_destination = def.dest
		get_tree().current_scene.add_child(civ)
		_runners.append({
			"codename":         def.codename,
			"dest":             def.dest,
			"escape_dest":      def.escape_dest,
			"civ":              civ,
			"ambush_triggered": false,
			"in_vehicle":       false,
			"vehicle_ref":      null,
			"resolved":         false,
		})

# ── Mission Objective ──────────────────────────────────────────────────────────

func _get_total_detained() -> int:
	var total  := 0
	var player := GameSession.player_faction
	for pen in get_tree().get_nodes_in_group("holding_pens"):
		if not (pen is HoldingPen) or not is_instance_valid(pen):
			continue
		if pen.faction == player:
			total += pen.civs_held
	return total

func _on_objective_met() -> void:
	AdvisorManager.speak("quota_met")
	var hud := get_tree().get_first_node_in_group("hud")
	if hud and hud.has_method("show_objective_complete"):
		hud.show_objective_complete()
	WorldStateManager.commit_state()

# ── Process ────────────────────────────────────────────────────────────────────

func _process(delta: float):
	# AI ticks
	_ai_produce_timer   -= delta
	_ai_order_timer     -= delta
	_ai_pen_raid_timer  -= delta

	if _ai_produce_timer <= 0.0:
		_ai_produce_timer = AI_PRODUCE_INTERVAL
		_ai_produce()

	if _ai_order_timer <= 0.0:
		_ai_order_timer = AI_ORDER_INTERVAL
		_ai_issue_orders()

	if _ai_pen_raid_timer <= 0.0:
		_ai_pen_raid_timer = AI_PEN_RAID_INTERVAL
		_ai_raid_pen()

	# Civilian dispersal — each stage expands all civ wander radii
	if _dispersal_stage < DISPERSAL_RADII.size():
		_dispersal_timer -= delta
		if _dispersal_timer <= 0.0:
			_dispersal_timer  = DISPERSAL_INTERVAL
			_dispersal_stage += 1
			var new_r: float  = DISPERSAL_RADII[_dispersal_stage - 1]
			for civ in get_tree().get_nodes_in_group("civilians"):
				if civ is Civilian and is_instance_valid(civ):
					civ.expand_wander(new_r)
			AdvisorManager.speak("dispersal")

	# Objective tracking
	if not _objective_met:
		var detained := _get_total_detained()
		if detained != _last_detained:
			_last_detained = detained
			var hud := get_tree().get_first_node_in_group("hud")
			if hud and hud.has_method("update_objective"):
				var time_left := _dispersal_timer if _dispersal_stage < DISPERSAL_RADII.size() else 0.0
				hud.update_objective(detained, DETENTION_QUOTA, time_left, _dispersal_stage)
		if detained >= DETENTION_QUOTA:
			_objective_met = true
			_on_objective_met()

	# Runner / HVP sub-objectives (rate-limited to every 0.5s)
	_runner_check_timer -= delta
	if _runner_check_timer <= 0.0:
		_runner_check_timer = 0.5
		_check_runners()

# ── AI Produce ────────────────────────────────────────────────────────────────

func _ai_produce():
	if not is_instance_valid(enemy_hq):
		return
	var enemy := GameSession.enemy_faction
	if not ResourceManager.spend_funds(enemy, UNIT_PRODUCTION_COST):
		return
	var unit_res: UnitResource = load(GameSession.default_unit_path(enemy))
	if unit_res:
		enemy_hq.spawn_unit(unit_res)

# ── AI Orders ─────────────────────────────────────────────────────────────────

func _ai_issue_orders():
	var enemy := GameSession.enemy_faction
	var idle_units: Array = get_tree().get_nodes_in_group("units").filter(
		func(u): return is_instance_valid(u) and u is Unit \
			and u.data.faction == enemy \
			and u.target_unit == null and u.target_building == null
	)
	if idle_units.is_empty():
		return

	var points: Array = get_tree().get_nodes_in_group("audit_points")

	# All audit points held — storm player HQ
	var uncaptured: Array = points.filter(
		func(p): return p is AuditPoint and p.controlling_faction != enemy
	)
	if uncaptured.is_empty() and is_instance_valid(player_hq):
		for unit in idle_units:
			unit.target_building = player_hq
			unit.target_unit     = null
		return

	# Push toward nearest uncaptured audit point
	if points.is_empty():
		return
	var target_point: AuditPoint = null
	for pt in points:
		if pt is AuditPoint and pt.controlling_faction != enemy:
			target_point = pt
			break
	if not target_point:
		target_point = points[0] as AuditPoint

	var base_pos := target_point.global_position
	for unit in idle_units:
		var offset := Vector3(randf_range(-4.0, 4.0), 0.0, randf_range(-4.0, 4.0))
		unit.target_position = base_pos + offset

func _ai_raid_pen() -> void:
	var player := GameSession.player_faction
	var enemy  := GameSession.enemy_faction

	# Find player pens that have civs and aren't already under attack
	var target_pens: Array = get_tree().get_nodes_in_group("holding_pens").filter(
		func(p): return p is HoldingPen and is_instance_valid(p) \
			and p.faction == player and p.civs_held > 0
	)
	if target_pens.is_empty():
		return

	# Pick the fullest pen — maximum disruption
	target_pens.sort_custom(func(a, b): return a.civs_held > b.civs_held)
	var target_pen := target_pens[0] as HoldingPen

	# Send up to 2 idle enemy units on the raid
	var raiders: Array = get_tree().get_nodes_in_group("units").filter(
		func(u): return is_instance_valid(u) and u is Unit \
			and u.data.faction == enemy \
			and u.target_unit == null and u.target_building == null
	)
	var raid_count := mini(2, raiders.size())
	for i in raid_count:
		raiders[i].target_building = target_pen
		raiders[i].target_unit     = null

# ── Runner / HVP sub-objectives ──────────────────────────────────────────────

func _check_runners() -> void:
	if _runners.is_empty():
		return
	var player := GameSession.player_faction
	var player_units: Array = get_tree().get_nodes_in_group("units").filter(
		func(u): return is_instance_valid(u) and u is Unit and u.data.faction == player
	)
	var state_changed := false
	for r in _runners:
		if r.resolved:
			continue
		# Detect dismount — car finished escaping or was wrecked
		if r.in_vehicle and (not is_instance_valid(r.vehicle_ref) or not r.vehicle_ref._escaping):
			r.in_vehicle  = false
			r.vehicle_ref = null
			state_changed = true
		if not is_instance_valid(r.civ):
			r.resolved = true
			state_changed = true
			continue
		if not r.ambush_triggered:
			var dest: Vector3 = r.dest
			for unit in player_units:
				if unit.global_position.distance_to(dest) < RUNNER_AMBUSH_RADIUS:
					r.ambush_triggered = true
					state_changed = true
					_trigger_runner_ambush(r)
					break
	if state_changed:
		var hud := get_tree().get_first_node_in_group("hud")
		if hud and hud.has_method("update_runner_objectives"):
			hud.update_runner_objectives(_runners)
	elif not _runners.is_empty():
		# Still push HUD update so ACTIVE runners show correctly on first call
		var hud := get_tree().get_first_node_in_group("hud")
		if hud and hud.has_method("update_runner_objectives"):
			hud.update_runner_objectives(_runners)

func _trigger_runner_ambush(r: Dictionary) -> void:
	var enemy := GameSession.enemy_faction
	var dest: Vector3 = r.dest
	AdvisorManager.speak("runner_ambush")

	# Spawn enemy squad at the hot zone
	var unit_res: UnitResource = load(GameSession.default_unit_path(enemy))
	if unit_res:
		for i in RUNNER_AMBUSH_SQUAD_SIZE:
			var unit: Unit = (load("res://scenes/units/unit_base.tscn") as PackedScene).instantiate()
			unit.data  = unit_res
			var angle  := float(i) / RUNNER_AMBUSH_SQUAD_SIZE * TAU
			unit.position = dest + Vector3(cos(angle) * 3.5, 0.0, sin(angle) * 3.5)
			get_tree().current_scene.add_child(unit)

	# HVP boards the nearest available car and flees to a secondary locale
	if is_instance_valid(r.civ):
		var car := _find_nearest_car(r.civ.global_position if is_instance_valid(r.civ) else dest)
		if car:
			car.pick_up_runner(r.civ, r.escape_dest)
			r.in_vehicle  = true
			r.vehicle_ref = car

func _find_nearest_car(from: Vector3) -> CivilianCar:
	var best:      CivilianCar = null
	var best_dist: float       = INF
	for node in get_tree().get_nodes_in_group("civilian_vehicles"):
		if not (node is CivilianCar) or not is_instance_valid(node):
			continue
		var car := node as CivilianCar
		if car._wrecked or car._escaping:
			continue
		var d := car.global_position.distance_to(from)
		if d < best_dist:
			best_dist = d
			best      = car
	return best

# ── Win / Loss ────────────────────────────────────────────────────────────────

func _on_building_destroyed(bname: String, faction: String):
	var hud = get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	if faction == GameSession.player_faction:
		hud.show_game_over(false)
	else:
		hud.show_game_over(true)
