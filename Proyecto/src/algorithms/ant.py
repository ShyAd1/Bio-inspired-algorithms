"""
Hormiga - Representa una hormiga exploradora en el algoritmo ACO
"""
from dataclasses import dataclass, field
from typing import List, Optional
import random
import math


@dataclass
class Ant:
    """
    Representa una hormiga en el algoritmo ACO.
    
    Las hormigas exploran el grafo construyendo soluciones
    y depositando feromonas basadas en la calidad de sus soluciones.
    """
    id: int
    start_node: int
    end_node: int
    alpha: float = 1.0          # Peso de feromonas
    beta: float = 2.0           # Peso de visibilidad/distancia
    gamma: float = 1.5          # Peso de congestión
    visited: List[int] = field(default_factory=list)
    current_node: int = field(init=False)
    tour_distance: float = 0.0
    tour_time: float = 0.0
    pheromone_deposited: float = 0.0
    
    def __post_init__(self):
        """Inicializa la hormiga en el nodo de inicio"""
        self.current_node = self.start_node
        self.visited = [self.start_node]
        self.tour_distance = 0.0
        self.tour_time = 0.0
    
    def reset(self) -> None:
        """Reinicia la hormiga para una nueva exploración"""
        self.current_node = self.start_node
        self.visited = [self.start_node]
        self.tour_distance = 0.0
        self.tour_time = 0.0
        self.pheromone_deposited = 0.0
    
    def has_visited(self, node: int) -> bool:
        """Verifica si la hormiga ya visitó un nodo"""
        return node in self.visited
    
    def move_to(self, next_node: int, distance: float, travel_time: float) -> None:
        """
        Mueve la hormiga a un nuevo nodo.
        
        Args:
            next_node: Nodo destino
            distance: Distancia recorrida
            travel_time: Tiempo de viaje
        """
        self.visited.append(next_node)
        self.current_node = next_node
        self.tour_distance += distance
        self.tour_time += travel_time
    
    def has_completed_tour(self) -> bool:
        """Verifica si la hormiga completó su tour"""
        return self.current_node == self.end_node
    
    def calculate_transition_probability(self, pheromone: float, visibility: float,
                                        congestion_factor: float) -> float:
        """
        Calcula la probabilidad de transición usando heurística ACO.
        
        Probabilidad = (Feromona^alpha) * (Visibilidad^beta) * (FactorCongestion^gamma)
        
        Args:
            pheromone: Cantidad de feromonas en el arco
            visibility: Inversa de la distancia (1/distancia)
            congestion_factor: Factor de congestión (1 / (1 + congestión))
            
        Returns:
            Valor de probabilidad (antes de normalizar)
        """
        # Evitar valores muy pequeños o cero
        pheromone = max(pheromone, 0.0001)
        visibility = max(visibility, 0.0001)
        congestion_factor = max(congestion_factor, 0.0001)
        
        # Calcular componentes
        pheromone_component = pheromone ** self.alpha
        visibility_component = visibility ** self.beta
        congestion_component = congestion_factor ** self.gamma
        
        # Multiplicar componentes
        probability = pheromone_component * visibility_component * congestion_component
        
        return probability
    
    def get_tour_quality(self) -> float:
        """
        Calcula la calidad del tour completado.
        
        Mejor si: menor distancia, menor tiempo, evitó congestión.
        
        Returns:
            Valor de calidad (mayor es mejor)
        """
        if self.tour_distance == 0:
            return 0.0
        
        # Invertir distancia y tiempo para que "mejor = mayor"
        quality = 1.0 / (self.tour_distance + self.tour_time * 0.1)
        return quality
    
    def get_path_as_string(self) -> str:
        """Retorna el camino visitado como string"""
        return " -> ".join(map(str, self.visited))
    
    def __repr__(self) -> str:
        return f"Ant(id={self.id}, pos={self.current_node}, dist={self.tour_distance:.1f}, visited={len(self.visited)})"
