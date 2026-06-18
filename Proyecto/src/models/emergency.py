"""
Modelo de Emergencia - Gestiona eventos de emergencia durante la simulación
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class EmergencyType(Enum):
    """Tipos de emergencias soportadas"""
    FIRE = "incendio"
    EARTHQUAKE = "terremoto"
    PREVENTIVE = "evacuacion_preventiva"


@dataclass
class BlockedZone:
    """Representa una zona bloqueada por una emergencia"""
    zone_id: int
    nodes_blocked: List[int] = field(default_factory=list)
    floor_level: int = 0
    severity: float = 1.0  # 0.0 a 1.0
    active: bool = True


@dataclass
class Emergency:
    """
    Gestiona emergencias durante la simulación.
    
    Atributos:
        emergency_type: Tipo de emergencia
        start_time: Momento en que comienza
        blocked_zones: Zonas afectadas
        affected_nodes: Nodos bloqueados actualmente
        is_active: Si la emergencia está activa
    """
    emergency_type: EmergencyType
    start_time: float = 0.0
    blocked_zones: List[BlockedZone] = field(default_factory=list)
    affected_nodes: set = field(default_factory=set)
    is_active: bool = False
    expansion_rate: float = 0.1  # Tasa de expansión por unidad de tiempo
    
    def activate(self) -> None:
        """Activa la emergencia"""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Desactiva la emergencia"""
        self.is_active = False
        self.affected_nodes.clear()
    
    def add_blocked_zone(self, zone_id: int, nodes: List[int], floor: int, 
                        severity: float = 1.0) -> None:
        """Añade una zona bloqueada por la emergencia"""
        zone = BlockedZone(
            zone_id=zone_id,
            nodes_blocked=nodes,
            floor_level=floor,
            severity=severity,
            active=True
        )
        self.blocked_zones.append(zone)
        self.affected_nodes.update(nodes)
    
    def update_affected_nodes(self) -> None:
        """Actualiza el conjunto de nodos afectados basado en zonas activas"""
        self.affected_nodes.clear()
        for zone in self.blocked_zones:
            if zone.active:
                self.affected_nodes.update(zone.nodes_blocked)
    
    def expand_zone(self, zone_id: int, new_nodes: List[int]) -> None:
        """Expande una zona con nuevos nodos bloqueados"""
        for zone in self.blocked_zones:
            if zone.zone_id == zone_id:
                zone.nodes_blocked.extend(new_nodes)
                self.affected_nodes.update(new_nodes)
                break
    
    def neutralize_zone(self, zone_id: int) -> None:
        """Neutraliza una zona de emergencia"""
        for zone in self.blocked_zones:
            if zone.zone_id == zone_id:
                zone.active = False
                break
        self.update_affected_nodes()
    
    def get_severity_at_node(self, node_id: int) -> float:
        """Obtiene la severidad de la emergencia en un nodo específico"""
        for zone in self.blocked_zones:
            if zone.active and node_id in zone.nodes_blocked:
                return zone.severity
        return 0.0
    
    def to_dict(self) -> dict:
        """Convierte la emergencia a diccionario"""
        return {
            'type': self.emergency_type.value,
            'start_time': self.start_time,
            'is_active': self.is_active,
            'affected_nodes': list(self.affected_nodes),
            'expansion_rate': self.expansion_rate
        }
    
    def __repr__(self) -> str:
        return f"Emergency(type={self.emergency_type.value}, active={self.is_active}, affected={len(self.affected_nodes)})"
