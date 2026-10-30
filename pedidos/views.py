import re

from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EditarPedidoForm, PedidoForm
from .models import Paquete, Pedido
from .services import avanzar_paquete, crear_pedido, rechazar_paquete


def registrar(request):
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

    return render(request, "pedidos/inicio.html", {"form": form, "pagina": "registrar"})


def inicio(request):
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
    ).prefetch_related(Prefetch("paquetes", queryset=Paquete.objects.order_by("id").prefetch_related("movimientos"))).order_by("-creado_en")

    def orden_pedido(pedido):
        coincidencia = re.fullmatch(r"PED-([0-9]+)", pedido.numero, re.IGNORECASE)
        if coincidencia:
            return (0, int(coincidencia.group(1)), pedido.numero.casefold())
        return (1, 0, pedido.numero.casefold())

    pedidos = sorted(pedidos, key=orden_pedido)

    for pedido in pedidos:
        if pedido.listos and pedido.listos == pedido.paquetes.count():
            pedido.estado_resumen, pedido.estado_texto = "listo", "Listo"
        elif pedido.en_revision:
            pedido.estado_resumen, pedido.estado_texto = "revision", "En revisión"
        elif pedido.en_proceso or pedido.listos:
            pedido.estado_resumen, pedido.estado_texto = "en_proceso", "En proceso"
        else:
            pedido.estado_resumen, pedido.estado_texto = "pendiente", "Pendiente"
        pedido.avance = round(
            pedido.unidades_listas * 100 / pedido.unidades, 2
        )

    columnas = [(estado, etiqueta, []) for estado, etiqueta in Paquete.Estado.choices]
    for pedido in pedidos:
        for numero, paquete in enumerate(pedido.paquetes.all(), start=1):
            paquete.numero_visible = numero
            paquete.rechazos = sum(m.es_rechazo for m in paquete.movimientos.all())
            for estado, etiqueta, lista in columnas:
                if paquete.estado == estado:
                    lista.append((pedido, paquete))
                    break
    resumen = {"pedidos": len(pedidos), "unidades_listas": sum(p.unidades_listas for p in pedidos), "unidades_totales": sum(p.unidades for p in pedidos), "en_revision": sum(p.en_revision for p in pedidos)}
    return render(
        request, "pedidos/inicio.html",
        {"pedidos": pedidos, "pagina": "seguimiento", "columnas": columnas, "resumen": resumen},
    )


def pedido_completo(pedido):
    paquetes = pedido.paquetes.all()
    return paquetes.exists() and not paquetes.exclude(estado=Paquete.Estado.LISTO).exists()


def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido_completo(pedido):
        messages.error(request, f"{pedido.numero}: el pedido está listo y no se puede editar.")
        return redirect("inicio")
    form = EditarPedidoForm(request.POST or None, instance=pedido)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            form.add_error("numero", "Ya existe un pedido con este número.")
        else:
            messages.success(request, f"{pedido.numero}: pedido actualizado correctamente.")
            return redirect("inicio")
    return render(request, "pedidos/inicio.html", {"form": form, "pagina": "editar", "pedido_edicion": pedido})


@require_POST
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido_completo(pedido):
        messages.error(request, f"{pedido.numero}: el pedido está listo y no se puede eliminar.")
        return redirect("inicio")
    numero = pedido.numero
    pedido.delete()
    messages.success(request, f"{numero}: pedido y paquetes eliminados.")
    return redirect("inicio")


@require_POST
def cambiar_estado(request, paquete_id, accion):
    get_object_or_404(Paquete, pk=paquete_id)

    actor = request.user.get_username() if request.user.is_authenticated else "Sin identificar"
    try:
        if accion == "avanzar":
            paquete = avanzar_paquete(paquete_id, actor=actor)
            numero = Paquete.objects.filter(pedido_id=paquete.pedido_id, pk__lte=paquete.pk).count()
            messages.success(request, f"{paquete.pedido.numero} · Paquete #{numero}: avanzó a {paquete.get_estado_display()}.")
        elif accion == "rechazar":
            paquete = rechazar_paquete(paquete_id, actor=actor)
            numero = Paquete.objects.filter(pedido_id=paquete.pedido_id, pk__lte=paquete.pk).count()
            messages.success(request, f"{paquete.pedido.numero} · Paquete #{numero}: rechazado y devuelto a {paquete.get_estado_display()}.")
        else:
            messages.error(request, "Acción no válida.")
    except ValueError as error:
        messages.error(request, str(error))

    return redirect("inicio")
