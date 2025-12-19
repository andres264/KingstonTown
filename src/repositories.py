from datetime import datetime, date
from typing import List, Optional, Tuple

from .database import db
from .utils import to_iso


# BARBEROS
def list_barbers(include_inactive: bool = True) -> List[dict]:
    cur = db.conn.cursor()
    if include_inactive:
        cur.execute("SELECT * FROM barbers ORDER BY name;")
    else:
        cur.execute("SELECT * FROM barbers WHERE active=1 ORDER BY name;")
    return [dict(r) for r in cur.fetchall()]


def create_barber(name: str, active: bool = True) -> int:
    cur = db.conn.cursor()
    cur.execute("INSERT INTO barbers(name, active) VALUES(?, ?);", (name, int(active)))
    db.conn.commit()
    return cur.lastrowid


def update_barber(barber_id: int, name: str, active: bool) -> None:
    cur = db.conn.cursor()
    cur.execute("UPDATE barbers SET name=?, active=? WHERE id=?;", (name, int(active), barber_id))
    db.conn.commit()


# SERVICIOS
def list_services(include_inactive: bool = False) -> List[dict]:
    cur = db.conn.cursor()
    if include_inactive:
        cur.execute("SELECT * FROM services ORDER BY active DESC, name;")
    else:
        cur.execute("SELECT * FROM services WHERE active=1 ORDER BY name;")
    return [dict(r) for r in cur.fetchall()]


def create_service(name: str, price: float, barber_earning: float, shop_liquidation: float, duration_min: int, active: bool = True) -> int:
    cur = db.conn.cursor()
    cur.execute(
        """
        INSERT INTO services(name, price, barber_earning, shop_liquidation, duration_min, active)
        VALUES(?,?,?,?,?,?);
        """,
        (name, price, barber_earning, shop_liquidation, duration_min, int(active)),
    )
    db.conn.commit()
    return cur.lastrowid


def update_service(service_id: int, name: str, price: float, barber_earning: float, shop_liquidation: float, duration_min: int, active: bool) -> None:
    cur = db.conn.cursor()
    cur.execute(
        """
        UPDATE services
        SET name=?, price=?, barber_earning=?, shop_liquidation=?, duration_min=?, active=?
        WHERE id=?;
        """,
        (name, price, barber_earning, shop_liquidation, duration_min, int(active), service_id),
    )
    db.conn.commit()


# CLIENTES
def create_client(name: str, phone: Optional[str]) -> int:
    cur = db.conn.cursor()
    cur.execute("INSERT INTO clients(name, phone) VALUES(?,?);", (name, phone))
    db.conn.commit()
    return cur.lastrowid


def get_client(client_id: int) -> Optional[dict]:
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?;", (client_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def get_or_create_client(name: str, phone: Optional[str]) -> int:
    cur = db.conn.cursor()
    cur.execute("SELECT id FROM clients WHERE name=? AND (phone=? OR phone IS NULL);", (name, phone))
    row = cur.fetchone()
    if row:
        return row[0]
    return create_client(name, phone)


# DESCANSOS
def list_days_off(barber_id: int) -> List[dict]:
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM barber_days_off WHERE barber_id=? ORDER BY off_date;", (barber_id,))
    return [dict(r) for r in cur.fetchall()]


def add_day_off(barber_id: int, off_date: date, note: Optional[str] = None) -> None:
    cur = db.conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO barber_days_off(barber_id, off_date, note) VALUES(?,?,?);",
        (barber_id, off_date.isoformat(), note),
    )
    db.conn.commit()


def remove_day_off(barber_id: int, off_date: date) -> None:
    cur = db.conn.cursor()
    cur.execute("DELETE FROM barber_days_off WHERE barber_id=? AND off_date=?;", (barber_id, off_date.isoformat()))
    db.conn.commit()


def is_barber_off(barber_id: int, date_value: date) -> bool:
    cur = db.conn.cursor()
    cur.execute(
        "SELECT 1 FROM barber_days_off WHERE barber_id=? AND off_date=?;",
        (barber_id, date_value.isoformat()),
    )
    return cur.fetchone() is not None


# CITAS
def list_appointments_by_range(start_iso: str, end_iso: str, barber_id: Optional[int] = None, status: Optional[str] = None) -> List[dict]:
    cur = db.conn.cursor()
    query = "SELECT * FROM appointments WHERE start_dt BETWEEN ? AND ?"
    params: Tuple = (start_iso, end_iso)
    if barber_id:
        query += " AND barber_id=?"
        params += (barber_id,)
    if status:
        query += " AND status=?"
        params += (status,)
    query += " ORDER BY start_dt;"
    cur.execute(query, params)
    return [dict(r) for r in cur.fetchall()]


