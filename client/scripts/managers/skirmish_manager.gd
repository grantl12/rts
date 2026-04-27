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
	# Clustered at the rally point (center of the Quad, around the Kirk podium)
	var center := Vector3(0.0, 0.5, -2.0)
	var initial_radius := 7.0
	for i in CIVILIAN_COUNT:
		var civ := Civilian.new()
		var angle := randf() * TAU
		var dist  := randf_range(0.5, initial_radius)
		civ.position = center + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
		get_tree().current_scene.add_child(civ)

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

# ── Win / Loss ────────────────────────────────────────────────────────────────

func _on_building_destroyed(bname: String, faction: String):
	var hud = get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	if faction == GameSession.player_faction:
		hud.show_game_over(false)
	else:
		hud.show_game_over(true)
