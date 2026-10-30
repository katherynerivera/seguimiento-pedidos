from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "paquetes/<int:paquete_id>/<str:accion>/",
        views.cambiar_estado,
        name="cambiar_estado",
    ),
]