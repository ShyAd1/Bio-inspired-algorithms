"""
Vista de Editor de Mapas - Interfaz visual para crear y editar mapas
"""
import pygame
from typing import Optional, Tuple
from ..models.map_model import MapModel, ElementType


class EditorView:
    """Vista gráfica del editor de mapas usando Pygame"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        """
        Inicializa la vista del editor.
        
        Args:
            width: Ancho de la ventana
            height: Alto de la ventana
        """
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.is_running = False
        self.current_floor = 0
        self.selected_element_type = ElementType.CORRIDOR
        self.selected_element = None
        
        # Colores
        self.COLORS = {
            'background': (255, 255, 255),
            'wall': (50, 50, 50),
            'door': (150, 75, 0),
            'stair': (100, 100, 255),
            'exit': (0, 200, 0),
            'obstacle': (200, 200, 200),
            'corridor': (240, 240, 240),
            'grid': (220, 220, 220),
            'selection': (255, 0, 0)
        }
    
    def initialize(self) -> bool:
        """Inicializa Pygame y la ventana"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Editor de Mapas - Sistema de Evacuación")
            self.clock = pygame.time.Clock()
            self.is_running = True
            return True
        except Exception as e:
            print(f"Error inicializando editor: {e}")
            return False
    
    def draw_background(self) -> None:
        """Dibuja el fondo y la grilla"""
        if self.screen is None:
            return
        
        self.screen.fill(self.COLORS['background'])
        
        # Dibujar grilla
        grid_size = 20
        for x in range(0, self.width, grid_size):
            pygame.draw.line(self.screen, self.COLORS['grid'], (x, 0), (x, self.height))
        for y in range(0, self.height, grid_size):
            pygame.draw.line(self.screen, self.COLORS['grid'], (0, y), (self.width, y))
    
    def draw_map_element(self, element_type: ElementType, position: Tuple[int, int],
                        width: int, height: int, selected: bool = False) -> None:
        """Dibuja un elemento del mapa"""
        if self.screen is None:
            return
        
        color_map = {
            ElementType.WALL: self.COLORS['wall'],
            ElementType.DOOR: self.COLORS['door'],
            ElementType.STAIR: self.COLORS['stair'],
            ElementType.EXIT: self.COLORS['exit'],
            ElementType.OBSTACLE: self.COLORS['obstacle'],
            ElementType.CORRIDOR: self.COLORS['corridor']
        }
        
        color = color_map.get(element_type, self.COLORS['corridor'])
        rect = pygame.Rect(position[0], position[1], width, height)
        pygame.draw.rect(self.screen, color, rect)
        
        if selected:
            pygame.draw.rect(self.screen, self.COLORS['selection'], rect, 3)
        else:
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
    
    def draw_map(self, map_model: MapModel) -> None:
        """Dibuja el mapa completo"""
        if self.screen is None:
            return
        
        floor = map_model.get_floor(self.current_floor)
        if floor is None:
            return
        
        # Dibujar todos los elementos del piso actual
        for element_id, element in floor.elements.items():
            selected = element_id == self.selected_element
            self.draw_map_element(
                element.element_type,
                element.position,
                element.width,
                element.height,
                selected
            )
    
    def draw_ui_panel(self) -> None:
        """Dibuja el panel de interfaz de usuario"""
        if self.screen is None:
            return
        
        # Panel lateral
        panel_width = 200
        panel_rect = pygame.Rect(self.width - panel_width, 0, panel_width, self.height)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.line(self.screen, (0, 0, 0), 
                        (self.width - panel_width, 0), 
                        (self.width - panel_width, self.height), 2)
        
        # Título del panel
        font = pygame.font.Font(None, 24)
        title = font.render("Herramientas", True, (0, 0, 0))
        self.screen.blit(title, (self.width - panel_width + 10, 10))
        
        # Información actual
        font_small = pygame.font.Font(None, 16)
        info_texts = [
            f"Piso: {self.current_floor}",
            f"Elemento: {self.selected_element_type.value}",
        ]
        
        y_offset = 50
        for text in info_texts:
            text_surface = font_small.render(text, True, (0, 0, 0))
            self.screen.blit(text_surface, (self.width - panel_width + 10, y_offset))
            y_offset += 25
    
    def display_map_editor(self, map_model: MapModel) -> None:
        """Muestra el editor de mapas"""
        self.draw_background()
        self.draw_map(map_model)
        self.draw_ui_panel()
        
        if self.screen:
            pygame.display.flip()
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Obtiene la posición del ratón"""
        return pygame.mouse.get_pos()
    
    def handle_events(self) -> bool:
        """Maneja eventos de Pygame. Retorna False si se debe cerrar"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def cleanup(self) -> None:
        """Limpia recursos"""
        pygame.quit()
        self.is_running = False
    
    def __repr__(self) -> str:
        return f"EditorView({self.width}x{self.height})"
