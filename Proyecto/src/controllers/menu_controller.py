"""
Controlador de Menú Principal - Gestiona la navegación de la aplicación
"""
from enum import Enum
from typing import Optional


class MenuOption(Enum):
    """Opciones disponibles en el menú principal"""
    CREATE_MAP = 1
    EDIT_MAP = 2
    SAVE_MAP = 3
    LOAD_MAP = 4
    RUN_SIMULATION = 5
    CONFIGURATION = 6
    STATISTICS = 7
    EXIT = 8


class MenuController:
    """Controlador del menú principal"""
    
    def __init__(self):
        """Inicializa el controlador del menú"""
        self.current_option: Optional[MenuOption] = None
        self.is_running = True
    
    def get_menu_options(self) -> dict:
        """Retorna las opciones disponibles del menú"""
        return {
            MenuOption.CREATE_MAP.value: "Crear Mapa",
            MenuOption.EDIT_MAP.value: "Editar Mapa",
            MenuOption.SAVE_MAP.value: "Guardar Mapa",
            MenuOption.LOAD_MAP.value: "Cargar Mapa",
            MenuOption.RUN_SIMULATION.value: "Ejecutar Simulación",
            MenuOption.CONFIGURATION.value: "Configuración de ACO",
            MenuOption.STATISTICS.value: "Estadísticas",
            MenuOption.EXIT.value: "Salir"
        }
    
    def handle_option(self, option: int) -> MenuOption:
        """
        Procesa una opción del menú.
        
        Args:
            option: Número de opción seleccionada
            
        Returns:
            MenuOption correspondiente
        """
        try:
            menu_option = MenuOption(option)
            self.current_option = menu_option
            if menu_option == MenuOption.EXIT:
                self.is_running = False
            return menu_option
        except ValueError:
            raise ValueError(f"Opción {option} no válida")
    
    def display_menu(self) -> None:
        """Muestra el menú principal"""
        print("\n" + "="*60)
        print("SISTEMA DE OPTIMIZACIÓN DE RUTAS DE EVACUACIÓN")
        print("Basado en Ant Colony Optimization (ACO)")
        print("="*60)
        
        options = self.get_menu_options()
        for key, value in options.items():
            print(f"{key}. {value}")
        print("="*60 + "\n")
    
    def __repr__(self) -> str:
        return f"MenuController(current_option={self.current_option})"
