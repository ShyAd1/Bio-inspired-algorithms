"""
Modelo de Agente - Representa una persona en la simulación de evacuación
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class AgentState(Enum):
    """Estados posibles de un agente"""
    WALKING = "caminando"
    WAITING = "esperando"
    EVACUATED = "evacuado"
    BLOCKED = "bloqueado"


@dataclass
class Agent:
    """
    Representa un agente (persona) en la simulación.
    
    Atributos:
        id: Identificador único del agente
        position: Posición actual (x, y)
        floor: Piso actual
        velocity: Velocidad de movimiento
        state: Estado actual del agente
        target_exit: Salida objetivo
        current_route: Ruta actual a seguir
        wait_time: Tiempo acumulado esperando
        evacuation_time: Tiempo cuando fue evacuado
    """
    id: int
    position: Tuple[float, float]
    floor: int = 0
    velocity: float = 2.0
    state: AgentState = AgentState.WALKING
    target_exit: Optional[int] = None
    current_route: List[int] = field(default_factory=list)
    route_index: int = 0
    wait_time: float = 0.0
    evacuation_time: Optional[float] = None
    
    def __post_init__(self):
        """Validación inicial del agente"""
        if self.id < 0:
            raise ValueError("El ID del agente no puede ser negativo")
        if self.velocity <= 0:
            raise ValueError("La velocidad debe ser positiva")
    
    def set_route(self, route: List[int]) -> None:
        """
        Establece una nueva ruta para el agente.
        
        Args:
            route: Lista de nodos que conforman la ruta
        """
        self.current_route = route
        self.route_index = 0
    
    def advance_in_route(self) -> None:
        """Avanza al siguiente nodo en la ruta actual"""
        if self.route_index < len(self.current_route) - 1:
            self.route_index += 1
    
    def get_next_node(self) -> Optional[int]:
        """Obtiene el siguiente nodo en la ruta"""
        if self.route_index < len(self.current_route):
            return self.current_route[self.route_index]
        return None
    
    def is_at_route_end(self) -> bool:
        """Verifica si el agente está al final de su ruta"""
        return self.route_index >= len(self.current_route) - 1
    
    def update_position(self, new_position: Tuple[float, float]) -> None:
        """Actualiza la posición del agente"""
        self.position = new_position
    
    def change_state(self, new_state: AgentState) -> None:
        """Cambia el estado del agente"""
        self.state = new_state
    
    def increment_wait_time(self, delta_time: float) -> None:
        """Incrementa el tiempo de espera"""
        if self.state == AgentState.WAITING:
            self.wait_time += delta_time
    
    def evacuate(self, evacuation_time: float) -> None:
        """Marca el agente como evacuado"""
        self.state = AgentState.EVACUATED
        self.evacuation_time = evacuation_time
    
    def reset_wait_time(self) -> None:
        """Reinicia el tiempo de espera"""
        self.wait_time = 0.0
    
    def to_dict(self) -> dict:
        """Convierte el agente a diccionario"""
        return {
            'id': self.id,
            'position': self.position,
            'floor': self.floor,
            'velocity': self.velocity,
            'state': self.state.value,
            'target_exit': self.target_exit,
            'evacuation_time': self.evacuation_time
        }
    
    def __repr__(self) -> str:
        return f"Agent(id={self.id}, pos={self.position}, floor={self.floor}, state={self.state.value})"
