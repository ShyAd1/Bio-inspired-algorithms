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
    def __init__(self, current_f, current_w, current_h, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redimensionar mapa")
        lay = QFormLayout(self)
        self.spin_f = QSpinBox(); self.spin_f.setRange(1, 10); self.spin_f.setValue(current_f)
        self.spin_w = QSpinBox(); self.spin_w.setRange(5, 500); self.spin_w.setValue(current_w)
        self.spin_h = QSpinBox(); self.spin_h.setRange(5, 500); self.spin_h.setValue(current_h)
        lay.addRow("Plantas (pisos):", self.spin_f)
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
        self._model = MapModel("nuevo_mapa", floors=1, width=33, height=20, cell_size=24)

        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._build_central()

        self._editor.set_model(self._model)
        self._aco_panel.set_model(self._model)
        self._editor.center_view()
        self._set_tool("wall")

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

    def _build_toolbar(self):
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tb)

        # NUEVO: Selector de Planta / Piso
        self.spin_floor = QSpinBox()
        self.spin_floor.setPrefix("Planta: ")
        self.spin_floor.setRange(0, self._model.floors - 1)
        self.spin_floor.valueChanged.connect(self._change_floor)
        tb.addWidget(self.spin_floor)
        tb.addSeparator()

        # Modificamos _btn para recibir un cuarto parámetro: 'shortcut'
        def _btn(label, tip, tool=None, shortcut=None):
            b = QToolButton()
            b.setText(label)
            
            # Si le pasamos un atajo, lo configuramos y lo mostramos en el tooltip
            if shortcut:
                b.setToolTip(f"{tip} ({shortcut})")
                b.setShortcut(QKeySequence(shortcut))
            else:
                b.setToolTip(tip)
                
            b.setCheckable(True)
            b.setMinimumWidth(80)
            if tool: 
                b.clicked.connect(lambda checked, t=tool: self._set_tool(t))
            return b

        self._tool_buttons = {}
        
        # Agregamos la tecla correspondiente como 4to elemento de cada tupla.
        # Usamos letras intuitivas (V para selección, como en Photoshop/Illustrator)
        tools = [
            ("Pared",    "Pintar paredes (#)",           "wall",    "P"),
            ("Borrar",   "Borrar celda",                 "erase",   "B"),
            ("Nodo S",   "Colocar nodo Spawn (S)",       "node_S",  "S"),
            ("Nodo N",   "Colocar nodo Conexión (N)",    "node_N",  "N"),
            ("Nodo L",   "Colocar Escalera a otra planta","node_L", "L"),
            ("Nodo E",   "Colocar nodo Salida (E)",      "node_E",  "E"),
            ("Conectar", "Conectar nodos",               "connect", "C"),
            ("Mover",    "Mover nodo",                   "move",    "M"),
            ("Selec.",   "Seleccionar/inspeccionar nodo","select",  "V"),
        ]

        # Desempaquetamos los 4 elementos en el bucle for
        for label, tip, tool, shortcut in tools:
            btn = _btn(label, tip, tool, shortcut)
            self._tool_buttons[tool] = btn
            tb.addWidget(btn)
        
        tb.addSeparator()
        lbl = QLabel("  - Rueda: zoom\n\n  - Botón medio: pan\n\n  - Clic derecho:\n    eliminar nodo")
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

    def _set_tool(self, tool: str):
        for t, btn in self._tool_buttons.items(): btn.setChecked(t == tool)
        self._editor.set_tool(tool)
        self._status.showMessage(f"Herramienta activa: {tool}")

    def _change_floor(self, new_floor: int):
        self._editor.current_floor = new_floor
        self._editor.update()
        self._status.showMessage(f"Viendo Planta {new_floor}")

    def _new_map(self):
        name, ok = QInputDialog.getText(self, "Nuevo mapa", "Nombre:", text="nuevo_mapa")
        if not ok: return
        self._model = MapModel(name, floors=1, width=33, height=20, cell_size=24)
        self._current_file = None
        self._post_load_update()

    def _open_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir mapa", "", "JSON (*.json)")
        if not path: return
        try: self._model = MapModel.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar", str(e))
            return
        self._current_file = path
        self._post_load_update()
        self._status.showMessage(f"Mapa cargado: {path}")

    def _save(self):
        if not self._current_file: self._save_as()
        else: self._do_save(self._current_file)

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", f"{self._model.name}.json", "JSON (*.json)")
        if path: self._current_file = path; self._do_save(path)

    def _do_save(self, path: str):
        try: self._model.save(path); self._status.showMessage(f"Guardado: {path}")
        except Exception as e: QMessageBox.critical(self, "Error al guardar", str(e))

    def _resize_map(self):
        dlg = ResizeDialog(self._model.floors, self._model.width, self._model.height, self)
        if dlg.exec():
            self._model.resize(dlg.spin_f.value(), dlg.spin_w.value(), dlg.spin_h.value())
            self.spin_floor.setMaximum(self._model.floors - 1)
            self._editor.center_view()
            self._on_map_changed()

    def _clear_map(self):
        reply = QMessageBox.question(self, "Limpiar mapa", "¿Eliminar todas las paredes y nodos?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._model = MapModel(self._model.name, self._model.floors, self._model.width, self._model.height, self._model.cell_size)
            self._post_load_update()

    def _on_map_changed(self):
        self._aco_panel.set_model(self._model)
        title = f"Proyecto — {self._model.name}"
        if self._current_file: title += f"  [{os.path.basename(self._current_file)}]"
        self.setWindowTitle(title + " *")

    def _post_load_update(self):
        self.setWindowTitle(f"Proyecto — {self._model.name}")
        self.spin_floor.setMaximum(self._model.floors - 1)
        self.spin_floor.setValue(0)
        self._editor.set_model(self._model)
        self._aco_panel.set_model(self._model)
        self._editor.center_view()