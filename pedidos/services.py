from django.db import transaction

from .models import Paquete, Pedido


@transaction.atomic
def crear_pedido(numero, cliente, unidades):
    """Crea un pedido y divide sus unidades en paquetes de máximo 100."""
    pedido = Pedido.objects.create(
        numero=numero,
        cliente=cliente,
        unidades=unidades,
    )

    restantes = unidades

    while restantes > 0:
        unidades_paquete = min(restantes, 100)

        Paquete.objects.create(
            pedido=pedido,
            unidades=unidades_paquete,
        )

        restantes -= unidades_paquete

    return pedido


@transaction.atomic
def avanzar_paquete(paquete_id):
    """Avanza un paquete al siguiente estado permitido."""
    paquete = Paquete.objects.select_for_update().get(pk=paquete_id)

    siguiente_estado = {
        Paquete.Estado.PENDIENTE: Paquete.Estado.EN_PROCESO,
        Paquete.Estado.EN_PROCESO: Paquete.Estado.REVISION,
        Paquete.Estado.REVISION: Paquete.Estado.LISTO,
    }

    if paquete.estado not in siguiente_estado:
        raise ValueError("Este paquete ya está listo y no puede avanzar.")

    paquete.estado = siguiente_estado[paquete.estado]
    paquete.save(update_fields=["estado"])
    return paquete


@transaction.atomic
def rechazar_paquete(paquete_id):
    """Devuelve a En proceso un paquete que está en Revisión."""
    paquete = Paquete.objects.select_for_update().get(pk=paquete_id)

    if paquete.estado != Paquete.Estado.REVISION:
        raise ValueError("Solo se pueden rechazar paquetes en revisión.")

    paquete.estado = Paquete.Estado.EN_PROCESO
    paquete.save(update_fields=["estado"])
    return paquete