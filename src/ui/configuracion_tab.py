from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QAbstractItemView,
)

from .. import repositories, config
from ..utils import format_currency
from .widgets import titulo_label, estilizar_tabla


class ConfiguracionTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._cargar_barberos()
        self._cargar_servicios()
        self._cargar_descansos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(titulo_label("Configuración"))
        layout.addWidget(titulo_label("Barberos"))
        self.tabla_barberos = QTableWidget(0, 3)
        self.tabla_barberos.setHorizontalHeaderLabels(["ID", "Nombre", "Activo"])
        estilizar_tabla(self.tabla_barberos)
        layout.addWidget(self.tabla_barberos)
        layout.addSpacing(12)
        form_barbero = QHBoxLayout()
        self.input_barbero = QLineEdit()
        self.input_barbero.setPlaceholderText("Nombre del barbero")
        self.check_barbero_activo = QCheckBox("Activo")
        self.check_barbero_activo.setChecked(True)
        btn_agregar_barbero = QPushButton("Agregar/Actualizar")
        btn_agregar_barbero.clicked.connect(self._guardar_barbero)
        form_barbero.addWidget(self.input_barbero)
        form_barbero.addWidget(self.check_barbero_activo)
        form_barbero.addWidget(btn_agregar_barbero)
        form_barbero.addStretch()
        layout.addLayout(form_barbero)

        layout.addWidget(titulo_label("Servicios"))
        self.tabla_servicios = QTableWidget(0, 6)
        self.tabla_servicios.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Precio", "Barbero", "Barbería", "Minutos"]
        )
        estilizar_tabla(self.tabla_servicios)
        self.tabla_servicios.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_servicios.itemSelectionChanged.connect(self._rellenar_servicio_form)
        layout.addWidget(self.tabla_servicios)
        form_serv = QHBoxLayout()
        self.input_nombre_serv = QLineEdit()
        self.input_nombre_serv.setPlaceholderText("Nombre servicio")
        self.precio_spin = QDoubleSpinBox()
        self.precio_spin.setMaximum(10_000_000)
        self.precio_spin.setSingleStep(1000)
        self.gan_barbero_spin = QDoubleSpinBox()
        self.gan_barbero_spin.setMaximum(10_000_000)
        self.gan_barbero_spin.setSingleStep(1000)
        self.gan_barberia_spin = QDoubleSpinBox()
        self.gan_barberia_spin.setMaximum(10_000_000)
        self.gan_barberia_spin.setSingleStep(1000)
        self.duracion_spin = QSpinBox()
        self.duracion_spin.setMinimum(config.INTERVALO_MINUTOS)
        self.duracion_spin.setMaximum(240)
        btn_serv = QPushButton("Agregar servicio")
        btn_serv.clicked.connect(self._guardar_servicio)
        self.btn_actualizar_serv = QPushButton("Actualizar servicio seleccionado")
        self.btn_actualizar_serv.clicked.connect(self._actualizar_servicio)
        form_serv.addWidget(self.input_nombre_serv)
        form_serv.addWidget(QLabel("Precio"))
        form_serv.addWidget(self.precio_spin)
        form_serv.addWidget(QLabel("Gan. barbero"))
        form_serv.addWidget(self.gan_barbero_spin)
        form_serv.addWidget(QLabel("Barbería"))
        form_serv.addWidget(self.gan_barberia_spin)
        form_serv.addWidget(QLabel("Duración (min)"))
        form_serv.addWidget(self.duracion_spin)
        form_serv.addWidget(btn_serv)
        form_serv.addWidget(self.btn_actualizar_serv)
        layout.addLayout(form_serv)
        layout.addSpacing(12)

        layout.addWidget(titulo_label("Descansos por barbero"))
        descanso = QHBoxLayout()
        self.combo_descanso_barbero = QComboBox()
        self.combo_descanso_barbero.currentIndexChanged.connect(self._cargar_descansos)
        self.fecha_descanso = QDateEdit(QDate.currentDate())
        self.fecha_descanso.setCalendarPopup(True)
        self.btn_agregar_descanso = QPushButton("Marcar descanso")
        self.btn_eliminar_descanso = QPushButton("Quitar descanso")
        self.btn_agregar_descanso.clicked.connect(self._agregar_descanso)
        self.btn_eliminar_descanso.clicked.connect(self._eliminar_descanso)
        descanso.addWidget(QLabel("Barbero"))
        descanso.addWidget(self.combo_descanso_barbero)
        descanso.addWidget(QLabel("Fecha"))
        descanso.addWidget(self.fecha_descanso)
        descanso.addWidget(self.btn_agregar_descanso)
        descanso.addWidget(self.btn_eliminar_descanso)
        descanso.addStretch()
        layout.addLayout(descanso)

        self.tabla_descansos = QTableWidget(0, 2)
        self.tabla_descansos.setHorizontalHeaderLabels(["Fecha", "Nota"])
        layout.addWidget(self.tabla_descansos)

    def _cargar_barberos(self):
        barberos = repositories.list_barbers(include_inactive=True)
        self.tabla_barberos.setRowCount(0)
        self.combo_descanso_barbero.clear()
        for idx, b in enumerate(barberos):
            self.tabla_barberos.insertRow(idx)
            self.tabla_barberos.setItem(idx, 0, QTableWidgetItem(str(b["id"])))
            self.tabla_barberos.setItem(idx, 1, QTableWidgetItem(b["name"]))
            self.tabla_barberos.setItem(idx, 2, QTableWidgetItem("Sí" if b["active"] else "No"))
            self.combo_descanso_barbero.addItem(b["name"], b["id"])

    def _guardar_barbero(self):
        nombre = self.input_barbero.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Ingrese un nombre")
            return
        # si selecciona fila, actualiza; si no, crea
        row = self.tabla_barberos.currentRow()
        activo = self.check_barbero_activo.isChecked()
        if row >= 0:
            barber_id = int(self.tabla_barberos.item(row, 0).text())
            repositories.update_barber(barber_id, nombre, activo)
        else:
            repositories.create_barber(nombre, activo)
        self.input_barbero.clear()
        self._cargar_barberos()

    def _cargar_servicios(self):
        servicios = repositories.list_services(include_inactive=True)
        self.tabla_servicios.setRowCount(0)
        self.current_service_id = None
        for idx, s in enumerate(servicios):
            self.tabla_servicios.insertRow(idx)
            self.tabla_servicios.setItem(idx, 0, QTableWidgetItem(str(s["id"])))
            self.tabla_servicios.setItem(idx, 1, QTableWidgetItem(s["name"]))
            self.tabla_servicios.setItem(idx, 2, QTableWidgetItem(format_currency(s["price"])))
            self.tabla_servicios.setItem(idx, 3, QTableWidgetItem(format_currency(s["barber_earning"])))
            self.tabla_servicios.setItem(idx, 4, QTableWidgetItem(format_currency(s["shop_liquidation"])))
            self.tabla_servicios.setItem(idx, 5, QTableWidgetItem(str(s["duration_min"])))

    def _guardar_servicio(self):
        nombre = self.input_nombre_serv.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Ingrese nombre del servicio")
            return
        repositories.create_service(
            nombre,
            self.precio_spin.value(),
            self.gan_barbero_spin.value(),
            self.gan_barberia_spin.value(),
            int(self.duracion_spin.value()),
            True,
        )
        self.input_nombre_serv.clear()
        self._cargar_servicios()

    def _rellenar_servicio_form(self):
        row = self.tabla_servicios.currentRow()
        if row < 0:
            return
        self.current_service_id = int(self.tabla_servicios.item(row, 0).text())
        self.input_nombre_serv.setText(self.tabla_servicios.item(row, 1).text())
        # valores mostrados están formateados, se requiere mapear al repo
        servicios = {s["id"]: s for s in repositories.list_services(include_inactive=True)}
        srv = servicios.get(self.current_service_id)
        if not srv:
            return
        self.precio_spin.setValue(float(srv["price"]))
        self.gan_barbero_spin.setValue(float(srv["barber_earning"]))
        self.gan_barberia_spin.setValue(float(srv["shop_liquidation"]))
        self.duracion_spin.setValue(int(srv["duration_min"]))

    def _actualizar_servicio(self):
        if not getattr(self, "current_service_id", None):
            QMessageBox.warning(self, "Seleccione", "Seleccione un servicio para actualizar")
            return
        nombre = self.input_nombre_serv.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Ingrese nombre del servicio")
            return
        repositories.update_service(
            self.current_service_id,
            nombre,
            self.precio_spin.value(),
            self.gan_barbero_spin.value(),
            self.gan_barberia_spin.value(),
            int(self.duracion_spin.value()),
            True,
        )
        QMessageBox.information(self, "Actualizado", "Servicio actualizado correctamente")
        self.input_nombre_serv.clear()
        self.current_service_id = None
        self._cargar_servicios()

    def _cargar_descansos(self):
        barber_id = self.combo_descanso_barbero.currentData()
        if barber_id is None and self.combo_descanso_barbero.count():
            barber_id = self.combo_descanso_barbero.itemData(0)
        if barber_id is None:
            return
        descansos = repositories.list_days_off(barber_id)
        self.tabla_descansos.setRowCount(0)
        for idx, d in enumerate(descansos):
            self.tabla_descansos.insertRow(idx)
            self.tabla_descansos.setItem(idx, 0, QTableWidgetItem(d["off_date"]))
            self.tabla_descansos.setItem(idx, 1, QTableWidgetItem(d.get("note") or ""))

    def _agregar_descanso(self):
        barber_id = self.combo_descanso_barbero.currentData()
        fecha = self.fecha_descanso.date().toPython()
        citas = repositories.count_appointments_for_barber_and_date(barber_id, fecha.isoformat())
        if citas > 0:
            QMessageBox.warning(self, "No permitido", "Hay citas en esa fecha. Reprograme o cancele antes de marcar descanso.")
            return
        try:
            repositories.add_day_off(barber_id, fecha)
            self._cargar_descansos()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _eliminar_descanso(self):
        barber_id = self.combo_descanso_barbero.currentData()
        fecha = self.fecha_descanso.date().toPython()
        repositories.remove_day_off(barber_id, fecha)
        self._cargar_descansos()

