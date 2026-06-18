"""Controlador de Simulación - Gestiona la ejecución de las simulaciones."""

import math
from typing import Optional, List, Dict, Tuple
from ..models.building import Building
from ..models.map_model import MapModel
from ..models.emergency import Emergency, EmergencyType
from ..models.agent import AgentState
from ..algorithms.aco import ACO


class SimulationController:
    """Controlador de simulaciones"""
    
    def __init__(self):
        """Inicializa el controlador de simulación"""
        self.building: Optional[Building] = None
        self.aco: Optional[ACO] = None
        self.emergency: Optional[Emergency] = None
        self.is_running = False
        self.current_time = 0.0
        self.max_time = 300.0  # 5 minutos máximo de simulación
        self.simulation_speed = 1.0
        self.exit_targets: Dict[int, Tuple[float, float, int]] = {}
        self.node_centers: Dict[int, Tuple[float, float, int]] = {}

    def _get_blocking_rects(self, floor_level: int) -> List[Tuple[float, float, float, float]]:
        """Obtiene rectángulos bloqueantes (muros/obstáculos) para un piso."""
        if self.building is None:
            return []

        floor = self.building.map_model.get_floor(floor_level)
        if floor is None:
            return []

        blockers: List[Tuple[float, float, float, float]] = []
        for element in floor.elements.values():
            if element.element_type.value in ("wall", "obstacle"):
                x1 = float(element.position[0])
                y1 = float(element.position[1])
                x2 = x1 + float(element.width)
                y2 = y1 + float(element.height)
                blockers.append((x1, y1, x2, y2))
        return blockers

    @staticmethod
    def _point_in_rect(x: float, y: float, rect: Tuple[float, float, float, float]) -> bool:
        """Verifica si un punto está dentro de un rectángulo."""
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _segment_hits_blocker(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        blockers: List[Tuple[float, float, float, float]],
    ) -> bool:
        """Aproxima intersección segmento-rectángulo por muestreo para evitar atravesar objetos."""
        sx, sy = start
        ex, ey = end

        # Muestreo cada ~5 px para detectar cruce en objetos
        dist = math.hypot(ex - sx, ey - sy)
        samples = max(2, int(dist / 5.0))

        for i in range(samples + 1):
            t = i / samples
            px = sx + (ex - sx) * t
            py = sy + (ey - sy) * t
            for rect in blockers:
                if self._point_in_rect(px, py, rect):
                    return True
        return False

    def _compute_safe_next_position(
        self,
        current: Tuple[float, float],
        target: Tuple[float, float],
        step: float,
        floor_level: int,
    ) -> Tuple[Tuple[float, float], bool]:
        """Calcula un movimiento seguro intentando desvíos si el camino directo está bloqueado.

        Returns:
            (next_position, blocked)
        """
        if self.building is None:
            return current, True

        cx, cy = current
        tx, ty = target
        dx = tx - cx
        dy = ty - cy
        dist = max(math.hypot(dx, dy), 1e-6)

        ux = dx / dist
        uy = dy / dist

        blockers = self._get_blocking_rects(floor_level)

        # Direcciones candidatas: directa, ejes y perpendiculares
        candidates = [
            (ux, uy),
            (math.copysign(1.0, ux) if abs(ux) > 1e-6 else 0.0, 0.0),
            (0.0, math.copysign(1.0, uy) if abs(uy) > 1e-6 else 0.0),
            (-uy, ux),
            (uy, -ux),
        ]

        floor = self.building.map_model.get_floor(floor_level)
        max_x = float(floor.width) if floor is not None else 2000.0
        max_y = float(floor.height) if floor is not None else 2000.0

        for vx, vy in candidates:
            mag = math.hypot(vx, vy)
            if mag < 1e-6:
                continue

            vx /= mag
            vy /= mag

            nx = cx + vx * step
            ny = cy + vy * step

            # Mantener dentro de límites del mapa
            nx = min(max(0.0, nx), max_x)
            ny = min(max(0.0, ny), max_y)

            if self._segment_hits_blocker((cx, cy), (nx, ny), blockers):
                continue

            return (nx, ny), False

        return current, True
    
    def initialize_simulation(self, map_model: MapModel) -> bool:
        """
        Inicializa una simulación con un mapa.
        
        Args:
            map_model: Modelo del mapa
            
        Returns:
            True si se inicializó exitosamente
        """
        try:
            self.building = Building(map_model=map_model)
            self.aco = ACO(building=self.building, map_model=map_model)
            self.current_time = 0.0
            self.is_running = False
            self._cache_map_geometry(map_model)
            return True
        except Exception as e:
            print(f"Error inicializando simulación: {e}")
            return False

    def _cache_map_geometry(self, map_model: MapModel) -> None:
        """Cachea geometría del mapa para cálculos de movimiento y congestión."""
        self.exit_targets = {}
        self.node_centers = {}

        for floor_level, floor in map_model.floors.items():
            for element_id, element in floor.elements.items():
                center_x = element.position[0] + element.width / 2
                center_y = element.position[1] + element.height / 2
                self.node_centers[element_id] = (center_x, center_y, floor_level)

                if element.element_type.value == "exit":
                    self.exit_targets[element_id] = (center_x, center_y, floor_level)

    def _nearest_exit_id(self, agent_x: float, agent_y: float, floor: int) -> Optional[int]:
        """Obtiene la salida más cercana para un agente."""
        candidates = [
            (eid, ex, ey)
            for eid, (ex, ey, efloor) in self.exit_targets.items()
            if efloor == floor
        ]
        if not candidates:
            return None

        nearest = min(candidates, key=lambda it: math.dist((agent_x, agent_y), (it[1], it[2])))
        return nearest[0]

    def _nearest_node_id(self, x: float, y: float, floor: int) -> Optional[int]:
        """Obtiene el nodo más cercano para estadísticas de ocupación."""
        candidates = [
            (nid, nx, ny)
            for nid, (nx, ny, nf) in self.node_centers.items()
            if nf == floor
        ]
        if not candidates:
            return None

        nearest = min(candidates, key=lambda it: math.dist((x, y), (it[1], it[2])))
        return nearest[0]

    def _update_node_occupancy(self) -> None:
        """Actualiza ocupación de nodos a partir de posiciones actuales de agentes."""
        if self.building is None:
            return

        # Reiniciar ocupaciones
        for occ in self.building.node_occupancy.values():
            occ.current_occupancy = 0
            occ.agents_in_node.clear()

        # Recalcular según posición
        for agent in self.building.agents.values():
            if agent.state == AgentState.EVACUATED:
                continue

            node_id = self._nearest_node_id(agent.position[0], agent.position[1], agent.floor)
            if node_id is None:
                continue

            occ = self.building.node_occupancy.get(node_id)
            if occ is None:
                continue

            occ.current_occupancy += 1
            occ.agents_in_node.append(agent.id)
    
    def start_simulation(self) -> bool:
        """Inicia la simulación"""
        if self.building is None:
            return False
        
        self.is_running = True
        self.current_time = 0.0
        return True
    
    def pause_simulation(self) -> None:
        """Pausa la simulación"""
        self.is_running = False
    
    def resume_simulation(self) -> None:
        """Reanuda la simulación"""
        if self.building is not None:
            self.is_running = True
    
    def stop_simulation(self) -> None:
        """Detiene la simulación"""
        self.is_running = False
        self.current_time = 0.0
    
    def update_simulation(self, delta_time: float) -> None:
        """
        Actualiza la simulación un paso temporal.
        
        Args:
            delta_time: Tiempo transcurrido en milisegundos
        """
        if not self.is_running or self.building is None:
            return
        
        # Convertir a segundos
        dt = delta_time / 1000.0 * self.simulation_speed
        self.current_time += dt
        self.building.update_time(dt)

        # Movimiento simple hacia la salida objetivo
        # Escala para hacer visible progreso en simulación por consola
        movement_scale = 45.0
        arrival_threshold = 12.0

        for agent in self.building.agents.values():
            if agent.state == AgentState.EVACUATED:
                continue

            # Asignar salida objetivo si no tiene
            if agent.target_exit is None:
                agent.target_exit = self._nearest_exit_id(agent.position[0], agent.position[1], agent.floor)

            if agent.target_exit is None or agent.target_exit not in self.exit_targets:
                agent.change_state(AgentState.BLOCKED)
                continue

            target_x, target_y, _ = self.exit_targets[agent.target_exit]
            current_x, current_y = agent.position
            dx = target_x - current_x
            dy = target_y - current_y
            dist = math.hypot(dx, dy)

            if dist <= arrival_threshold:
                agent.update_position((target_x, target_y))
                agent.evacuate(self.current_time)
                continue

            # Avanzar hacia destino
            step = max(agent.velocity * movement_scale * dt, 0.1)
            new_position, blocked = self._compute_safe_next_position(
                current=(current_x, current_y),
                target=(target_x, target_y),
                step=step,
                floor_level=agent.floor,
            )

            if blocked:
                agent.change_state(AgentState.WAITING)
                agent.increment_wait_time(dt)
            else:
                agent.update_position(new_position)
                agent.change_state(AgentState.WALKING)

        # Actualizar congestión/ocupación
        self._update_node_occupancy()
        
        # Detener si excede el tiempo máximo
        if self.current_time > self.max_time:
            self.is_running = False
    
    def add_agent(self, position_x: float, position_y: float, floor: int = 0) -> int:
        """
        Añade un agente a la simulación.
        
        Args:
            position_x: Posición X
            position_y: Posición Y
            floor: Piso
            
        Returns:
            ID del agente añadido
        """
        if self.building is None:
            raise RuntimeError("Simulación no inicializada")
        
        return self.building.add_agent((position_x, position_y), floor)
    
    def add_agents_from_zone(self, floor: int, zone_x: int, zone_y: int,
                            zone_width: int, zone_height: int, count: int) -> List[int]:
        """
        Añade múltiples agentes en una zona rectangular.
        
        Args:
            floor: Piso
            zone_x, zone_y: Posición de la zona
            zone_width, zone_height: Dimensiones de la zona
            count: Número de agentes a añadir
            
        Returns:
            Lista de IDs de agentes añadidos
        """
        if self.building is None:
            raise RuntimeError("Simulación no inicializada")
        
        agent_ids = []
        import random
        
        for _ in range(count):
            x = zone_x + random.randint(0, zone_width)
            y = zone_y + random.randint(0, zone_height)
            agent_id = self.building.add_agent((x, y), floor)
            agent_ids.append(agent_id)
        
        return agent_ids
    
    def activate_emergency(self, emergency_type: EmergencyType, 
                          start_time: Optional[float] = None) -> Emergency:
        """
        Activa una emergencia en la simulación.
        
        Args:
            emergency_type: Tipo de emergencia
            start_time: Tiempo de inicio (si None, comienza inmediatamente)
            
        Returns:
            Objeto Emergency creado
        """
        if start_time is None:
            start_time = self.current_time
        
        self.emergency = Emergency(emergency_type=emergency_type, start_time=start_time)
        self.emergency.activate()
        return self.emergency
    
    def get_evacuation_stats(self) -> dict:
        """Obtiene estadísticas de evacuación"""
        if self.building is None:
            return {}
        
        stats = self.building.get_evacuation_stats()
        stats['current_time'] = self.current_time
        stats['simulation_running'] = self.is_running
        return stats
    
    def get_all_agents_data(self) -> List[dict]:
        """Obtiene datos de todos los agentes"""
        if self.building is None:
            return []
        
        return [agent.to_dict() for agent in self.building.agents.values()]
    
    def set_simulation_speed(self, speed: float) -> None:
        """
        Establece la velocidad de simulación.
        
        Args:
            speed: Multiplicador de velocidad (1.0 = normal)
        """
        if speed > 0:
            self.simulation_speed = speed
    
    def __repr__(self) -> str:
        return f"SimulationController(running={self.is_running}, time={self.current_time:.1f}s)"
