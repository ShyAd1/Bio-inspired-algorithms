"""
Fase 3: Sistema de Grafos
Generación automática de grafos desde mapas con conectividad real
"""
import math
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
from ..models.map_model import MapModel, MapElement, ElementType


@dataclass
class Node:
    """Representa un nodo en el grafo"""
    id: str
    position: Tuple[float, float]  # Centro del nodo
    element_type: ElementType
    capacity: int
    floor: int
    adjacent_nodes: Set[str] = field(default_factory=set)
    connections: Dict[str, Dict] = field(default_factory=dict)  # {node_id: {'distance': float, 'type': str}}


@dataclass
class Edge:
    """Representa una arista entre dos nodos"""
    from_node: str
    to_node: str
    distance: float
    connection_type: str  # "direct", "corridor", "door", "stair"
    weight: float = 1.0  # Para ponderación en ACO


class GraphGenerator:
    """Genera grafos automáticamente desde mapas"""
    
    # Tolerancia para conectividad
    CONNECTION_TOLERANCE = 5  # píxeles
    MIN_CONNECTION_DISTANCE = 10
    MAX_CONNECTION_DISTANCE = 500
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency_matrix: Optional[np.ndarray] = None
        self.distance_matrix: Optional[np.ndarray] = None
        self.node_id_to_index: Dict[str, int] = {}
    
    def generate_from_map(self, map_model: MapModel) -> bool:
        """
        Genera el grafo a partir del mapa.
        Retorna True si tuvo éxito, False si hay errores.
        """
        try:
            self.nodes.clear()
            self.edges.clear()
            
            # Paso 1: Crear nodos para cada elemento
            for floor_idx, floor in map_model.floors.items():
                for element_id, element in floor.elements.items():
                    node_id = f"floor{floor_idx}_{element_id}"
                    center = self._calculate_center(element)
                    
                    node = Node(
                        id=node_id,
                        position=center,
                        element_type=element.element_type,
                        capacity=element.capacity,
                        floor=floor_idx
                    )
                    self.nodes[node_id] = node
            
            # Paso 2: Detectar conectividad entre nodos
            self._detect_connectivity(map_model)
            
            # Paso 3: Crear matrices
            self._create_matrices()
            
            return True
        except Exception as e:
            print(f"Error generando grafo: {e}")
            return False
    
    def _calculate_center(self, element: MapElement) -> Tuple[float, float]:
        """Calcula el centro de un elemento"""
        x = element.position[0] + element.width / 2
        y = element.position[1] + element.height / 2
        return (x, y)
    
    def _detect_connectivity(self, map_model: MapModel) -> None:
        """Detecta conectividad entre nodos automáticamente"""
        node_list = list(self.nodes.values())
        
        for i, node1 in enumerate(node_list):
            for node2 in node_list[i+1:]:
                # Solo conectar si están en el mismo piso o si hay escalera
                distance = self._calculate_distance(node1.position, node2.position)
                
                if node1.floor == node2.floor:
                    # Mismo piso
                    if self._can_connect(node1, node2, distance):
                        connection_type = self._determine_connection_type(node1, node2)
                        self._add_connection(node1, node2, distance, connection_type)
                
                elif self._has_stair_connection(node1, node2, map_model):
                    # Conectar a través de escalera
                    self._add_connection(node1, node2, distance + 50, "stair")
    
    def _can_connect(self, node1: Node, node2: Node, distance: float) -> bool:
        """Verifica si dos nodos pueden estar conectados"""
        # Distancia debe estar en rango
        if distance < self.MIN_CONNECTION_DISTANCE or distance > self.MAX_CONNECTION_DISTANCE:
            return False
        
        # Los exits no se conectan con otros exits
        if node1.element_type == ElementType.EXIT and node2.element_type == ElementType.EXIT:
            return False
        
        # Muros no se conectan (excepto con puertas)
        if node1.element_type == ElementType.WALL or node2.element_type == ElementType.WALL:
            return False
        
        return True
    
    def _determine_connection_type(self, node1: Node, node2: Node) -> str:
        """Determina el tipo de conexión entre nodos"""
        types = {node1.element_type, node2.element_type}
        
        if ElementType.DOOR in types:
            return "door"
        elif ElementType.STAIR in types:
            return "stair"
        elif ElementType.CORRIDOR in types or ElementType.CORRIDOR in types:
            return "corridor"
        else:
            return "direct"
    
    def _has_stair_connection(self, node1: Node, node2: Node, map_model: MapModel) -> bool:
        """Verifica si dos nodos en pisos diferentes están conectados por escalera"""
        # Simplificación: asumir que todos los pisos están conectados por escalera
        return node1.element_type == ElementType.STAIR or node2.element_type == ElementType.STAIR
    
    def _add_connection(self, node1: Node, node2: Node, distance: float, connection_type: str) -> None:
        """Añade una conexión bidireccional entre nodos"""
        # Actualizar nodos
        node1.adjacent_nodes.add(node2.id)
        node2.adjacent_nodes.add(node1.id)
        
        # Agregar información de conexión
        node1.connections[node2.id] = {
            'distance': distance,
            'type': connection_type,
            'weight': self._calculate_weight(distance, connection_type)
        }
        node2.connections[node1.id] = {
            'distance': distance,
            'type': connection_type,
            'weight': self._calculate_weight(distance, connection_type)
        }
        
        # Crear arista
        edge = Edge(
            from_node=node1.id,
            to_node=node2.id,
            distance=distance,
            connection_type=connection_type,
            weight=self._calculate_weight(distance, connection_type)
        )
        self.edges.append(edge)
    
    def _calculate_weight(self, distance: float, connection_type: str) -> float:
        """Calcula el peso de una conexión"""
        # Factor de tipo de conexión
        type_factors = {
            'corridor': 1.0,
            'door': 1.2,
            'stair': 1.5,
            'direct': 0.9
        }
        type_factor = type_factors.get(connection_type, 1.0)
        
        # Weight es distancia * factor de tipo
        return distance * type_factor
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calcula distancia euclidiana entre dos posiciones"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _create_matrices(self) -> None:
        """Crea matrices de adyacencia y distancias"""
        n = len(self.nodes)
        node_ids = list(self.nodes.keys())
        
        # Crear mapeo de IDs a índices
        self.node_id_to_index = {nid: i for i, nid in enumerate(node_ids)}
        
        # Matrices
        self.adjacency_matrix = np.zeros((n, n), dtype=int)
        self.distance_matrix = np.zeros((n, n), dtype=float)
        
        for edge in self.edges:
            i = self.node_id_to_index[edge.from_node]
            j = self.node_id_to_index[edge.to_node]
            
            self.adjacency_matrix[i, j] = 1
            self.adjacency_matrix[j, i] = 1
            
            self.distance_matrix[i, j] = edge.distance
            self.distance_matrix[j, i] = edge.distance
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Obtiene un nodo por ID"""
        return self.nodes.get(node_id)
    
    def get_adjacent_nodes(self, node_id: str) -> List[str]:
        """Obtiene nodos adyacentes a uno dado"""
        node = self.nodes.get(node_id)
        return list(node.adjacent_nodes) if node else []
    
    def get_distance(self, node1_id: str, node2_id: str) -> float:
        """Obtiene la distancia entre dos nodos"""
        node1 = self.nodes.get(node1_id)
        node2 = self.nodes.get(node2_id)
        
        if not node1 or not node2:
            return float('inf')
        
        if node2_id in node1.connections:
            return node1.connections[node2_id]['distance']
        
        return float('inf')
    
    def get_connectivity_info(self) -> Dict:
        """Retorna información sobre la conectividad del grafo"""
        total_edges = len(self.edges)
        total_nodes = len(self.nodes)
        
        nodes_by_type = {}
        for node in self.nodes.values():
            tname = node.element_type.name
            nodes_by_type[tname] = nodes_by_type.get(tname, 0) + 1
        
        avg_degree = 2 * total_edges / total_nodes if total_nodes > 0 else 0
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'nodes_by_type': nodes_by_type,
            'average_degree': avg_degree,
            'is_connected': self._is_connected()
        }
    
    def _is_connected(self) -> bool:
        """Verifica si el grafo es conexo"""
        if not self.nodes:
            return False
        
        visited = set()
        start_node = list(self.nodes.keys())[0]
        queue = [start_node]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            node = self.nodes[node_id]
            for adjacent_id in node.adjacent_nodes:
                if adjacent_id not in visited:
                    queue.append(adjacent_id)
        
        return len(visited) == len(self.nodes)
    
    def find_shortest_path(self, start_id: str, end_id: str) -> List[str]:
        """Encuentra el camino más corto entre dos nodos usando Dijkstra"""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        # Inicializar
        distances = {nid: float('inf') for nid in self.nodes}
        distances[start_id] = 0.0
        previous: Dict[str, Optional[str]] = {nid: None for nid in self.nodes}
        unvisited = set(self.nodes.keys())
        
        while unvisited:
            # Nodo no visitado con menor distancia
            current = min(unvisited, key=lambda n: distances[n])
            
            if distances[current] == float('inf'):
                break  # No hay camino
            
            unvisited.remove(current)
            current_node = self.nodes[current]
            
            # Actualizar distancias a vecinos
            for neighbor_id in current_node.adjacent_nodes:
                if neighbor_id in unvisited:
                    distance = self.get_distance(current, neighbor_id)
                    alt_distance = distances[current] + distance
                    
                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current
        
        # Reconstruir camino
        path = []
        current = end_id
        while current is not None:
            path.insert(0, current)
            current = previous[current]
        
        return path if path[0] == start_id else []
    
    def export_to_dict(self) -> Dict:
        """Exporta el grafo a diccionario"""
        return {
            'nodes': {
                nid: {
                    'position': node.position,
                    'element_type': node.element_type.name,
                    'capacity': node.capacity,
                    'floor': node.floor,
                    'adjacent_nodes': list(node.adjacent_nodes)
                }
                for nid, node in self.nodes.items()
            },
            'edges': [
                {
                    'from': edge.from_node,
                    'to': edge.to_node,
                    'distance': edge.distance,
                    'type': edge.connection_type
                }
                for edge in self.edges
            ],
            'connectivity_info': self.get_connectivity_info()
        }
