# Especificación: Seguimiento de pedidos

## Objetivo

Crear una aplicación web para registrar pedidos y dar
seguimiento al estado de sus paquetes.

## Registro de pedidos

Cada pedido tendrá:
- Número de pedido único.
- Nombre del cliente.
- Cantidad de unidades: número entero mayor que cero.

Al registrar un pedido, el sistema creará automáticamente
paquetes de máximo 100 unidades.

Ejemplo: un pedido de 250 unidades genera tres paquetes:
100, 100 y 50 unidades.

## Estados de los paquetes

Los paquetes comienzan en Pendiente y avanzan en este orden:

Pendiente → En proceso → Revisión → Listo

No se pueden saltar estados ni volver a un estado anterior.
La excepción es que un paquete en Revisión puede rechazarse
y regresar a En proceso.

## Seguimiento

Para cada pedido se mostrará:
- Número, cliente y cantidad total de unidades.
- Cantidad de paquetes en cada estado.
- Porcentaje de avance, calculado así:

  (unidades de paquetes Listos / unidades totales) × 100

Ejemplo: si hay 100 unidades listas de un pedido de 250,
el avance es 40 %.

## Persistencia

Los pedidos, paquetes y estados se guardarán en una base de
datos para que permanezcan después de reiniciar la aplicación.

## Criterios de aceptación

- Un pedido de 250 unidades genera paquetes de 100, 100 y 50.
- No se aceptan cantidades menores que 1 ni números decimales.
- No se aceptan números de pedido duplicados.
- Un paquete solo puede avanzar al siguiente estado.
- Solo un paquete en Revisión puede rechazarse y regresar
  a En proceso.
- El avance se calcula usando las unidades listas, no la
  cantidad de paquetes.
- Los datos permanecen después de reiniciar la aplicación.