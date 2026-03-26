from django.contrib import admin

from .models import Asistencia, AsistenciaDetalle


class AsistenciaDetalleInline(admin.TabularInline):
    model = AsistenciaDetalle
    extra = 0


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("curso", "profesor", "fecha", "estado_control", "hora_inicio", "hora_confirmacion")
    list_filter = ("estado_control", "fecha")
    search_fields = ("curso__nombre", "curso__codigo", "profesor__nombres", "profesor__apellidos")
    inlines = [AsistenciaDetalleInline]


@admin.register(AsistenciaDetalle)
class AsistenciaDetalleAdmin(admin.ModelAdmin):
    list_display = ("asistencia", "alumno", "estado", "corregido")
    list_filter = ("estado", "corregido")
    search_fields = ("alumno__documento", "alumno__nombres", "alumno__apellidos")
