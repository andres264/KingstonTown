from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..database import db
from ..utils import format_currency
from .. import repositories


class ReportService:
    def resumen(self, inicio: datetime, fin: datetime, barber_id: Optional[int] = None) -> Dict:
        conn = db.conn
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.*, a.barber_id, b.name as barber_name
            FROM payments p
            JOIN appointments a ON p.appointment_id = a.id
            JOIN barbers b ON a.barber_id = b.id
            WHERE p.paid_at BETWEEN ? AND ?
            {barber_filter}
            ORDER BY p.paid_at;
            """.format(barber_filter="AND a.barber_id=?" if barber_id else ""),
            (inicio.isoformat(), fin.isoformat()) + ((barber_id,) if barber_id else ()),
        )
        pagos = cur.fetchall()

        totales = {"ventas": 0.0, "barberos": 0.0, "barberia": 0.0}
        por_barbero = defaultdict(lambda: {"ventas": 0.0, "barbero": 0.0, "barberia": 0.0, "servicios": []})
        por_dia = defaultdict(lambda: {"ventas": 0.0, "barbero": 0.0, "barberia": 0.0})
        servicios_por_pago = defaultdict(list)

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

        # Traer líneas de servicios por pago para agregar nombres y qty
        cur.execute(
            """
            SELECT p.appointment_id, a.barber_id, b.name as barber_name, l.qty, s.name as service_name
            FROM payments p
            JOIN appointments a ON p.appointment_id = a.id
            JOIN barbers b ON a.barber_id = b.id
            JOIN appointment_service_lines l ON l.appointment_id = p.appointment_id
            JOIN services s ON s.id = l.service_id
            WHERE p.paid_at BETWEEN ? AND ?
            {barber_filter};
            """.format(barber_filter="AND a.barber_id=?" if barber_id else ""),
            (inicio.isoformat(), fin.isoformat()) + ((barber_id,) if barber_id else ()),
        )
        for row in cur.fetchall():
            etiqueta = f"{row['service_name']} x{row['qty']}"
            servicios_por_pago[row["appointment_id"]].append(etiqueta)
            por_barbero[row["barber_name"]]["servicios"].append(etiqueta)

        citas_totales = self._contar_citas(inicio, fin, barber_id)
        pagos_detalle = []
        for p in pagos:
            pagos_detalle.append(
                {
                    "appointment_id": p["appointment_id"],
                    "barber": p["barber_name"],
                    "total": p["total_amount"],
                    "servicios": ", ".join(servicios_por_pago.get(p["appointment_id"], [])),
                    "fecha": p["paid_at"][:10],
                }
            )
        return {
            "pagos": [dict(p) for p in pagos],
            "totales": totales,
            "por_barbero": por_barbero,
            "por_dia": por_dia,
            "citas": citas_totales,
            "pagos_detalle": pagos_detalle,
        }

    def _contar_citas(self, inicio: datetime, fin: datetime, barber_id: Optional[int]) -> Dict[str, int]:
        cur = db.conn.cursor()
        query = """
            SELECT status, COUNT(*) as total
            FROM appointments
            WHERE start_dt BETWEEN ? AND ?
        """
        params = [inicio.isoformat(), fin.isoformat()]
        if barber_id:
            query += " AND barber_id=?"
            params.append(barber_id)
        query += " GROUP BY status;"
        cur.execute(query, params)
        resumen = {"ATENDIDA": 0, "CANCELADA": 0, "NO ASISTIÓ": 0, "RESERVADA": 0}
        for row in cur.fetchall():
            resumen[row["status"]] = row["total"]
        return resumen

    def exportar_pdf(self, path: Path, data: Dict, titulo: str, rango: Tuple[datetime, datetime]) -> Path:
        doc = SimpleDocTemplate(str(path), pagesize=landscape(letter))
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
            tabla_data = [["Nombre Barbero", "Ventas", "Total Barbero", "Barbería", "Servicios"]]
            for barber, valores in data["por_barbero"].items():
                tabla_data.append(
                    [
                        barber,
                        format_currency(valores["ventas"]),
                        format_currency(valores["barbero"]),
                        format_currency(valores["barberia"]),
                        ", ".join(valores.get("servicios", [])),
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

    def borrar_cobro(self, appointment_id: int) -> None:
        repositories.delete_payment(appointment_id)
        repositories.update_appointment_status(appointment_id, "RESERVADA")


report_service = ReportService()


