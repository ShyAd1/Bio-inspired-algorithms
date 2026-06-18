"""
Matriz de Feromonas - Gestiona las feromonas en el grafo
"""
import numpy as np
from typing import Dict, Optional


class PheromoneMatrix:
    """
    Gestiona la concentración de feromonas en los arcos del grafo.
    
    Las feromonas representan la "calidad" de una ruta aprendida por las hormigas.
    La evaporación permite olvidar rutas malas con el tiempo.
    """
    
    def __init__(self, num_nodes: int, initial_pheromone: float = 1.0):
        """
        Inicializa la matriz de feromonas.
        
        Args:
            num_nodes: Número de nodos en el grafo
            initial_pheromone: Cantidad inicial de feromonas en cada arco
        """
        self.num_nodes = num_nodes
        self.initial_pheromone = initial_pheromone
        
        # Matriz de feromonas (simétrica): pheromone[i][j]
        self.pheromone = np.full((num_nodes, num_nodes), initial_pheromone, dtype=np.float64)
        
        # Diagonal = 0 (no hay ciclos propios)
        np.fill_diagonal(self.pheromone, 0.0)
    
    def add_pheromone(self, from_node: int, to_node: int, amount: float) -> None:
        """
        Añade feromonas a un arco.
        
        Args:
            from_node: Nodo origen
            to_node: Nodo destino
            amount: Cantidad a añadir
        """
        if 0 <= from_node < self.num_nodes and 0 <= to_node < self.num_nodes:
            self.pheromone[from_node][to_node] += amount
            self.pheromone[to_node][from_node] += amount  # Simétrico
    
    def evaporate(self, evaporation_rate: float) -> None:
        """
        Aplica evaporación a todas las feromonas.
        
        Args:
            evaporation_rate: Tasa de evaporación (0.0 a 1.0)
        """
        # Reducir feromonas pero mantener mínimo
        self.pheromone *= (1.0 - evaporation_rate)
        self.pheromone = np.maximum(self.pheromone, self.initial_pheromone * 0.1)
    
    def reset(self) -> None:
        """Reinicia todas las feromonas al valor inicial"""
        self.pheromone.fill(self.initial_pheromone)
        np.fill_diagonal(self.pheromone, 0.0)
    
    def get_pheromone(self, from_node: int, to_node: int) -> float:
        """Obtiene la cantidad de feromonas entre dos nodos"""
        if 0 <= from_node < self.num_nodes and 0 <= to_node < self.num_nodes:
            return self.pheromone[from_node][to_node]
        return 0.0
    
    def normalize_pheromone(self, max_value: float = 100.0) -> None:
        """
        Normaliza los valores de feromonas para evitar overflow.
        
        Args:
            max_value: Valor máximo permitido
        """
        current_max = np.max(self.pheromone)
        if current_max > max_value:
            self.pheromone = self.pheromone * (max_value / current_max)
    
    def __repr__(self) -> str:
        max_pheromone = np.max(self.pheromone)
        avg_pheromone = np.mean(self.pheromone[self.pheromone > 0])
        return f"PheromoneMatrix(nodes={self.num_nodes}, max={max_pheromone:.2f}, avg={avg_pheromone:.2f})"
