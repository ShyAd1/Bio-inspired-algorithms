"""Controlador de simulación en cuadrícula (simple y robusto)."""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional
from collections import deque

from ..models.grid_map import GridMap


@dataclass
class GridAgent:
    id: int
    cell: Tuple[int, int]
    evacuated: bool = False
    wait_time: float = 0.0
    evacuation_time: Optional[float] = None


class GridSimulationController:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        self.agents: Dict[int, GridAgent] = {}
        self.current_time = 0.0
        self.is_running = False
        self._dist_to_exit: Dict[Tuple[int, int], int] = {}
        self._precompute_exit_distances()

    def _precompute_exit_distances(self) -> None:
        exits = self.grid_map.exit_cells()
        self._dist_to_exit = {}
        if not exits:
            return

        q = deque()
        for ex in exits:
            self._dist_to_exit[ex] = 0
            q.append(ex)

        while q:
            x, y = q.popleft()
            d = self._dist_to_exit[(x, y)]
            for nx, ny in self.grid_map.neighbors4(x, y):
                if (nx, ny) not in self._dist_to_exit:
                    self._dist_to_exit[(nx, ny)] = d + 1
                    q.append((nx, ny))

    def add_agents(self, count: int) -> int:
        spawns = self.grid_map.spawn_cells()
        if not spawns:
            return 0

        created = 0
        for i in range(count):
            cell = spawns[i % len(spawns)]
            self.agents[i] = GridAgent(id=i, cell=cell)
            created += 1
        return created

    def start(self) -> None:
        self.is_running = True
        self.current_time = 0.0

    def stop(self) -> None:
        self.is_running = False

    def _best_next_cell(self, cell: Tuple[int, int], occupied: Set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        x, y = cell
        candidates = self.grid_map.neighbors4(x, y)
        best = None
        best_d = 10**9
        for c in candidates:
            if c in occupied:
                continue
            d = self._dist_to_exit.get(c, 10**9)
            if d < best_d:
                best_d = d
                best = c
        return best

    def update(self, dt: float = 0.1) -> None:
        if not self.is_running:
            return

        self.current_time += dt
        exits = set(self.grid_map.exit_cells())

        occupied = {a.cell for a in self.agents.values() if not a.evacuated}
        reserved: Set[Tuple[int, int]] = set()

        for agent in self.agents.values():
            if agent.evacuated:
                continue

            if agent.cell in exits:
                agent.evacuated = True
                agent.evacuation_time = self.current_time
                continue

            nxt = self._best_next_cell(agent.cell, occupied | reserved)
            if nxt is None:
                agent.wait_time += dt
                continue

            occupied.discard(agent.cell)
            agent.cell = nxt
            reserved.add(nxt)
            occupied.add(nxt)

            if agent.cell in exits:
                agent.evacuated = True
                agent.evacuation_time = self.current_time

        if self.get_stats()["evacuated"] >= self.get_stats()["total_agents"]:
            self.is_running = False

    def get_stats(self) -> dict:
        total = len(self.agents)
        evac = sum(1 for a in self.agents.values() if a.evacuated)
        waiting = sum(1 for a in self.agents.values() if not a.evacuated)
        times = [a.evacuation_time for a in self.agents.values() if a.evacuation_time is not None]
        return {
            "total_agents": total,
            "evacuated": evac,
            "waiting": waiting,
            "evacuation_percentage": (evac / total * 100.0) if total > 0 else 0.0,
            "current_time": self.current_time,
            "avg_evacuation_time": (sum(times) / len(times)) if times else 0.0,
        }
