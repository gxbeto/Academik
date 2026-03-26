from django.contrib import admin

from .models import Auditoria


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("entidad", "entidad_id", "accion", "usuario", "fecha_hora")
    list_filter = ("entidad", "accion")
    search_fields = ("entidad", "accion", "ip", "user_agent")
