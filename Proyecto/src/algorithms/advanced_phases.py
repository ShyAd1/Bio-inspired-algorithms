"""
Fase 7: Control Dinámico de Congestión
Fase 8: Replanificación Dinámica  
Fase 9: Visualización de Feromonas
Fase 10: Métricas y Reportes

Todas las fases finales integradas en este módulo
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import numpy as np
from ..models.building import Building
from ..models.map_model import MapModel


@dataclass
class CongestionData:
    """Datos de congestión en tiempo real"""
    node_id: str
    congestion_level: float
    occupancy: int
    capacity: int
    prediction: float  # Predicción para siguiente frame
    timestamp: float


class DynamicCongestionController:
    """Fase 7: Control dinámico de congestión"""
    
    def __init__(self, building: Building):
        self.building = building
        self.congestion_history: Dict[str, List[CongestionData]] = {}
        self.reroute_threshold = 0.75
        self.prediction_window = 10  # frames
    
    def predict_congestion(self, node_id: str, lookahead: int = 5) -> float:
        """Predice congestión futura en un nodo"""
        if node_id not in self.congestion_history:
            return 0.0
        
        history = self.congestion_history[node_id][-self.prediction_window:]
        if len(history) < 2:
            return history[-1].congestion_level if history else 0.0
        
        # Promedio móvil exponencial
        levels = [h.congestion_level for h in history]
        alpha = 0.3
        prediction = levels[-1]
        
        for level in reversed(levels[:-1]):
            prediction = alpha * level + (1 - alpha) * prediction
        
        return min(1.0, prediction)
    
    def identify_bottlenecks(self) -> List[str]:
        """Identifica cuellos de botella actuales"""
        bottlenecks = []
        for node_id, occupancy in self.building.node_occupancy.items():
            if occupancy.congestion_level > 0.8:
                bottlenecks.append(node_id)
        return bottlenecks
    
    def suggest_load_balancing(self) -> Dict[str, List[str]]:
        """Sugiere redistribución de carga"""
        redistribution = {}
        bottlenecks = self.identify_bottlenecks()
        
        for bottleneck in bottlenecks:
            # Encontrar rutas alternativas
            similar_exits = []  # Buscar salidas alternativas
            redistribution[bottleneck] = similar_exits
        
        return redistribution
    
    def update_congestion_data(self) -> None:
        """Actualiza datos de congestión"""
        for node_id, occupancy in self.building.node_occupancy.items():
            node_key = str(node_id)
            if node_key not in self.congestion_history:
                self.congestion_history[node_key] = []
            
            prediction = self.predict_congestion(node_key)
            data = CongestionData(
                node_id=node_key,
                congestion_level=occupancy.congestion_level,
                occupancy=occupancy.current_occupancy,
                capacity=occupancy.capacity,
                prediction=prediction,
                timestamp=datetime.now().timestamp()
            )
            self.congestion_history[node_key].append(data)


class DynamicReplanningController:
    """Fase 8: Replanificación dinámica de rutas"""
    
    def __init__(self, building: Building):
        self.building = building
        self.last_replan_time = 0
        self.replan_interval = 5  # segundos
        self.trigger_conditions = []
    
    def check_replan_needed(self, current_time: float, congestion_controller: DynamicCongestionController) -> bool:
        """Verifica si se necesita replanificación"""
        # Condición 1: Intervalo de tiempo
        if current_time - self.last_replan_time >= self.replan_interval:
            return True
        
        # Condición 2: Cambio significativo de congestión
        bottlenecks = congestion_controller.identify_bottlenecks()
        if len(bottlenecks) > 0:
            return True
        
        # Condición 3: Predicción de congestión futura crítica
        for node_id in self.building.node_occupancy.keys():
            node_key = str(node_id)
            prediction = congestion_controller.predict_congestion(node_key, lookahead=5)
            if prediction > 0.85:
                return True
        
        return False
    
    def trigger_replan(self, agents_list: List) -> None:
        """Dispara replanificación para todos los agentes"""
        for agent in agents_list:
            agent.should_recalculate_route = True
        
        self.last_replan_time = datetime.now().timestamp()


class PheromoneVisualizer:
    """Fase 9: Visualización de feromonas"""
    
    def __init__(self, width: int = 1000, height: int = 800):
        self.width = width
        self.height = height
        self.pheromone_data: Optional[np.ndarray] = None
        self.heatmap_colors = [
            (0, 0, 139),      # Azul oscuro (bajo)
            (0, 100, 200),
            (30, 144, 255),   # Azul claro
            (0, 255, 255),    # Cian
            (0, 255, 0),      # Verde
            (255, 255, 0),    # Amarillo
            (255, 165, 0),    # Naranja
            (255, 0, 0),      # Rojo (alto)
        ]
    
    def render_pheromone_heatmap(self, pheromone_matrix: np.ndarray) -> List[Tuple[int, int, int]]:
        """Convierte matriz de feromonas a colores"""
        # Normalizar
        max_pheromone = np.max(pheromone_matrix) if np.max(pheromone_matrix) > 0 else 1.0
        normalized = pheromone_matrix / max_pheromone
        
        # Mapear a colores
        colors = []
        for val in normalized.flatten():
            color_idx = int(val * (len(self.heatmap_colors) - 1))
            colors.append(self.heatmap_colors[color_idx])
        
        return colors
    
    def create_pheromone_overlay(self, pheromone_matrix: np.ndarray) -> np.ndarray:
        """Crea overlay de feromonas para mostrar en simulación"""
        overlay = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Escalar matriz de feromonas al tamaño de la pantalla
        if pheromone_matrix.size > 0:
            scaled = np.repeat(
                np.repeat(pheromone_matrix, self.height // pheromone_matrix.shape[0], axis=0),
                self.width // pheromone_matrix.shape[1],
                axis=1
            )
            
            # Normalizar
            max_phero = np.max(scaled) if np.max(scaled) > 0 else 1.0
            scaled = (scaled / max_phero * 255).astype(np.uint8)
            
            # Aplicar colormap
            overlay[:, :, 0] = scaled  # Canal rojo
            overlay[:, :, 1] = (scaled * 0.7).astype(np.uint8)  # Canal verde reducido
        
        return overlay


@dataclass
class EvacuationMetrics:
    """Métricas de evacuación"""
    total_agents: int
    evacuated_agents: int
    total_time: float
    average_wait_time: float
    average_evacuation_time: float
    max_congestion: float
    efficiency_rating: float
    critical_bottlenecks: List[str]
    timeline: List[Dict]  # Hitos temporales


class MetricsAndReportsGenerator:
    """Fase 10: Generación de métricas y reportes"""
    
    def __init__(self):
        self.metrics_history: List[EvacuationMetrics] = []
        self.start_time = datetime.now()
    
    def calculate_metrics(self, building: Building, simulation_time: float) -> EvacuationMetrics:
        """Calcula métricas de evacuación"""
        stats = building.get_evacuation_stats()
        
        total_agents = stats['total_agents']
        evacuated = stats.get('evacuated', 0)
        avg_wait = 0.0
        avg_evac = stats.get('avg_evacuation_time', 0.0)
        
        # Calcular máxima congestión
        max_congestion = 0.0
        for occupancy in building.node_occupancy.values():
            max_congestion = max(max_congestion, occupancy.congestion_level)
        
        # Rating de eficiencia (0-100)
        if total_agents > 0:
            evac_rate = evacuated / total_agents
            efficiency_rating = (evac_rate * 100) * (1.0 - max_congestion * 0.5)
        else:
            efficiency_rating = 0.0
        
        metrics = EvacuationMetrics(
            total_agents=total_agents,
            evacuated_agents=evacuated,
            total_time=simulation_time,
            average_wait_time=avg_wait,
            average_evacuation_time=avg_evac,
            max_congestion=max_congestion,
            efficiency_rating=efficiency_rating,
            critical_bottlenecks=[],
            timeline=[]
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def generate_report(self, metrics: EvacuationMetrics) -> Dict:
        """Genera reporte completo"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'simulation': {
                'total_agents': metrics.total_agents,
                'evacuated': metrics.evacuated_agents,
                'evacuation_rate': (metrics.evacuated_agents / metrics.total_agents * 100) if metrics.total_agents > 0 else 0,
                'total_time_seconds': metrics.total_time,
            },
            'timing': {
                'average_wait_time': metrics.average_wait_time,
                'average_evacuation_time': metrics.average_evacuation_time,
            },
            'efficiency': {
                'max_congestion': metrics.max_congestion,
                'efficiency_rating': metrics.efficiency_rating,
                'critical_bottlenecks': metrics.critical_bottlenecks,
            }
        }
        return report
    
    def export_to_json(self, filepath: str, metrics: EvacuationMetrics) -> bool:
        """Exporta reporte a JSON"""
        try:
            report = self.generate_report(metrics)
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exportando reporte: {e}")
            return False
    
    def export_to_csv(self, filepath: str) -> bool:
        """Exporta historial de métricas a CSV"""
        try:
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'total_agents', 'evacuated', 'total_time', 'avg_wait',
                    'avg_evacuation', 'max_congestion', 'efficiency_rating'
                ])
                for m in self.metrics_history:
                    writer.writerow([
                        m.total_agents, m.evacuated_agents, m.total_time,
                        m.average_wait_time, m.average_evacuation_time,
                        m.max_congestion, m.efficiency_rating
                    ])
            return True
        except Exception as e:
            print(f"Error exportando CSV: {e}")
            return False
    
    def get_comparison_metrics(self) -> Dict:
        """Compara métricas de múltiples simulaciones"""
        if len(self.metrics_history) < 2:
            return {}
        
        return {
            'average_efficiency': sum(m.efficiency_rating for m in self.metrics_history) / len(self.metrics_history),
            'best_efficiency': max(m.efficiency_rating for m in self.metrics_history),
            'worst_efficiency': min(m.efficiency_rating for m in self.metrics_history),
            'simulations_count': len(self.metrics_history),
        }
