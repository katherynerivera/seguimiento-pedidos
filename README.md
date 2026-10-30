# Seguimiento de pedidos

Aplicación web para registrar pedidos, dividirlos en paquetes y
seguir su avance por unidades listas.

## Tecnologías

- Python 3.14
- Django 5.2
- SQLite para desarrollo local

## Instalación en Windows

Clonar el repositorio y abrir una terminal en la carpeta del proyecto:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "Django>=5.2.8,<5.3"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver