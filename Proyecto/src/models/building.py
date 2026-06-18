"""
Modelo de Edificio - Gestiona el estado actual de la simulación
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .map_model import MapModel
from .agent import Agent, AgentState


@dataclass
class NodeOccupancy:
    """Información de ocupación de un nodo"""
    node_id: int
    current_occupancy: int = 0
    capacity: int = 1
    agents_in_node: List[int] = field(default_factory=list)  # IDs de agentes
    
    @property
    def congestion_level(self) -> float:
        """Calcula el nivel de congestión (0.0 a 1.0)"""
        if self.capacity == 0:
            return 0.0
        return min(self.current_occupancy / self.capacity, 1.0)
    
    def add_agent(self, agent_id: int) -> bool:
        """Intenta añadir un agente. Retorna True si hay capacidad"""
        if self.current_occupancy < self.capacity:
            self.agents_in_node.append(agent_id)
            self.current_occupancy += 1
            return True
        return False
    
    def remove_agent(self, agent_id: int) -> bool:
        """Remueve un agente del nodo"""
        if agent_id in self.agents_in_node:
            self.agents_in_node.remove(agent_id)
            self.current_occupancy -= 1
            return True
        return False


@dataclass
class Building:
    """
    Representa el edificio durante la simulación.
    
    Atributos:
        map_model: Modelo del mapa del edificio
        agents: Diccionario de agentes activos
        node_occupancy: Información de ocupación por nodo
        blocked_nodes: Conjunto de nodos bloqueados
        current_time: Tiempo actual de simulación
    """
    map_model: MapModel
    agents: Dict[int, Agent] = field(default_factory=dict)
    node_occupancy: Dict[int, NodeOccupancy] = field(default_factory=dict)
    blocked_nodes: set = field(default_factory=set)
    current_time: float = 0.0
    agent_counter: int = 0
    
    def __post_init__(self):
        """Inicializa la ocupancia de nodos"""
        self._initialize_node_occupancy()
    
    def _initialize_node_occupancy(self) -> None:
        """Inicializa el registro de ocupancia para todos los nodos"""
        for floor_level, floor in self.map_model.floors.items():
            for element_id, element in floor.elements.items():
                self.node_occupancy[element_id] = NodeOccupancy(
                    node_id=element_id,
                    capacity=element.capacity
                )
    
    def add_agent(self, position: Tuple[float, float], floor: int) -> int:
        """
        Añade un nuevo agente al edificio.
        
        Args:
            position: Posición inicial (x, y)
            floor: Piso inicial
            
        Returns:
            ID del agente añadido
        """
        agent_id = self.agent_counter
        agent = Agent(
            id=agent_id,
            position=position,
            floor=floor,
            velocity=2.0
        )
        self.agents[agent_id] = agent
        self.agent_counter += 1
        return agent_id
    
    def remove_agent(self, agent_id: int) -> bool:
        """Remueve un agente del edificio"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            # Remover del nodo donde estaba
            for node_id, occupancy in self.node_occupancy.items():
                if agent_id in occupancy.agents_in_node:
                    occupancy.remove_agent(agent_id)
                    break
            del self.agents[agent_id]
            return True
        return False
    
    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Obtiene un agente por su ID"""
        return self.agents.get(agent_id)
    
    def move_agent_to_node(self, agent_id: int, node_id: int) -> bool:
        """
        Mueve un agente a un nodo.
        
        Returns:
            True si el movimiento fue exitoso, False si no hay capacidad
        """
        agent = self.get_agent(agent_id)
        if agent is None:
            return False
        
        # Remover del nodo anterior si estaba en alguno
        for occupancy in self.node_occupancy.values():
            if agent_id in occupancy.agents_in_node:
                occupancy.remove_agent(agent_id)
                break
        
        # Intentar añadir al nuevo nodo
        if node_id in self.node_occupancy:
            occupancy = self.node_occupancy[node_id]
            if occupancy.add_agent(agent_id):
                return True
            else:
                # No hay capacidad, el agente espera
                agent.change_state(AgentState.WAITING)
                return False
        
        return False
    
    def get_node_occupancy(self, node_id: int) -> Optional[NodeOccupancy]:
        """Obtiene información de ocupancia de un nodo"""
        return self.node_occupancy.get(node_id)
    
    def block_node(self, node_id: int) -> None:
        """Bloquea un nodo (por ejemplo, por un incendio)"""
        self.blocked_nodes.add(node_id)
    
    def unblock_node(self, node_id: int) -> None:
        """Desbloquea un nodo"""
        self.blocked_nodes.discard(node_id)
    
    def is_node_blocked(self, node_id: int) -> bool:
        """Verifica si un nodo está bloqueado"""
        return node_id in self.blocked_nodes
    
    def get_evacuation_stats(self) -> dict:
        """Obtiene estadísticas de evacuación"""
        total_agents = len(self.agents)
        evacuated_agents = sum(1 for a in self.agents.values() 
                              if a.state == AgentState.EVACUATED)
        blocked_agents = sum(1 for a in self.agents.values() 
                            if a.state == AgentState.BLOCKED)
        waiting_agents = sum(1 for a in self.agents.values() 
                            if a.state == AgentState.WAITING)
        walking_agents = sum(1 for a in self.agents.values() 
                            if a.state == AgentState.WALKING)
        
        evacuation_times = [a.evacuation_time for a in self.agents.values() 
                           if a.evacuation_time is not None]
        
        return {
            'total_agents': total_agents,
            'evacuated': evacuated_agents,
            'blocked': blocked_agents,
            'waiting': waiting_agents,
            'walking': walking_agents,
            'evacuation_percentage': (evacuated_agents / total_agents * 100) if total_agents > 0 else 0,
            'avg_evacuation_time': sum(evacuation_times) / len(evacuation_times) if evacuation_times else 0,
            'max_evacuation_time': max(evacuation_times) if evacuation_times else 0,
            'min_evacuation_time': min(evacuation_times) if evacuation_times else 0
        }
    
    def update_time(self, delta_time: float) -> None:
        """Actualiza el tiempo de simulación"""
        self.current_time += delta_time
    
    def __repr__(self) -> str:
        return f"Building(agents={len(self.agents)}, pisos={self.map_model.num_floors})"
