"""
Panel that runs the ACO path-finding algorithm in a background thread
and shows live progress to the user.
"""
import threading
from PyQt6 import QtWidgets
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from core.aco import ACOSolver
from core.map_model import MapModel


class _ACOSignals(QObject):
    iteration = pyqtSignal(int, list, float, object, list)
    done      = pyqtSignal(list, float)
    step      = pyqtSignal(dict)


class ACOPanel(QWidget):
    ant_step_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model: MapModel | None = None
        self._solver: ACOSolver | None = None
        self._signals = _ACOSignals()
        self._signals.iteration.connect(self._on_iteration)
        self._signals.done.connect(self._on_done)
        self._signals.step.connect(self.ant_step_signal.emit)
        self._thread: threading.Thread | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        # ── Parameters ───────────────────────────────────────────────────
        params_box = QtWidgets.QGroupBox("Parámetros ACO")
        params_box.setStyleSheet(
                "QGroupBox { font-weight: 600; border: 1px solid #374151; border-radius: 6px; margin-top: 20px; padding-top: 6px; }"
                "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            )
        form = QtWidgets.QFormLayout(params_box)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin_iter   = QtWidgets.QSpinBox();        self.spin_iter.setRange(1, 500);    self.spin_iter.setSingleStep(10);    self.spin_iter.setValue(5)
        self.spin_ants   = QtWidgets.QSpinBox();        self.spin_ants.setRange(0, 2000);    self.spin_ants.setSingleStep(50);    self.spin_ants.setValue(100)
        self.dspin_rho   = QtWidgets.QDoubleSpinBox();  self.dspin_rho.setRange(0.01, 1.0); self.dspin_rho.setSingleStep(0.05); self.dspin_rho.setValue(0.2)
        self.dspin_Q     = QtWidgets.QDoubleSpinBox();  self.dspin_Q.setRange(0.1, 100.0);  self.dspin_Q.setSingleStep(0.5);   self.dspin_Q.setValue(1.0)
        self.dspin_alpha = QtWidgets.QDoubleSpinBox();  self.dspin_alpha.setRange(0.1, 10.0); self.dspin_alpha.setSingleStep(0.1); self.dspin_alpha.setValue(1.5)
        self.dspin_beta  = QtWidgets.QDoubleSpinBox();  self.dspin_beta.setRange(0.1, 10.0);  self.dspin_beta.setSingleStep(0.1);  self.dspin_beta.setValue(2.0)

        form.addRow("Iteraciones:", self.spin_iter)
        form.addRow("Hormigas (0=auto):", self.spin_ants)
        form.addRow("Evaporación ρ:", self.dspin_rho)
        form.addRow("Depósito Q:", self.dspin_Q)
        form.addRow("Peso feromona α:", self.dspin_alpha)
        form.addRow("Peso heurística β:", self.dspin_beta)
        root.addWidget(params_box)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.btn_run  = QPushButton("▶ Ejecutar ACO")
        self.btn_stop = QPushButton("■ Detener")
        self.btn_stop.setEnabled(False)
        self.btn_run.clicked.connect(self._run)
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_run)
        btn_row.addWidget(self.btn_stop)
        root.addLayout(btn_row)

        # ── Status ────────────────────────────────────────────────────────
        self.lbl_status = QLabel("Listo. Construye el mapa y presiona Ejecutar.")
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)

        # ── Splitter: matrix + log ────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Distance matrix display (N-N only, for reference)
        mat_box = QGroupBox("Matriz N-N (distancias entre nodos de conexión)")
        mat_lay = QVBoxLayout(mat_box)
        self.matrix_table = QTableWidget()
        self.matrix_table.setFont(QFont("Courier New", 8))
        self.matrix_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        mat_lay.addWidget(self.matrix_table)
        splitter.addWidget(mat_box)

        # NUEVO: Pheromone matrix display
        phero_box = QGroupBox("Matriz de Feromonas")
        phero_lay = QVBoxLayout(phero_box)
        self.phero_table = QTableWidget()
        self.phero_table.setFont(QFont("Courier New", 8))
        self.phero_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        phero_lay.addWidget(self.phero_table)
        splitter.addWidget(phero_box)

        # Log
        log_box = QGroupBox("Log de ejecución")
        log_lay = QVBoxLayout(log_box)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 15))
        log_lay.addWidget(self.log_text)
        splitter.addWidget(log_box)

        splitter.setSizes([150, 150, 200])
        root.addWidget(splitter, 1)

    def set_model(self, model: MapModel):
        self._model = model
        self._refresh_matrix()

    def _refresh_matrix(self):
        if not self._model:
            return
        labels, mat = self._model.build_adjacency_matrix()
        if len(labels) == 0:
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            return
        self._fill_table(self.matrix_table, labels, mat)

    def _fill_table(self, table: QTableWidget, labels: list, mat: np.ndarray):
        n = len(labels)
        
        # 1. Apagamos el redibujado visual para que PyQt no se asfixie
        table.setUpdatesEnabled(False)
        
        # Solo reconfiguramos encabezados si cambió el número de nodos
        if table.rowCount() != n:
            table.setRowCount(n)
            table.setColumnCount(n)
            table.setHorizontalHeaderLabels(labels)
            table.setVerticalHeaderLabels(labels)
            
            # 2. QUITAMOS el lentísimo ResizeToContents y usamos tamaños fijos
            table.horizontalHeader().setDefaultSectionSize(55)
            table.verticalHeader().setDefaultSectionSize(25)

        # 3. Llenamos los datos reciclando celdas
        for i in range(n):
            for j in range(n):
                v = mat[i][j]
                if np.isinf(v):
                    text = "∞"
                elif v == 0:
                    text = "0"
                else:
                    text = f"{v:.2f}"
                
                item = table.item(i, j)
                if item is None:
                    # Si la celda no existe, la creamos
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(i, j, item)
                else:
                    # Si ya existe, SOLO le actualizamos el texto
                    item.setText(text)
                    
        # 4. Volvemos a encender la pantalla de la tabla
        table.setUpdatesEnabled(True)

    def _fill_phero_table(self, table: QTableWidget, labels: list, mat: np.ndarray):
        n = len(labels)
        
        table.setUpdatesEnabled(False)
        
        if table.rowCount() != n:
            table.setRowCount(n)
            table.setColumnCount(n)
            table.setHorizontalHeaderLabels(labels)
            table.setVerticalHeaderLabels(labels)
            
            table.horizontalHeader().setDefaultSectionSize(55)
            table.verticalHeader().setDefaultSectionSize(25)

        for i in range(n):
            for j in range(n):
                v = mat[i][j]
                text = f"{v:.4f}"
                
                item = table.item(i, j)
                if item is None:
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(i, j, item)
                else:
                    item.setText(text)
                    
        table.setUpdatesEnabled(True)

    # ── ACO execution ─────────────────────────────────────────────────────

    def _run(self):
        if not self._model:
            self.lbl_status.setText("No hay mapa cargado.")
            return

        graph, spawn_ids, exit_ids, all_node_ids = self._model.build_graph()
        self._current_node_ids = all_node_ids

        if not spawn_ids:
            self.lbl_status.setText("No hay nodos S (spawn) en el mapa.")
            return
        if not exit_ids:
            self.lbl_status.setText("No hay nodos E (salida) en el mapa.")
            return

        self.log_text.clear()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText(
            f"Ejecutando ACO: {len(spawn_ids)} spawns → {len(exit_ids)} salidas  "
            f"| {len(all_node_ids)} nodos totales…"
        )

        def step_callback(positions):
            import time
            time.sleep(0.500)  # Pausa de 500ms para verlas caminar
            self._signals.step.emit(positions)

        def iter_callback(*args):
            import time
            time.sleep(0.05)
            self._signals.iteration.emit(*args)

        self._solver = ACOSolver(
            graph=graph,
            spawn_ids=spawn_ids,
            exit_ids=exit_ids,
            all_node_ids=all_node_ids,
            rho=self.dspin_rho.value(),
            Q=self.dspin_Q.value(),
            alpha=self.dspin_alpha.value(),
            beta=self.dspin_beta.value(),
            iterations=self.spin_iter.value(),
            num_ants=self.spin_ants.value(),
            on_iteration=iter_callback,
            on_done=lambda *a: self._signals.done.emit(*a),
            on_step=step_callback,
        )

        self._thread = threading.Thread(target=self._solver.run, daemon=True)
        self._thread.start()

    def _stop(self):
        if self._solver:
            self._solver.stop()
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Detenido por el usuario.")
        self.ant_step_signal.emit({})  # Limpia las hormigas del mapa

    def _on_iteration(self, it: int, best_path: list, best_dist: float, phero: np.ndarray, log_lines: list):
        if best_path:
            self.lbl_status.setText(
                f"Iter {it}  |  Mejor ruta: {' → '.join(best_path)}  |  Dist: {best_dist:.2f}"
            )
        else:
            self.lbl_status.setText(f"Iter {it}  |  Buscando ruta…")

        if hasattr(self, "_current_node_ids"):
            self._fill_phero_table(self.phero_table, self._current_node_ids, phero)

        if it % 5 == 1 or it == 1:
            self.log_text.append(f"\n=== Iteración {it} ===")
            for line in log_lines:
                self.log_text.append(line)

    def _on_done(self, best_path: list, best_dist: float):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.ant_step_signal.emit({})  # Limpia las hormigas del mapa

        if best_path:
            route_str = " → ".join(best_path)
            self.lbl_status.setText(f"✅ Mejor ruta: {route_str}  |  Distancia: {best_dist:.2f}")
            self.log_text.append(f"\n{'='*50}")
            self.log_text.append("RESULTADO FINAL")
            self.log_text.append(f"Mejor ruta:  {route_str}")
            self.log_text.append(f"Distancia:   {best_dist:.2f}")
        else:
            self.lbl_status.setText("❌ No se encontró ninguna ruta S→E. Revisa las conexiones del mapa.")
            self.log_text.append("\n[!] Ninguna hormiga llegó a un nodo E.")
            self.log_text.append("    Verifica que exista un camino conectado desde S hasta E.")

        self.log_text.moveCursor(self.log_text.textCursor().MoveOperation.End)
