import pygame
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QImage
import random

from core.map_model import (MapModel, Node, CELL_WALL, CELL_EMPTY, PREFIX_S, PREFIX_N, PREFIX_E, PREFIX_L)

# ── Colours ───────────────────────────────────────────────────────────────
C_BG        = (30, 30, 35)
C_EMPTY     = (50, 52, 58)
C_WALL      = (20, 20, 22)
C_GRID_LINE = (60, 62, 68)
C_NODE_S    = (70, 200, 100)
C_NODE_N    = (100, 160, 240)
C_NODE_E    = (240, 100, 80)
C_NODE_L    = (180, 80, 220)  # Morado para escaleras
C_CONN      = (220, 190, 60)
C_SEL       = (255, 255, 255)
C_TEXT_DARK = (10, 10, 10)

NODE_RADIUS = 15

class MapEditorWidget(QWidget):
    status_message = pyqtSignal(str)
    map_changed    = pyqtSignal()

    def __init__(self, model: MapModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.tool = "wall"
        self._painting = False
        self._paint_value = CELL_WALL
        
        self.current_floor = 0   # NUEVO: Estado del piso actual
        self.selected_node_id: str | None = None
        self.connect_src_id:   str | None = None
        self.hover_cell: tuple[int, int] | None = None

        self._offset_x = 0
        self._offset_y = 0
        self._zoom = 1.0
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_offset_start = (0, 0)

        self._moving_node_id: str | None = None
        self.active_ants: dict[int, str] = {}
        self._needs_map_emit = False

        pygame.init()
        self._surf: pygame.Surface | None = None
        self._font = None
        # self._timer = QTimer(self)
        # self._timer.timeout.connect(self._tick)
        # self._timer.start(33)

    def set_ants(self, ants_dict: dict):
        self.active_ants = ants_dict
        self.update()

    def set_tool(self, tool: str):
        self.tool = tool
        self.selected_node_id = None
        self.connect_src_id = None
        self.status_message.emit(f"Herramienta: {tool}")

    def set_model(self, model: MapModel):
        self.model = model
        self.current_floor = 0
        self._offset_x = self._offset_y = 0
        self._zoom = 1.0
        self.selected_node_id = self.connect_src_id = None
        self.update()

    def center_view(self):
        if self.model:
            cs = self._cell_size()
            mw, mh = self.model.width * cs, self.model.height * cs
            self._offset_x = (self.width()  - mw) // 2
            self._offset_y = (self.height() - mh) // 2
            self._zoom = 1.0

    def _cell_size(self) -> int: return max(4, int(self.model.cell_size * self._zoom))

    def _screen_to_cell(self, sx: int, sy: int) -> tuple[int, int]:
        cs = self._cell_size()
        return (sy - self._offset_y) // cs, (sx - self._offset_x) // cs

    def _cell_center(self, row: int, col: int) -> tuple[int, int]:
        cs = self._cell_size()
        return self._offset_x + col * cs + cs // 2, self._offset_y + row * cs + cs // 2

    def _ensure_surface(self):
        w, h = max(1, self.width()), max(1, self.height())
        if self._surf is None or self._surf.get_size() != (w, h): self._surf = pygame.Surface((w, h))
        if self._font is None: self._font = pygame.font.Font(None, 14)

    def _node_color(self, node: Node):
        p = node.prefix()
        if p == PREFIX_S: return C_NODE_S
        if p == PREFIX_N: return C_NODE_N
        if p == PREFIX_E: return C_NODE_E
        if p == PREFIX_L: return C_NODE_L
        return (200, 200, 200)

    def _tick(self): self.update()

    def _render(self):
        self._ensure_surface()
        surf = self._surf
        surf.fill(C_BG)
        if not self.model: return

        cs = self._cell_size()
        m = self.model
        f = self.current_floor

        # Dibujar Grilla de la planta actual
        for r in range(m.height):
            for c in range(m.width):
                x, y = self._offset_x + c * cs, self._offset_y + r * cs
                color = C_WALL if m.get_cell(f, r, c) == CELL_WALL else C_EMPTY
                pygame.draw.rect(surf, color, (x, y, cs, cs))
                pygame.draw.rect(surf, C_GRID_LINE, (x, y, cs, cs), 1)

        # Highlighting interactivo
        if self.hover_cell and self.tool in ("wall", "erase", "node_S", "node_N", "node_E", "node_L"):
            hr, hc = self.hover_cell
            if m.in_bounds(f, hr, hc):
                x, y = self._offset_x + hc * cs, self._offset_y + hr * cs
                hover_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                hover_surf.fill((180, 180, 255, 60))
                surf.blit(hover_surf, (x, y))

        # Dibujar conexiones (solo si pertenecen a nodos en la planta actual)
        for node in m.nodes.values():
            if node.floor != f: continue
            x1, y1 = self._cell_center(node.row, node.col)
            for conn_id in node.connections:
                if conn_id in m.nodes:
                    cn = m.nodes[conn_id]
                    if cn.floor == f: # Conexión en el mismo piso
                        x2, y2 = self._cell_center(cn.row, cn.col)
                        pygame.draw.line(surf, C_CONN, (x1, y1), (x2, y2), 2)
                        _draw_arrow(surf, C_CONN, (x1, y1), (x2, y2))

        # Línea de conexión pendiente
        if self.connect_src_id and self.connect_src_id in m.nodes:
            src = m.nodes[self.connect_src_id]
            if src.floor == f and self.hover_cell:
                hr, hc = self.hover_cell
                if m.in_bounds(f, hr, hc):
                    x1, y1 = self._cell_center(src.row, src.col)
                    x2, y2 = self._offset_x + hc * cs + cs // 2, self._offset_y + hr * cs + cs // 2
                    pygame.draw.line(surf, (200, 200, 60), (x1, y1), (x2, y2), 1)

        # Dibujar nodos en esta planta
        for node in m.nodes.values():
            if node.floor != f: continue
            x, y = self._cell_center(node.row, node.col)
            r = max(5, NODE_RADIUS - max(0, (20 - cs) // 2))
            pygame.draw.circle(surf, self._node_color(node), (x, y), r)
            
            # NUEVO: Indicador visual de escaleras que bajan/suben
            if node.prefix() == PREFIX_L:
                has_vertical_conn = any(m.nodes[c].floor != f for c in node.connections if c in m.nodes)
                if has_vertical_conn: pygame.draw.circle(surf, (255, 230, 0), (x, y), r - 6)

            if node.node_id in (self.selected_node_id, self.connect_src_id):
                pygame.draw.circle(surf, C_SEL, (x, y), r + 3, 2)
                
            if cs >= 14 and self._font:
                txt = self._font.render(node.node_id, True, C_TEXT_DARK)
                surf.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))

        # Dibujar hormigas (con dispersión)
        for ant_idx, node_id in self.active_ants.items():
            if node_id in m.nodes:
                node = m.nodes[node_id]
                if node.floor != f: continue # Solo dibuja hormigas si están en la planta actual
                x, y = self._cell_center(node.row, node.col)
                dibujo_x, dibujo_y = x + random.randint(-8, 8), y + random.randint(-8, 8)
                pygame.draw.circle(surf, (255, 140, 0), (dibujo_x, dibujo_y), 5)
                pygame.draw.circle(surf, (255, 255, 255), (dibujo_x, dibujo_y), 6, 1)

    def paintEvent(self, event):
        self._render()
        if self._surf is None: return
        try: raw = pygame.image.tobytes(self._surf, "RGB")
        except Exception: return
        w, h = self._surf.get_width(), self._surf.get_height()
        img = QImage(raw, w, h, w * 3, QImage.Format.Format_RGB888)
        p = QPainter(self)
        p.drawImage(0, 0, img)
        p.end()

    def mousePressEvent(self, event):
        sx, sy = int(event.position().x()), int(event.position().y())
        row, col = self._screen_to_cell(sx, sy)
        btn = event.button()
        f = self.current_floor

        if btn == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start, self._pan_offset_start = (sx, sy), (self._offset_x, self._offset_y)
            return

        if btn == Qt.MouseButton.RightButton:
            node = self.model.node_at(f, row, col)
            if node:
                self.model.remove_node(node.node_id)
                if self.selected_node_id == node.node_id: self.selected_node_id = None
                if self.connect_src_id == node.node_id: self.connect_src_id = None
                self.map_changed.emit()
                self.status_message.emit(f"Nodo {node.node_id} eliminado")
            return

        if btn != Qt.MouseButton.LeftButton: return
        
        node = self.model.node_at(f, row, col)

        if self.tool == "wall":
            if not node:
                self._painting, self._paint_value = True, CELL_WALL
                self.model.set_cell(f, row, col, CELL_WALL)
                self.map_changed.emit()
        elif self.tool == "erase":
            if not node:
                self._painting, self._paint_value = True, CELL_EMPTY
                self.model.set_cell(f, row, col, CELL_EMPTY)
                self.map_changed.emit()
        elif self.tool in ("node_S", "node_N", "node_E", "node_L"):
            prefix = {"node_S": PREFIX_S, "node_N": PREFIX_N, "node_E": PREFIX_E, "node_L": PREFIX_L}[self.tool]
            if not node:
                new_node = self.model.add_node(prefix, f, row, col)
                if new_node: 
                    self.map_changed.emit()
                    self.status_message.emit(f"Nodo {new_node.node_id} creado")
        elif self.tool == "connect":
            if node:
                if not self.connect_src_id: 
                    self.connect_src_id = node.node_id
                    self.status_message.emit(f"Conectando {node.node_id} -> Haz clic en el destino")
                else:
                    ok, reason = self.model.add_connection(self.connect_src_id, node.node_id)
                    if ok: 
                        self.map_changed.emit()
                        self.status_message.emit(f"¡Conexión exitosa a {node.node_id}!")
                    else: 
                        self.status_message.emit(reason)
                    self.connect_src_id = None
            else: 
                self.connect_src_id = None
        elif self.tool == "select":
            self.selected_node_id = node.node_id if node else None
            if node: self.status_message.emit(f"Seleccionado: {node.node_id} | Planta: {node.floor} | Conecta a: {node.connections}")
        elif self.tool == "move":
            if node:
                self._moving_node_id = node.node_id
                self.status_message.emit(f"Moviendo {node.node_id}... (Arrastra y suelta)")
            else:
                self._moving_node_id = None

        self.update()


    def mouseMoveEvent(self, event):
        sx, sy = int(event.position().x()), int(event.position().y())
        row, col = self._screen_to_cell(sx, sy)
        new_hover = (row, col)

        needs_update = False

        if self.hover_cell != new_hover:
            self.hover_cell = new_hover
            needs_update = True

        if self._panning:
            self._offset_x = self._pan_offset_start[0] + (sx - self._pan_start[0])
            self._offset_y = self._pan_offset_start[1] + (sy - self._pan_start[1])
            if needs_update: self.update()
            return

        # Pintar paredes arrastrando
        if self._painting and self.model.in_bounds(self.current_floor, row, col):
            if not self.model.node_at(self.current_floor, row, col):
                if self.model.get_cell(self.current_floor, row, col) != self._paint_value:
                    self.model.set_cell(self.current_floor, row, col, self._paint_value)
                    self._needs_map_emit = True
                    needs_update = True

        # Arrastrar nodo activo
        if self._moving_node_id and self.model.in_bounds(self.current_floor, row, col):
            if self.model.move_node(self._moving_node_id, self.current_floor, row, col):
                self._needs_map_emit = True
                needs_update = True

        if needs_update:
            self.update()


    def mouseReleaseEvent(self, event): 
        self._painting = False
        self._panning = False
        
        # Feedback al soltar el nodo
        if self._moving_node_id:
            self.status_message.emit(f"Nodo {self._moving_node_id} soltado en nueva posición")
            
        self._moving_node_id = None
        
        # Una vez que soltamos el ratón, AHORA SÍ recalculamos matemáticas y tablas
        if getattr(self, "_needs_map_emit", False):
            self.map_changed.emit()
            self._needs_map_emit = False
    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        sx, sy = int(event.position().x()), int(event.position().y())
        self._offset_x = int(sx - (sx - self._offset_x) * factor)
        self._offset_y = int(sy - (sy - self._offset_y) * factor)
        self._zoom = max(0.2, min(5.0, self._zoom * factor))
        self.update()
    def resizeEvent(self, event): self._surf = None; super().resizeEvent(event); self.update()

def _draw_arrow(surf, color, p1, p2, size=6):
    import math
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1: return
    ux, uy = dx / length, dy / length
    tx, ty = p2[0] - ux * 12, p2[1] - uy * 12
    lx, ly, rx, ry = tx - uy * size, ty + ux * size, tx + uy * size, ty - ux * size
    pygame.draw.polygon(surf, color, [(int(p2[0]), int(p2[1])), (int(lx), int(ly)), (int(rx), int(ry))])