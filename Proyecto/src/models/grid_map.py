"""Modelo de mapa en cuadrícula para simulación simple de evacuación."""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import json


@dataclass
class GridMap:
    name: str
    width: int
    height: int
    cell_size: int
    grid: List[str]

    @staticmethod
    def load_from_file(filepath: str) -> Optional["GridMap"]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GridMap(
                name=data.get("name", "grid_map"),
                width=int(data["width"]),
                height=int(data["height"]),
                cell_size=int(data.get("cell_size", 20)),
                grid=list(data["grid"]),
            )
        except Exception as e:
            print(f"Error cargando GridMap: {e}")
            return None

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cell(self, x: int, y: int) -> str:
        if not self.in_bounds(x, y):
            return "#"
        return self.grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        return self.get_cell(x, y) in {".", "S", "E"}

    def spawn_cells(self) -> List[Tuple[int, int]]:
        cells: List[Tuple[int, int]] = []
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == "S":
                    cells.append((x, y))
        return cells

    def exit_cells(self) -> List[Tuple[int, int]]:
        cells: List[Tuple[int, int]] = []
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == "E":
                    cells.append((x, y))
        return cells

    def neighbors4(self, x: int, y: int) -> List[Tuple[int, int]]:
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [(nx, ny) for nx, ny in candidates if self.is_walkable(nx, ny)]
