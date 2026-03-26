from django.db import migrations


def seed_roles(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")

    Rol.objects.update_or_create(
        nombre="ADMINISTRADOR",
        defaults={
            "descripcion": (
                "Administra alumnos, cursos, profesores, importaciones, "
                "reportes y correcciones"
            ),
            "activo": True,
        },
    )
    Rol.objects.update_or_create(
        nombre="PROFESOR",
        defaults={
            "descripcion": (
                "Accede a cursos asignados, registra ausencias y confirma asistencia"
            ),
            "activo": True,
        },
    )


def unseed_roles(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")
    Rol.objects.filter(nombre__in=["ADMINISTRADOR", "PROFESOR"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
