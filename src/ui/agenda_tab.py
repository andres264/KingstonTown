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

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Barbero", "Cliente", "Servicio", "Estado", "Notas"]
        )
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self._estilizar_tabla(self.tabla)
        layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar cita")
        self.btn_noshow = QPushButton("Marca no asistió")
        self.btn_cancelar.clicked.connect(self._cancelar)
        self.btn_noshow.clicked.connect(self._no_show)
        acciones.addWidget(self.btn_cancelar)
        acciones.addWidget(self.btn_noshow)
        acciones.addStretch()
        layout.addLayout(acciones)

        layout.addWidget(self._titulo_label("Crear cita"))
        form = QHBoxLayout()
        self.barbero_combo = QComboBox()
        self.servicio_combo = QComboBox()
        self.fecha_cita = QDateEdit(QDate.currentDate())
        self.fecha_cita.setCalendarPopup(True)
        self.hora_cita = QTimeEdit()
        self.hora_cita.setDisplayFormat("hh:mm ap")
        self.hora_cita.setTime(QTime(9, 30))
        self.nombre_cliente = QLineEdit()
        self.nombre_cliente.setPlaceholderText("Nombre cliente")
        self.tel_cliente = QLineEdit()
        self.tel_cliente.setPlaceholderText("Teléfono (opcional)")
        self.notas = QTextEdit()
        self.notas.setPlaceholderText("Notas")
        self.notas.setFixedHeight(60)
        self.btn_crear = QPushButton("Crear")
        self.btn_crear.clicked.connect(self._crear_cita)

        form.addWidget(QLabel("Barbero"))
        form.addWidget(self.barbero_combo)
        form.addWidget(QLabel("Servicio"))
        form.addWidget(self.servicio_combo)
        form.addWidget(QLabel("Fecha"))
        form.addWidget(self.fecha_cita)
        form.addWidget(QLabel("Hora"))
        form.addWidget(self.hora_cita)
        form.addWidget(self.btn_crear)
        layout.addLayout(form)

        detalle = QHBoxLayout()
        detalle.addWidget(QLabel("Cliente"))
        detalle.addWidget(self.nombre_cliente)
        detalle.addWidget(QLabel("Teléfono"))
        detalle.addWidget(self.tel_cliente)
        detalle.addWidget(QLabel("Notas"))
        detalle.addWidget(self.notas)
        layout.addLayout(detalle)

    def _load_comboboxes(self):
        self.barbero_combo.clear()
        self.barbero_filtro.clear()
        self.barbero_filtro.addItem("Todos", None)
        for b in repositories.list_barbers():
            self.barbero_combo.addItem(b["name"], b["id"])
            if b["active"]:
                self.barbero_filtro.addItem(b["name"], b["id"])

        self.servicio_combo.clear()
        for s in repositories.list_services():
            self.servicio_combo.addItem(f"{s['name']} ({format_currency(s['price'])})", s["id"])

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
            self.tabla.setItem(row, 0, QTableWidgetItem(str(cita["id"])))
            self.tabla.setItem(row, 1, QTableWidgetItem(format_time_12h(cita["start_dt"])))
            self.tabla.setItem(row, 2, QTableWidgetItem(format_time_12h(cita["end_dt"])))
            self.tabla.setItem(row, 3, QTableWidgetItem(barberos.get(cita["barber_id"], "")))
            cliente_nombre = ""
            if cita.get("client_id"):
                cliente = repositories.get_client(cita["client_id"])
                if cliente:
                    cliente_nombre = cliente["name"]
            self.tabla.setItem(row, 4, QTableWidgetItem(cliente_nombre))
            self.tabla.setItem(row, 5, QTableWidgetItem(servicios.get(cita.get("primary_service_id"), "")))
            self.tabla.setItem(row, 6, QTableWidgetItem(cita["status"]))
            self.tabla.setItem(row, 7, QTableWidgetItem(cita.get("notes") or ""))

    def _crear_cita(self):
        try:
            barber_id = self.barbero_combo.currentData()
            servicio_id = self.servicio_combo.currentData()
            fecha = self.fecha_cita.date().toPython()
            hora = self.hora_cita.time().toPython()
            inicio = datetime.combine(fecha, hora)
            agenda_service.crear_cita(
                barber_id=barber_id,
                client_name=self.nombre_cliente.text().strip() or None,
                client_phone=self.tel_cliente.text().strip() or None,
                servicio_principal_id=servicio_id,
                fecha=inicio,
                notas=self.notas.toPlainText().strip() or None,
            )
            QMessageBox.information(self, "Éxito", "Cita creada")
            self._cargar_citas()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

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

    def _titulo_label(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:16px; font-weight:bold;")
        return lbl

    def _estilizar_tabla(self, tabla: QTableWidget):
        tabla.horizontalHeader().setStyleSheet(
            "QHeaderView::section {background-color:#e3f2fd; font-weight:bold;}"
        )

