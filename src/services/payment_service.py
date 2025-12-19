from datetime import datetime
from typing import List, Dict

from .. import repositories
from ..utils import format_currency


class PaymentService:
    def cobrar(
        self,
        appointment_id: int,
        servicios: List[Dict[str, int]],
        metodo_pago: str,
    ) -> Dict[str, float]:
        cita = repositories.get_appointment(appointment_id)
        if not cita:
            raise ValueError("Cita no encontrada")

        existing = repositories.get_payment_with_lines(appointment_id)
        if existing:
            raise ValueError("La cita ya fue cobrada")

        servicios_catalogo = {s["id"]: s for s in repositories.list_services(include_inactive=True)}
        lines = []
        total = 0.0
        total_barbero = 0.0
        total_tienda = 0.0
        for item in servicios:
            servicio_id = item["service_id"]
            qty = int(item.get("qty", 1))
            servicio = servicios_catalogo.get(servicio_id)
            if not servicio:
                raise ValueError("Servicio no encontrado")
            line_total = servicio["price"] * qty
            total += line_total
            total_barbero += servicio["barber_earning"] * qty
            total_tienda += servicio["shop_liquidation"] * qty
            lines.append(
                (
                    appointment_id,
                    servicio_id,
                    qty,
                    servicio["price"],
                    servicio["barber_earning"],
                    servicio["shop_liquidation"],
                )
            )

        repositories.create_payment(
            appointment_id=appointment_id,
            total_amount=total,
            barber_total=total_barbero,
            shop_total=total_tienda,
            payment_method=metodo_pago,
            paid_at=datetime.now(),
            lines=lines,
        )
        repositories.update_appointment_status(appointment_id, "ATENDIDA")
        return {
            "total": total,
            "barbero": total_barbero,
            "barberia": total_tienda,
            "mensaje": f"Cobro guardado: {format_currency(total)}",
        }


payment_service = PaymentService()

