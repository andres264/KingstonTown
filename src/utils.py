from datetime import datetime, time, timedelta
from typing import Tuple

from . import config


def format_currency(value: float) -> str:
    """Formatea número a COP con separador de miles usando punto."""
    try:
        formatted = f"${value:,.0f}"
    except Exception:
        formatted = "$0"
    return formatted.replace(",", ".")


def clamp_time_to_schedule(dt: datetime) -> datetime:
    """Ajusta un datetime al rango permitido del día."""
    start = dt.replace(
        hour=config.HORARIO_APERTURA[0],
        minute=config.HORARIO_APERTURA[1],
        second=0,
        microsecond=0,
    )
    end = dt.replace(
        hour=config.HORARIO_CIERRE[0],
        minute=config.HORARIO_CIERRE[1],
        second=0,
        microsecond=0,
    )
    if dt < start:
        return start
    if dt > end:
        return end
    return dt


def is_within_schedule(start_dt: datetime, end_dt: datetime) -> bool:
    """Verifica que la cita esté dentro del horario."""
    apertura = time(*config.HORARIO_APERTURA)
    cierre = time(*config.HORARIO_CIERRE)
    return (
        start_dt.time() >= apertura
        and end_dt.time() <= cierre
        and start_dt.date() == end_dt.date()
    )


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Detecta solapamiento entre intervalos."""
    return a_start < b_end and b_start < a_end


def add_minutes(dt: datetime, minutes: int) -> datetime:
    return dt + timedelta(minutes=minutes)


def parse_date(date_str: str) -> datetime.date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def to_iso(dt: datetime) -> str:
    return dt.isoformat()


def format_time_12h(iso_dt: str) -> str:
    """Convierte un datetime ISO a formato 12h con am/pm."""
    try:
        dt = datetime.fromisoformat(iso_dt)
        txt = dt.strftime("%I:%M %p").lower()
        return txt.lstrip("0")
    except Exception:
        return iso_dt


