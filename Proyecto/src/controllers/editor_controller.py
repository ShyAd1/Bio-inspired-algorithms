"""
Controlador de Editor de Mapas - Gestiona la creación y edición de mapas
"""
from typing import Optional, Tuple
from ..models.map_model import MapModel, ElementType


class EditorController:
    """Controlador para la creación y edición de mapas"""
    
    def __init__(self):
        """Inicializa el controlador del editor"""
        self.current_map: Optional[MapModel] = None
        self.unsaved_changes = False
    
    def create_new_map(self, name: str, scenario_type: int, num_floors: int = 1) -> MapModel:
        """
        Crea un nuevo mapa.
        
        Args:
            name: Nombre del mapa
            scenario_type: Tipo de escenario (1, 2, o 3)
            num_floors: Número de pisos (relevante para tipo 3)
            
        Returns:
            MapModel creado
        """
        if scenario_type not in [1, 2, 3]:
            raise ValueError("El tipo de escenario debe ser 1, 2, o 3")
        
        if scenario_type == 1:
            num_floors = 1
        elif scenario_type == 2:
            num_floors = 1
        elif scenario_type == 3 and num_floors < 1:
            num_floors = 3
        
        self.current_map = MapModel(
            name=name,
            num_floors=num_floors,
            scenario_type=scenario_type
        )
        self.unsaved_changes = True
        
        # Inicializar con dimensiones por defecto
        for i in range(num_floors):
            if i == 0:
                self.current_map.floors[i].width = 800
                self.current_map.floors[i].height = 600
        
        return self.current_map
    
    def load_map(self, filepath: str) -> Optional[MapModel]:
        """
        Carga un mapa desde archivo.
        
        Args:
            filepath: Ruta del archivo a cargar
            
        Returns:
            MapModel cargado o None si hay error
        """
        self.current_map = MapModel.load_from_file(filepath)
        self.unsaved_changes = False
        return self.current_map
    
    def save_current_map(self, filepath: str) -> bool:
        """
        Guarda el mapa actual.
        
        Args:
            filepath: Ruta donde guardar
            
        Returns:
            True si se guardó exitosamente
        """
        if self.current_map is None:
            return False
        
        success = self.current_map.save_to_file(filepath)
        if success:
            self.unsaved_changes = False
        return success
    
    def add_element(self, floor_level: int, element_type: ElementType,
                   position: Tuple[int, int], width: int, height: int,
                   capacity: int = 1) -> Optional[int]:
        """
        Añade un elemento al mapa.
        
        Args:
            floor_level: Piso donde añadir
            element_type: Tipo de elemento
            position: Posición (x, y)
            width: Ancho del elemento
            height: Alto del elemento
            capacity: Capacidad del elemento
            
        Returns:
            ID del elemento añadido o None si hay error
        """
        if self.current_map is None:
            return None
        
        try:
            element_id = self.current_map.add_element_to_floor(
                floor_level, element_type, position, width, height, capacity
            )
            self.unsaved_changes = True
            return element_id
        except ValueError:
            return None
    
    def remove_element(self, floor_level: int, element_id: int) -> bool:
        """
        Remueve un elemento del mapa.
        
        Args:
            floor_level: Piso
            element_id: ID del elemento
            
        Returns:
            True si fue removido exitosamente
        """
        if self.current_map is None:
            return False
        
        floor = self.current_map.get_floor(floor_level)
        if floor is None:
            return False
        
        # Si es una salida o escalera, remover de listas también
        if element_id in self.current_map.exits:
            self.current_map.exits.remove(element_id)
        if element_id in self.current_map.stairs:
            self.current_map.stairs.remove(element_id)
        
        success = floor.remove_element(element_id)
        if success:
            self.unsaved_changes = True
        return success
    
    def validate_current_map(self) -> Tuple[bool, list]:
        """
        Valida el mapa actual.
        
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        if self.current_map is None:
            return False, ["No hay mapa cargado"]
        
        return self.current_map.validate_map()
    
    def get_scenario_description(self) -> str:
        """Obtiene descripción del tipo de escenario actual"""
        if self.current_map is None:
            return ""
        
        descriptions = {
            1: "Salón Simple (Aula, Laboratorio, Oficina)",
            2: "Edificio de Planta Única",
            3: f"Edificio de {self.current_map.num_floors} Pisos"
        }
        
        return descriptions.get(self.current_map.scenario_type, "Desconocido")
    
    def __repr__(self) -> str:
        return f"EditorController(current_map={self.current_map}, unsaved={self.unsaved_changes})"
