from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout

from .agenda_tab import AgendaTab
from .cobros_tab import CobrosTab
from .reportes_tab import ReportesTab
from .configuracion_tab import ConfiguracionTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barbería - Gestión Offline")
        self.resize(1100, 720)

        self.tabs = QTabWidget()
        self.tabs.addTab(AgendaTab(), "Agenda")
        self.tabs.addTab(CobrosTab(), "Cobros")
        self.tabs.addTab(ReportesTab(), "Reportes")
        self.tabs.addTab(ConfiguracionTab(), "Configuración")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)


