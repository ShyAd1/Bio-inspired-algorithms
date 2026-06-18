"""
Vista de Menú - Interfaz de usuario para el menú principal
"""
import sys
from typing import Optional


class MenuView:
    """Vista del menú principal de la aplicación"""
    
    def __init__(self):
        """Inicializa la vista del menú"""
        self.running = True
    
    def display_menu(self) -> None:
        """Muestra el menú principal"""
        print("\n" + "="*70)
        print("  SISTEMA INTELIGENTE DE OPTIMIZACIÓN DE RUTAS DE EVACUACIÓN".center(70))
        print("  Basado en Ant Colony Optimization (ACO)".center(70))
        print("="*70)
        print("\n  MENÚ PRINCIPAL\n")
        print("  1. Crear Mapa")
        print("  2. Editar Mapa")
        print("  3. Guardar Mapa")
        print("  4. Cargar Mapa")
        print("  5. Ejecutar Simulación")
        print("  6. Configuración de ACO")
        print("  7. Estadísticas")
        print("  8. Salir")
        print("\n" + "="*70)
    
    def get_user_choice(self) -> int:
        """Obtiene la opción del usuario"""
        while True:
            try:
                choice = int(input("\nSeleccione una opción (1-8): "))
                if 1 <= choice <= 8:
                    return choice
                else:
                    print("❌ Opción no válida. Intente entre 1 y 8.")
            except ValueError:
                print("❌ Ingrese un número válido.")
    
    def display_message(self, message: str, message_type: str = "info") -> None:
        """
        Muestra un mensaje al usuario.
        
        Args:
            message: Mensaje a mostrar
            message_type: Tipo de mensaje ('info', 'success', 'error', 'warning')
        """
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }
        icon = icons.get(message_type, 'ℹ️')
        print(f"\n{icon} {message}")
    
    def prompt_text(self, prompt: str) -> str:
        """Solicita un texto al usuario"""
        return input(f"\n{prompt}: ").strip()
    
    def prompt_number(self, prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Solicita un número al usuario"""
        while True:
            try:
                value = int(input(f"\n{prompt}: "))
                if min_val is not None and value < min_val:
                    print(f"❌ El valor debe ser mayor o igual a {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"❌ El valor debe ser menor o igual a {max_val}")
                    continue
                return value
            except ValueError:
                print("❌ Ingrese un número válido.")
    
    def prompt_choice(self, options: dict) -> int:
        """
        Solicita una opción de un diccionario.
        
        Args:
            options: Diccionario {id: descripción}
            
        Returns:
            ID de la opción seleccionada
        """
        print("\nOpciones disponibles:")
        for key, value in options.items():
            print(f"  {key}. {value}")
        
        while True:
            try:
                choice = int(input("\nSeleccione una opción: "))
                if choice in options:
                    return choice
                else:
                    print(f"❌ Opción no válida.")
            except ValueError:
                print("❌ Ingrese un número válido.")
    
    def confirm_action(self, message: str) -> bool:
        """
        Solicita confirmación del usuario.
        
        Args:
            message: Mensaje a mostrar
            
        Returns:
            True si usuario confirma, False si cancela
        """
        response = input(f"\n{message} (s/n): ").strip().lower()
        return response in ['s', 'si', 'sí', 'yes', 'y']
    
    def show_loading(self, message: str = "Procesando...") -> None:
        """Muestra un mensaje de carga"""
        print(f"\n⏳ {message}")
    
    def show_separator(self) -> None:
        """Muestra un separador visual"""
        print("\n" + "-"*70 + "\n")
    
    def __repr__(self) -> str:
        return f"MenuView(running={self.running})"
