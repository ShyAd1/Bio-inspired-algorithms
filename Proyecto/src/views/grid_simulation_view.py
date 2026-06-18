"""Vista Pygame para simulación en cuadrícula."""

from typing import Optional
import pygame

from ..controllers.grid_simulation_controller import GridSimulationController


class GridSimulationView:
    def __init__(self):
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.paused = False

    def initialize(self, width: int, height: int) -> bool:
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Simulación Grid - Evacuación ACO")
            self.clock = pygame.time.Clock()
            return True
        except Exception as e:
            print(f"Error iniciando vista grid: {e}")
            return False

    def handle_events(self) -> dict:
        actions = {"quit": False, "pause": False, "resume": False}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions["quit"] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    actions["quit"] = True
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    if self.paused:
                        actions["pause"] = True
                    else:
                        actions["resume"] = True
        return actions

    def render(self, controller: GridSimulationController) -> None:
        if self.screen is None:
            return

        gm = controller.grid_map
        cs = gm.cell_size
        self.screen.fill((250, 250, 250))

        # celdas
        for y in range(gm.height):
            for x in range(gm.width):
                c = gm.get_cell(x, y)
                rect = pygame.Rect(x * cs, y * cs, cs, cs)
                if c == "#":
                    color = (60, 60, 60)
                elif c == "E":
                    color = (60, 200, 60)
                elif c == "S":
                    color = (80, 140, 240)
                else:
                    color = (235, 240, 248)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (205, 205, 205), rect, 1)

        # agentes
        for agent in controller.agents.values():
            if agent.evacuated:
                continue
            cx = agent.cell[0] * cs + cs // 2
            cy = agent.cell[1] * cs + cs // 2
            pygame.draw.circle(self.screen, (220, 40, 40), (cx, cy), max(2, cs // 3))

        # stats
        stats = controller.get_stats()
        font = pygame.font.Font(None, 24)
        text = (
            f"t={stats['current_time']:.1f}s | evac={stats['evacuated']}/{stats['total_agents']} "
            f"({stats['evacuation_percentage']:.1f}%)"
        )
        surf = font.render(text, True, (15, 15, 15))
        self.screen.blit(surf, (10, 10))

        pygame.display.flip()

    def tick(self, fps: int = 30) -> None:
        if self.clock:
            self.clock.tick(fps)

    def cleanup(self) -> None:
        pygame.quit()
