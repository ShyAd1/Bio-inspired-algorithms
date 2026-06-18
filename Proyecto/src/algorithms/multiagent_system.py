"""
Fase 5: Sistema Multiagente Avanzado
Comportamiento inteligente de agentes, comunicación, evitación de colisiones
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import math
from ..models.agent import Agent, AgentState


class AgentRole(Enum):
    """Roles que pueden tener los agentes"""
    INDIVIDUAL = "individual"  # Actúa solo
    SCOUT = "scout"  # Explora caminos
    LEADER = "leader"  # Guía al grupo
    FOLLOWER = "follower"  # Sigue al líder
    COORDINATOR = "coordinator"  # Coordina evacuación


@dataclass
class AgentCommunication:
    """Mensaje de comunicación entre agentes"""
    sender_id: int
    receiver_id: int
    message_type: str  # "route", "congestion", "danger", "help", "status"
    content: Dict
    priority: int = 0


@dataclass
class AdvancedAgent(Agent):
    """Agente mejorado con comportamientos avanzados"""
    role: AgentRole = AgentRole.INDIVIDUAL
    group_id: Optional[int] = None
    nearby_agents: List[int] = field(default_factory=list)
    communication_buffer: List[AgentCommunication] = field(default_factory=list)
    knowledge_base: Dict = field(default_factory=dict)  # Información aprendida
    stress_level: float = 0.0  # 0-1, afecta la toma de decisiones
    panic_threshold: float = 0.7
    is_panicking: bool = False
    preferred_group_size: int = 3
    
    def receive_message(self, msg: AgentCommunication) -> None:
        """Recibe un mensaje de otro agente"""
        self.communication_buffer.append(msg)
        
        # Procesamiento inmediato de ciertos tipos
        if msg.message_type == "danger":
            self.stress_level = min(1.0, self.stress_level + 0.2)
        elif msg.message_type == "help":
            self.stress_level = max(0.0, self.stress_level - 0.1)
    
    def process_messages(self) -> None:
        """Procesa mensajes acumulados"""
        for msg in self.communication_buffer:
            if msg.message_type == "route":
                # Actualizar conocimiento de rutas
                self.knowledge_base['suggested_route'] = msg.content.get('route')
            elif msg.message_type == "congestion":
                # Evitar zonas congestionadas
                congested_node = msg.content.get('node')
                if congested_node:
                    if 'congested_nodes' not in self.knowledge_base:
                        self.knowledge_base['congested_nodes'] = set()
                    self.knowledge_base['congested_nodes'].add(congested_node)
        
        self.communication_buffer.clear()
    
    def update_stress_level(self, dt: float) -> None:
        """Actualiza nivel de estrés con el tiempo"""
        # El estrés disminuye con el tiempo si la evacuación va bien
        if self.state == AgentState.WAITING:
            self.stress_level = min(1.0, self.stress_level + 0.01 * dt)
        else:
            self.stress_level = max(0.0, self.stress_level - 0.005 * dt)
        
        # Verificar pánico
        if self.stress_level > self.panic_threshold and not self.is_panicking:
            self.is_panicking = True
        elif self.stress_level < self.panic_threshold * 0.7:
            self.is_panicking = False
    
    def get_decision_bias(self) -> float:
        """Retorna sesgo de decisión basado en estrés y pánico"""
        if self.is_panicking:
            return 0.3  # Menos racional, más impulsivo
        return 1.0 - (self.stress_level * 0.3)  # Disminuye con estrés
    
    def broadcast_message(self, message_type: str, content: Dict, priority: int = 0) -> AgentCommunication:
        """Crea un mensaje para broadcast a agentes cercanos"""
        return AgentCommunication(
            sender_id=self.id,
            receiver_id=-1,  # -1 indica broadcast
            message_type=message_type,
            content=content,
            priority=priority
        )


class AgentGroup:
    """Representa un grupo de agentes que se mueven juntos"""
    
    def __init__(self, group_id: int, leader_id: int, members: List[int]):
        self.group_id = group_id
        self.leader_id = leader_id
        self.members = set(members)
        self.formation = "column"  # column, circle, wedge
        self.shared_target = None
        self.group_stress = 0.0
    
    def add_member(self, agent_id: int) -> None:
        """Añade miembro al grupo"""
        self.members.add(agent_id)
    
    def remove_member(self, agent_id: int) -> None:
        """Remueve miembro del grupo"""
        self.members.discard(agent_id)
        if agent_id == self.leader_id and self.members:
            # Elegir nuevo líder
            self.leader_id = min(self.members)
    
    def update_stress(self, agents_dict: Dict[int, AdvancedAgent]) -> None:
        """Actualiza estrés grupal promediando estrés de miembros"""
        if not self.members:
            return
        
        total_stress = sum(
            agents_dict[aid].stress_level 
            for aid in self.members 
            if aid in agents_dict
        )
        self.group_stress = total_stress / len(self.members)


class CollisionAvoidance:
    """Sistema de evitación de colisiones"""
    
    PERSONAL_SPACE = 30  # píxeles
    REACTION_DISTANCE = 50  # píxeles
    
    @staticmethod
    def check_collision(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> bool:
        """Verifica si dos agentes colisionarían"""
        dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        return dist < CollisionAvoidance.PERSONAL_SPACE
    
    @staticmethod
    def get_avoidance_vector(
        agent_pos: Tuple[float, float],
        nearby_agents: List[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Calcula vector de evitación basado en agentes cercanos"""
        if not nearby_agents:
            return (0, 0)
        
        avoidance_x, avoidance_y = 0.0, 0.0
        
        for other_pos in nearby_agents:
            dx = agent_pos[0] - other_pos[0]
            dy = agent_pos[1] - other_pos[1]
            dist = max(math.sqrt(dx**2 + dy**2), 0.1)
            
            # Fuerza de repulsión inversamente proporcional a distancia
            if dist < CollisionAvoidance.REACTION_DISTANCE:
                force = (CollisionAvoidance.REACTION_DISTANCE - dist) / CollisionAvoidance.REACTION_DISTANCE
                avoidance_x += (dx / dist) * force
                avoidance_y += (dy / dist) * force
        
        # Normalizar
        magnitude = math.sqrt(avoidance_x**2 + avoidance_y**2)
        if magnitude > 0:
            avoidance_x /= magnitude
            avoidance_y /= magnitude
        
        return (avoidance_x, avoidance_y)


