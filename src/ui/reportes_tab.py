from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from ..services.report_service import report_service
from ..utils import format_currency
from .. import config


class ReportesTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._aplicar_rango_rapido("Hoy")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        controles = QHBoxLayout()
        controles.addWidget(QLabel("Rango"))
        self.rango_combo = QComboBox()
        for item in ["Hoy", "Esta semana", "Este mes", "Personalizado"]:
            self.rango_combo.addItem(item)
        self.rango_combo.currentTextChanged.connect(self._on_rango_change)
        controles.addWidget(self.rango_combo)
        self.fecha_inicio = QDateEdit(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_fin = QDateEdit(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        controles.addWidget(QLabel("Inicio"))
        controles.addWidget(self.fecha_inicio)
        controles.addWidget(QLabel("Fin"))
        controles.addWidget(self.fecha_fin)
        self.btn_generar = QPushButton("Generar")
        self.btn_generar.clicked.connect(self._generar)
        controles.addWidget(self.btn_generar)
        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.clicked.connect(self._exportar_pdf)
        controles.addWidget(self.btn_pdf)
        controles.addStretch()
        layout.addLayout(controles)

        self.resumen_label = QLabel("Totales")
        layout.addWidget(self.resumen_label)

        self.tabla_barbero = QTableWidget(0, 4)
        self.tabla_barbero.setHorizontalHeaderLabels(["Barbero", "Ventas", "Barbero", "Barbería"])
        self.tabla_barbero.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla_barbero)

        self.tabla_dias = QTableWidget(0, 4)
        self.tabla_dias.setHorizontalHeaderLabels(["Fecha", "Ventas", "Barbero", "Barbería"])
        self.tabla_dias.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla_dias)

    def _on_rango_change(self, texto: str):
        if texto != "Personalizado":
            self._aplicar_rango_rapido(texto)

    def _aplicar_rango_rapido(self, texto: str):
        hoy = datetime.now().date()
        if texto == "Hoy":
            inicio = fin = hoy
        elif texto == "Esta semana":
            inicio = hoy - timedelta(days=hoy.weekday())
            fin = inicio + timedelta(days=6)
        elif texto == "Este mes":
            inicio = hoy.replace(day=1)
            fin = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            inicio = fin = hoy
        self.fecha_inicio.setDate(QDate(inicio.year, inicio.month, inicio.day))
        self.fecha_fin.setDate(QDate(fin.year, fin.month, fin.day))

    def _generar(self):
        inicio_dt = datetime.combine(self.fecha_inicio.date().toPython(), datetime.min.time())
        fin_dt = datetime.combine(self.fecha_fin.date().toPython(), datetime.max.time())
        data = report_service.resumen(inicio_dt, fin_dt)
        tot = data["totales"]
        self.resumen_label.setText(
            f"Ventas: {format_currency(tot['ventas'])} | Barberos: {format_currency(tot['barberos'])} | Barbería: {format_currency(tot['barberia'])}"
        )
        self._llenar_tabla(self.tabla_barbero, data["por_barbero"])
        self._llenar_tabla(self.tabla_dias, data["por_dia"])
        self._ultimo_resumen = (inicio_dt, fin_dt, data)

    def _llenar_tabla(self, tabla: QTableWidget, data_map):
        tabla.setRowCount(0)
        for idx, (key, valores) in enumerate(data_map.items()):
            tabla.insertRow(idx)
            tabla.setItem(idx, 0, QTableWidgetItem(str(key)))
            tabla.setItem(idx, 1, QTableWidgetItem(format_currency(valores["ventas"])))
            tabla.setItem(idx, 2, QTableWidgetItem(format_currency(valores["barbero"])))
            tabla.setItem(idx, 3, QTableWidgetItem(format_currency(valores["barberia"])))

    def _exportar_pdf(self):
        if not hasattr(self, "_ultimo_resumen"):
            QMessageBox.warning(self, "Sin datos", "Genere un reporte primero")
            return
        inicio, fin, data = self._ultimo_resumen
        path = config.BASE_DIR / "reporte.pdf"
        report_service.exportar_pdf(path, data, "Reporte Barbería", (inicio, fin))
        QMessageBox.information(self, "PDF generado", f"Archivo: {path}")

