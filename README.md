# Seguimiento de pedidos

Aplicación web para registrar pedidos, dividirlos en paquetes
y dar seguimiento a su avance por unidades listas.

## Aplicación publicada

https://seguimiento-pedidos-b3uq.onrender.com

La aplicación publicada utiliza PostgreSQL en Render.
La base de datos gratuita vence el 29 de noviembre de 2026.

## Tecnologías

- Python 3.14
- Django 5.2
- SQLite para desarrollo local
- PostgreSQL y Render para la aplicación publicada

## Instalación en Windows

Clona el repositorio y abre una terminal en la carpeta del proyecto.
Ejecuta los siguientes comandos:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Abre http://127.0.0.1:8000/ en el navegador.

## Pruebas automatizadas

Desde la carpeta del proyecto, ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

## Desarrollo con SDD y apoyo de IA

Primero se documentaron los requisitos y criterios de aceptación
en `SPEC.md`. Después se implementaron los modelos, servicios,
formulario y pantallas, y se añadieron pruebas automatizadas.

## Error del agente de IA y corrección

El agente recomendó instalar Django 6.1.3 o superior con Python
3.15, pero la instalación indicada no encontró una versión
disponible en el entorno. Se corrigió instalando Python 3.14
y Django 5.2.18 en un entorno virtual nuevo. Después se verificó
la instalación y se ejecutaron las pruebas.
## Funcionalidades de IA pendientes

Se consideran como mejoras futuras el resumen inteligente por pedido,
la sugerencia de prioridades y un asistente para consultas en lenguaje
natural. Su implementación y configuración con un proveedor de IA
quedan pendientes; requieren credenciales y pueden generar costos.
Estas funciones no están activas ni se probaron con un modelo real.
