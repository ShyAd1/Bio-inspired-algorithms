"""Editor simple de mapas GRID con Tkinter."""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Optional

from ..models.grid_map import GridMap


class GridMapEditorWindow:
    """Ventana de edición básica para mapas en cuadrícula."""

    CELL_TYPES = {
        "Vacío": ".",
        "Muro": "#",
        "Spawn": "S",
        "Salida": "E",
    }

    COLORS = {
        ".": "#eaf0f8",
        "#": "#3c3c3c",
        "S": "#4f8cff",
        "E": "#35c85a",
    }

    def __init__(self, parent: tk.Tk, maps_dir: Path, on_saved_callback):
        self.parent = parent
        self.maps_dir = maps_dir
        self.on_saved_callback = on_saved_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Editor GRID")
        self.window.geometry("980x680")

        self.map_name = tk.StringVar(value="grid_nuevo")
        self.width_var = tk.IntVar(value=30)
        self.height_var = tk.IntVar(value=20)
        self.cell_size_var = tk.IntVar(value=24)
        self.current_brush = tk.StringVar(value=".")

        self.grid: List[List[str]] = []
        self.canvas: Optional[tk.Canvas] = None
        self._drag_paint = False

        self._build_ui()
        self._create_blank_grid()

    def _build_ui(self) -> None:
        root = ttk.Frame(self.window, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(root)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Nombre:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.map_name, width=20).pack(side=tk.LEFT, padx=(4, 10))

        ttk.Label(top, text="Ancho:").pack(side=tk.LEFT)
        ttk.Spinbox(top, from_=10, to=80, textvariable=self.width_var, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="Alto:").pack(side=tk.LEFT)
        ttk.Spinbox(top, from_=10, to=60, textvariable=self.height_var, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="Celda:").pack(side=tk.LEFT)
        ttk.Spinbox(top, from_=12, to=40, textvariable=self.cell_size_var, width=5).pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Nuevo", command=self._create_blank_grid).pack(side=tk.LEFT, padx=(10, 4))
        ttk.Button(top, text="Cargar", command=self._load_from_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Guardar", command=self._save).pack(side=tk.LEFT, padx=4)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        left = ttk.LabelFrame(body, text="Herramientas", padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)

        for label, value in self.CELL_TYPES.items():
            ttk.Radiobutton(left, text=label, value=value, variable=self.current_brush).pack(anchor="w", pady=2)

        ttk.Label(left, text="\nAtajos:").pack(anchor="w", pady=(8, 0))
        ttk.Label(left, text="1=Vacío  2=Muro\n3=Spawn  4=Salida").pack(anchor="w")

        self.canvas = tk.Canvas(body, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.window.bind("1", lambda _e: self.current_brush.set("."))
        self.window.bind("2", lambda _e: self.current_brush.set("#"))
        self.window.bind("3", lambda _e: self.current_brush.set("S"))
        self.window.bind("4", lambda _e: self.current_brush.set("E"))

    def _create_blank_grid(self) -> None:
        w = max(10, int(self.width_var.get()))
        h = max(10, int(self.height_var.get()))
        self.grid = [["." for _ in range(w)] for _ in range(h)]

        # borde de muro
        for x in range(w):
            self.grid[0][x] = "#"
            self.grid[h - 1][x] = "#"
        for y in range(h):
            self.grid[y][0] = "#"
            self.grid[y][w - 1] = "#"

        # spawn/salida base
        if w > 4 and h > 4:
            self.grid[1][1] = "S"
            self.grid[1][2] = "S"
            self.grid[h - 2][w - 2] = "E"

        self._redraw()

    def _load_from_selected(self) -> None:
        candidate = simpledialog.askstring(
            "Cargar mapa",
            "Nombre archivo grid (ej: grid_basico.json)",
            parent=self.window,
        )
        if not candidate:
            return

        path = self.maps_dir / candidate
        gm = GridMap.load_from_file(str(path))
        if gm is None:
            messagebox.showerror("Error", "No se pudo cargar ese mapa.", parent=self.window)
            return

        self.map_name.set(gm.name)
        self.width_var.set(gm.width)
        self.height_var.set(gm.height)
        self.cell_size_var.set(gm.cell_size)
        self.grid = [list(row) for row in gm.grid]
        self._redraw()

    def _save(self) -> None:
        if not self.grid:
            return

        # Validaciones mínimas
        has_spawn = any("S" in row for row in self.grid)
        has_exit = any("E" in row for row in self.grid)
        if not has_spawn or not has_exit:
            messagebox.showwarning("Mapa inválido", "Debe haber al menos una celda S y una E.", parent=self.window)
            return

        name = self.map_name.get().strip() or "grid_mapa"
        data = {
            "name": name,
            "width": len(self.grid[0]),
            "height": len(self.grid),
            "cell_size": int(self.cell_size_var.get()),
            "grid": ["".join(row) for row in self.grid],
        }

        filename = f"{name}.json" if name.endswith(".json") else f"{name}.json"
        if not filename.startswith("grid"):
            filename = f"grid_{filename}"

        self.maps_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.maps_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo("Guardado", f"Mapa guardado en:\n{filepath}", parent=self.window)
        self.on_saved_callback()

    def _on_click(self, event) -> None:
        self._drag_paint = True
        self._paint_at(event.x, event.y)

    def _on_drag(self, event) -> None:
        if self._drag_paint:
            self._paint_at(event.x, event.y)

    def _on_release(self, _event) -> None:
        self._drag_paint = False

    def _paint_at(self, px: int, py: int) -> None:
        if self.canvas is None or not self.grid:
            return

        cs = int(self.cell_size_var.get())
        x = px // cs
        y = py // cs
        h = len(self.grid)
        w = len(self.grid[0])
        if not (0 <= x < w and 0 <= y < h):
            return

        self.grid[y][x] = self.current_brush.get()
        self._redraw()

    def _redraw(self) -> None:
        if self.canvas is None or not self.grid:
            return

        self.canvas.delete("all")
        cs = int(self.cell_size_var.get())
        h = len(self.grid)
        w = len(self.grid[0])
        self.canvas.config(scrollregion=(0, 0, w * cs, h * cs))

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                color = self.COLORS.get(cell, "#ffffff")
                x1 = x * cs
                y1 = y * cs
                x2 = x1 + cs
                y2 = y1 + cs
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#bcbcbc")
