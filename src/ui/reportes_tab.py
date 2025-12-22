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
    QInputDialog,
    QLineEdit,
    QHeaderView,
)

from ..services.report_service import report_service
from ..utils import format_currency
from .. import config, repositories
from .widgets import titulo_label, estilizar_tabla


class ReportesTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._aplicar_rango_rapido("Hoy")
        self._cargar_barberos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(titulo_label("Reportes"))
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
        controles.addWidget(QLabel("Barbero"))
        self.barbero_combo = QComboBox()
        controles.addWidget(self.barbero_combo)
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

        layout.addWidget(titulo_label("Detalle por servicio"))
        self.tabla_barbero = QTableWidget(0, 5)
        self.tabla_barbero.setHorizontalHeaderLabels(["Nombre Barbero", "Ventas", "Total Barbero", "Barbería", "Servicios"])
        self.tabla_barbero.horizontalHeader().setStretchLastSection(True)
        estilizar_tabla(self.tabla_barbero)
        layout.addWidget(self.tabla_barbero)

        layout.addWidget(titulo_label("Totales generales"))
        self.tabla_dias = QTableWidget(0, 4)
        self.tabla_dias.setHorizontalHeaderLabels(["Fecha", "Ventas", "Ganancia Total Barberos", "Ganancia Total Barbería"])
        header_totales = self.tabla_dias.horizontalHeader()
        header_totales.setStretchLastSection(True)
        header_totales.setSectionResizeMode(QHeaderView.Stretch)
        estilizar_tabla(self.tabla_dias)
        layout.addWidget(self.tabla_dias)

        layout.addWidget(titulo_label("Cobros realizados"))
        self.tabla_cobros = QTableWidget(0, 6)
        self.tabla_cobros.setHorizontalHeaderLabels(["ID Cita", "Fecha", "Barbero", "Total", "Método de pago", "Servicios"])
        self.tabla_cobros.horizontalHeader().setStretchLastSection(True)
        estilizar_tabla(self.tabla_cobros)
        layout.addWidget(self.tabla_cobros)

        acciones = QHBoxLayout()
        self.btn_borrar = QPushButton("Borrar cobro")
        self.btn_borrar.clicked.connect(self._borrar_cobro)
        acciones.addWidget(self.btn_borrar)
        acciones.addStretch()
        layout.addLayout(acciones)

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
        barber_id = self.barbero_combo.currentData()
        data = report_service.resumen(inicio_dt, fin_dt, barber_id)
        tot = data["totales"]
        self.resumen_label.setText(
            f"Ventas: {format_currency(tot['ventas'])} | Barberos: {format_currency(tot['barberos'])} | Barbería: {format_currency(tot['barberia'])}"
        )
        self._llenar_tabla(self.tabla_barbero, data["por_barbero"], True)
        self._llenar_tabla(self.tabla_dias, data["por_dia"], False)
        self._llenar_cobros(data.get("pagos_detalle", []))
        self._ultimo_resumen = (inicio_dt, fin_dt, data, barber_id)

    def _llenar_tabla(self, tabla: QTableWidget, data_map, incluir_servicios: bool):
        tabla.setRowCount(0)
        for idx, (key, valores) in enumerate(data_map.items()):
            tabla.insertRow(idx)
            tabla.setItem(idx, 0, QTableWidgetItem(str(key)))
            tabla.setItem(idx, 1, QTableWidgetItem(format_currency(valores["ventas"])))
            tabla.setItem(idx, 2, QTableWidgetItem(format_currency(valores["barbero"])))
            tabla.setItem(idx, 3, QTableWidgetItem(format_currency(valores["barberia"])))
            if incluir_servicios:
                servicios_raw = valores.get("servicios", [])
                if servicios_raw and isinstance(servicios_raw[0], tuple):
                    agregados = {}
                    for nombre, qty in servicios_raw:
                        agregados[nombre] = agregados.get(nombre, 0) + qty
                    servicios_txt = ", ".join([f"{n} x{q}" for n, q in agregados.items()])
                else:
                    servicios_txt = ", ".join(servicios_raw)
                tabla.setItem(idx, 4, QTableWidgetItem(servicios_txt))

    def _exportar_pdf(self):
        if not hasattr(self, "_ultimo_resumen"):
            QMessageBox.warning(self, "Sin datos", "Genere un reporte primero")
            return
        inicio, fin, data, _ = self._ultimo_resumen
        path = config.BASE_DIR / "reporte.pdf"
        report_service.exportar_pdf(path, data, "Reporte Barbería", (inicio, fin))
        QMessageBox.information(self, "PDF generado", f"Archivo: {path}")

    def _llenar_cobros(self, pagos_detalle):
        self.tabla_cobros.setRowCount(0)
        for idx, pago in enumerate(pagos_detalle):
            self.tabla_cobros.insertRow(idx)
            self.tabla_cobros.setItem(idx, 0, QTableWidgetItem(str(pago["appointment_id"])))
            self.tabla_cobros.setItem(idx, 1, QTableWidgetItem(pago["fecha"]))
            self.tabla_cobros.setItem(idx, 2, QTableWidgetItem(pago["barber"]))
            self.tabla_cobros.setItem(idx, 3, QTableWidgetItem(format_currency(pago["total"])))
            self.tabla_cobros.setItem(idx, 4, QTableWidgetItem(pago.get("metodo_pago", "")))
            self.tabla_cobros.setItem(idx, 5, QTableWidgetItem(pago.get("servicios", "")))

    def _borrar_cobro(self):
        if not self.tabla_cobros.rowCount():
            return
        row = self.tabla_cobros.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Seleccione", "Seleccione un cobro de la lista")
            return
        cid_item = self.tabla_cobros.item(row, 0)
        if not cid_item:
            return
        appointment_id = int(cid_item.text())
        pwd, ok = QInputDialog.getText(self, "Contraseña requerida", "Ingrese contraseña para borrar:", QLineEdit.Password)
        if not ok:
            return
        if pwd != "Kingston2025":
            QMessageBox.warning(self, "No autorizado", "Contraseña incorrecta")
            return
        try:
            report_service.borrar_cobro(appointment_id)
            QMessageBox.information(self, "Cobro eliminado", "El cobro fue eliminado y la cita volvió a RESERVADA")
            # regenerar para reflejar cambios
            self._generar()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _cargar_barberos(self):
        self.barbero_combo.clear()
        self.barbero_combo.addItem("Todos", None)
        for b in repositories.list_barbers():
            self.barbero_combo.addItem(b["name"], b["id"])


