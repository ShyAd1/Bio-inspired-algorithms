"""
Ant Colony Optimization (ACO) — Path finding from S nodes to E nodes.

Each ant starts at a spawn (S) node and follows connections through N nodes
until it reaches an exit (E) node. The goal is to find the shortest such path.
"""
import random
import numpy as np
from typing import Callable, Optional


class ACOSolver:
    """
    Path-finding ACO on the map graph.

    The graph is represented as an adjacency dict:
        graph[node_id] = [(neighbour_id, distance), ...]

    Ants start from spawn nodes (S_*) and walk until they reach an exit (E_*).
    Pheromones are deposited on edges of successful (S→E) paths.

    Parameters
    ----------
    graph        : dict[str, list[tuple[str, float]]]  adjacency list
    spawn_ids    : list[str]   starting nodes (S_*)
    exit_ids     : set[str]    goal nodes (E_*)
    all_node_ids : list[str]   full node list (for pheromone matrix indexing)
    rho          : evaporation rate
    Q            : pheromone deposit constant
    alpha        : pheromone exponent
    beta         : heuristic (1/d) exponent
    iterations   : ACO iterations
    num_ants     : ants per iteration (0 = len(spawn_ids))
    on_iteration : callback(iter, best_path_labels, best_dist, log_lines)
    on_done      : callback(best_path_labels, best_dist)
    """

    def __init__(
        self,
        graph: dict,
        spawn_ids: list,
        exit_ids: set,
        all_node_ids: list,
        rho: float = 0.2,
        Q: float = 1.0,
        alpha: float = 1.5,
        beta: float = 2.0,
        iterations: int = 50,
        num_ants: int = 0,
        on_iteration: Optional[Callable] = None,
        on_done: Optional[Callable] = None,
        on_step: Optional[Callable] = None,
        # --- NUEVOS PARÁMETROS DE TRÁFICO ---
        congestion_threshold: int = 5,    # A partir de 5 hormigas, es "embotellamiento"
        congestion_penalty: float = 10.0, # Divide el atractivo de la ruta entre 10
    ):
        self.graph = graph
        self.spawn_ids = spawn_ids
        self.exit_ids = exit_ids
        self.all_node_ids = all_node_ids
        self.idx = {nid: i for i, nid in enumerate(all_node_ids)}

        self.rho = rho
        self.Q = Q
        self.alpha = alpha
        self.beta = beta
        self.iterations = iterations
        self.num_ants = num_ants if num_ants > 0 else max(len(spawn_ids), 10)
        self.on_iteration = on_iteration
        self.on_done = on_done
        self.on_step = on_step
        
        self.congestion_threshold = congestion_threshold
        self.congestion_penalty = congestion_penalty

        self.pheromones = np.ones((len(all_node_ids), len(all_node_ids))) * 0.1
        self.best_path: Optional[list[str]] = None
        self.best_distance: float = float("inf")
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def _next_node(self, current: str, visited: set, occupancy: dict) -> Optional[str]:
        """Pick next node using ACO probability with congestion penalty."""
        neighbours = [
            (nid, d) for nid, d in self.graph.get(current, [])
            if nid not in visited and d > 0
        ]
        if not neighbours:
            return None

        ci = self.idx[current]
        probabilidades = []
        nodos_posibles = []

        for nid, d in neighbours:
            ni = self.idx[nid]
            tau = self.pheromones[ci][ni] ** self.alpha
            eta = (1.0 / d) ** self.beta
            peso = tau * eta
            ants_there = occupancy.get(nid, 0)
            
            if ants_there >= self.congestion_threshold:
                # Si hay tráfico, dividimos el atractivo drásticamente.
                # Entre más hormigas haya, peor se vuelve la penalización.
                factor = self.congestion_penalty * (ants_there - self.congestion_threshold + 1)
                peso /= factor
                
            probabilidades.append(peso)
            nodos_posibles.append(nid)

        probabilidades = np.array(probabilidades)
        suma_total = probabilidades.sum()

        if suma_total == 0:
            probabilidades = np.ones(len(nodos_posibles)) / len(nodos_posibles)
        else:
            probabilidades /= suma_total

        acumulado_probabilidades = np.cumsum(probabilidades)
        variable_aleatoria = random.uniform(0, 1)
        indice_elegido = np.argmax(acumulado_probabilidades >= variable_aleatoria)

        return nodos_posibles[indice_elegido]

    # def _walk(self, start: str) -> Optional[tuple[list[str], float]]:
    #     """
    #     One ant walk from `start` until it reaches an E node or gets stuck.
    #     Returns (path, distance) or None if stuck.
    #     Max steps = 2 * number of nodes to avoid infinite loops.
    #     """
    #     path = [start]
    #     visited = {start}
    #     total_d = 0.0
    #     max_steps = len(self.all_node_ids) * 2

    #     for _ in range(max_steps):
    #         current = path[-1]
    #         if current in self.exit_ids:
    #             return path, total_d

    #         nxt = self._next_node(current, visited)
    #         if nxt is None:
    #             return None  # stuck

    #         # get distance for this edge
    #         d = next((dist for nid, dist in self.graph.get(current, []) if nid == nxt), 1.0)
    #         path.append(nxt)
    #         visited.add(nxt)
    #         total_d += d

    #     return None  # exceeded max steps

    def _deposit(self, path: list[str], dist: float):
        if dist == 0:
            return
        dep = self.Q / dist
        for i in range(len(path) - 1):
            a, b = self.idx[path[i]], self.idx[path[i + 1]]
            self.pheromones[a][b] += dep
            self.pheromones[b][a] += dep

    def run(self) -> tuple[list[str], float]:
        self._stop_flag = False
        self.best_path = None
        self.best_distance = float("inf")
        n = len(self.all_node_ids)
        self.pheromones = np.ones((n, n)) * 0.1

        if not self.spawn_ids:
            if self.on_done: self.on_done([], float("inf"))
            return [], float("inf")

        for iteration in range(self.iterations):
            if self._stop_flag: break

            # Inicializamos cada hormiga en un nodo S
            paths = {i: [self.spawn_ids[i % len(self.spawn_ids)]] for i in range(self.num_ants)}
            visited = {i: {paths[i][0]} for i in range(self.num_ants)}
            distances = {i: 0.0 for i in range(self.num_ants)}
            status = {i: "walking" for i in range(self.num_ants)} # walking, success, stuck

            max_steps = n * 2

            # Simulamos paso a paso
            for step in range(max_steps):
                if self._stop_flag: break
                
                active_ants = 0
                
                # 1. Radar de tráfico: contamos cuántas hormigas hay en cada nodo para aplicar penalizaciones por congestión
                node_occupancy = {}
                for ant, stat in status.items():
                    if stat == "walking":
                        pos = paths[ant][-1]
                        node_occupancy[pos] = node_occupancy.get(pos, 0) + 1

                step_positions = {}
                
                for ant in range(self.num_ants):
                    if status[ant] != "walking": continue
                        
                    active_ants += 1
                    current = paths[ant][-1]
                    
                    if current in self.exit_ids:
                        status[ant] = "success"
                        step_positions[ant] = current
                        node_occupancy[current] = max(0, node_occupancy.get(current, 0) - 1)
                        continue

                    # Le pasamos el radar de tráfico al cerebro de la hormiga
                    nxt = self._next_node(current, visited[ant], node_occupancy)
                    if nxt is None:
                        status[ant] = "stuck"
                        continue

                    d = next((dist for nid, dist in self.graph.get(current, []) if nid == nxt), 1.0)
                    paths[ant].append(nxt)
                    visited[ant].add(nxt)
                    distances[ant] += d
                    step_positions[ant] = nxt
                    
                    # 2. Actualizamos el radar "en vivo": la hormiga dejó su celda anterior y ocupó la nueva
                    node_occupancy[current] = max(0, node_occupancy.get(current, 0) - 1)
                    node_occupancy[nxt] = node_occupancy.get(nxt, 0) + 1

                if active_ants > 0 and self.on_step:
                    self.on_step(step_positions)
                
                if active_ants == 0:
                    break  # Todas terminaron o se atascaron
            
            # --- Evaluar resultados de la iteración ---
            log_lines = []
            successful = 0
            
            for ant in range(self.num_ants):
                if status[ant] == "success":
                    successful += 1
                    p, d = paths[ant], distances[ant]
                    log_lines.append(f"Hormiga {ant+1}: {' → '.join(p)}  dist={d:.2f}")
                    if d < self.best_distance:
                        self.best_distance = d
                        self.best_path = p[:]
                    self._deposit(p, d)
                else:
                    log_lines.append(f"Hormiga {ant+1}: atrapada")

            self.pheromones *= (1 - self.rho)
            self.pheromones = np.clip(self.pheromones, 0.001, None)
            log_lines.insert(0, f"  {successful}/{self.num_ants} hormigas llegaron a salida")

            if self.on_iteration:
                self.on_iteration(iteration + 1, self.best_path or [], self.best_distance, self.pheromones.copy(), log_lines)

        if self.on_done:
            self.on_done(self.best_path or [], self.best_distance)
        return self.best_path or [], self.best_distance
