"""
Pygame map editor embedded inside a PyQt6 QWidget.
Handles drawing the grid, nodes, connections, and user interactions.
"""
import random

import pygame
import sys
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QImage

from core.map_model import (
    MapModel, Node,
    CELL_WALL, CELL_EMPTY,
    PREFIX_S, PREFIX_N, PREFIX_E,
)

# ── Colours ───────────────────────────────────────────────────────────────
C_BG        = (30, 30, 35)
C_EMPTY     = (50, 52, 58)
C_WALL      = (20, 20, 22)
C_GRID_LINE = (60, 62, 68)
C_NODE_S    = (70, 200, 100)
C_NODE_N    = (100, 160, 240)
C_NODE_E    = (240, 100, 80)
C_CONN      = (220, 190, 60)
C_SEL       = (255, 255, 255)
C_HOVER     = (180, 180, 255, 80)
C_TEXT      = (230, 230, 230)
C_TEXT_DARK = (10, 10, 10)

NODE_RADIUS = 15
FONT_SIZE   = 20


class MapEditorWidget(QWidget):
    """Embeds a pygame surface inside Qt and handles all map editing."""

    status_message = pyqtSignal(str)
    map_changed    = pyqtSignal()

    def __init__(self, model: MapModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Tool state
        self.tool = "wall"          # "wall", "erase", "node_S", "node_N", "node_E", "connect", "move", "select"
        self._painting = False      # left-button drag for wall/erase
        self._paint_value = CELL_WALL

        # Selection / connection
        self.selected_node_id: str | None = None
        self.connect_src_id:   str | None = None
        self.hover_cell: tuple[int, int] | None = None   # (row, col)

        # Pan / zoom
        self._offset_x = 0
        self._offset_y = 0
        self._zoom = 1.0
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_offset_start = (0, 0)

        # Move node drag
        self._moving_node_id: str | None = None
        self.active_ants: dict[int, str] = {}  # ant_id → node_id

        # Pygame
        pygame.init()
        self._surf: pygame.Surface | None = None
        self._font = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)   # ~30 fps

    # ── Public ───────────────────────────────────────────────────────────────

    def set_tool(self, tool: str):
        self.tool = tool
        self.selected_node_id = None
        self.connect_src_id = None
        self.status_message.emit(f"Herramienta: {tool}")

    def set_model(self, model: MapModel):
        self.model = model
        self._offset_x = 0
        self._offset_y = 0
        self._zoom = 1.0
        self.selected_node_id = None
        self.connect_src_id = None
        self.update()

    def set_ants(self, ants_dict: dict):
        self.active_ants = ants_dict
        self.update()  # Forzar a redibujar el mapa inmediatamente

    def center_view(self):
        if self.model:
            cs = self.model.cell_size
            mw = self.model.width  * cs
            mh = self.model.height * cs
            self._offset_x = (self.width()  - mw) // 2
            self._offset_y = (self.height() - mh) // 2
            self._zoom = 1.0

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _cell_size(self) -> int:
        return max(4, int(self.model.cell_size * self._zoom))

    def _screen_to_cell(self, sx: int, sy: int) -> tuple[int, int]:
        cs = self._cell_size()
        col = (sx - self._offset_x) // cs
        row = (sy - self._offset_y) // cs
        return row, col

    def _cell_center(self, row: int, col: int) -> tuple[int, int]:
        cs = self._cell_size()
        x = self._offset_x + col * cs + cs // 2
        y = self._offset_y + row * cs + cs // 2
        return x, y

    def _ensure_surface(self):
        w, h = max(1, self.width()), max(1, self.height())
        if self._surf is None or self._surf.get_size() != (w, h):
            self._surf = pygame.Surface((w, h))
        if self._font is None:
            self._font = pygame.font.Font(None, 14)  # 14px — works on all DPI scales

    def _node_color(self, node: Node):
        p = node.prefix()
        if p == PREFIX_S:
            return C_NODE_S
        if p == PREFIX_N:
            return C_NODE_N
        if p == PREFIX_E:
            return C_NODE_E
        return (200, 200, 200)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _tick(self):
        self.update()  # triggers paintEvent which calls _render()

    def _render(self):
        self._ensure_surface()
        surf = self._surf
        surf.fill(C_BG)

        if not self.model:
            return

        cs = self._cell_size()
        m = self.model

        # Draw grid cells
        for r in range(m.height):
            for c in range(m.width):
                x = self._offset_x + c * cs
                y = self._offset_y + r * cs
                cell = m.get_cell(r, c)
                color = C_WALL if cell == CELL_WALL else C_EMPTY
                pygame.draw.rect(surf, color, (x, y, cs, cs))
                pygame.draw.rect(surf, C_GRID_LINE, (x, y, cs, cs), 1)

        # Hover highlight
        if self.hover_cell and self.tool in ("wall", "erase", "node_S", "node_N", "node_E"):
            hr, hc = self.hover_cell
            if m.in_bounds(hr, hc):
                x = self._offset_x + hc * cs
                y = self._offset_y + hr * cs
                hover_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                hover_surf.fill((180, 180, 255, 60))
                surf.blit(hover_surf, (x, y))

        # Draw connections
        for node in m.nodes.values():
            x1, y1 = self._cell_center(node.row, node.col)
            for conn_id in node.connections:
                if conn_id in m.nodes:
                    cn = m.nodes[conn_id]
                    x2, y2 = self._cell_center(cn.row, cn.col)
                    pygame.draw.line(surf, C_CONN, (x1, y1), (x2, y2), 2)
                    # Arrow head
                    _draw_arrow(surf, C_CONN, (x1, y1), (x2, y2))

        # Pending connection line
        if self.connect_src_id and self.connect_src_id in m.nodes:
            src = m.nodes[self.connect_src_id]
            x1, y1 = self._cell_center(src.row, src.col)
            if self.hover_cell:
                hr, hc = self.hover_cell
                if m.in_bounds(hr, hc):
                    x2 = self._offset_x + hc * cs + cs // 2
                    y2 = self._offset_y + hr * cs + cs // 2
                    pygame.draw.line(surf, (200, 200, 60), (x1, y1), (x2, y2), 1)

        # Draw nodes
        for node in m.nodes.values():
            x, y = self._cell_center(node.row, node.col)
            color = self._node_color(node)
            r = max(5, NODE_RADIUS - max(0, (20 - cs) // 2))
            pygame.draw.circle(surf, color, (x, y), r)
            # Selection ring
            if node.node_id == self.selected_node_id or node.node_id == self.connect_src_id:
                pygame.draw.circle(surf, C_SEL, (x, y), r + 3, 2)
            # Label
            if cs >= 14 and self._font:
                label = node.node_id
                txt = self._font.render(label, True, C_TEXT_DARK)
                surf.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))

        # Draw active ants
        for ant_idx, node_id in self.active_ants.items():
            if node_id in m.nodes:
                node = m.nodes[node_id]
                x, y = self._cell_center(node.row, node.col)
                
                # SOLUCIÓN: Le damos un pequeño desplazamiento aleatorio (offset) 
                # a cada hormiga. Así, si hay 5 en el mismo nodo, se verán 
                # como un enjambre alrededor del centro, no una sola bola.
                offset_x = random.randint(-8, 8)
                offset_y = random.randint(-8, 8)
                
                dibujo_x = x + offset_x
                dibujo_y = y + offset_y
                
                # Dibujamos una pequeña hormiguita naranja con borde blanco
                pygame.draw.circle(surf, (255, 140, 0), (dibujo_x, dibujo_y), 5)
                pygame.draw.circle(surf, (255, 255, 255), (dibujo_x, dibujo_y), 6, 1)

    def paintEvent(self, event):
        # Render into surface first (may recreate on resize)
        self._render()
        if self._surf is None:
            return
        try:
            raw = pygame.image.tobytes(self._surf, "RGB")
        except Exception:
            return
        w, h = self._surf.get_width(), self._surf.get_height()
        
        bytes_per_line = w * 3  
        
        img = QImage(raw, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = QPainter(self)
        p.drawImage(0, 0, img)
        p.end()

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        sx, sy = event.position().x(), event.position().y()
        sx, sy = int(sx), int(sy)
        row, col = self._screen_to_cell(sx, sy)
        btn = event.button()

        if btn == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = (sx, sy)
            self._pan_offset_start = (self._offset_x, self._offset_y)
            return

        if btn == Qt.MouseButton.RightButton:
            # Right-click: remove node or connection at cell
            node = self.model.node_at(row, col)
            if node:
                self.model.remove_node(node.node_id)
                if self.selected_node_id == node.node_id:
                    self.selected_node_id = None
                if self.connect_src_id == node.node_id:
                    self.connect_src_id = None
                self.map_changed.emit()
                self.status_message.emit(f"Nodo {node.node_id} eliminado")
            return

        if btn != Qt.MouseButton.LeftButton:
            return

        node = self.model.node_at(row, col)

        if self.tool == "wall":
            if node is None:
                self._painting = True
                self._paint_value = CELL_WALL
                self.model.set_cell(row, col, CELL_WALL)
                self.map_changed.emit()

        elif self.tool == "erase":
            if node is None:
                self._painting = True
                self._paint_value = CELL_EMPTY
                self.model.set_cell(row, col, CELL_EMPTY)
                self.map_changed.emit()

        elif self.tool in ("node_S", "node_N", "node_E"):
            prefix = {"node_S": PREFIX_S, "node_N": PREFIX_N, "node_E": PREFIX_E}[self.tool]
            if node:
                self.status_message.emit(f"Celda ocupada por {node.node_id}")
            else:
                new_node = self.model.add_node(prefix, row, col)
                if new_node:
                    self.map_changed.emit()
                    self.status_message.emit(f"Nodo {new_node.node_id} añadido en ({row},{col})")

        elif self.tool == "connect":
            if node:
                if self.connect_src_id is None:
                    self.connect_src_id = node.node_id
                    self.status_message.emit(f"Origen: {node.node_id} — haz clic en el nodo destino")
                else:
                    ok, reason = self.model.add_connection(self.connect_src_id, node.node_id)
                    if ok:
                        self.map_changed.emit()
                        self.status_message.emit(f"Conexión: {self.connect_src_id} → {node.node_id}")
                    else:
                        self.status_message.emit(f"No se puede conectar: {reason}")
                    self.connect_src_id = None
            else:
                self.connect_src_id = None

        elif self.tool == "select":
            if node:
                self.selected_node_id = node.node_id
                self.status_message.emit(f"Seleccionado: {node.node_id}  pos=({node.row},{node.col})  conn={node.connections}")
            else:
                self.selected_node_id = None

        elif self.tool == "move":
            if node:
                self._moving_node_id = node.node_id
            else:
                self._moving_node_id = None

    def mouseMoveEvent(self, event):
        sx, sy = int(event.position().x()), int(event.position().y())
        row, col = self._screen_to_cell(sx, sy)
        self.hover_cell = (row, col)

        if self._panning:
            dx = sx - self._pan_start[0]
            dy = sy - self._pan_start[1]
            self._offset_x = self._pan_offset_start[0] + dx
            self._offset_y = self._pan_offset_start[1] + dy
            return

        if self._painting and self.model.in_bounds(row, col):
            if self.model.node_at(row, col) is None:
                self.model.set_cell(row, col, self._paint_value)
                self.map_changed.emit()

        if self._moving_node_id:
            if self.model.in_bounds(row, col):
                self.model.move_node(self._moving_node_id, row, col)
                self.map_changed.emit()

    def mouseReleaseEvent(self, event):
        self._painting = False
        self._panning = False
        self._moving_node_id = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        sx, sy = int(event.position().x()), int(event.position().y())
        # Zoom toward cursor
        self._offset_x = int(sx - (sx - self._offset_x) * factor)
        self._offset_y = int(sy - (sy - self._offset_y) * factor)
        self._zoom = max(0.2, min(5.0, self._zoom * factor))

    def resizeEvent(self, event):
        self._surf = None   # force recreate on next paint
        super().resizeEvent(event)
        self.update()


def _draw_arrow(surf, color, p1, p2, size=6):
    """Draw a small arrowhead at p2 pointing from p1."""
    import math
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    # Tip
    tx, ty = p2[0] - ux * 12, p2[1] - uy * 12
    lx = tx - uy * size
    ly = ty + ux * size
    rx = tx + uy * size
    ry = ty - ux * size
    pygame.draw.polygon(surf, color, [(int(p2[0]), int(p2[1])), (int(lx), int(ly)), (int(rx), int(ry))])
