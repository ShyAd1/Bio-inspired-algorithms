"""Editor visual avanzado (compatible con Fase 1)."""

import pygame
from enum import Enum
from typing import Optional, Tuple

from ..models.map_model import MapModel, ElementType


class EditorTool(Enum):
    """Herramientas disponibles en el editor."""

    SELECT = "select"
    DRAW_CORRIDOR = "corridor"
    DRAW_DOOR = "door"
    DRAW_STAIR = "stair"
    DRAW_EXIT = "exit"
    DRAW_WALL = "wall"
    DRAW_OBSTACLE = "obstacle"
    ERASE = "erase"


class AdvancedEditorView:
    """Editor visual avanzado simplificado y compatible."""

    COLORS = {
        "background": (245, 245, 245),
        "grid": (225, 225, 225),
        "wall": (50, 50, 50),
        "door": (200, 110, 50),
        "stair": (100, 150, 255),
        "exit": (60, 200, 60),
        "obstacle": (180, 180, 180),
        "corridor": (235, 240, 248),
        "selection": (255, 60, 60),
    }

    GRID_SIZE = 20
    MIN_ELEMENT_SIZE = 20

    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font: Optional[pygame.font.Font] = None

        self.is_running = False
        self.map_model: Optional[MapModel] = None
        self.current_floor = 0
        self.current_tool = EditorTool.DRAW_CORRIDOR

        self.dragging = False
        self.drag_start: Tuple[int, int] = (0, 0)
        self.last_mouse: Tuple[int, int] = (0, 0)

        self.selected_element_id: Optional[int] = None
    
    def initialize(self) -> bool:
        """Inicializa Pygame y ventana."""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Editor Visual Avanzado")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 20)
            self.is_running = True
            return True
        except Exception as e:
            print(f"Error al inicializar Pygame: {e}")
            return False
    
    def load_map(self, map_model: MapModel) -> None:
        """Carga un mapa para edición."""
        self.map_model = map_model
        self.current_floor = 0
        self.selected_element_id = None

    def create_new_map(self, name: str, width: int, height: int, floors: int = 1) -> MapModel:
        """Crea mapa nuevo compatible con `MapModel`."""
        scenario_type = 3 if floors > 1 else 2
        self.map_model = MapModel(name=name, num_floors=floors, scenario_type=scenario_type)
        for idx in range(floors):
            floor = self.map_model.get_floor(idx)
            if floor is not None:
                floor.width = width
                floor.height = height
        self.current_floor = 0
        self.selected_element_id = None
        return self.map_model
    
    def handle_events(self) -> bool:
        """Maneja eventos de editor."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEMOTION:
                self.last_mouse = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
                self.drag_start = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._finish_draw(event.pos)
                self.dragging = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected_element_id = None
                elif event.key == pygame.K_1:
                    self.current_tool = EditorTool.DRAW_CORRIDOR
                elif event.key == pygame.K_2:
                    self.current_tool = EditorTool.DRAW_WALL
                elif event.key == pygame.K_3:
                    self.current_tool = EditorTool.DRAW_DOOR
                elif event.key == pygame.K_4:
                    self.current_tool = EditorTool.DRAW_STAIR
                elif event.key == pygame.K_5:
                    self.current_tool = EditorTool.DRAW_EXIT
                elif event.key == pygame.K_6:
                    self.current_tool = EditorTool.DRAW_OBSTACLE
                elif event.key == pygame.K_UP and self.map_model is not None:
                    self.current_floor = min(self.current_floor + 1, self.map_model.num_floors - 1)
                elif event.key == pygame.K_DOWN:
                    self.current_floor = max(0, self.current_floor - 1)
        return True

    def _finish_draw(self, pos: Tuple[int, int]) -> None:
        if self.map_model is None:
            return
        floor = self.map_model.get_floor(self.current_floor)
        if floor is None:
            return

        x1, y1 = self.drag_start
        x2, y2 = pos
        x = min(x1, x2)
        y = min(y1, y2)
        w = max(self.MIN_ELEMENT_SIZE, abs(x2 - x1))
        h = max(self.MIN_ELEMENT_SIZE, abs(y2 - y1))

        x = (x // self.GRID_SIZE) * self.GRID_SIZE
        y = (y // self.GRID_SIZE) * self.GRID_SIZE
        w = max(self.MIN_ELEMENT_SIZE, (w // self.GRID_SIZE) * self.GRID_SIZE)
        h = max(self.MIN_ELEMENT_SIZE, (h // self.GRID_SIZE) * self.GRID_SIZE)

        tool_map = {
            EditorTool.DRAW_CORRIDOR: ElementType.CORRIDOR,
            EditorTool.DRAW_WALL: ElementType.WALL,
            EditorTool.DRAW_DOOR: ElementType.DOOR,
            EditorTool.DRAW_STAIR: ElementType.STAIR,
            EditorTool.DRAW_EXIT: ElementType.EXIT,
            EditorTool.DRAW_OBSTACLE: ElementType.OBSTACLE,
        }
        element_type = tool_map.get(self.current_tool)
        if element_type is not None:
            floor.add_element(element_type, (x, y), w, h, capacity=10)
    
    def display(self) -> None:
        """Renderiza editor."""
        if self.screen is None or self.map_model is None:
            return

        self.screen.fill(self.COLORS["background"])
        self._draw_grid()
        self._draw_floor_elements()
        self._draw_status_text()

        pygame.display.flip()

        if self.clock is not None:
            self.clock.tick(60)

    def _draw_grid(self) -> None:
        if self.screen is None:
            return
        for x in range(0, self.width, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.COLORS["grid"], (x, 0), (x, self.height), 1)
        for y in range(0, self.height, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.COLORS["grid"], (0, y), (self.width, y), 1)

    def _draw_floor_elements(self) -> None:
        if self.screen is None or self.map_model is None:
            return
        floor = self.map_model.get_floor(self.current_floor)
        if floor is None:
            return

        color_map = {
            ElementType.WALL: self.COLORS["wall"],
            ElementType.DOOR: self.COLORS["door"],
            ElementType.STAIR: self.COLORS["stair"],
            ElementType.EXIT: self.COLORS["exit"],
            ElementType.OBSTACLE: self.COLORS["obstacle"],
            ElementType.CORRIDOR: self.COLORS["corridor"],
        }

        for elem_id, element in floor.elements.items():
            color = color_map.get(element.element_type, self.COLORS["corridor"])
            rect = pygame.Rect(element.position[0], element.position[1], element.width, element.height)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
            if self.selected_element_id == elem_id:
                pygame.draw.rect(self.screen, self.COLORS["selection"], rect, 2)

    def _draw_status_text(self) -> None:
        if self.screen is None or self.font is None or self.map_model is None:
            return
        info = (
            f"Piso: {self.current_floor + 1}/{self.map_model.num_floors} | "
            "Herramienta: 1-Corr 2-Wall 3-Door 4-Stair 5-Exit 6-Obs"
        )
        surf = self.font.render(info, True, (20, 20, 20))
        self.screen.blit(surf, (10, 10))
    
    def cleanup(self) -> None:
        """Libera recursos."""
        pygame.quit()
