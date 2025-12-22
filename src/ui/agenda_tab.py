from datetime import datetime, time

from PySide6.QtCore import QDate, Qt, QTime
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
    QTimeEdit,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QHeaderView,
)

from .. import repositories
from ..services.agenda_service import agenda_service
from ..utils import format_currency, format_time_12h


class AgendaTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_comboboxes()
        self._cargar_citas()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filtros = QHBoxLayout()
        filtros.addWidget(self._titulo_label("Agenda"))
        filtros.addStretch()
        filtros.addWidget(QLabel("Fecha"))
        self.fecha_filtro = QDateEdit(QDate.currentDate())
        self.fecha_filtro.setCalendarPopup(True)
        filtros.addWidget(self.fecha_filtro)

        filtros.addWidget(QLabel("Barbero"))
        self.barbero_filtro = QComboBox()
        filtros.addWidget(self.barbero_filtro)

        filtros.addWidget(QLabel("Estado"))
        self.estado_filtro = QComboBox()
        self.estado_filtro.addItem("Todos")
        for estado in ["RESERVADA", "ATENDIDA", "CANCELADA", "NO ASISTIÓ"]:
            self.estado_filtro.addItem(estado)
        filtros.addWidget(self.estado_filtro)

        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.clicked.connect(self._cargar_citas)
        filtros.addWidget(self.btn_refrescar)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, 9)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Barbero", "Cliente", "Servicio", "Estado", "Teléfono", "Notas"]
        )
        header = self.tabla.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._estilizar_tabla(self.tabla)
        layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar cita")
        self.btn_noshow = QPushButton("Marca no asistió")
        self.btn_agendar = QPushButton("Agendar cita")
        self.btn_eliminar = QPushButton("Eliminar cita")
        self.btn_cancelar.clicked.connect(self._cancelar)
        self.btn_noshow.clicked.connect(self._no_show)
        self.btn_agendar.clicked.connect(self._abrir_dialogo_cita)
        self.btn_eliminar.clicked.connect(self._eliminar_cita)
        acciones.addWidget(self.btn_agendar)
        acciones.addWidget(self.btn_cancelar)
        acciones.addWidget(self.btn_eliminar)
        acciones.addWidget(self.btn_noshow)
        acciones.addStretch()
        layout.addLayout(acciones)

    def _load_comboboxes(self):
        self.barbero_filtro.clear()
        self.barbero_filtro.addItem("Todos", None)
        for b in repositories.list_barbers():
            if b["active"]:
                self.barbero_filtro.addItem(b["name"], b["id"])

    def _cargar_citas(self):
        fecha = self.fecha_filtro.date().toPython()
        inicio = datetime.combine(fecha, time(0, 0))
        fin = datetime.combine(fecha, time(23, 59))
        barber_id = self.barbero_filtro.currentData()
        estado = None if self.estado_filtro.currentText() == "Todos" else self.estado_filtro.currentText()
        citas = repositories.list_appointments_by_range(inicio.isoformat(), fin.isoformat(), barber_id, estado)
        barberos = {b["id"]: b["name"] for b in repositories.list_barbers()}
        servicios = {s["id"]: s["name"] for s in repositories.list_services(True)}
        self.tabla.setRowCount(0)
        for row, cita in enumerate(citas):
            self.tabla.insertRow(row)
            self._set_cell(self.tabla, row, 0, str(cita["id"]))
            self._set_cell(self.tabla, row, 1, format_time_12h(cita["start_dt"]))
            self._set_cell(self.tabla, row, 2, format_time_12h(cita["end_dt"]))
            self._set_cell(self.tabla, row, 3, barberos.get(cita["barber_id"], ""))
            cliente_nombre = ""
            if cita.get("client_id"):
                cliente = repositories.get_client(cita["client_id"])
                if cliente:
                    cliente_nombre = cliente["name"]
            self._set_cell(self.tabla, row, 4, cliente_nombre, Qt.AlignCenter)
            self._set_cell(self.tabla, row, 5, servicios.get(cita.get("primary_service_id"), ""))
            self._set_cell(self.tabla, row, 6, cita["status"])
            telefono = ""
            if cita.get("client_id") and cliente and cliente.get("phone"):
                telefono = cliente["phone"]
            self._set_cell(self.tabla, row, 7, telefono, Qt.AlignCenter)
            self._set_cell(self.tabla, row, 8, cita.get("notes") or "", Qt.AlignLeft | Qt.AlignVCenter)

    def _selected_id(self) -> int:
        row = self.tabla.currentRow()
        if row < 0:
            return 0
        item = self.tabla.item(row, 0)
        return int(item.text()) if item else 0

    def _cancelar(self):
        cid = self._selected_id()
        if not cid:
            return
        repositories.update_appointment_status(cid, "CANCELADA")
        self._cargar_citas()

    def _no_show(self):
        cid = self._selected_id()
        if not cid:
            return
        repositories.update_appointment_status(cid, "NO ASISTIÓ")
        self._cargar_citas()

    def _eliminar_cita(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Seleccione", "Seleccione una cita")
            return
        pago = repositories.get_payment_with_lines(cid)
        if pago:
            QMessageBox.warning(self, "No permitido", "No puede eliminar una cita que ya tiene cobro")
            return
        resp = QMessageBox.question(self, "Confirmar", "¿Desea eliminar la cita seleccionada?")
        if resp == QMessageBox.StandardButton.Yes:
            repositories.delete_appointment(cid)
            self._cargar_citas()

    def _titulo_label(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:16px; font-weight:bold;")
        return lbl

    def _estilizar_tabla(self, tabla: QTableWidget):
        tabla.horizontalHeader().setStyleSheet(
            "QHeaderView::section {background-color:#e3f2fd; font-weight:bold;}"
        )

    def _set_cell(self, tabla: QTableWidget, row: int, col: int, text: str, align=Qt.AlignCenter):
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        tabla.setItem(row, col, item)

    def _abrir_dialogo_cita(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Agendar cita")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        cb_barbero = QComboBox()
        for b in repositories.list_barbers():
            cb_barbero.addItem(b["name"], b["id"])

        cb_servicio = QComboBox()
        for s in repositories.list_services():
            cb_servicio.addItem(f"{s['name']} ({format_currency(s['price'])})", s["id"])

        de_fecha = QDateEdit(QDate.currentDate())
        de_fecha.setCalendarPopup(True)
        te_hora = QTimeEdit()
        te_hora.setDisplayFormat("hh:mm ap")
        te_hora.setTime(QTime(9, 30))
        le_cliente = QLineEdit()
        le_cliente.setPlaceholderText("Nombre cliente")
        le_tel = QLineEdit()
        le_tel.setPlaceholderText("Teléfono (opcional)")
        te_notas = QTextEdit()
        te_notas.setPlaceholderText("Notas")
        te_notas.setFixedHeight(60)

        form.addRow("Barbero", cb_barbero)
        form.addRow("Servicio", cb_servicio)
        form.addRow("Fecha", de_fecha)
        form.addRow("Hora", te_hora)
        form.addRow("Cliente", le_cliente)
        form.addRow("Teléfono", le_tel)
        form.addRow("Notas", te_notas)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def crear_cita():
            try:
                barber_id = cb_barbero.currentData()
                servicio_id = cb_servicio.currentData()
                fecha = de_fecha.date().toPython()
                hora = te_hora.time().toPython()
                inicio = datetime.combine(fecha, hora)
                agenda_service.crear_cita(
                    barber_id=barber_id,
                    client_name=le_cliente.text().strip() or None,
                    client_phone=le_tel.text().strip() or None,
                    servicio_principal_id=servicio_id,
                    fecha=inicio,
                    notas=te_notas.toPlainText().strip() or None,
                )
                QMessageBox.information(self, "Éxito", "Cita creada")
                dialog.accept()
                self._cargar_citas()
            except Exception as exc:
                QMessageBox.warning(self, "Error", str(exc))

        buttons.accepted.connect(crear_cita)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

