"""
Conway's Game of Life — Versión Unificada (Todo en PyQt6)
- Navegación: Clic derecho para arrastrar la cámara.
- Zoom: Rueda del ratón para acercar/alejar la vista al cursor.
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QSlider, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen


# ── Paleta de colores (Escala de Grises) ──────────────────────────────────────
BG_DARK   = "#222222"
BG_MID    = "#2d2d2d"
BG_PANEL  = "#3a3a3a"
ACCENT    = "#777777"
ACCENT2   = "#dddddd"
TEXT      = "#eeeeee"
TEXT_DIM  = "#aaaaaa"
CELL_ALIVE = QColor(220, 220, 220)
CELL_DEAD  = QColor(34, 34, 34)
GRID_COLOR = QColor(70, 70, 70)


# ── Lógica del juego (NumPy) ──────────────────────────────────────────────────
class GameOfLife:
    def __init__(self, rows: int, cols: int, boundary: str = "toroid"):
        self.rows = rows
        self.cols = cols
        self.boundary = boundary
        self.grid = np.zeros((rows, cols), dtype=np.uint8)
        self.generation = 0
        self.population = 0

    def randomize(self, density: float = 0.3):
        self.grid = (np.random.random((self.rows, self.cols)) < density).astype(np.uint8)
        self.generation = 0
        self._update_pop()

    def clear(self):
        self.grid[:] = 0
        self.generation = 0
        self.population = 0

    def set_cell(self, r: int, c: int, state: int):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.grid[r, c] = state
            self._update_pop()

    def step(self):
        # Matriz vacía donde acumularemos cuántos vecinos vivos tiene cada celda
        neighbors = np.zeros((self.rows, self.cols), dtype=np.int32)

        # Si el borde es muerto, creamos una versión del mapa con un marco de ceros (0).
        # Así, las celdas de las orillas pueden buscar vecinos afuera sin dar error.
        if self.boundary == "dead":
            padded_grid = np.pad(self.grid, pad_width=1, mode='constant', constant_values=0)

        # Exploramos los 8 desplazamientos posibles alrededor de una celda
        for dr in [-1, 0, 1]:      # dr: Desplazamiento en la fila (Arriba, Centro, Abajo)
            for dc in [-1, 0, 1]:  # dc: Desplazamiento en la columna (Izq, Centro, Der)
                
                # Ignoramos el desplazamiento (0, 0) porque es la celda misma, no un vecino
                if dr == 0 and dc == 0:
                    continue
                
                # ── CASO A: Toroide (Modo Pac-Man) ──
                if self.boundary == "toroid":
                    # np.roll "empuja" toda la matriz en la dirección que le digamos.
                    # Lo que se sale por un borde, entra mágicamente por el borde opuesto.
                    shifted_grid = np.roll(self.grid, shift=dr, axis=0) # Empuja verticalmente
                    shifted_grid = np.roll(shifted_grid, shift=dc, axis=1) # Empuja horizontalmente
                    
                    neighbors += shifted_grid

                # ── CASO B: Borde Muerto (Paredes vacías) ──
                else: 
                    # Como nuestra matriz padded_grid es más grande (tiene un marco extra),
                    # tomamos un "recorte" del tamaño exacto de la pantalla, pero desplazado.
                    row_start = 1 + dr
                    row_end   = row_start + self.rows
                    col_start = 1 + dc
                    col_end   = col_start + self.cols
                    
                    # Sumamos ese recorte desplazado a nuestro conteo de vecinos
                    neighbors += padded_grid[row_start:row_end, col_start:col_end]

        # ── APLICAR LAS REGLAS DE CONWAY ──
        # Regla 1: Una celda muerta (0) con exactamente 3 vecinos, NACE.
        born = (neighbors == 3) & (self.grid == 0)
        
        # Regla 2: Una celda viva (1) con 2 o 3 vecinos, SOBREVIVE.
        survive = ((neighbors == 2) | (neighbors == 3)) & (self.grid == 1)
        
        # El nuevo estado de la malla será la unión de las que nacen y las que sobreviven.
        # Todo lo demás (vecinos < 2 o vecinos > 3) muere por soledad o sobrepoblación.
        self.grid = (born | survive).astype(np.uint8)
        
        self.generation += 1
        self._update_pop()

    def _update_pop(self):
        self.population = int(self.grid.sum())


# ── Widget del Lienzo (Cámara interactiva y Zoom) ─────────────────────────────
class GridWidget(QWidget):
    def __init__(self, game_logic):
        super().__init__()
        self.game = game_logic
        self.cell_size = 12.0 # Usamos flotantes para un zoom suave
        self.show_grid = True
        
        self.drawing_state = None 
        self.offset = QPointF(0, 0)
        self.last_pan_pos = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True) 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), CELL_DEAD) 

        painter.save()
        painter.translate(self.offset)

        # Dibujar celdas
        brush = QBrush(CELL_ALIVE)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.grid[r, c]:
                    # QRectF permite dibujar usando decimales, evitando huecos al hacer zoom
                    rect = QRectF(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                    painter.drawRect(rect)

        # Dibujar líneas de cuadrícula
        if self.show_grid and self.cell_size >= 4.0:
            pen = QPen(GRID_COLOR)
            pen.setWidth(1)
            # Para zoom de alto nivel, evitar que la línea escale su grosor usando Cosmetic pen
            pen.setCosmetic(True) 
            painter.setPen(pen)
            
            grid_w = self.game.cols * self.cell_size
            grid_h = self.game.rows * self.cell_size

            for c in range(self.game.cols + 1):
                painter.drawLine(QPointF(c * self.cell_size, 0), QPointF(c * self.cell_size, grid_h))
            for r in range(self.game.rows + 1):
                painter.drawLine(QPointF(0, r * self.cell_size), QPointF(grid_w, r * self.cell_size))
                
        painter.restore()

    def wheelEvent(self, event):
        """Maneja el zoom con la rueda del ratón, centrado en el cursor."""
        zoom_factor = 1.15 # Qué tan rápido se hace el zoom
        
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
            
        old_size = self.cell_size
        # Limitamos el zoom para que no colapse ni explote la memoria (min 2px, max 150px)
        new_size = max(2.0, min(old_size * zoom_factor, 150.0))
        
        if old_size == new_size:
            return
            
        # Matemáticas para hacer el zoom hacia donde está el cursor
        mouse_pos = event.position()
        rel_pos = mouse_pos - self.offset
        
        new_rel_pos = rel_pos * (new_size / old_size)
        self.offset = mouse_pos - new_rel_pos
        self.cell_size = new_size
        
        self.update()

    def _handle_draw(self, pos):
        c = int((pos.x() - self.offset.x()) // self.cell_size)
        r = int((pos.y() - self.offset.y()) // self.cell_size)
        
        if 0 <= r < self.game.rows and 0 <= c < self.game.cols:
            if self.drawing_state is None:
                self.drawing_state = 1 if self.game.grid[r, c] == 0 else 0
            self.game.set_cell(r, c, self.drawing_state)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_draw(event.position())
        elif event.button() == Qt.MouseButton.RightButton:
            self.last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_draw(event.position())
        elif event.buttons() & Qt.MouseButton.RightButton and self.last_pan_pos:
            delta = event.position() - self.last_pan_pos
            self.offset += delta
            self.last_pan_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing_state = None
        elif event.button() == Qt.MouseButton.RightButton:
            self.last_pan_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)


# ── Ventana Principal Unificada ───────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conway's Game of Life")
        self.setMinimumSize(1000, 650)
        self._apply_dark_theme()
        
        self.game = GameOfLife(80, 120, "toroid")
        self.is_playing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)

        self._build_ui()
        QTimer.singleShot(50, self._center_view)

    def _apply_dark_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {BG_DARK}; color: {TEXT}; font-family: 'Segoe UI', sans-serif; }}
            QGroupBox {{ background-color: {BG_MID}; border: 1px solid {BG_PANEL}; border-radius: 8px; margin-top: 15px; padding: 15px 10px 10px 10px; font-weight: bold; color: {ACCENT2}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; background-color: {BG_DARK}; }}
            QLabel {{ background: transparent; }}
            QSpinBox, QComboBox {{ background-color: {BG_PANEL}; border: 1px solid #555; border-radius: 4px; padding: 4px 8px; min-height: 26px; }}
            QSlider::groove:horizontal {{ background: {BG_PANEL}; height: 6px; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {ACCENT2}; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
            QPushButton {{ background: {BG_PANEL}; border: 1px solid #555; border-radius: 4px; padding: 8px; font-weight: bold; }}
            QPushButton:hover {{ background: {ACCENT}; color: {BG_DARK}; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid {ACCENT2}; background: {BG_PANEL}; }}
            QCheckBox::indicator:checked {{ background: {ACCENT2}; }}
        """)

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # ── PANEL LATERAL ──
        side_panel = QWidget()
        side_panel.setFixedWidth(300)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(10)

        title = QLabel("Game of Life")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        side_layout.addWidget(title)

        ctrl_layout = QHBoxLayout()
        self.btn_play = QPushButton("INICIAR")
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_step = QPushButton("Paso")
        self.btn_step.clicked.connect(self._step_once)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_step)
        side_layout.addLayout(ctrl_layout)

        action_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.clicked.connect(self._clear_grid)
        self.btn_random = QPushButton("Aleatorio")
        self.btn_random.clicked.connect(self._randomize_grid)
        action_layout.addWidget(self.btn_clear)
        action_layout.addWidget(self.btn_random)
        side_layout.addLayout(action_layout)

        # Info de estado
        self.lbl_info = QLabel("Gen: 0  |  Pob: 0")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; margin: 5px 0;")
        side_layout.addWidget(self.lbl_info)

        # Configuración de malla
        grp_grid = QGroupBox("Tamaño de la Malla")
        gl = QVBoxLayout(grp_grid)
        
        row_r = QHBoxLayout()
        row_r.addWidget(QLabel("Filas:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(10, 500)
        self.spin_rows.setValue(80)
        row_r.addWidget(self.spin_rows)
        gl.addLayout(row_r)

        row_c = QHBoxLayout()
        row_c.addWidget(QLabel("Columnas:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(10, 800)
        self.spin_cols.setValue(120)
        row_c.addWidget(self.spin_cols)
        gl.addLayout(row_c)

        btn_apply = QPushButton("Aplicar Tamaño y Centrar")
        btn_apply.clicked.connect(self._apply_config)
        gl.addWidget(btn_apply)
        side_layout.addWidget(grp_grid)

        # Opciones
        grp_opts = QGroupBox("Configuración de Reglas")
        ol = QVBoxLayout(grp_opts)
        
        self.combo_border = QComboBox()
        self.combo_border.addItem("Frontera: Toroide", "toroid")
        self.combo_border.addItem("Frontera: Borde Muerto", "dead")
        self.combo_border.currentIndexChanged.connect(lambda: setattr(self.game, 'boundary', self.combo_border.currentData()))
        ol.addWidget(self.combo_border)

        self.chk_grid = QCheckBox("Mostrar cuadrícula")
        self.chk_grid.setChecked(True)
        self.chk_grid.stateChanged.connect(self._update_canvas_settings)
        ol.addWidget(self.chk_grid)
        
        btn_center = QPushButton("Centrar Vista (Cámara)")
        btn_center.clicked.connect(self._center_view)
        ol.addWidget(btn_center)
        side_layout.addWidget(grp_opts)

        # Velocidad
        grp_speed = QGroupBox("Velocidad (FPS)")
        sl = QVBoxLayout(grp_speed)
        self.lbl_fps = QLabel("15 FPS")
        sl.addWidget(self.lbl_fps)
        self.slider_fps = QSlider(Qt.Orientation.Horizontal)
        self.slider_fps.setRange(1, 60)
        self.slider_fps.setValue(15)
        self.slider_fps.valueChanged.connect(self._update_speed)
        sl.addWidget(self.slider_fps)
        side_layout.addWidget(grp_speed)

        side_layout.addStretch()
        
        hint = QLabel("• Clic Izquierdo: Dibujar celdas\n• Clic Derecho: Arrastrar cámara\n• Rueda del Ratón: Zoom")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignLeft)
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; margin-left: 5px;")
        side_layout.addWidget(hint)

        # ── LIENZO PRINCIPAL ──
        self.canvas = GridWidget(self.game)
        main_layout.addWidget(side_panel)
        main_layout.addWidget(self.canvas)

    def _apply_config(self):
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()
        
        if self.is_playing:
            self._toggle_play()

        self.game = GameOfLife(rows, cols, self.combo_border.currentData())
        self.canvas.game = self.game
        self._update_canvas_settings()
        self._center_view()
        self._update_labels()

    def _center_view(self):
        grid_w = self.game.cols * self.canvas.cell_size
        grid_h = self.game.rows * self.canvas.cell_size
        
        x = (self.canvas.width() - grid_w) / 2
        y = (self.canvas.height() - grid_h) / 2
        
        self.canvas.offset = QPointF(x, y)
        self.canvas.update()

    def _update_canvas_settings(self):
        self.canvas.show_grid = self.chk_grid.isChecked()
        self.canvas.update()

    def _update_speed(self, fps):
        self.lbl_fps.setText(f"{fps} FPS")
        if self.is_playing:
            self.timer.start(1000 // fps)

    def _toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("PAUSAR")
            self.timer.start(1000 // self.slider_fps.value())
        else:
            self.btn_play.setText("INICIAR")
            self.timer.stop()

    def _step_once(self):
        if self.is_playing:
            self._toggle_play()
        self._next_frame()

    def _clear_grid(self):
        self.game.clear()
        self.canvas.update()
        self._update_labels()

    def _randomize_grid(self):
        self.game.randomize(0.3)
        self.canvas.update()
        self._update_labels()

    def _next_frame(self):
        self.game.step()
        self.canvas.update()
        self._update_labels()

    def _update_labels(self):
        self.lbl_info.setText(f"Gen: {self.game.generation:,}  |  Pob: {self.game.population:,}")


# ── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())