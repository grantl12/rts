extends Node3D

## THE DEEP STATE: The Quad Visualizer
## Generates the lo-fi "Academic" aesthetic.

func _ready():
	_generate_lawns()
	_generate_paths()
	_generate_billboard_trees()

func _generate_lawns():
	# Large grass patches (Dull green, pixelated)
	var lawn_positions = [
		Vector3(-15, 0.51, -15),
		Vector3(15, 0.51, -15),
		Vector3(-15, 0.51, 15),
		Vector3(15, 0.51, 15)
	]
	
	for pos in lawn_positions:
		var lawn = CSGBox3D.new()
		lawn.size = Vector3(20, 0.1, 20)
		lawn.position = pos
		var mat = StandardMaterial3D.new()
		mat.albedo_color = Color(0.2, 0.35, 0.15) # Depressed grass green
		mat.roughness = 1.0
		lawn.material = mat
		add_child(lawn)

func _generate_paths():
	# Concrete walkways (Grey)
	var paths = [
		Vector3(0, 0.51, 0),    # Central North-South
		Vector3(0, 0.51, 0)     # Central East-West (handled by sizing)
	]
	
	# NS Path
	var ns_path = CSGBox3D.new()
	ns_path.size = Vector3(6, 0.1, 80)
	ns_path.position = Vector3(0, 0.51, 0)
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.4, 0.4, 0.4)
	ns_path.material = mat
	add_child(ns_path)
	
	# EW Path
	var ew_path = CSGBox3D.new()
	ew_path.size = Vector3(80, 0.1, 6)
	ew_path.position = Vector3(0, 0.51, 0)
	ew_path.material = mat
	add_child(ew_path)

func _generate_billboard_trees():
	# Lo-fi 2D Tree billboards
	var tree_spots = [
		Vector3(-8, 0.5, -8), Vector3(8, 0.5, -8),
		Vector3(-8, 0.5, 8), Vector3(8, 0.5, 8),
		Vector3(-25, 0.5, -25), Vector3(25, 0.5, -25)
	]
	
	for spot in tree_spots:
		var tree = Sprite3D.new()
		tree.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		tree.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		# In a real setup, we'd load a lo-fi tree sprite. 
		# For now, we'll use a placeholder or stylized mesh.
		_create_stylized_tree(spot)

func _create_stylized_tree(pos: Vector3):
	var tree_node = Node3D.new()
	tree_node.position = pos
	add_child(tree_node)
	
	# Trunk
	var trunk = CSGCylinder3D.new()
	trunk.radius = 0.2
	trunk.height = 1.5
	var t_mat = StandardMaterial3D.new()
	t_mat.albedo_color = Color(0.3, 0.2, 0.1)
	trunk.material = t_mat
	tree_node.add_child(trunk)
	
	# Foliage (Lo-fi cube cluster)
	var foliage = CSGBox3D.new()
	foliage.size = Vector3(1.5, 1.5, 1.5)
	foliage.position.y = 1.5
	var f_mat = StandardMaterial3D.new()
	f_mat.albedo_color = Color(0.1, 0.4, 0.1)
	foliage.material = f_mat
	tree_node.add_child(foliage)
