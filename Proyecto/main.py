"""Punto de entrada GRID-only con GUI básica e intuitiva."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from src.models.grid_map import GridMap
from src.controllers.grid_simulation_controller import GridSimulationController
from src.views.grid_simulation_view import GridSimulationView
from src.views.grid_map_editor import GridMapEditorWindow


class GridOnlyApp:
    """Aplicación restringida a mapas de cuadrícula."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Evacuación ACO - GRID")
        self.root.geometry("500x320")
        self.root.resizable(False, False)

        self.maps_dir = Path("maps")
        self.map_var = tk.StringVar()
        self.agents_var = tk.IntVar(value=40)

        self._build_ui()
        self._load_grid_maps()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Simulación de Evacuación en Cuadrícula", font=("Arial", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Modo único: GRID (simple y robusto)").pack(anchor="w", pady=(2, 12))

        ttk.Label(frame, text="Mapa GRID:").pack(anchor="w")
        self.map_combo = ttk.Combobox(frame, textvariable=self.map_var, state="readonly", width=55)
        self.map_combo.pack(anchor="w", pady=(4, 12))

        ttk.Label(frame, text="Número de agentes:").pack(anchor="w")
        ttk.Spinbox(frame, from_=1, to=500, textvariable=self.agents_var, width=10).pack(anchor="w", pady=(4, 12))

        tips = (
            "Controles durante simulación:\n"
            "• SPACE: pausar/reanudar\n"
            "• ESC: cerrar simulación"
        )
        ttk.Label(frame, text=tips).pack(anchor="w", pady=(0, 14))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X)

        ttk.Button(actions, text="Refrescar mapas", command=self._load_grid_maps).pack(side=tk.LEFT)
        ttk.Button(actions, text="Editor GRID", command=self._open_editor).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Iniciar simulación", command=self._start_simulation).pack(side=tk.RIGHT)

    def _open_editor(self) -> None:
        GridMapEditorWindow(self.root, self.maps_dir, self._load_grid_maps)

    def _load_grid_maps(self) -> None:
        self.maps_dir.mkdir(parents=True, exist_ok=True)
        maps = sorted([p.name for p in self.maps_dir.glob("grid*.json")])

        self.map_combo["values"] = maps
        if maps:
            self.map_var.set(maps[0])
        else:
            self.map_var.set("")

    def _start_simulation(self) -> None:
        map_name = self.map_var.get().strip()
        if not map_name:
            messagebox.showwarning("Mapa requerido", "No hay mapas GRID disponibles en maps/.")
            return

        map_path = str(self.maps_dir / map_name)
        grid_map = GridMap.load_from_file(map_path)
        if grid_map is None:
            messagebox.showerror("Error", "No se pudo cargar el mapa GRID.")
            return

        num_agents = max(1, int(self.agents_var.get()))
        controller = GridSimulationController(grid_map)
        created = controller.add_agents(num_agents)
        if created <= 0:
            messagebox.showerror("Error", "El mapa no tiene celdas de spawn (S).")
            return

        view = GridSimulationView()
        view_w = grid_map.width * grid_map.cell_size
        view_h = grid_map.height * grid_map.cell_size
        if not view.initialize(view_w, view_h):
            messagebox.showerror("Error", "No se pudo abrir la ventana de simulación.")
            return

        controller.start()
        paused = False

        try:
            while True:
                actions = view.handle_events()
                if actions.get("quit"):
                    break
                if actions.get("pause"):
                    paused = True
                if actions.get("resume"):
                    paused = False

                if not paused and controller.is_running:
                    controller.update(0.1)

                view.render(controller)
                view.tick(30)

                if not controller.is_running:
                    break
        finally:
            stats = controller.get_stats()
            view.cleanup()
            messagebox.showinfo(
                "Simulación finalizada",
                f"Mapa: {grid_map.name}\n"
                f"Agentes: {stats['total_agents']}\n"
                f"Evacuación: {stats['evacuation_percentage']:.1f}%\n"
                f"Tiempo: {stats['current_time']:.1f}s",
            )

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = GridOnlyApp()
    app.run()


if __name__ == "__main__":
    main()
