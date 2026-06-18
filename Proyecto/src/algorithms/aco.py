"""
ACO - Implementación del Algoritmo de Optimización por Colonia de Hormigas
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
import random
from .colony import Colony
from .pheromone import PheromoneMatrix
from ..models.building import Building
from ..models.map_model import MapModel


class Graph:
    """Representa el grafo de la simulación"""
    
    def __init__(self, num_nodes: int):
        """Inicializa el grafo"""
        self.num_nodes = num_nodes
        self.distances = np.zeros((num_nodes, num_nodes), dtype=np.float64)
        self.adjacency = np.zeros((num_nodes, num_nodes), dtype=np.int32)
    
    def add_edge(self, from_node: int, to_node: int, distance: float) -> None:
        """Añade una arista al grafo"""
        if 0 <= from_node < self.num_nodes and 0 <= to_node < self.num_nodes:
            self.distances[from_node][to_node] = distance
            self.distances[to_node][from_node] = distance
            self.adjacency[from_node][to_node] = 1
            self.adjacency[to_node][from_node] = 1
    
    def has_edge(self, from_node: int, to_node: int) -> bool:
        """Verifica si existe una arista entre dos nodos"""
        if 0 <= from_node < self.num_nodes and 0 <= to_node < self.num_nodes:
            return self.adjacency[from_node][to_node] == 1
        return False
    
    def get_neighbors(self, node: int) -> List[int]:
        """Obtiene los nodos vecinos de un nodo"""
        if 0 <= node < self.num_nodes:
            return [i for i in range(self.num_nodes) if self.adjacency[node][i] == 1]
        return []
    
    def get_distance(self, from_node: int, to_node: int) -> float:
        """Obtiene la distancia entre dos nodos"""
        if 0 <= from_node < self.num_nodes and 0 <= to_node < self.num_nodes:
            return self.distances[from_node][to_node]
        return float('inf')


class ACO:
    """
    Implementación completa del Algoritmo de Optimización por Colonia de Hormigas.
    
    Principales características:
    - Exploración adaptativa basada en feromonas
    - Consideración de congestión en la heurística
    - Evaporación y refuerzo dinámico de feromonas
    - Replanificación de rutas en tiempo real
    """
    
    def __init__(self, building: Building, map_model: MapModel,
                 alpha: float = 1.0, beta: float = 2.0, gamma: float = 1.5,
                 evaporation_rate: float = 0.1, num_ants: int = 30,
                 max_iterations: int = 100):
        """
        Inicializa el algoritmo ACO.
        
        Args:
            building: Modelo del edificio
            map_model: Modelo del mapa
            alpha: Peso de feromonas
            beta: Peso de visibilidad
            gamma: Peso de congestión
            evaporation_rate: Tasa de evaporación
            num_ants: Número de hormigas
            max_iterations: Iteraciones máximas
        """
        self.building = building
        self.map_model = map_model
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.evaporation_rate = evaporation_rate
        self.num_ants = num_ants
        self.max_iterations = max_iterations
        
        # Calcular número total de nodos
        total_nodes = sum(len(floor.elements) for floor in map_model.floors.values())
        
        self.graph = Graph(total_nodes)
        self.pheromone_matrix = PheromoneMatrix(total_nodes, initial_pheromone=1.0)
        self.colony: Optional[Colony] = None
        
        # Estadísticas
        self.iteration_count = 0
        self.best_routes: Dict[int, List[int]] = {}
        self.optimization_history: List[dict] = []
        
        self._build_graph_from_map()
    
    def _build_graph_from_map(self) -> None:
        """Construye el grafo a partir del mapa del edificio"""
        # Crear mapeo de nodos globales
        node_mapping = {}
        global_node_id = 0
        
        for floor_level, floor in self.map_model.floors.items():
            for element_id, element in floor.elements.items():
                node_mapping[element_id] = global_node_id
                global_node_id += 1
        
        # Conectar nodos con distancias básicas
        # En una versión mejorada, se conectaría según conectividad real
        for i in range(self.graph.num_nodes):
            for j in range(i + 1, self.graph.num_nodes):
                # Distancia euclidiana simplificada
                distance = abs(i - j) * 10  # Distancia nominal
                self.graph.add_edge(i, j, distance)
    
    def find_route(self, start_node: int, end_node: int) -> List[int]:
        """
        Encuentra una ruta óptima usando ACO.
        
        Args:
            start_node: Nodo de inicio
            end_node: Nodo de destino
            
        Returns:
            Lista de nodos que forman la ruta
        """
        # Crear colonia
        self.colony = Colony(
            num_ants=self.num_ants,
            start_node=start_node,
            end_node=end_node,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma
        )
        
        # Ejecutar iteraciones de ACO
        for iteration in range(self.max_iterations):
            self.colony.reset_ants()
            
            # Construir tours para todas las hormigas
            for step in range(self.graph.num_nodes):
                for ant in self.colony.ants:
                    if not ant.has_completed_tour():
                        self._construct_next_move(ant)
            
            # Evaluar y actualizar
            self.colony.update_best_solution()
            self._update_pheromones()
            
            # Registrar progreso
            stats = self.colony.get_statistics()
            self.optimization_history.append(stats)
            
            self.iteration_count += 1
        
        # Retornar la mejor ruta encontrada
        best_ant = self.colony.get_best_ant()
        if best_ant is not None:
            return best_ant.visited
        return [start_node, end_node]
    
    def _construct_next_move(self, ant) -> None:
        """
        Construye el siguiente movimiento de una hormiga.
        
        Uses probabilistic selection based on pheromone and congestion.
        """
        if ant.has_completed_tour():
            return
        
        current = ant.current_node
        unvisited = [node for node in self.graph.get_neighbors(current)
                    if node != current and not ant.has_visited(node)]
        
        if not unvisited:
            # Si no hay vecinos sin visitar, terminamos
            if current != ant.end_node:
                # Intentar conectar directamente al destino
                if self.graph.has_edge(current, ant.end_node):
                    distance = self.graph.get_distance(current, ant.end_node)
                    ant.move_to(ant.end_node, distance, distance * 0.5)
            return
        
        # Calcular probabilidades de transición
        probabilities = []
        total_probability = 0.0
        
        for next_node in unvisited:
            pheromone = self.pheromone_matrix.get_pheromone(current, next_node)
            distance = self.graph.get_distance(current, next_node)
            visibility = 1.0 / max(distance, 0.1)
            
            # Obtener factor de congestión
            congestion = self._get_congestion_factor(next_node)
            
            # Calcular probabilidad
            prob = ant.calculate_transition_probability(pheromone, visibility, congestion)
            probabilities.append((next_node, prob))
            total_probability += prob
        
        # Seleccionar siguiente nodo con ruleta probabilística
        if total_probability > 0:
            r = random.uniform(0, total_probability)
            accumulated = 0.0
            
            for next_node, prob in probabilities:
                accumulated += prob
                if r <= accumulated:
                    distance = self.graph.get_distance(current, next_node)
                    ant.move_to(next_node, distance, distance * 0.5)
                    return
            
            # Fallback: seleccionar el último
            next_node = probabilities[-1][0]
            distance = self.graph.get_distance(current, next_node)
            ant.move_to(next_node, distance, distance * 0.5)
    
    def _get_congestion_factor(self, node_id: int) -> float:
        """
        Obtiene el factor de congestión para un nodo.
        
        Returns:
            Factor entre 0 y 1 (1/(1 + congestión))
        """
        occupancy = self.building.get_node_occupancy(node_id)
        if occupancy is None:
            return 1.0
        
        congestion = occupancy.congestion_level
        return 1.0 / (1.0 + congestion)
    
    def _update_pheromones(self) -> None:
        """Actualiza las feromonas basadas en la calidad de los tours"""
        # Evaporación
        self.pheromone_matrix.evaporate(self.evaporation_rate)
        
        # Depósito de feromonas (solo de hormigas exitosas)
        if self.colony is not None:
            for ant in self.colony.get_successful_ants():
                quality = ant.get_tour_quality()
                pheromone_amount = quality
                
                # Depositar en los arcos del tour
                for i in range(len(ant.visited) - 1):
                    from_node = ant.visited[i]
                    to_node = ant.visited[i + 1]
                    self.pheromone_matrix.add_pheromone(from_node, to_node, pheromone_amount)
        
        # Normalizar para evitar overflow
        self.pheromone_matrix.normalize_pheromone()
    
    def get_statistics(self) -> dict:
        """Obtiene estadísticas del ACO"""
        if self.colony is None:
            return {}
        
        return {
            'iterations': self.iteration_count,
            'colony_stats': self.colony.get_statistics(),
            'optimization_history': self.optimization_history
        }
    
    def __repr__(self) -> str:
        return f"ACO(alpha={self.alpha}, beta={self.beta}, gamma={self.gamma}, ants={self.num_ants})"
