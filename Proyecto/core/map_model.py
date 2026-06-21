"""
Map model: holds grid data, nodes, connections, and adjacency matrix generation.
"""
import json
import math
import numpy as np
from typing import Optional


# ── Cell types ──────────────────────────────────────────────────────────────
CELL_EMPTY = "."
CELL_WALL  = "#"

# Node prefixes
PREFIX_S = "S"   # spawn
PREFIX_N = "N"   # connection
PREFIX_E = "E"   # exit


class Node:
    """A labeled node placed on the grid."""

    def __init__(self, node_id: str, row: int, col: int):
        self.node_id = node_id          # e.g. "S_1", "N_3", "E"
        self.row = row
        self.col = col
        self.connections: list[str] = []   # node_ids this node connects TO

    def prefix(self) -> str:
        return self.node_id.split("_")[0]

    def number(self) -> Optional[int]:
        parts = self.node_id.split("_")
        if len(parts) == 2:
            try:
                return int(parts[1])
            except ValueError:
                pass
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.node_id,
            "row": self.row,
            "col": self.col,
            "connections": self.connections,
        }

    @staticmethod
    def from_dict(d: dict) -> "Node":
        n = Node(d["id"], d["row"], d["col"])
        n.connections = d.get("connections", [])
        return n


class MapModel:
    """Holds the full map state."""

    def __init__(self, name="new_map", width=33, height=20, cell_size=24):
        self.name = name
        self.width = width        # columns
        self.height = height      # rows
        self.cell_size = cell_size
        # grid[row][col] = CELL_EMPTY | CELL_WALL
        self.grid: list[list[str]] = [
            [CELL_EMPTY for _ in range(width)] for _ in range(height)
        ]
        self.nodes: dict[str, Node] = {}   # node_id -> Node
        self._next_number: dict[str, int] = {PREFIX_S: 1, PREFIX_N: 1}

    # ── Grid helpers ─────────────────────────────────────────────────────────

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def get_cell(self, row: int, col: int) -> str:
        return self.grid[row][col]

    def set_cell(self, row: int, col: int, value: str):
        if self.in_bounds(row, col):
            self.grid[row][col] = value

    def node_at(self, row: int, col: int) -> Optional[Node]:
        for n in self.nodes.values():
            if n.row == row and n.col == col:
                return n
        return None

    # ── Node management ──────────────────────────────────────────────────────

    def _new_id(self, prefix: str) -> str:
        if prefix == PREFIX_E:
            # E nodes can be multiple; find next free number
            used = {n.number() for n in self.nodes.values() if n.prefix() == PREFIX_E and n.number() is not None}
            i = 1
            while i in used:
                i += 1
            return f"E_{i}"
        n = self._next_number.get(prefix, 1)
        while f"{prefix}_{n}" in self.nodes:
            n += 1
        self._next_number[prefix] = n + 1
        return f"{prefix}_{n}"

    def add_node(self, prefix: str, row: int, col: int) -> Optional[Node]:
        if not self.in_bounds(row, col):
            return None
        if self.node_at(row, col):
            return None   # already occupied
        node_id = self._new_id(prefix)
        node = Node(node_id, row, col)
        self.nodes[node_id] = node
        return node

    def remove_node(self, node_id: str):
        if node_id not in self.nodes:
            return
        # Remove all connections to this node
        for n in self.nodes.values():
            if node_id in n.connections:
                n.connections.remove(node_id)
        del self.nodes[node_id]

    def move_node(self, node_id: str, row: int, col: int) -> bool:
        if node_id not in self.nodes:
            return False
        if not self.in_bounds(row, col):
            return False
        existing = self.node_at(row, col)
        if existing and existing.node_id != node_id:
            return False
        self.nodes[node_id].row = row
        self.nodes[node_id].col = col
        return True

    # ── Connection management ─────────────────────────────────────────────────

    def can_connect(self, src_id: str, dst_id: str) -> tuple[bool, str]:
        """Return (ok, reason). Enforces the connection rules."""
        if src_id not in self.nodes or dst_id not in self.nodes:
            return False, "Node not found"
        if src_id == dst_id:
            return False, "Cannot connect to itself"
        src = self.nodes[src_id]
        dst = self.nodes[dst_id]
        sp = src.prefix()
        dp = dst.prefix()

        # S → N only, S can have max 1 outgoing
        if sp == PREFIX_S:
            if dp != PREFIX_N:
                return False, "S can only connect to N"
            if len(src.connections) >= 1:
                return False, "S can only have 1 outgoing connection"
            # Check N not already attached to another S
            for n in self.nodes.values():
                if n.prefix() == PREFIX_S and dst_id in n.connections:
                    return False, "That N is already connected to an S"

        # N → N (max 10 outgoing from N), or N → E
        elif sp == PREFIX_N:
            if dp not in (PREFIX_N, PREFIX_E):
                return False, "N can only connect to N or E"
            if dp == PREFIX_N and len(src.connections) >= 10:  # <--- CAMBIADO A 10
                return False, "N can have at most 10 outgoing connections"

        # S-S not allowed, E outgoing not allowed
        elif sp == PREFIX_S and dp == PREFIX_S:
            return False, "S cannot connect to S"
        elif sp == PREFIX_E:
            return False, "E nodes have no outgoing connections"
        else:
            return False, "Connection not allowed"

        # Prevent duplicate
        if dst_id in src.connections:
            return False, "Already connected"

        return True, ""

    def add_connection(self, src_id: str, dst_id: str) -> tuple[bool, str]:
        ok, reason = self.can_connect(src_id, dst_id)
        if ok:
            self.nodes[src_id].connections.append(dst_id)
        return ok, reason

    def remove_connection(self, src_id: str, dst_id: str):
        if src_id in self.nodes and dst_id in self.nodes[src_id].connections:
            self.nodes[src_id].connections.remove(dst_id)

    # ── Adjacency / distance matrix ──────────────────────────────────────────

    def euclidean_distance(self, a: Node, b: Node) -> float:
        dr = a.row - b.row
        dc = a.col - b.col
        return round(math.sqrt(dr * dr + dc * dc), 2)

    def build_adjacency_matrix(self) -> tuple[list[str], np.ndarray]:
        """
        Build a symmetric distance matrix from all N nodes.
        Only explicitly connected N-N pairs get a distance; others get inf.
        """
        n_nodes = sorted(
            [n for n in self.nodes.values() if n.prefix() == PREFIX_N],
            key=lambda x: x.number() or 0,
        )
        if not n_nodes:
            return [], np.array([])

        labels = [n.node_id for n in n_nodes]
        size = len(n_nodes)
        idx = {n.node_id: i for i, n in enumerate(n_nodes)}
        mat = np.full((size, size), np.inf)
        np.fill_diagonal(mat, 0.0)

        for node in n_nodes:
            for conn_id in node.connections:
                if conn_id in idx:
                    i = idx[node.node_id]
                    j = idx[conn_id]
                    dist = self.euclidean_distance(node, self.nodes[conn_id])
                    mat[i][j] = dist
                    mat[j][i] = dist

        return labels, mat

    def build_graph(self) -> tuple[dict, list, set, list]:
        """
        Build a full adjacency-list graph including S, N, and E nodes.
        Used by ACOSolver for path-finding (S -> ... -> E).

        Returns
        -------
        graph        : dict[node_id -> list[(neighbour_id, distance)]]
        spawn_ids    : list[str]   all S node ids
        exit_ids     : set[str]    all E node ids
        all_node_ids : list[str]   every node id (for pheromone matrix)
        """
        graph: dict = {nid: [] for nid in self.nodes}
        for node in self.nodes.values():
            for conn_id in node.connections:
                if conn_id in self.nodes:
                    d = self.euclidean_distance(node, self.nodes[conn_id])
                    graph[node.node_id].append((conn_id, d))

        spawn_ids = sorted(
            [nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_S],
            key=lambda x: self.nodes[x].number() or 0,
        )
        exit_ids = {nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_E}
        all_node_ids = list(self.nodes.keys())

        return graph, spawn_ids, exit_ids, all_node_ids

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        grid_rows = ["".join(row) for row in self.grid]
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "grid": grid_rows,
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(path: str) -> "MapModel":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        m = MapModel(
            name=data.get("name", "map"),
            width=data.get("width", 33),
            height=data.get("height", 20),
            cell_size=data.get("cell_size", 24),
        )
        raw_grid = data.get("grid", [])
        for r, row_str in enumerate(raw_grid):
            for c, ch in enumerate(row_str):
                if m.in_bounds(r, c):
                    m.grid[r][c] = ch
        for nd in data.get("nodes", []):
            node = Node.from_dict(nd)
            m.nodes[node.node_id] = node
        # Rebuild _next_number counters
        for prefix in (PREFIX_S, PREFIX_N):
            nums = [n.number() for n in m.nodes.values() if n.prefix() == prefix and n.number()]
            m._next_number[prefix] = (max(nums) + 1) if nums else 1
        return m

    def resize(self, new_width: int, new_height: int):
        """Resize grid, cropping or padding as needed."""
        new_grid = []
        for r in range(new_height):
            if r < self.height:
                row = self.grid[r][:new_width]
                row += [CELL_EMPTY] * (new_width - len(row))
            else:
                row = [CELL_EMPTY] * new_width
            new_grid.append(row)
        self.grid = new_grid
        self.width = new_width
        self.height = new_height
        # Remove out-of-bounds nodes
        to_remove = [nid for nid, n in self.nodes.items()
                     if not self.in_bounds(n.row, n.col)]
        for nid in to_remove:
            self.remove_node(nid)
