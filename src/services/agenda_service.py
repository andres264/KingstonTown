from datetime import datetime, timedelta
from typing import List, Optional

from .. import config, repositories
from ..utils import add_minutes, is_within_schedule, overlaps


class AgendaService:
    def __init__(self):
        pass

    def crear_cita(
        self,
        barber_id: int,
        client_name: Optional[str],
        client_phone: Optional[str],
        servicio_principal_id: int,
        fecha: datetime,
        notas: Optional[str] = None,
    ) -> int:
        servicio = self._get_servicio(servicio_principal_id)
        start_dt = fecha
        end_dt = add_minutes(start_dt, servicio["duration_min"])
        self._validar_barbero_activo(barber_id)
        self._validar_descanso(barber_id, start_dt)
        self._validar_horario(start_dt, end_dt)
        self._validar_choque(barber_id, start_dt, end_dt)

        client_id = None
        if client_name:
            client_id = repositories.get_or_create_client(client_name, client_phone)
        return repositories.create_appointment(
            barber_id=barber_id,
            primary_service_id=servicio_principal_id,
            client_id=client_id,
            start_dt=start_dt,
            end_dt=end_dt,
            status="RESERVADA",
            notes=notas,
        )

    def editar_cita(
        self,
        appointment_id: int,
        barber_id: int,
        fecha_inicio: datetime,
        servicio_principal_id: int,
        notas: Optional[str],
    ) -> None:
        cita = repositories.get_appointment(appointment_id)
        if not cita:
            raise ValueError("Cita no encontrada")
        servicio = self._get_servicio(servicio_principal_id)
        start_dt = fecha_inicio
        end_dt = add_minutes(start_dt, servicio["duration_min"])
        self._validar_descanso(barber_id, start_dt)
        self._validar_horario(start_dt, end_dt)
        self._validar_choque(barber_id, start_dt, end_dt, exclude_id=appointment_id)
        repositories.update_appointment(
            appointment_id, barber_id, start_dt, end_dt, cita["status"], notas, servicio_principal_id
        )

    def reprogramar(self, appointment_id: int, barber_id: int, nueva_fecha: datetime) -> None:
        cita = repositories.get_appointment(appointment_id)
        if not cita:
            raise ValueError("Cita no encontrada")
        servicio = self._infer_service_duration(cita)
        start_dt = nueva_fecha
        end_dt = add_minutes(start_dt, servicio["duration_min"])
        self._validar_descanso(barber_id, start_dt)
        self._validar_horario(start_dt, end_dt)
        self._validar_choque(barber_id, start_dt, end_dt, exclude_id=appointment_id)
        repositories.update_appointment(
            appointment_id, barber_id, start_dt, end_dt, cita["status"], cita.get("notes"), cita.get("primary_service_id")
        )

    def cancelar(self, appointment_id: int) -> None:
        repositories.update_appointment_status(appointment_id, "CANCELADA")

    def marcar_no_show(self, appointment_id: int) -> None:
        repositories.update_appointment_status(appointment_id, "NO ASISTIÓ")

    def listar_por_rango(self, inicio: datetime, fin: datetime, barber_id: Optional[int], estado: Optional[str]):
        return repositories.list_appointments_by_range(inicio.isoformat(), fin.isoformat(), barber_id, estado)

    # Validaciones internas
    def _validar_barbero_activo(self, barber_id: int) -> None:
        barberos = repositories.list_barbers()
        if not any(b["id"] == barber_id and b["active"] for b in barberos):
            raise ValueError("El barbero no está activo")

    def _validar_descanso(self, barber_id: int, start_dt: datetime) -> None:
        if repositories.is_barber_off(barber_id, start_dt.date()):
            raise ValueError(f"El barbero descansa el {start_dt.date().strftime('%d/%m/%Y')}")

    def _validar_horario(self, start_dt: datetime, end_dt: datetime) -> None:
        if not is_within_schedule(start_dt, end_dt):
            raise ValueError("La cita está fuera del horario 09:30 - 20:00")
        if end_dt <= start_dt:
            raise ValueError("La hora fin debe ser posterior a la hora inicio")

    def _validar_intervalo(self, start_dt: datetime, end_dt: datetime) -> None:
        return

    def _validar_choque(self, barber_id: int, start_dt: datetime, end_dt: datetime, exclude_id: Optional[int] = None) -> None:
        if repositories.has_overlap(barber_id, start_dt, end_dt, exclude_id=exclude_id):
            raise ValueError("Existe un choque de horario con otra cita para el mismo barbero")

    def _get_servicio(self, service_id: int) -> dict:
        servicios = repositories.list_services(include_inactive=False)
        for s in servicios:
            if s["id"] == service_id:
                return s
        raise ValueError("Servicio no encontrado")

    def _infer_service_duration(self, cita: dict) -> dict:
        service_id = cita.get("primary_service_id")
        if service_id:
            try:
                return self._get_servicio(service_id)
            except Exception:
                pass
        return {"duration_min": config.INTERVALO_MINUTOS}


agenda_service = AgendaService()

