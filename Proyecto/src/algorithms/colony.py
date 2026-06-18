"""
Colonia de Hormigas - Gestiona la población de hormigas
"""
from typing import List, Dict, Optional
from .ant import Ant


class Colony:
    """
    Representa una colonia de hormigas.
    
    Gestiona la población de hormigas, su ciclo de vida,
    y la mejor solución encontrada.
    """
    
    def __init__(self, num_ants: int, start_node: int, end_node: int,
                 alpha: float = 1.0, beta: float = 2.0, gamma: float = 1.5):
        """
        Inicializa la colonia de hormigas.
        
        Args:
            num_ants: Número de hormigas en la colonia
            start_node: Nodo de inicio para los tours
            end_node: Nodo de destino
            alpha: Peso de feromonas
            beta: Peso de visibilidad
            gamma: Peso de congestión
        """
        self.num_ants = num_ants
        self.start_node = start_node
        self.end_node = end_node
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        self.ants: List[Ant] = []
        self.best_ant: Optional[Ant] = None
        self.best_distance = float('inf')
        self.best_time = float('inf')
        self.iteration_count = 0
        
        self._initialize_ants()
    
    def _initialize_ants(self) -> None:
        """Inicializa las hormigas de la colonia"""
        self.ants = []
        for i in range(self.num_ants):
            ant = Ant(
                id=i,
                start_node=self.start_node,
                end_node=self.end_node,
                alpha=self.alpha,
                beta=self.beta,
                gamma=self.gamma
            )
            self.ants.append(ant)
    
    def reset_ants(self) -> None:
        """Reinicia todos los tours de las hormigas"""
        for ant in self.ants:
            ant.reset()
        self.iteration_count += 1
    
    def get_best_ant(self) -> Optional[Ant]:
        """Retorna la hormiga que encontró la mejor solución"""
        return self.best_ant
    
    def get_best_distance(self) -> float:
        """Retorna la mejor distancia encontrada"""
        return self.best_distance
    
    def get_best_time(self) -> float:
        """Retorna el mejor tiempo encontrado"""
        return self.best_time
    
    def update_best_solution(self) -> None:
        """
        Actualiza la mejor solución encontrada en la iteración actual.
        
        Se considera mejor si tiene menor distancia y/o menor tiempo.
        """
        for ant in self.ants:
            if ant.has_completed_tour():
                # Criterio combinado: distancia + tiempo
                combined_metric = ant.tour_distance + ant.tour_time * 0.5
                best_combined = self.best_distance + self.best_time * 0.5
                
                if combined_metric < best_combined:
                    self.best_ant = ant
                    self.best_distance = ant.tour_distance
                    self.best_time = ant.tour_time
    
    def get_successful_ants(self) -> List[Ant]:
        """Retorna las hormigas que completaron su tour"""
        return [ant for ant in self.ants if ant.has_completed_tour()]
    
    def get_average_distance(self) -> float:
        """Calcula la distancia promedio de los tours completados"""
        successful = self.get_successful_ants()
        if not successful:
            return 0.0
        return sum(ant.tour_distance for ant in successful) / len(successful)
    
    def get_average_time(self) -> float:
        """Calcula el tiempo promedio de los tours completados"""
        successful = self.get_successful_ants()
        if not successful:
            return 0.0
        return sum(ant.tour_time for ant in successful) / len(successful)
    
    def get_statistics(self) -> dict:
        """Obtiene estadísticas de la colonia"""
        successful = self.get_successful_ants()
        
        return {
            'iteration': self.iteration_count,
            'total_ants': self.num_ants,
            'successful_ants': len(successful),
            'best_distance': self.best_distance,
            'best_time': self.best_time,
            'average_distance': self.get_average_distance(),
            'average_time': self.get_average_time()
        }
    
    def __repr__(self) -> str:
        return f"Colony(ants={self.num_ants}, best_dist={self.best_distance:.1f}, iter={self.iteration_count})"