class MultiagentCoordinator:
    """Coordinador de sistemas multiagente"""
    
    def __init__(self):
        self.agents: Dict[int, AdvancedAgent] = {}
        self.groups: Dict[int, AgentGroup] = {}
        self.group_counter = 0
        self.communication_network: List[AgentCommunication] = []
    
    def add_agent(self, agent: AdvancedAgent) -> None:
        """Añade agente al coordinador"""
        self.agents[agent.id] = agent
    
    def form_group(self, leader_id: int, member_ids: List[int]) -> int:
        """Forma un nuevo grupo de agentes"""
        group_id = self.group_counter
        self.group_counter += 1
        
        group = AgentGroup(group_id, leader_id, member_ids)
        self.groups[group_id] = group
        
        # Asignar grupo a agentes
        for member_id in member_ids:
            if member_id in self.agents:
                self.agents[member_id].group_id = group_id
                if member_id == leader_id:
                    self.agents[member_id].role = AgentRole.LEADER
                else:
                    self.agents[member_id].role = AgentRole.FOLLOWER
        
        return group_id
    
    def distribute_messages(self) -> None:
        """Distribuye mensajes entre agentes"""
        # Recolectar mensajes
        all_messages = []
        for agent in self.agents.values():
            # El agente puede generar mensajes
            if agent.is_panicking:
                msg = agent.broadcast_message(
                    "danger",
                    {'reason': 'panic'},
                    priority=2
                )
                all_messages.append(msg)
        
        # Distribuir mensajes cercanos
        for msg in all_messages:
            sender = self.agents.get(msg.sender_id)
            if not sender:
                continue
            
            for agent in self.agents.values():
                if agent.id != msg.sender_id:
                    # Calcular distancia
                    dist = math.sqrt(
                        (sender.position[0] - agent.position[0])**2 +
                        (sender.position[1] - agent.position[1])**2
                    )
                    
                    # Mensajes se propagan en radio de 150 píxeles
                    if dist < 150:
                        msg.receiver_id = agent.id
                        agent.receive_message(msg)
    
    def update_all_agents(self, dt: float) -> None:
        """Actualiza todos los agentes"""
        for agent in self.agents.values():
            # Procesar mensajes
            agent.process_messages()
            
            # Actualizar estrés
            agent.update_stress_level(dt)
            
            # Detectar agentes cercanos
            agent.nearby_agents = self._find_nearby_agents(agent)
        
        # Distribuir nuevos mensajes
        self.distribute_messages()
        
        # Actualizar grupos
        for group in self.groups.values():
            group.update_stress(self.agents)
    
    def _find_nearby_agents(self, agent: AdvancedAgent) -> List[int]:
        """Encuentra agentes cercanos a uno dado"""
        nearby = []
        for other_id, other in self.agents.items():
            if other_id == agent.id:
                continue
            
            dist = math.sqrt(
                (agent.position[0] - other.position[0])**2 +
                (agent.position[1] - other.position[1])**2
            )
            
            if dist < 100:  # Radio de percepción
                nearby.append(other_id)
        
        return nearby
    
    def get_coordination_stats(self) -> Dict:
        """Obtiene estadísticas de coordinación"""
        if not self.agents:
            return {}
        
        panicked = sum(1 for a in self.agents.values() if a.is_panicking)
        avg_stress = sum(a.stress_level for a in self.agents.values()) / len(self.agents)
        total_groups = len(self.groups)
        
        return {
            'total_agents': len(self.agents),
            'panicked_agents': panicked,
            'average_stress': avg_stress,
            'total_groups': total_groups,
            'messages_pending': len(self.communication_network)
        }
