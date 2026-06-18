"""
Vista de Simulación - Visualiza la simulación de evacuación en tiempo real
"""
import pygame
from typing import Optional, List, Dict, Tuple
from ..models.building import Building
from ..models.agent import Agent, AgentState
from ..models.map_model import ElementType


class SimulationView:
    """Vista de la simulación usando Pygame"""
    
    def __init__(self, width: int = 1400, height: int = 900):
        """
        Inicializa la vista de simulación.
        
        Args:
            width: Ancho de la ventana
            height: Alto de la ventana
        """
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.is_running = False
        self.paused = False
        self.show_stats = True
        self.show_pheromones = False
        
        # Colores
        self.COLORS = {
            'background': (255, 255, 255),
            'wall': (50, 50, 50),
            'door': (150, 75, 0),
            'stair': (100, 100, 255),
            'exit': (0, 200, 0),
            'agent_walking': (255, 0, 0),
            'agent_waiting': (255, 165, 0),
            'agent_evacuated': (0, 150, 0),
            'agent_blocked': (128, 0, 0),
            'pheromone': (255, 255, 0),
            'grid': (220, 220, 220),
            'text': (0, 0, 0),
            'fps': (100, 100, 100)
        }
    
    def initialize(self) -> bool:
        """Inicializa Pygame y la ventana de simulación"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Simulación de Evacuación - ACO")
            self.clock = pygame.time.Clock()
            self.is_running = True
            return True
        except Exception as e:
            print(f"Error inicializando vista de simulación: {e}")
            return False
    
    def draw_background(self) -> None:
        """Dibuja el fondo"""
        if self.screen is None:
            return
        self.screen.fill(self.COLORS['background'])

    def draw_map(self, building: Building, floor_level: int = 0) -> None:
        """Dibuja elementos del mapa para el piso actual."""
        if self.screen is None:
            return

        floor = building.map_model.get_floor(floor_level)
        if floor is None:
            return

        color_map = {
            ElementType.WALL: self.COLORS['wall'],
            ElementType.DOOR: self.COLORS['door'],
            ElementType.STAIR: self.COLORS['stair'],
            ElementType.EXIT: self.COLORS['exit'],
            ElementType.OBSTACLE: (160, 160, 160),
            ElementType.CORRIDOR: (232, 238, 246),
        }

        # Primero pasillos y luego el resto para mejor visibilidad
        element_items = list(floor.elements.items())
        element_items.sort(key=lambda item: 0 if item[1].element_type == ElementType.CORRIDOR else 1)

        for _, element in element_items:
            rect = pygame.Rect(
                int(element.position[0]),
                int(element.position[1]),
                int(element.width),
                int(element.height),
            )
            color = color_map.get(element.element_type, (200, 200, 200))
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (70, 70, 70), rect, 1)
    
    def draw_agent(self, agent: Agent, position: Tuple[float, float]) -> None:
        """Dibuja un agente en la pantalla"""
        if self.screen is None:
            return
        
        # Seleccionar color según estado
        color_map = {
            AgentState.WALKING: self.COLORS['agent_walking'],
            AgentState.WAITING: self.COLORS['agent_waiting'],
            AgentState.EVACUATED: self.COLORS['agent_evacuated'],
            AgentState.BLOCKED: self.COLORS['agent_blocked']
        }
        
        color = color_map.get(agent.state, self.COLORS['agent_walking'])
        radius = 3
        pygame.draw.circle(self.screen, color, 
                          (int(position[0]), int(position[1])), radius)
        
        # Bordes para visibilidad
        pygame.draw.circle(self.screen, (0, 0, 0), 
                          (int(position[0]), int(position[1])), radius, 1)
    
    def draw_agents(self, agents: Dict[int, Agent]) -> None:
        """Dibuja todos los agentes"""
        for agent in agents.values():
            self.draw_agent(agent, agent.position)
    
    def draw_exit(self, position: Tuple[int, int], size: int = 10) -> None:
        """Dibuja una salida de emergencia"""
        if self.screen is None:
            return
        
        rect = pygame.Rect(position[0], position[1], size, size)
        pygame.draw.rect(self.screen, self.COLORS['exit'], rect)
        pygame.draw.rect(self.screen, (0, 100, 0), rect, 2)
    
    def draw_stair(self, position: Tuple[int, int], width: int, height: int) -> None:
        """Dibuja una escalera"""
        if self.screen is None:
            return
        
        rect = pygame.Rect(position[0], position[1], width, height)
        pygame.draw.rect(self.screen, self.COLORS['stair'], rect)
        pygame.draw.rect(self.screen, (50, 50, 150), rect, 2)
    
    def draw_stats_panel(self, stats: Dict) -> None:
        """Dibuja el panel de estadísticas"""
        if self.screen is None or not self.show_stats:
            return
        
        # Fondo del panel
        panel_width = 350
        panel_height = 200
        panel_rect = pygame.Rect(10, 10, panel_width, panel_height)
        pygame.draw.rect(self.screen, (245, 245, 245), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        # Textos
        font_title = pygame.font.Font(None, 20)
        font_text = pygame.font.Font(None, 16)
        
        title = font_title.render("ESTADÍSTICAS", True, self.COLORS['text'])
        self.screen.blit(title, (20, 20))
        
        # Información
        y_offset = 50
        lines = [
            f"Tiempo: {stats.get('current_time', 0):.1f}s",
            f"Evacuados: {stats.get('evacuated', 0)}/{stats.get('total_agents', 0)}",
            f"Porcentaje: {stats.get('evacuation_percentage', 0):.1f}%",
            f"Esperando: {stats.get('waiting', 0)}",
            f"Caminando: {stats.get('walking', 0)}",
            f"Tiempo promedio: {stats.get('avg_evacuation_time', 0):.1f}s",
        ]
        
        for line in lines:
            text_surface = font_text.render(line, True, self.COLORS['text'])
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 25
    
    def draw_fps(self, fps: float) -> None:
        """Dibuja el contador FPS"""
        if self.screen is None:
            return
        
        font = pygame.font.Font(None, 14)
        fps_text = font.render(f"FPS: {fps:.0f}", True, self.COLORS['fps'])
        self.screen.blit(fps_text, (self.width - 100, 10))
    
    def draw_pause_overlay(self) -> None:
        """Dibuja overlay cuando la simulación está pausada"""
        if self.screen is None or not self.paused:
            return
        
        # Overlay semi-transparente
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Texto PAUSADO
        font = pygame.font.Font(None, 60)
        text = font.render("PAUSADO", True, (255, 255, 0))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
    
    def display_simulation(self, building: Building, stats: Dict, fps: float) -> None:
        """Muestra la simulación completa"""
        self.draw_background()
        self.draw_map(building, floor_level=0)
        self.draw_agents(building.agents)
        self.draw_stats_panel(stats)
        self.draw_fps(fps)
        self.draw_pause_overlay()
        
        if self.screen:
            pygame.display.flip()
    
    def handle_events(self) -> Dict[str, bool]:
        """
        Maneja eventos y retorna acciones.
        
        Returns:
            Dict con acciones: {'quit': bool, 'pause': bool, 'resume': bool, 'toggle_stats': bool}
        """
        actions = {
            'quit': False,
            'pause': False,
            'resume': False,
            'toggle_stats': False,
            'speed_up': False,
            'speed_down': False
        }
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions['quit'] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    actions['quit'] = True
                elif event.key == pygame.K_SPACE:
                    if self.paused:
                        actions['resume'] = True
                        self.paused = False
                    else:
                        actions['pause'] = True
                        self.paused = True
                elif event.key == pygame.K_s:
                    actions['toggle_stats'] = True
                    self.show_stats = not self.show_stats
                elif event.key == pygame.K_UP:
                    actions['speed_up'] = True
                elif event.key == pygame.K_DOWN:
                    actions['speed_down'] = True
        
        return actions
    
    def get_fps(self) -> float:
        """Obtiene FPS actual"""
        if self.clock is None:
            return 0.0
        return self.clock.get_fps()
    
    def tick(self, fps: int = 60) -> None:
        """Limita los FPS"""
        if self.clock:
            self.clock.tick(fps)
    
    def cleanup(self) -> None:
        """Limpia recursos"""
        pygame.quit()
        self.is_running = False
    
    def __repr__(self) -> str:
        return f"SimulationView({self.width}x{self.height}, paused={self.paused})"
