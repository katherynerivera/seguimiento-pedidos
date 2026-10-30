from django.test import TestCase
from django.urls import reverse

from .models import MovimientoPaquete, Paquete, Pedido
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
                    reverse("registrar"),
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
            reverse("registrar"),
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
    def test_aviso_muestra_estado_al_avanzar_y_rechazar(self):
        url = reverse("cambiar_estado", args=[self.paquete.id, "avanzar"])
        respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "PED-004 · Paquete #1: avanzó a En proceso.")
        respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "avanzó a Revisión")
        url_rechazar = reverse("cambiar_estado", args=[self.paquete.id, "rechazar"])
        respuesta = self.client.post(url_rechazar, follow=True)
        self.assertContains(respuesta, "PED-004 · Paquete #1: rechazado y devuelto a En proceso.")

    def test_aviso_muestra_cuando_paquete_esta_listo(self):
        url = reverse("cambiar_estado", args=[self.paquete.id, "avanzar"])
        for _ in range(3):
            respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "avanzó a Listo")

    def test_paginas_separadas_y_registro_redirige_al_seguimiento(self):
        registro = self.client.get(reverse("registrar"))
        self.assertContains(registro, "Datos del pedido")
        self.assertNotContains(registro, "Pedidos registrados")
        seguimiento = self.client.get(reverse("inicio"))
        self.assertContains(seguimiento, "Pedidos registrados")
        self.assertNotContains(seguimiento, "Datos del pedido")
        respuesta = self.client.post(reverse("registrar"), {
            "numero": "PED-123", "cliente": "Cliente", "unidades": 250,
        }, follow=True)
        self.assertRedirects(respuesta, reverse("inicio"))
        self.assertContains(respuesta, "PED-123")
        self.assertEqual(Pedido.objects.get(numero="PED-123").paquetes.count(), 3)

    def test_formato_duplicado_y_campos_obligatorios(self):
        for datos, texto in [
            ({"numero": "ABC", "cliente": "A", "unidades": 1}, "Usa el formato"),
            ({"numero": "PED-004", "cliente": "A", "unidades": 1}, "Ya existe"),
            ({"numero": "", "cliente": "", "unidades": ""}, "Ingresa el nombre del cliente"),
        ]:
            with self.subTest(datos=datos):
                respuesta = self.client.post(reverse("registrar"), datos)
                self.assertContains(respuesta, texto)

    def test_editar_y_eliminar_pedido(self):
        url = reverse("editar_pedido", args=[self.pedido.pk])
        respuesta = self.client.post(url, {"numero": "PED-777", "cliente": "Nuevo"})
        self.assertRedirects(respuesta, reverse("inicio"))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.numero, "PED-777")
        self.assertEqual(self.pedido.paquetes.count(), 3)
        url = reverse("eliminar_pedido", args=[self.pedido.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("inicio"))
        self.assertFalse(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertFalse(Paquete.objects.filter(pedido_id=self.pedido.pk).exists())

    def test_historial_y_rechazos_se_guardan(self):
        avanzar_paquete(self.paquete.id, actor="operador")
        avanzar_paquete(self.paquete.id, actor="operador")
        rechazar_paquete(self.paquete.id, actor="operador")
        movimientos = MovimientoPaquete.objects.filter(paquete=self.paquete)
        self.assertEqual(movimientos.count(), 3)
        self.assertEqual(movimientos.filter(es_rechazo=True).count(), 1)
        rechazo = movimientos.get(es_rechazo=True)
        self.assertEqual((rechazo.estado_anterior, rechazo.estado_nuevo, rechazo.actor), ("revision", "en_proceso", "operador"))
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, "Rechazos: 1")
        self.assertContains(respuesta, "operador")
        self.assertContains(respuesta, "Tablero de paquetes")

    def test_accion_invalida_no_crea_movimiento(self):
        with self.assertRaises(ValueError):
            rechazar_paquete(self.paquete.id)
        self.assertFalse(MovimientoPaquete.objects.filter(paquete=self.paquete).exists())

    def test_numeracion_visible_comienza_en_uno_por_pedido(self):
        otro = crear_pedido("PED-999", "Otro", 150)
        segundo = otro.paquetes.order_by("id").last()
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, "Paquete #1:")
        self.assertContains(respuesta, "Paquete #2:")
        url = reverse("cambiar_estado", args=[segundo.pk, "avanzar"])
        respuesta = self.client.post(url, follow=True)
        self.assertContains(respuesta, "PED-999 · Paquete #2: avanzó a En proceso.")

    def test_pedidos_ordenados_por_numero_numerico(self):
        crear_pedido("PED-010", "Cliente", 10)
        crear_pedido("PED-002", "Cliente", 10)
        crear_pedido("PED-001", "Cliente", 10)
        respuesta = self.client.get(reverse("inicio"))
        numeros = [p.numero for p in respuesta.context["pedidos"]]
        self.assertEqual(numeros, ["PED-001", "PED-002", "PED-004", "PED-010"])

    def test_pedido_listo_no_se_puede_editar_ni_eliminar(self):
        for paquete in self.pedido.paquetes.all():
            for _ in range(3):
                avanzar_paquete(paquete.pk)
        editar = reverse("editar_pedido", args=[self.pedido.pk])
        eliminar = reverse("eliminar_pedido", args=[self.pedido.pk])
        respuesta = self.client.post(editar, {"numero": "PED-888", "cliente": "Otro"}, follow=True)
        self.assertContains(respuesta, "no se puede editar")
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.numero, "PED-004")
        respuesta = self.client.post(eliminar, follow=True)
        self.assertContains(respuesta, "no se puede eliminar")
        self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertNotContains(respuesta, "Editar pedido</a>")

    def test_tablero_y_porcentajes_muestran_formato_esperado(self):
        paquete = self.pedido.paquetes.order_by("id").first()
        for _ in range(3):
            avanzar_paquete(paquete.pk)
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, "40.0 %")
        self.assertContains(respuesta, "Paquete 1 de 3")
        self.assertContains(respuesta, "estado-en_proceso")

    def test_resumen_incluye_total_de_unidades_y_tarjetas_plegables(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.context["resumen"]["unidades_totales"], 250)
        self.assertContains(respuesta, "de 250")
        self.assertContains(respuesta, "resumen-pedido")

    def test_registro_incluye_vista_previa(self):
        respuesta = self.client.get(reverse("registrar"))
        self.assertContains(respuesta, "vista-previa")
        self.assertContains(respuesta, "Ej: 250")
