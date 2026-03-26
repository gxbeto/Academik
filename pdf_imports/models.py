from django.db import models
from django.db.models import Q

from core.models import ModeloCreado, ModeloTrazable


class ImportacionPDF(ModeloTrazable):
    class Estados(models.TextChoices):
        CARGADO = "CARGADO", "Cargado"
        PROCESADO = "PROCESADO", "Procesado"
        VALIDADO = "VALIDADO", "Validado"
        IMPORTADO = "IMPORTADO", "Importado"
        ERROR = "ERROR", "Error"

    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.CharField(max_length=500, blank=True)
    tipo_importacion = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.CARGADO)
    total_registros = models.IntegerField(default=0)
    total_ok = models.IntegerField(default=0)
    total_error = models.IntegerField(default=0)
    usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="importaciones_pdf",
    )
    fecha_proceso = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "importaciones_pdf"
        ordering = ["-creado"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=["CARGADO", "PROCESADO", "VALIDADO", "IMPORTADO", "ERROR"]),
                name="chk_importaciones_pdf_estado",
            )
        ]
        indexes = [
            models.Index(fields=["estado"], name="idx_importaciones_pdf_estado"),
        ]
        verbose_name = "importacion PDF"
        verbose_name_plural = "importaciones PDF"

    def __str__(self) -> str:
        return self.nombre_archivo


class ImportacionPDFDetalle(ModeloCreado):
    importacion = models.ForeignKey(
        ImportacionPDF,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    nro_linea = models.IntegerField(blank=True, null=True)
    tipo_registro = models.CharField(max_length=50, blank=True)
    dato_original = models.TextField(blank=True)
    mensaje_error = models.TextField(blank=True)
    procesado_ok = models.BooleanField(default=False)

    class Meta:
        db_table = "importacion_pdf_detalle"
        ordering = ["id"]
        verbose_name = "detalle de importacion PDF"
        verbose_name_plural = "detalles de importacion PDF"

    def __str__(self) -> str:
        return f"Linea {self.nro_linea or '-'}"
