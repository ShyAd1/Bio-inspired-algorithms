"""
Main application window.
Left: toolbar + pygame map editor.
Right: ACO panel.
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QToolBar, QLabel, QFileDialog, QMessageBox,
    QStatusBar, QSplitter, QInputDialog, QDialog,
    QFormLayout, QSpinBox, QDialogButtonBox, QLineEdit,
    QToolButton,
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt

from core.map_model import MapModel
from ui.map_editor_widget import MapEditorWidget
from ui.aco_panel import ACOPanel


class ResizeDialog(QDialog):
    def __init__(self, current_w, current_h, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redimensionar mapa")
        lay = QFormLayout(self)
        self.spin_w = QSpinBox(); self.spin_w.setRange(5, 500); self.spin_w.setValue(current_w)
        self.spin_h = QSpinBox(); self.spin_h.setRange(5, 500); self.spin_h.setValue(current_h)
        lay.addRow("Ancho (columnas):", self.spin_w)
        lay.addRow("Alto (filas):", self.spin_h)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proyecto")
        self.resize(1200, 700)

        self._current_file: str | None = None
        self._model = MapModel("nuevo_mapa", 33, 20, 24)

        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._build_central()

        self._editor.set_model(self._model)
        self._aco_panel.set_model(self._model)
        self._editor.center_view()
        self._set_tool("wall")

    # ── UI construction ───────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("&Archivo")
        a_new  = file_menu.addAction("&Nuevo mapa");      a_new.setShortcut(QKeySequence.StandardKey.New)
        a_open = file_menu.addAction("&Abrir mapa…");     a_open.setShortcut(QKeySequence.StandardKey.Open)
        a_save = file_menu.addAction("&Guardar");         a_save.setShortcut(QKeySequence.StandardKey.Save)
        a_saveas = file_menu.addAction("Guardar &como…"); a_saveas.setShortcut(QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        a_exit = file_menu.addAction("S&alir");           a_exit.setShortcut(QKeySequence.StandardKey.Quit)
        a_new.triggered.connect(self._new_map)
        a_open.triggered.connect(self._open_map)
        a_save.triggered.connect(self._save)
        a_saveas.triggered.connect(self._save_as)
        a_exit.triggered.connect(self.close)

        map_menu = mb.addMenu("&Mapa")
        a_resize = map_menu.addAction("&Redimensionar…")
        a_center = map_menu.addAction("&Centrar vista")
        a_clear  = map_menu.addAction("Li&mpiar mapa")
        a_resize.triggered.connect(self._resize_map)
        a_center.triggered.connect(lambda: self._editor.center_view())
        a_clear.triggered.connect(self._clear_map)

        view_menu = mb.addMenu("&Vista")
        a_aco = view_menu.addAction("Panel &ACO")
        a_aco.triggered.connect(lambda: self._splitter.setSizes([700, 400]))

    def _build_toolbar(self):
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tb)

        def _btn(label: str, tip: str, tool: str | None = None) -> QToolButton:
            b = QToolButton()
            b.setText(label)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setMinimumWidth(80)
            if tool:
                b.clicked.connect(lambda checked, t=tool: self._set_tool(t))
            return b

        self._tool_buttons: dict[str, QToolButton] = {}

        tools = [
            ("Pared",    "Pintar paredes (#)",           "wall"),
            ("Borrar",   "Borrar celda",                 "erase"),
            ("Nodo S",   "Colocar nodo Spawn (S)",       "node_S"),
            ("Nodo N",   "Colocar nodo Conexión (N)",    "node_N"),
            ("Nodo E",   "Colocar nodo Salida (E)",      "node_E"),
            ("Conectar", "Conectar nodos",               "connect"),
            ("Mover",    "Mover nodo",                   "move"),
            ("Selec.",   "Seleccionar/inspeccionar nodo","select"),
        ]

        for label, tip, tool in tools:
            btn = _btn(label, tip, tool)
            self._tool_buttons[tool] = btn
            tb.addWidget(btn)

        tb.addSeparator()
        lbl = QLabel("  Rueda: zoom\n  Botón medio: pan\n  Clic derecho:\n  eliminar nodo")
        lbl.setStyleSheet("color:#aaa; font-size:9px;")
        tb.addWidget(lbl)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(self._splitter)

        self._editor = MapEditorWidget(self._model)
        self._editor.status_message.connect(self._status.showMessage)
        self._editor.map_changed.connect(self._on_map_changed)

        self._aco_panel = ACOPanel()

        self._aco_panel.ant_step_signal.connect(self._editor.set_ants)

        self._splitter.addWidget(self._editor)
        self._splitter.addWidget(self._aco_panel)
        self._splitter.setSizes([750, 400])

    def _build_statusbar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Listo")

    # ── Tool selection ────────────────────────────────────────────────────

    def _set_tool(self, tool: str):
        for t, btn in self._tool_buttons.items():
            btn.setChecked(t == tool)
        if hasattr(self, "_editor"):
            self._editor.set_tool(tool)
        if hasattr(self, "_status"):
            self._status.showMessage(f"Herramienta activa: {tool}")

    # ── Map operations ────────────────────────────────────────────────────

    def _new_map(self):
        name, ok = QInputDialog.getText(self, "Nuevo mapa", "Nombre del mapa:", text="nuevo_mapa")
        if not ok:
            return
        self._model = MapModel(name, 33, 20, 24)
        self._current_file = None
        self.setWindowTitle(f"Proyecto — {name}")
        self._editor.set_model(self._model)
        self._aco_panel.set_model(self._model)
        self._editor.center_view()

    def _open_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir mapa", "", "JSON (*.json)")
        if not path:
            return
        try:
            self._model = MapModel.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar", str(e))
            return
        self._current_file = path
        self.setWindowTitle(f"Proyecto — {self._model.name}")
        self._editor.set_model(self._model)
        self._aco_panel.set_model(self._model)
        self._editor.center_view()
        self._status.showMessage(f"Mapa cargado: {path}")

    def _save(self):
        if not self._current_file:
            self._save_as()
        else:
            self._do_save(self._current_file)

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar mapa", f"{self._model.name}.json", "JSON (*.json)")
        if path:
            self._current_file = path
            self._do_save(path)

    def _do_save(self, path: str):
        try:
            self._model.save(path)
            self._status.showMessage(f"Guardado: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    def _resize_map(self):
        dlg = ResizeDialog(self._model.width, self._model.height, self)
        if dlg.exec():
            self._model.resize(dlg.spin_w.value(), dlg.spin_h.value())
            self._editor.center_view()
            self._on_map_changed()

    def _clear_map(self):
        reply = QMessageBox.question(
            self, "Limpiar mapa",
            "¿Eliminar todas las paredes y nodos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._model = MapModel(self._model.name, self._model.width, self._model.height, self._model.cell_size)
            self._editor.set_model(self._model)
            self._aco_panel.set_model(self._model)

    def _on_map_changed(self):
        self._aco_panel.set_model(self._model)
        title = f"Proyecto — {self._model.name}"
        if self._current_file:
            title += f"  [{os.path.basename(self._current_file)}]"
        self.setWindowTitle(title + " *")
