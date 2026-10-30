import re

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
        error_messages = {
            "numero": {"required": "Ingresa el número de pedido.", "unique": "Ya existe un pedido con este número."},
            "cliente": {"required": "Ingresa el nombre del cliente."},
            "unidades": {"required": "Ingresa la cantidad de unidades.", "invalid": "Ingresa un número entero mayor que cero.", "min_value": "La cantidad debe ser mayor que cero."},
        }
        widgets = {
            "numero": forms.TextInput(
                attrs={"placeholder": "Ejemplo: PED-001"}
            ),
            "cliente": forms.TextInput(
                attrs={"placeholder": "Nombre del cliente"}
            ),
            "unidades": forms.NumberInput(
                attrs={"min": 1, "step": 1, "placeholder": "Ej: 250"}
            ),
        }
    def clean_numero(self):
        numero = self.cleaned_data["numero"].strip().upper()
        if not re.fullmatch(r"PED-[0-9]{3,}", numero):
            raise forms.ValidationError("Usa el formato PED-001: PED-, seguido de al menos 3 dígitos.")
        return numero


class EditarPedidoForm(PedidoForm):
    class Meta(PedidoForm.Meta):
        fields = ["numero", "cliente"]
