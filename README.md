# Academik

Aplicacion web responsive para control de asistencia escolar, pensada primero para celulares y operable tambien desde escritorio.

## Estado inicial

Este repositorio deja aplicadas las primeras iteracciones documentadas:

1. Base conceptual del proyecto y arquitectura modular.
2. Entorno local de desarrollo en VS Code, sin Docker para desarrollo y con PostgreSQL en `localhost`.
3. Esquema inicial de base de datos modelado en Django con migraciones preparadas.

## Stack

- Python 3.12+
- Django 5.2
- PostgreSQL 15+ en `localhost`
- Tailwind CSS 3.4
- HTMX 2
- Alpine.js 3
- django-pwa
- Gunicorn para produccion

## Puesta en marcha local

1. Crear `.env` a partir de `.env.example`.
2. Verificar que exista la base `Academik` en PostgreSQL.
3. Activar el virtualenv:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Instalar dependencias si hace falta:

```powershell
python -m pip install -r requirements.txt
npm install
```

5. Sincronizar assets JS de proveedor y compilar Tailwind:

```powershell
npm run setup
```

6. Ejecutar migraciones:

```powershell
python manage.py migrate
```

7. Levantar el servidor:

```powershell
python manage.py runserver
```

## Estructura

- `config/`: configuracion global de Django.
- `core/`: clases base y pantalla inicial.
- `accounts/`: roles, usuarios y profesores.
- `academics/`: cursos, alumnos y asignaciones.
- `attendance/`: cabecera y detalle de asistencias.
- `pdf_imports/`: importaciones de PDF.
- `communications/`: notificaciones salientes.
- `auditing/`: auditoria de cambios.
