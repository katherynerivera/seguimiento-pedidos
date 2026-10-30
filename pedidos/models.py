from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Pedido(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    cliente = models.CharField(max_length=150)
    unidades = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente}"


class Paquete(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        REVISION = "revision", "Revisión"
        LISTO = "listo", "Listo"

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="paquetes",
    )
    unidades = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    def __str__(self):
        return f"Paquete {self.pk} - {self.get_estado_display()}"