def count_appointments_for_barber_and_date(barber_id: int, date_str: str) -> int:
    cur = db.conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM appointments WHERE barber_id=? AND date(start_dt)=? AND status IN ('RESERVADA','ATENDIDA');",
        (barber_id, date_str),
    )
    row = cur.fetchone()
    return row[0] if row else 0


def get_appointment(appointment_id: int) -> Optional[dict]:
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM appointments WHERE id=?;", (appointment_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def create_appointment(
    barber_id: int,
    primary_service_id: int,
    client_id: Optional[int],
    start_dt: datetime,
    end_dt: datetime,
    status: str,
    notes: Optional[str],
) -> int:
    cur = db.conn.cursor()
    cur.execute(
        """
        INSERT INTO appointments(barber_id, primary_service_id, client_id, start_dt, end_dt, status, notes, created_at)
        VALUES(?,?,?,?,?,?,?,?);
        """,
        (
            barber_id,
            primary_service_id,
            client_id,
            to_iso(start_dt),
            to_iso(end_dt),
            status,
            notes,
            datetime.utcnow().isoformat(),
        ),
    )
    db.conn.commit()
    return cur.lastrowid


def update_appointment(
    appointment_id: int,
    barber_id: int,
    start_dt: datetime,
    end_dt: datetime,
    status: str,
    notes: Optional[str],
    primary_service_id: Optional[int],
) -> None:
    cur = db.conn.cursor()
    cur.execute(
        """
        UPDATE appointments
        SET barber_id=?, start_dt=?, end_dt=?, status=?, notes=?, primary_service_id=?
        WHERE id=?;
        """,
        (barber_id, to_iso(start_dt), to_iso(end_dt), status, notes, primary_service_id, appointment_id),
    )
    db.conn.commit()


def update_appointment_status(appointment_id: int, status: str) -> None:
    cur = db.conn.cursor()
    cur.execute("UPDATE appointments SET status=? WHERE id=?;", (status, appointment_id))
    db.conn.commit()


def delete_appointment(appointment_id: int) -> None:
    cur = db.conn.cursor()
    cur.execute("DELETE FROM appointments WHERE id=?;", (appointment_id,))
    db.conn.commit()


def has_overlap(barber_id: int, start_dt: datetime, end_dt: datetime, exclude_id: Optional[int] = None) -> bool:
    cur = db.conn.cursor()
    query = """
    SELECT 1 FROM appointments
    WHERE barber_id=?
    AND status IN ('RESERVADA', 'ATENDIDA')
    AND NOT(end_dt <= ? OR start_dt >= ?)
    """
    params: Tuple = (barber_id, to_iso(start_dt), to_iso(end_dt))
    if exclude_id:
        query += " AND id != ?"
        params += (exclude_id,)
    cur.execute(query, params)
    return cur.fetchone() is not None


# PAGOS
def create_payment(
    appointment_id: int,
    total_amount: float,
    barber_total: float,
    shop_total: float,
    payment_method: str,
    paid_at: datetime,
    lines: List[Tuple[int, int, float, float, float]],
) -> int:
    cur = db.conn.cursor()
    cur.execute(
        """
        INSERT INTO payments(appointment_id, total_amount, barber_total, shop_total, payment_method, paid_at)
        VALUES(?,?,?,?,?,?);
        """,
        (appointment_id, total_amount, barber_total, shop_total, payment_method, to_iso(paid_at)),
    )
    payment_id = cur.lastrowid
    cur.executemany(
        """
        INSERT INTO appointment_service_lines(appointment_id, service_id, qty, unit_price_snapshot, barber_earning_snapshot, shop_liquidation_snapshot)
        VALUES(?,?,?,?,?,?);
        """,
        lines,
    )
    db.conn.commit()
    return payment_id


def list_payments_by_range(start_iso: str, end_iso: str) -> List[dict]:
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM payments WHERE paid_at BETWEEN ? AND ? ORDER BY paid_at;", (start_iso, end_iso))
    return [dict(r) for r in cur.fetchall()]


def get_payment_with_lines(appointment_id: int) -> Optional[Tuple[dict, List[dict]]]:
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM payments WHERE appointment_id=?;", (appointment_id,))
    pay = cur.fetchone()
    if not pay:
        return None
    cur.execute("SELECT * FROM appointment_service_lines WHERE appointment_id=?;", (appointment_id,))
    lines = cur.fetchall()
    return dict(pay), [dict(l) for l in lines]


def delete_payment(appointment_id: int) -> None:
    cur = db.conn.cursor()
    cur.execute("DELETE FROM appointment_service_lines WHERE appointment_id=?;", (appointment_id,))
    cur.execute("DELETE FROM payments WHERE appointment_id=?;", (appointment_id,))
    db.conn.commit()

