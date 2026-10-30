from django.test import TestCase
from django.urls import reverse

from .models import Paquete, Pedido
from .services import avanzar_paquete, crear_pedido, rechazar_paquete


class PedidoTests(TestCase):
    def test_divide_250_unidades_en_tres_paquetes(self):
        pedido = crear_pedido("PED-001", "Katherine", 250)

        unidades = list(
            pedido.paquetes.order_by("id").values_list("unidades", flat=True)
        )

        self.assertEqual(unidades, [100, 100, 50])
        self.assertTrue(
            all(p.estado == Paquete.Estado.PENDIENTE
                for p in pedido.paquetes.all())
        )

    def test_rechaza_cantidades_invalidas(self):
        for cantidad in ["0", "-1", "2.5"]:
            with self.subTest(cantidad=cantidad):
                respuesta = self.client.post(
                    reverse("inicio"),
                    {
                        "numero": "PED-002",
                        "cliente": "Cliente",
                        "unidades": cantidad,
                    },
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertFalse(Pedido.objects.filter(numero="PED-002").exists())

    def test_rechaza_numero_de_pedido_duplicado(self):
        crear_pedido("PED-003", "Cliente", 100)

        respuesta = self.client.post(
            reverse("inicio"),
            {
                "numero": "PED-003",
                "cliente": "Otro cliente",
                "unidades": 50,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Pedido.objects.filter(numero="PED-003").count(), 1)


class PaqueteTests(TestCase):
    def setUp(self):
        self.pedido = crear_pedido("PED-004", "Cliente", 250)
        self.paquete = self.pedido.paquetes.order_by("id").first()

    def test_avanza_en_orden_y_no_avanza_despues_de_listo(self):
        estados = [
            Paquete.Estado.EN_PROCESO,
            Paquete.Estado.REVISION,
            Paquete.Estado.LISTO,
        ]

        for estado in estados:
            avanzar_paquete(self.paquete.id)
            self.paquete.refresh_from_db()
            self.assertEqual(self.paquete.estado, estado)

        with self.assertRaises(ValueError):
            avanzar_paquete(self.paquete.id)

    def test_solo_se_puede_rechazar_en_revision(self):
        with self.assertRaises(ValueError):
            rechazar_paquete(self.paquete.id)

        avanzar_paquete(self.paquete.id)
        avanzar_paquete(self.paquete.id)
        rechazar_paquete(self.paquete.id)

        self.paquete.refresh_from_db()
        self.assertEqual(self.paquete.estado, Paquete.Estado.EN_PROCESO)

    def test_avance_se_calcula_por_unidades_listas(self):
        paquete_pequeno = self.pedido.paquetes.get(unidades=50)

        for _ in range(3):
            avanzar_paquete(paquete_pequeno.id)

        respuesta = self.client.get(reverse("inicio"))
        pedido_mostrado = respuesta.context["pedidos"][0]

        self.assertEqual(pedido_mostrado.unidades_listas, 50)
        self.assertEqual(pedido_mostrado.avance, 20)
        self.assertEqual(pedido_mostrado.pendientes, 2)
        self.assertEqual(pedido_mostrado.listos, 1)

    def test_cambio_de_estado_requiere_post(self):
        respuesta = self.client.get(
            reverse("cambiar_estado", args=[self.paquete.id, "avanzar"])
        )

        self.assertEqual(respuesta.status_code, 405)
        self.paquete.refresh_from_db()
        self.assertEqual(self.paquete.estado, Paquete.Estado.PENDIENTE)