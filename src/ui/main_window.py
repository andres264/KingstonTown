from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout
from PySide6.QtGui import QIcon

from .agenda_tab import AgendaTab
from .cobros_tab import CobrosTab
from .reportes_tab import ReportesTab
from .configuracion_tab import ConfiguracionTab
from .. import config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barberia Kignston Town")
        self.resize(1100, 720)
        self._apply_global_styles()
        self._set_icon()

        self.tabs = QTabWidget()
        self.tabs.addTab(AgendaTab(), "Agenda")
        self.tabs.addTab(CobrosTab(), "Cobros")
        self.tabs.addTab(ReportesTab(), "Reportes")
        self.tabs.addTab(ConfiguracionTab(), "Configuración")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

    def _apply_global_styles(self):
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QHeaderView::section { background-color: #e3f2fd; font-weight: bold; }
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #cccccc;
            }
            QTableWidget::item:selected { background-color: #e0f2ff; }
            QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            """
        )

    def _set_icon(self):
        if config.LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(config.LOGO_PATH)))


