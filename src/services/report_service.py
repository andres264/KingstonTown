from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from ..database import db
from ..utils import format_currency


class ReportService:
    def resumen(self, inicio: datetime, fin: datetime) -> Dict:
        conn = db.conn
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.*, a.barber_id, b.name as barber_name
            FROM payments p
            JOIN appointments a ON p.appointment_id = a.id
            JOIN barbers b ON a.barber_id = b.id
            WHERE p.paid_at BETWEEN ? AND ?
            ORDER BY p.paid_at;
            """,
            (inicio.isoformat(), fin.isoformat()),
        )
        pagos = cur.fetchall()

        totales = {"ventas": 0.0, "barberos": 0.0, "barberia": 0.0}
        por_barbero = defaultdict(lambda: {"ventas": 0.0, "barbero": 0.0, "barberia": 0.0})
        por_dia = defaultdict(lambda: {"ventas": 0.0, "barbero": 0.0, "barberia": 0.0})

        for p in pagos:
            totales["ventas"] += p["total_amount"]
            totales["barberos"] += p["barber_total"]
            totales["barberia"] += p["shop_total"]
            dia = p["paid_at"][:10]
            por_barbero[p["barber_name"]]["ventas"] += p["total_amount"]
            por_barbero[p["barber_name"]]["barbero"] += p["barber_total"]
            por_barbero[p["barber_name"]]["barberia"] += p["shop_total"]
            por_dia[dia]["ventas"] += p["total_amount"]
            por_dia[dia]["barbero"] += p["barber_total"]
            por_dia[dia]["barberia"] += p["shop_total"]

        citas_totales = self._contar_citas(inicio, fin)
        return {
            "pagos": [dict(p) for p in pagos],
            "totales": totales,
            "por_barbero": por_barbero,
            "por_dia": por_dia,
            "citas": citas_totales,
        }

    def _contar_citas(self, inicio: datetime, fin: datetime) -> Dict[str, int]:
        cur = db.conn.cursor()
        cur.execute(
            """
            SELECT status, COUNT(*) as total
            FROM appointments
            WHERE start_dt BETWEEN ? AND ?
            GROUP BY status;
            """,
            (inicio.isoformat(), fin.isoformat()),
        )
        resumen = {"ATENDIDA": 0, "CANCELADA": 0, "NO ASISTIÓ": 0, "RESERVADA": 0}
        for row in cur.fetchall():
            resumen[row["status"]] = row["total"]
        return resumen

    def exportar_pdf(self, path: Path, data: Dict, titulo: str, rango: Tuple[datetime, datetime]) -> Path:
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(titulo, styles["Title"]))
        story.append(Paragraph(f"Rango: {rango[0].strftime('%d/%m/%Y')} - {rango[1].strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Spacer(1, 12))
        tot = data["totales"]
        story.append(
            Paragraph(
                f"Total ventas: {format_currency(tot['ventas'])} | Ganancia barberos: {format_currency(tot['barberos'])} | Liquidación barbería: {format_currency(tot['barberia'])}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

        # Tabla por barbero
        if data["por_barbero"]:
            tabla_data = [["Barbero", "Ventas", "Barbero", "Barbería"]]
            for barber, valores in data["por_barbero"].items():
                tabla_data.append(
                    [
                        barber,
                        format_currency(valores["ventas"]),
                        format_currency(valores["barbero"]),
                        format_currency(valores["barberia"]),
                    ]
                )
            table = Table(tabla_data, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ]
                )
            )
            story.append(Paragraph("Detalle por barbero", styles["Heading3"]))
            story.append(table)

        story.append(Spacer(1, 16))
        doc.build(story)
        return path


report_service = ReportService()


