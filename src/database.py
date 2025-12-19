import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

from . import config


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_db(self) -> None:
        """Crea tablas y aplica semilla inicial."""
        self._create_tables()
        self._seed_barbers()
        self._seed_services()

    def _create_tables(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS barbers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS services(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                barber_earning REAL NOT NULL,
                shop_liquidation REAL NOT NULL,
                duration_min INTEGER NOT NULL DEFAULT 30,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS clients(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT
            );
            CREATE TABLE IF NOT EXISTS appointments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barber_id INTEGER NOT NULL,
                primary_service_id INTEGER,
                client_id INTEGER,
                start_dt TEXT NOT NULL,
                end_dt TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(barber_id) REFERENCES barbers(id),
                FOREIGN KEY(primary_service_id) REFERENCES services(id),
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            CREATE INDEX IF NOT EXISTS idx_appointments_barber_date ON appointments(barber_id, start_dt);
            CREATE TABLE IF NOT EXISTS payments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER UNIQUE NOT NULL,
                total_amount REAL NOT NULL,
                barber_total REAL NOT NULL,
                shop_total REAL NOT NULL,
                payment_method TEXT NOT NULL,
                paid_at TEXT NOT NULL,
                FOREIGN KEY(appointment_id) REFERENCES appointments(id)
            );
            CREATE TABLE IF NOT EXISTS appointment_service_lines(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                unit_price_snapshot REAL NOT NULL,
                barber_earning_snapshot REAL NOT NULL,
                shop_liquidation_snapshot REAL NOT NULL,
                FOREIGN KEY(appointment_id) REFERENCES appointments(id),
                FOREIGN KEY(service_id) REFERENCES services(id)
            );
            CREATE TABLE IF NOT EXISTS barber_days_off(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barber_id INTEGER NOT NULL,
                off_date TEXT NOT NULL,
                note TEXT,
                UNIQUE(barber_id, off_date),
                FOREIGN KEY(barber_id) REFERENCES barbers(id)
            );
            """
        )
        self.conn.commit()

    def _seed_barbers(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM barbers;")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO barbers(name, active) VALUES(?, ?);", config.DEFAULT_BARBERS)
            self.conn.commit()

    def _seed_services(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM services;")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO services(name, price, barber_earning, shop_liquidation, duration_min, active) VALUES(?,?,?,?,?,?);",
                config.DEFAULT_SERVICES,
            )
            self.conn.commit()

    def run_query(self, query: str, params: Tuple = (), many: bool = False) -> Iterable[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(query, params)
        if many:
            return cur.fetchall()
        return cur.fetchone()


db = Database(config.DB_PATH)

