from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget


def titulo_label(texto: str) -> QLabel:
    lbl = QLabel(texto)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:16px; font-weight:bold;")
    return lbl


def estilizar_tabla(tabla: QTableWidget) -> None:
    tabla.horizontalHeader().setStyleSheet(
        "QHeaderView::section {background-color:#e3f2fd; font-weight:bold;}"
    )





