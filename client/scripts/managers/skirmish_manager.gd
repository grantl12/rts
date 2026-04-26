extends Node

## THE DEEP STATE: Skirmish Manager
## Spawns starting forces, wires win detection, and runs the enemy AI tick.

const UNIT_PRODUCTION_COST := 50
const AI_PRODUCE_INTERVAL := 15.0
const AI_ORDER_INTERVAL  := 6.0

var player_hq: Building = null
var enemy_hq: Building  = null

var _ai_produce_timer: float = AI_PRODUCE_INTERVAL
var _ai_order_timer: float   = AI_ORDER_INTERVAL

func _ready():
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

# ── Spawning ─────────────────────────────────────────────────────────────────

func _spawn_base(pos: Vector3, faction: String) -> Building:
	var base: Building = (load("res://scenes/buildings/building_base.tscn") as PackedScene).instantiate()
	base.building_name = faction + " HQ"
	base.faction = faction
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

# ── Win / Loss ────────────────────────────────────────────────────────────────

func _on_building_destroyed(bname: String, faction: String):
	var hud = get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	if faction == GameSession.player_faction:
		hud.show_game_over(false)
	else:
		hud.show_game_over(true)

# ── AI Tick ───────────────────────────────────────────────────────────────────

func _process(delta: float):
	_ai_produce_timer -= delta
	_ai_order_timer   -= delta

	if _ai_produce_timer <= 0.0:
		_ai_produce_timer = AI_PRODUCE_INTERVAL
		_ai_produce()

	if _ai_order_timer <= 0.0:
		_ai_order_timer = AI_ORDER_INTERVAL
		_ai_issue_orders()

func _ai_produce():
	if not is_instance_valid(enemy_hq):
		return
	var enemy := GameSession.enemy_faction
	if not ResourceManager.spend_funds(enemy, UNIT_PRODUCTION_COST):
		return
	var unit_res: UnitResource = load(GameSession.default_unit_path(enemy))
	if unit_res:
		enemy_hq.spawn_unit(unit_res)

func _ai_issue_orders():
	var enemy := GameSession.enemy_faction
	var enemy_units: Array = get_tree().get_nodes_in_group("units").filter(
		func(u): return is_instance_valid(u) and u is Unit \
			and u.data.faction == enemy and u.target_unit == null \
			and u.target_building == null
	)
	if enemy_units.is_empty():
		return

	var points: Array = get_tree().get_nodes_in_group("audit_points")

	# Once all points belong to the enemy, storm the player HQ
	var uncaptured: Array = points.filter(
		func(p): return p is AuditPoint and p.controlling_faction != enemy
	)
	if uncaptured.is_empty() and is_instance_valid(player_hq):
		for unit in enemy_units:
			unit.target_building = player_hq
			unit.target_unit = null
		return

	# Otherwise push toward the most valuable uncaptured point
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
	for unit in enemy_units:
		var offset := Vector3(randf_range(-4.0, 4.0), 0.0, randf_range(-4.0, 4.0))
		unit.target_position = base_pos + offset
