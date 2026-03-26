from django.contrib import admin

from .models import ImportacionPDF, ImportacionPDFDetalle


class ImportacionPDFDetalleInline(admin.TabularInline):
    model = ImportacionPDFDetalle
    extra = 0


@admin.register(ImportacionPDF)
class ImportacionPDFAdmin(admin.ModelAdmin):
    list_display = ("nombre_archivo", "tipo_importacion", "estado", "total_registros", "total_ok", "total_error")
    list_filter = ("estado", "tipo_importacion")
    search_fields = ("nombre_archivo", "tipo_importacion")
    inlines = [ImportacionPDFDetalleInline]
