from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registrar/", views.registrar, name="registrar"),
    path("pedidos/<int:pedido_id>/editar/", views.editar_pedido, name="editar_pedido"),
    path("pedidos/<int:pedido_id>/eliminar/", views.eliminar_pedido, name="eliminar_pedido"),
    path(
        "paquetes/<int:paquete_id>/<str:accion>/",
        views.cambiar_estado,
        name="cambiar_estado",
    ),
]