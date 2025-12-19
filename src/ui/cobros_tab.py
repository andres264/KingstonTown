from datetime import datetime, time

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QDateEdit,
    QSpinBox,
    QMessageBox,
)

from .. import repositories, config
from ..services.payment_service import payment_service
from ..utils import format_currency


class CobrosTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_comboboxes()
        self._cargar_pendientes()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("Fecha"))
        self.fecha = QDateEdit(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        filtros.addWidget(self.fecha)
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.clicked.connect(self._cargar_pendientes)
        filtros.addWidget(self.btn_refrescar)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Hora", "Barbero", "Estado", "Notas"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.itemSelectionChanged.connect(self._prefill_servicio_principal)
        layout.addWidget(self.tabla)

        form = QHBoxLayout()
        self.servicio_combo = QComboBox()
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.btn_agregar = QPushButton("Agregar servicio")
        self.btn_agregar.clicked.connect(self._agregar_servicio)
        form.addWidget(QLabel("Servicio"))
        form.addWidget(self.servicio_combo)
        form.addWidget(QLabel("Cantidad"))
        form.addWidget(self.qty_spin)
        form.addWidget(self.btn_agregar)
        form.addStretch()
        layout.addLayout(form)

        self.lines_table = QTableWidget(0, 3)
        self.lines_table.setHorizontalHeaderLabels(["Servicio", "Cant.", "Subtotal"])
        self.lines_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.lines_table)

        pago_layout = QHBoxLayout()
        pago_layout.addWidget(QLabel("Método de pago"))
        self.metodo_pago = QComboBox()
        pago_layout.addWidget(self.metodo_pago)
        self.btn_cobrar = QPushButton("Cobrar")
        self.btn_cobrar.clicked.connect(self._cobrar)
        pago_layout.addWidget(self.btn_cobrar)
        pago_layout.addStretch()
        layout.addLayout(pago_layout)

    def _load_comboboxes(self):
        self.servicio_combo.clear()
        for s in repositories.list_services():
            self.servicio_combo.addItem(f"{s['name']} ({format_currency(s['price'])})", s["id"])
        self.metodo_pago.clear()
        for m in config.METODOS_PAGO:
            self.metodo_pago.addItem(m)

    def _cargar_pendientes(self):
        fecha = self.fecha.date().toPython()
        inicio = datetime.combine(fecha, time(0, 0))
        fin = datetime.combine(fecha, time(23, 59))
        citas = repositories.list_appointments_by_range(inicio.isoformat(), fin.isoformat(), None, "RESERVADA")
        barberos = {b["id"]: b["name"] for b in repositories.list_barbers()}
        self.tabla.setRowCount(0)
        for row, cita in enumerate(citas):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(str(cita["id"])))
            self.tabla.setItem(row, 1, QTableWidgetItem(cita["start_dt"][11:16]))
            self.tabla.setItem(row, 2, QTableWidgetItem(barberos.get(cita["barber_id"], "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(cita["status"]))
            self.tabla.setItem(row, 4, QTableWidgetItem(cita.get("notes") or ""))
        self.lines_table.setRowCount(0)

    def _selected_appointment_id(self) -> int:
        row = self.tabla.currentRow()
        if row < 0:
            return 0
        item = self.tabla.item(row, 0)
        return int(item.text()) if item else 0

    def _prefill_servicio_principal(self):
        cita_id = self._selected_appointment_id()
        if not cita_id:
            return
        cita = repositories.get_appointment(cita_id)
        self.lines_table.setRowCount(0)
        if cita and cita.get("primary_service_id"):
            servicio = next((s for s in repositories.list_services(True) if s["id"] == cita["primary_service_id"]), None)
            if servicio:
                self._add_line(servicio, 1)

    def _agregar_servicio(self):
        servicio_id = self.servicio_combo.currentData()
        servicio = next((s for s in repositories.list_services(True) if s["id"] == servicio_id), None)
        if not servicio:
            return
        qty = self.qty_spin.value()
        self._add_line(servicio, qty)

    def _add_line(self, servicio: dict, qty: int):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.lines_table.setItem(row, 0, QTableWidgetItem(servicio["name"]))
        self.lines_table.setItem(row, 1, QTableWidgetItem(str(qty)))
        subtotal = servicio["price"] * qty
        self.lines_table.setItem(row, 2, QTableWidgetItem(format_currency(subtotal)))
        self.lines_table.resizeColumnsToContents()

    def _build_payload(self):
        servicios = []
        for row in range(self.lines_table.rowCount()):
            nombre = self.lines_table.item(row, 0).text()
            qty = int(self.lines_table.item(row, 1).text())
            servicio = next((s for s in repositories.list_services(True) if s["name"] == nombre), None)
            if servicio:
                servicios.append({"service_id": servicio["id"], "qty": qty})
        return servicios

    def _cobrar(self):
        cita_id = self._selected_appointment_id()
        if not cita_id:
            QMessageBox.warning(self, "Seleccione", "Seleccione una cita")
            return
        servicios = self._build_payload()
        if not servicios:
            QMessageBox.warning(self, "Servicios", "Agregue al menos un servicio")
            return
        try:
            result = payment_service.cobrar(cita_id, servicios, self.metodo_pago.currentText())
            QMessageBox.information(
                self,
                "Cobro registrado",
                f"Total: {format_currency(result['total'])}\nBarbero: {format_currency(result['barbero'])}\nBarbería: {format_currency(result['barberia'])}",
            )
            self._cargar_pendientes()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


