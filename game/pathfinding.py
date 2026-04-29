"""A* pathfinding on the isometric tile grid."""
import heapq
from game.map_data import TERRAIN, W, H, VOID


def _passable(gx, gy, blocked_tiles):
    if not (0 <= gx < W and 0 <= gy < H):
        return False
    if TERRAIN[gy][gx] == VOID:
        return False
    if (gx, gy) in blocked_tiles:
        return False
    return True


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


NEIGHBORS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
DIAG_COST = 1.414


def find_path(start, goal, blocked_tiles=()):
    """
    Return list of (gx, gy) int tuples from start to goal (inclusive).
    Returns empty list if no path found.
    blocked_tiles: set of (gx,gy) that are impassable (buildings, etc.)
    """
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]),  int(goal[1])

    if not _passable(gx, gy, blocked_tiles):
        # Try nearby tiles
        for dx, dy in NEIGHBORS:
            nx, ny = gx + dx, gy + dy
            if _passable(nx, ny, blocked_tiles):
                gx, gy = nx, ny
                break
        else:
            return []

    open_heap = []
    heapq.heappush(open_heap, (0, sx, sy))
    came_from = {}
    g_score = {(sx, sy): 0.0}

    while open_heap:
        _, cx, cy = heapq.heappop(open_heap)

        if cx == gx and cy == gy:
            # Reconstruct
            path = []
            node = (cx, cy)
            while node in came_from:
                path.append(node)
                node = came_from[node]
            path.append((sx, sy))
            path.reverse()
            return path

        for dx, dy in NEIGHBORS:
            nx, ny = cx + dx, cy + dy
            if not _passable(nx, ny, blocked_tiles):
                continue
            cost = DIAG_COST if (dx and dy) else 1.0
            new_g = g_score[(cx, cy)] + cost
            if new_g < g_score.get((nx, ny), float("inf")):
                came_from[(nx, ny)] = (cx, cy)
                g_score[(nx, ny)] = new_g
                f = new_g + _heuristic((nx, ny), (gx, gy))
                heapq.heappush(open_heap, (f, nx, ny))

    return []


def formation_goals(center_gx, center_gy, count, blocked_tiles=()):
    """
    Spread `count` units around a center tile in a rough square.
    Returns list of (gx, gy) tuples.
    """
    goals = []
    visited = set()
    queue = [(center_gx, center_gy)]
    while len(goals) < count and queue:
        nx, ny = queue.pop(0)
        if (nx, ny) in visited:
            continue
        visited.add((nx, ny))
        if _passable(nx, ny, blocked_tiles):
            goals.append((nx, ny))
        for dx, dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),
                        (2,0),(-2,0),(0,2),(0,-2)]:
            nn = (nx + dx, ny + dy)
            if nn not in visited:
                queue.append(nn)
    return goals
