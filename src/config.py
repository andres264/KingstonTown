import os
from pathlib import Path

# Rutas principales
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "barberia.db"
BACKUP_DIR = BASE_DIR / "backups"
LOGO_PATH = BASE_DIR / "logo_barberia.png"

# Horario de la barbería
HORARIO_APERTURA = (9, 30)  # 09:30
HORARIO_CIERRE = (20, 0)    # 20:00
INTERVALO_MINUTOS = 15

# Estados de cita
ESTADOS_CITA = ["RESERVADA", "ATENDIDA", "CANCELADA", "NO ASISTIÓ"]

# Métodos de pago
METODOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta"]


def ensure_directories() -> None:
    """Crea carpetas requeridas (backups) si no existen."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# Semilla de servicios y barberos
DEFAULT_BARBERS = [
    ("Esteban Fabra", 1),
    ("Miguel Giraldo", 1),
    ("Miguel Bedoya", 1),
]

DEFAULT_SERVICES = [
    ("Corte", 20000, 10000, 10000, 40, 1),
    ("Corte y barba", 28000, 16000, 12000, 55, 1),
    ("Marcada", 12000, 12000, 0, 30, 1),
    ("Cejas", 6000, 6000, 0, 20, 1),
    ("Mascarilla negra", 2000, 0, 2000, 15, 1),
]


