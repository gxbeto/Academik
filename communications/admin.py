from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("tipo", "destinatario", "estado_envio", "fecha_envio", "creado")
    list_filter = ("estado_envio", "tipo")
    search_fields = ("destinatario", "asunto", "mensaje", "referencia_entidad")
