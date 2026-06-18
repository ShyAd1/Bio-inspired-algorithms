"""
Sistema Integrado de Fases 2-10
Controlador unificado que integra todas las características avanzadas
"""
from typing import Optional, Dict, List
from ..views.editor_view_advanced import AdvancedEditorView
from ..algorithms.graph_generator import GraphGenerator
from ..algorithms.graph_representation import GraphRepresentation
from ..algorithms.multiagent_system import MultiagentCoordinator, AdvancedAgent, AgentRole, CollisionAvoidance
from ..algorithms.aco_advanced import ACOAdvanced
from ..algorithms.advanced_phases import (
    DynamicCongestionController,
    DynamicReplanningController,
    PheromoneVisualizer,
    MetricsAndReportsGenerator
)
from ..models.map_model import MapModel
from ..models.building import Building


class IntegratedSystemController:
    """
    Controlador integrado de todas las fases 2-10
    Coordina editor visual, generador de grafos, ACO avanzado, 
    sistemas multiagente, control de congestión y reportes
    """
    
    def __init__(self, map_model: Optional[MapModel] = None, building: Optional[Building] = None):
        # Fase 2: Editor Visual
        self.editor = AdvancedEditorView()
        
        # Fase 3 & 4: Grafos
        self.graph_generator = GraphGenerator()
        self.graph_representation: Optional[GraphRepresentation] = None
        
        # Fase 5: Sistema Multiagente
        self.multiagent_coordinator = MultiagentCoordinator()
        self.collision_avoidance = CollisionAvoidance()
        
        # Fase 6: ACO Avanzado
        self.aco_advanced: Optional[ACOAdvanced] = None
        
        # Fases 7-10: Control dinámico, replanificación, visualización, métricas
        self.congestion_controller: Optional[DynamicCongestionController] = None
        self.replan_controller: Optional[DynamicReplanningController] = None
        self.pheromone_visualizer = PheromoneVisualizer()
        self.metrics_generator = MetricsAndReportsGenerator()
        
        # Estado
        self.map_model = map_model
        self.building = building
        self.simulation_active = False
    
    def initialize_all_systems(
        self,
        map_model: MapModel,
        building: Building,
        initialize_editor: bool = False,
    ) -> bool:
        """Inicializa todos los sistemas integrados.

        Args:
            map_model: Mapa activo
            building: Edificio/simulación activa
            initialize_editor: Si True, abre editor Pygame. Para simulación por consola usar False.
        """
        try:
            self.map_model = map_model
            self.building = building
            
            # Inicializar editor (opcional para evitar bloqueos en modo consola)
            if initialize_editor:
                if not self.editor.initialize():
                    return False
                self.editor.load_map(map_model)
            
            # Generar grafo (Fase 3)
            if not self.graph_generator.generate_from_map(map_model):
                return False
            
            # Crear representación gráfica (Fase 4)
            self.graph_representation = GraphRepresentation(self.graph_generator)
            if self.graph_representation:
                if not self.graph_representation.build_networkx_graph():
                    return False
                self.graph_representation.calculate_metrics()
                self.graph_representation.calculate_centrality_measures()
                self.graph_representation.detect_communities()
            
            # Inicializar ACO Avanzado (Fase 6)
            self.aco_advanced = ACOAdvanced(building, map_model)
            
            # Inicializar control de congestión (Fase 7)
            self.congestion_controller = DynamicCongestionController(building)
            
            # Inicializar replanificación dinámica (Fase 8)
            self.replan_controller = DynamicReplanningController(building)
            
            print("✓ Todos los sistemas inicializados correctamente")
            return True
        except Exception as e:
            print(f"✗ Error inicializando sistemas: {e}")
            return False
    
    def add_advanced_agent(self, agent_id: int, position: tuple, role: AgentRole = AgentRole.INDIVIDUAL) -> bool:
        """Añade un agente avanzado al sistema"""
        try:
            agent = AdvancedAgent(
                id=agent_id,
                position=position,
                floor=0,
                velocity=2.0,
                role=role
            )
            self.multiagent_coordinator.add_agent(agent)
            return True
        except Exception as e:
            print(f"Error añadiendo agente: {e}")
            return False
    
    def update_simulation_frame(self, dt: float) -> Dict:
        """Actualiza un frame de simulación con todas las fases"""
        if not self.simulation_active or not self.building:
            return {}
        
        stats = {}
        
        # Actualizar control de congestión (Fase 7)
        if self.congestion_controller:
            self.congestion_controller.update_congestion_data()
            bottlenecks = self.congestion_controller.identify_bottlenecks()
            stats['bottlenecks'] = bottlenecks
        
        # Verificar necesidad de replanificación (Fase 8)
        if self.replan_controller and self.congestion_controller:
            import time
            current_time = time.time()
            if self.replan_controller.check_replan_needed(current_time, self.congestion_controller):
                stats['replanning_triggered'] = True
        
        # Actualizar sistema multiagente (Fase 5)
        self.multiagent_coordinator.update_all_agents(dt)
        stats['multiagent_stats'] = self.multiagent_coordinator.get_coordination_stats()
        
        # Aplicar evitación de colisiones
        for agent in self.multiagent_coordinator.agents.values():
            nearby_positions = [
                self.multiagent_coordinator.agents[aid].position 
                for aid in agent.nearby_agents
            ]
            avoidance = CollisionAvoidance.get_avoidance_vector(agent.position, nearby_positions)
            agent.knowledge_base['avoidance_vector'] = avoidance
        
        # Calcular métricas (Fase 10)
        metrics = self.metrics_generator.calculate_metrics(self.building, dt)
        stats['metrics'] = {
            'evacuated': metrics.evacuated_agents,
            'total': metrics.total_agents,
            'efficiency': metrics.efficiency_rating,
            'max_congestion': metrics.max_congestion
        }
        
        return stats
    
    def get_graph_analysis(self) -> Dict:
        """Obtiene análisis del grafo (Fases 3-4)"""
        if not self.graph_representation:
            return {}
        
        return self.graph_representation.get_graph_summary()
    
    def get_aco_route(self, start_node: str, end_node: str) -> tuple:
        """Obtiene ruta optimizada usando ACO Avanzado (Fase 6)"""
        if not self.aco_advanced:
            return ([], float('inf'))
        
        return self.aco_advanced.find_route_advanced(start_node, end_node)
    
    def export_metrics_report(self, filepath: str) -> bool:
        """Exporta reporte completo (Fase 10)"""
        if not self.metrics_generator.metrics_history:
            return False
        
        last_metrics = self.metrics_generator.metrics_history[-1]
        return self.metrics_generator.export_to_json(filepath, last_metrics)
    
    def export_graph_visualization(self, format: str = 'gexf') -> bool:
        """Exporta visualización del grafo"""
        if not self.graph_representation:
            return False
        
        if format == 'gexf':
            return self.graph_representation.export_to_gexf('reports/graph.gexf')
        elif format == 'graphml':
            return self.graph_representation.export_to_graphml('reports/graph.graphml')
        
        return False
    
    def get_system_status(self) -> Dict:
        """Obtiene estado completo del sistema"""
        return {
            'editor_initialized': self.editor.is_running,
            'graph_generated': self.graph_generator.nodes is not None and len(self.graph_generator.nodes) > 0,
            'multiagent_system': {
                'agents': len(self.multiagent_coordinator.agents),
                'groups': len(self.multiagent_coordinator.groups)
            },
            'congestion_monitoring': self.congestion_controller is not None,
            'dynamic_replanning': self.replan_controller is not None,
            'simulation_active': self.simulation_active,
        }
    
    def cleanup(self) -> None:
        """Limpia todos los recursos"""
        try:
            if self.editor:
                self.editor.cleanup()
            self.simulation_active = False
            print("✓ Sistema integrado limpiado correctamente")
        except Exception as e:
            print(f"Error durante limpieza: {e}")
