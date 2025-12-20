from datetime import datetime, time

from PySide6.QtCore import QDate, Qt
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
    QStyle,
    QHeaderView,
)

from .. import repositories, config
from ..services.payment_service import payment_service
from ..utils import format_currency, format_time_12h
from .widgets import titulo_label, estilizar_tabla
class CobrosTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_comboboxes()
        self._cargar_pendientes()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(titulo_label("Cobros pendientes"))

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

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Hora", "Barbero", "Cliente", "Estado", "Notas"])
        header = self.tabla.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._prefill_servicio_principal)
        estilizar_tabla(self.tabla)
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

        layout.addWidget(titulo_label("Servicios realizados"))

        self.lines_table = QTableWidget(0, 3)
        self.lines_table.setHorizontalHeaderLabels(["Servicio", "Cant.", "Subtotal"])
        header2 = self.lines_table.horizontalHeader()
        header2.setStretchLastSection(True)
        header2.setSectionResizeMode(QHeaderView.Stretch)
        estilizar_tabla(self.lines_table)
        layout.addWidget(self.lines_table)

        acciones_lineas = QHBoxLayout()
        self.btn_eliminar_linea = QPushButton("Quitar servicio seleccionado")
        self.btn_eliminar_linea.clicked.connect(self._eliminar_linea)
        acciones_lineas.addWidget(self.btn_eliminar_linea)
        acciones_lineas.addStretch()
        layout.addLayout(acciones_lineas)

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
        clientes_cache = {}
        self.tabla.setRowCount(0)
        for row, cita in enumerate(citas):
            self.tabla.insertRow(row)
            self._set_cell(self.tabla, row, 0, str(cita["id"]))
            self._set_cell(self.tabla, row, 1, format_time_12h(cita["start_dt"]))
            self._set_cell(self.tabla, row, 2, barberos.get(cita["barber_id"], ""))
            cliente_nombre = ""
            if cita.get("client_id"):
                if cita["client_id"] not in clientes_cache:
                    clientes_cache[cita["client_id"]] = repositories.get_client(cita["client_id"])
                cdata = clientes_cache[cita["client_id"]]
                if cdata:
                    cliente_nombre = cdata["name"]
            self._set_cell(self.tabla, row, 3, cliente_nombre, Qt.AlignCenter)
            self._set_cell(self.tabla, row, 4, cita["status"])
            self._set_cell(self.tabla, row, 5, cita.get("notes") or "", Qt.AlignLeft | Qt.AlignVCenter)
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
        self._set_cell(self.lines_table, row, 0, servicio["name"], Qt.AlignCenter)
        self._set_cell(self.lines_table, row, 1, str(qty))
        subtotal = servicio["price"] * qty
        self._set_cell(self.lines_table, row, 2, format_currency(subtotal))
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

    def _eliminar_linea(self):
        row = self.lines_table.currentRow()
        if row < 0:
            return
        self.lines_table.removeRow(row)

    def _set_cell(self, tabla: QTableWidget, row: int, col: int, text: str, align=Qt.AlignCenter):
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        tabla.setItem(row, col, item)

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
            msg = QMessageBox(self)
            msg.setWindowTitle("Cobro registrado")
            msg.setText(
                f"Total: {format_currency(result['total'])}\nBarbero: {format_currency(result['barbero'])}\nBarbería: {format_currency(result['barberia'])}"
            )
            icono = self.style().standardIcon(QStyle.SP_DialogApplyButton)
            msg.setIconPixmap(icono.pixmap(48, 48))
            msg.exec()
            self._cargar_pendientes()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


