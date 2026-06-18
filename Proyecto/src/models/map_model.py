"""
Modelo de Mapa - Gestiona la estructura del edificio
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ElementType(Enum):
    """Tipos de elementos en el mapa"""
    WALL = "wall"
    DOOR = "door"
    STAIR = "stair"
    EXIT = "exit"
    OBSTACLE = "obstacle"
    CORRIDOR = "corridor"


@dataclass
class MapElement:
    """Representa un elemento en el mapa"""
    element_type: ElementType
    position: Tuple[int, int]
    width: int
    height: int
    node_id: Optional[int] = None
    capacity: int = 1
    connected_floor: Optional[int] = None  # Para escaleras


@dataclass
class Floor:
    """Representa un piso del edificio"""
    level: int
    width: int
    height: int
    elements: Dict[int, MapElement] = field(default_factory=dict)
    element_counter: int = 0
    
    def add_element(self, element_type: ElementType, position: Tuple[int, int],
                   width: int, height: int, capacity: int = 1) -> int:
        """Añade un elemento al piso y retorna su ID"""
        element_id = self.element_counter
        element = MapElement(
            element_type=element_type,
            position=position,
            width=width,
            height=height,
            node_id=element_id,
            capacity=capacity
        )
        self.elements[element_id] = element
        self.element_counter += 1
        return element_id
    
    def remove_element(self, element_id: int) -> bool:
        """Elimina un elemento del piso"""
        if element_id in self.elements:
            del self.elements[element_id]
            return True
        return False
    
    def get_element(self, element_id: int) -> Optional[MapElement]:
        """Obtiene un elemento del piso"""
        return self.elements.get(element_id)


@dataclass
class MapModel:
    """
    Modelo centralizado del mapa del edificio.
    
    Atributos:
        name: Nombre del mapa
        floors: Lista de pisos
        num_floors: Número total de pisos
        scenario_type: Tipo de escenario (1, 2 o 3)
        exits: Lista de nodos que son salidas
        stairs: Lista de nodos que son escaleras
    """
    name: str
    num_floors: int = 1
    scenario_type: int = 1  # 1: salón, 2: planta única, 3: múltiples pisos
    floors: Dict[int, Floor] = field(default_factory=dict)
    exits: List[int] = field(default_factory=list)
    stairs: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Inicializa los pisos del mapa"""
        if self.num_floors < 1:
            raise ValueError("El número de pisos debe ser mayor a 0")
        
        # Crear pisos por defecto
        for i in range(self.num_floors):
            self.floors[i] = Floor(level=i, width=100, height=100)
    
    def add_floor(self, width: int = 100, height: int = 100) -> int:
        """Añade un nuevo piso y retorna su nivel"""
        level = len(self.floors)
        self.floors[level] = Floor(level=level, width=width, height=height)
        self.num_floors += 1
        return level
    
    def get_floor(self, floor_level: int) -> Optional[Floor]:
        """Obtiene un piso específico"""
        return self.floors.get(floor_level)
    
    def add_element_to_floor(self, floor_level: int, element_type: ElementType,
                            position: Tuple[int, int], width: int, height: int,
                            capacity: int = 1, connected_floor: Optional[int] = None) -> int:
        """Añade un elemento a un piso específico"""
        floor = self.get_floor(floor_level)
        if floor is None:
            raise ValueError(f"El piso {floor_level} no existe")
        
        element_id = floor.add_element(element_type, position, width, height, capacity)
        
        # Registrar salidas y escaleras
        if element_type == ElementType.EXIT:
            self.exits.append(element_id)
        elif element_type == ElementType.STAIR:
            self.stairs.append(element_id)
            # Si tiene un piso conectado, registrarlo
            if connected_floor is not None:
                element = floor.get_element(element_id)
                if element is not None:
                    element.connected_floor = connected_floor
        
        return element_id
    
    def validate_map(self) -> Tuple[bool, List[str]]:
        """
        Valida que el mapa sea válido para la simulación.
        
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []
        
        # Verificar que hay al menos una salida
        if not self.exits:
            errors.append("El mapa debe tener al menos una salida")
        
        # Verificar escaleras para edificios de múltiples pisos
        if self.num_floors > 1 and not self.stairs:
            errors.append("Los edificios de múltiples pisos deben tener escaleras")
        
        # Verificar que todos los pisos tengan elementos
        for level in range(self.num_floors):
            if level not in self.floors:
                errors.append(f"Falta el piso {level}")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """Convierte el mapa a diccionario para guardarlo en JSON"""
        floors_data = []
        for level, floor in self.floors.items():
            elements_data = []
            for element_id, element in floor.elements.items():
                elements_data.append({
                    'id': element_id,
                    'type': element.element_type.value,
                    'position': element.position,
                    'width': element.width,
                    'height': element.height,
                    'capacity': element.capacity,
                    'connected_floor': element.connected_floor
                })
            floors_data.append({
                'level': level,
                'width': floor.width,
                'height': floor.height,
                'elements': elements_data
            })
        
        return {
            'name': self.name,
            'scenario_type': self.scenario_type,
            'num_floors': self.num_floors,
            'floors': floors_data,
            'exits': self.exits,
            'stairs': self.stairs
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'MapModel':
        """Crea un MapModel desde un diccionario (cargado de JSON)"""
        map_model = MapModel(
            name=data['name'],
            num_floors=data['num_floors'],
            scenario_type=data.get('scenario_type', 1)
        )
        map_model.floors = {}
        
        # Reconstruir pisos
        for floor_data in data['floors']:
            level = floor_data['level']
            floor = Floor(level=level, width=floor_data['width'], height=floor_data['height'])
            floor.element_counter = len(floor_data['elements'])
            
            # Reconstruir elementos
            for element_data in floor_data['elements']:
                element = MapElement(
                    element_type=ElementType(element_data['type']),
                    position=tuple(element_data['position']),
                    width=element_data['width'],
                    height=element_data['height'],
                    node_id=element_data['id'],
                    capacity=element_data['capacity'],
                    connected_floor=element_data.get('connected_floor')
                )
                floor.elements[element_data['id']] = element
            
            map_model.floors[level] = floor
        
        map_model.exits = data.get('exits', [])
        map_model.stairs = data.get('stairs', [])
        
        return map_model
    
    def save_to_file(self, filepath: str) -> bool:
        """Guarda el mapa en un archivo JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar mapa: {e}")
            return False
    
    @staticmethod
    def load_from_file(filepath: str) -> Optional['MapModel']:
        """Carga un mapa desde un archivo JSON"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return MapModel.from_dict(data)
        except Exception as e:
            print(f"Error al cargar mapa: {e}")
            return None
