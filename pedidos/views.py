from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PedidoForm
from .models import Paquete, Pedido
from .services import avanzar_paquete, crear_pedido, rechazar_paquete


def inicio(request):
    if request.method == "POST":
        form = PedidoForm(request.POST)

        if form.is_valid():
            try:
                crear_pedido(**form.cleaned_data)
            except IntegrityError:
                form.add_error("numero", "Este número de pedido ya existe.")
            else:
                messages.success(request, "Pedido registrado correctamente.")
                return redirect("inicio")
    else:
        form = PedidoForm()

    pedidos = Pedido.objects.annotate(
        pendientes=Count(
            "paquetes",
            filter=Q(paquetes__estado=Paquete.Estado.PENDIENTE),
        ),
        en_proceso=Count(
            "paquetes",
            filter=Q(paquetes__estado=Paquete.Estado.EN_PROCESO),
        ),
        en_revision=Count(
            "paquetes",
            filter=Q(paquetes__estado=Paquete.Estado.REVISION),
        ),
        listos=Count(
            "paquetes",
            filter=Q(paquetes__estado=Paquete.Estado.LISTO),
        ),
        unidades_listas=Sum(
            "paquetes__unidades",
            filter=Q(paquetes__estado=Paquete.Estado.LISTO),
            default=0,
        ),
    ).prefetch_related("paquetes").order_by("-creado_en")

    for pedido in pedidos:
        pedido.avance = round(
            pedido.unidades_listas * 100 / pedido.unidades, 2
        )

    return render(
        request,
        "pedidos/inicio.html",
        {"form": form, "pedidos": pedidos},
    )


@require_POST
def cambiar_estado(request, paquete_id, accion):
    get_object_or_404(Paquete, pk=paquete_id)

    try:
        if accion == "avanzar":
            avanzar_paquete(paquete_id)
            messages.success(request, "Paquete actualizado.")
        elif accion == "rechazar":
            rechazar_paquete(paquete_id)
            messages.success(request, "Paquete devuelto a En proceso.")
        else:
            messages.error(request, "Acción no válida.")
    except ValueError as error:
        messages.error(request, str(error))

    return redirect("inicio")