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
PREFIX_L = "L"   # ladder (escalera para cambiar de planta)

class Node:
    """A labeled node placed on the grid."""
    def __init__(self, node_id: str, floor: int, row: int, col: int):
        self.node_id = node_id
        self.floor = floor              # NUEVO: Planta en la que se encuentra
        self.row = row
        self.col = col
        self.connections: list[str] = []

    def prefix(self) -> str:
        return self.node_id.split("_")[0]

    def number(self) -> Optional[int]:
        parts = self.node_id.split("_")
        if len(parts) == 2:
            try: return int(parts[1])
            except ValueError: pass
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.node_id,
            "floor": self.floor,
            "row": self.row,
            "col": self.col,
            "connections": self.connections,
        }

    @staticmethod
    def from_dict(d: dict) -> "Node":
        n = Node(d["id"], d.get("floor", 0), d["row"], d["col"])
        n.connections = d.get("connections", [])
        return n

class MapModel:
    """Holds the full 3D map state."""
    def __init__(self, name="new_map", floors=1, width=33, height=20, cell_size=24):
        self.name = name
        self.floors = floors      # plantas
        self.width = width        # columnas
        self.height = height      # filas
        self.cell_size = cell_size
        
        # grid[floor][row][col] = CELL_EMPTY | CELL_WALL
        self.grid: list[list[list[str]]] = [
            [[CELL_EMPTY for _ in range(width)] for _ in range(height)] 
            for _ in range(floors)
        ]
        self.nodes: dict[str, Node] = {}
        self._next_number: dict[str, int] = {PREFIX_S: 1, PREFIX_N: 1, PREFIX_L: 1}

    # ── Grid helpers ─────────────────────────────────────────────────────────
    def in_bounds(self, floor: int, row: int, col: int) -> bool:
        return 0 <= floor < self.floors and 0 <= row < self.height and 0 <= col < self.width

    def get_cell(self, floor: int, row: int, col: int) -> str:
        if self.in_bounds(floor, row, col): return self.grid[floor][row][col]
        return CELL_WALL

    def set_cell(self, floor: int, row: int, col: int, value: str):
        if self.in_bounds(floor, row, col):
            self.grid[floor][row][col] = value

    def node_at(self, floor: int, row: int, col: int) -> Optional[Node]:
        for n in self.nodes.values():
            if n.floor == floor and n.row == row and n.col == col:
                return n
        return None

    # ── Node management ──────────────────────────────────────────────────────
    def _new_id(self, prefix: str) -> str:
        if prefix == PREFIX_E:
            used = {n.number() for n in self.nodes.values() if n.prefix() == PREFIX_E and n.number() is not None}
            i = 1
            while i in used: i += 1
            return f"E_{i}"
        n = self._next_number.get(prefix, 1)
        while f"{prefix}_{n}" in self.nodes: n += 1
        self._next_number[prefix] = n + 1
        return f"{prefix}_{n}"

    def add_node(self, prefix: str, floor: int, row: int, col: int) -> Optional[Node]:
        if not self.in_bounds(floor, row, col): return None
        if self.node_at(floor, row, col): return None
        node_id = self._new_id(prefix)
        node = Node(node_id, floor, row, col)
        self.nodes[node_id] = node
        return node

    def remove_node(self, node_id: str):
        if node_id not in self.nodes: return
        for n in self.nodes.values():
            if node_id in n.connections:
                n.connections.remove(node_id)
        del self.nodes[node_id]

    def move_node(self, node_id: str, floor: int, row: int, col: int) -> bool:
        if node_id not in self.nodes: return False
        if not self.in_bounds(floor, row, col): return False
        existing = self.node_at(floor, row, col)
        if existing and existing.node_id != node_id: return False
        self.nodes[node_id].floor = floor
        self.nodes[node_id].row = row
        self.nodes[node_id].col = col
        return True

    # ── Connection management ─────────────────────────────────────────────────
    def can_connect(self, src_id: str, dst_id: str) -> tuple[bool, str]:
        if src_id not in self.nodes or dst_id not in self.nodes: return False, "Node not found"
        if src_id == dst_id: return False, "Cannot connect to itself"
        src, dst = self.nodes[src_id], self.nodes[dst_id]
        sp, dp = src.prefix(), dst.prefix()

        # REGLAS PARA ESCALERAS (L)
        if sp == PREFIX_L:
            if dp not in (PREFIX_N, PREFIX_L, PREFIX_E):
                return False, "L solo conecta con N, L o E"
            if dp == PREFIX_L:
                if abs(src.floor - dst.floor) != 1:
                    return False, "Las escaleras deben conectar plantas adyacentes"
                if src.row != dst.row or src.col != dst.col:
                    return False, "Las escaleras deben estar en la misma coordenada exacta (fila, columna) para conectarse verticalmente"
        elif dp == PREFIX_L:
            if sp not in (PREFIX_S, PREFIX_N, PREFIX_L):
                return False, "Solo S, N o L pueden conectar hacia una Escalera"

        # REGLAS GENERALES ADAPTADAS
        if sp == PREFIX_S:
            if dp not in (PREFIX_N, PREFIX_L): return False, "S solo puede conectar a N o L"
        elif sp == PREFIX_N:
            if dp not in (PREFIX_N, PREFIX_E, PREFIX_L): return False, "N solo puede conectar con N, L o E"
        elif sp == PREFIX_E:
            return False, "Nodos E no tienen salidas"
            
        if dst_id in src.connections: return False, "Ya están conectados"
        return True, ""

    def add_connection(self, src_id: str, dst_id: str) -> tuple[bool, str]:
        ok, reason = self.can_connect(src_id, dst_id)
        if ok: self.nodes[src_id].connections.append(dst_id)
        return ok, reason

    # ── Distancias ──────────────────────────────────────────────────────────
    def euclidean_distance(self, a: Node, b: Node) -> float:
        dr = a.row - b.row
        dc = a.col - b.col
        # Magia matemática: Si la diferencia de piso es 1, y X,Y son iguales, 
        # la distancia será exactamente la raíz de 100, es decir: 10.
        dz = (a.floor - b.floor) * 10 
        return round(math.sqrt(dr * dr + dc * dc + dz * dz), 2)

    def build_adjacency_matrix(self) -> tuple[list[str], np.ndarray]:
        # Ahora incluimos nodos L en la tabla de distancias para ver su costo
        n_nodes = sorted([n for n in self.nodes.values() if n.prefix() in (PREFIX_N, PREFIX_L)],
                         key=lambda x: x.number() or 0)
        if not n_nodes: return [], np.array([])
        labels = [n.node_id for n in n_nodes]
        size = len(n_nodes)
        idx = {n.node_id: i for i, n in enumerate(n_nodes)}
        mat = np.full((size, size), np.inf)
        np.fill_diagonal(mat, 0.0)

        for node in n_nodes:
            for conn_id in node.connections:
                if conn_id in idx:
                    i, j = idx[node.node_id], idx[conn_id]
                    dist = self.euclidean_distance(node, self.nodes[conn_id])
                    mat[i][j] = mat[j][i] = dist
        return labels, mat

    # def build_graph(self) -> tuple[dict, list, set, list]:
    #     graph: dict = {nid: [] for nid in self.nodes}
    #     for node in self.nodes.values():
    #         for conn_id in node.connections:
    #             if conn_id in self.nodes:
    #                 d = self.euclidean_distance(node, self.nodes[conn_id])
    #                 graph[node.node_id].append((conn_id, d))
    #     spawn_ids = sorted([nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_S], key=lambda x: self.nodes[x].number() or 0)
    #     exit_ids = {nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_E}
    #     return graph, spawn_ids, exit_ids, list(self.nodes.keys())
    def build_graph(self) -> tuple[dict, list, set, list]:
        graph: dict = {nid: [] for nid in self.nodes}
        for node in self.nodes.values():
            for conn_id in node.connections:
                if conn_id in self.nodes:
                    d = self.euclidean_distance(node, self.nodes[conn_id])
                    
                    # 1. Agregamos la conexión original (Ida)
                    graph[node.node_id].append((conn_id, d))
                    
                    # 2. NUEVO: Magia de Doble Sentido
                    # Si ambos nodos son pasillos (N) o escaleras (L), permitimos que se pueda caminar de regreso.
                    # Ignoramos los S y E porque S solo es salida y E solo es llegada.
                    target_node = self.nodes[conn_id]
                    if node.prefix() in (PREFIX_N, PREFIX_L) and target_node.prefix() in (PREFIX_N, PREFIX_L):
                        # Verificamos que no exista ya la conexión para no duplicarla
                        if not any(n == node.node_id for n, _ in graph[conn_id]):
                            graph[conn_id].append((node.node_id, d))

        spawn_ids = sorted([nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_S], key=lambda x: self.nodes[x].number() or 0)
        exit_ids = {nid for nid, n in self.nodes.items() if n.prefix() == PREFIX_E}
        return graph, spawn_ids, exit_ids, list(self.nodes.keys())

    # ── Serialization ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        # Convertir grid 3D a JSON
        grid_floors = [["".join(row) for row in floor_grid] for floor_grid in self.grid]
        return {
            "name": self.name, "floors": self.floors, "width": self.width,
            "height": self.height, "cell_size": self.cell_size,
            "grid": grid_floors,
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f: json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(path: str) -> "MapModel":
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        floors = data.get("floors", 1)
        m = MapModel(name=data.get("name", "map"), floors=floors, width=data.get("width", 33), height=data.get("height", 20), cell_size=data.get("cell_size", 24))
        raw_grid = data.get("grid", [])
        
        # Compatibilidad con mapas 2D antiguos
        if raw_grid and isinstance(raw_grid[0], str):
            for r, row_str in enumerate(raw_grid):
                for c, ch in enumerate(row_str):
                    if m.in_bounds(0, r, c): m.grid[0][r][c] = ch
        else: # Nuevo formato 3D
            for f, floor_data in enumerate(raw_grid):
                for r, row_str in enumerate(floor_data):
                    for c, ch in enumerate(row_str):
                        if m.in_bounds(f, r, c): m.grid[f][r][c] = ch
                        
        for nd in data.get("nodes", []):
            node = Node.from_dict(nd)
            m.nodes[node.node_id] = node
        return m

    def resize(self, new_floors: int, new_width: int, new_height: int):
        new_grid = []
        for f in range(new_floors):
            floor_grid = []
            for r in range(new_height):
                if f < self.floors and r < self.height:
                    row = self.grid[f][r][:new_width]
                    row += [CELL_EMPTY] * (new_width - len(row))
                else:
                    row = [CELL_EMPTY] * new_width
                floor_grid.append(row)
            new_grid.append(floor_grid)
        self.grid = new_grid
        self.floors = new_floors
        self.width = new_width
        self.height = new_height
        
        to_remove = [nid for nid, n in self.nodes.items() if not self.in_bounds(n.floor, n.row, n.col)]
        for nid in to_remove: self.remove_node(nid)