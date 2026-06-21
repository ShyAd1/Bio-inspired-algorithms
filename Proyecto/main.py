"""
Punto de entrada principal.
Editor de Mapas con nodos S/N/E + Algoritmo ACO de enjambre de hormigas.
"""
import sys
import os

# Make sure imports resolve from this directory
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    # Needed for high-DPI displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Proyecto")

    # Dark stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget { background: #1e1e23; color: #ddd; }
        QToolButton { background: #2a2a32; border: 1px solid #444; border-radius: 4px;
                      padding: 4px 6px; color: #ddd; font-size: 11px; }
        QToolButton:checked { background: #3a5a8a; border-color: #6af; }
        QToolButton:hover   { background: #33334a; }
        
        /* --- CORRECCIÓN DEL MENÚ --- */
        QMenuBar            { background: #16161c; color: #ddd; }
        QMenuBar::item      { padding: 5px 10px; background: transparent; }
        QMenuBar::item:selected { background: #3a5a8a; }
        
        QMenu               { background: #1e1e23; color: #ddd; border: 1px solid #444; }
        /* El padding es: arriba, derecha (más grande para los atajos), abajo, izquierda */
        QMenu::item         { padding: 5px 40px 5px 25px; background: transparent; color: #ddd; }
        QMenu::item:selected{ background: #3a5a8a; color: #ffffff; }
        QMenu::separator    { height: 1px; background: #444; margin: 4px 0px; }
        /* --------------------------- */

        QGroupBox           { border: 1px solid #444; border-radius: 4px; margin-top: 8px;
                              font-weight: bold; color: #adf; }
        QGroupBox::title    { subcontrol-origin: margin; left: 8px; }
        QPushButton         { background: #2a2a32; border: 1px solid #555; border-radius: 4px;
                              padding: 4px 10px; color: #ddd; }
        QPushButton:hover   { background: #33334a; }
        QPushButton:disabled{ color: #555; }
        QTextEdit           { background: #111116; color: #b8ffb8; }
        QTableWidget        { background: #111116; color: #ccc; gridline-color: #333; }
        QHeaderView::section{ background: #2a2a32; color: #adf; border: 1px solid #444; }
        QStatusBar          { background: #16161c; color: #aaa; }
        QSplitter::handle   { background: #333; }
        QLabel              { color: #ccc; }
    """)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
