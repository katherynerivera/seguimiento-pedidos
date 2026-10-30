from django import forms

from .models import Pedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["numero", "cliente", "unidades"]
        labels = {
            "numero": "Número de pedido",
            "cliente": "Cliente",
            "unidades": "Cantidad de unidades",
        }
        widgets = {
            "numero": forms.TextInput(
                attrs={"placeholder": "Ejemplo: PED-001"}
            ),
            "cliente": forms.TextInput(
                attrs={"placeholder": "Nombre del cliente"}
            ),
            "unidades": forms.NumberInput(
                attrs={"min": 1, "step": 1}
            ),
        }