from django.db import models
from django.db.models import Q

from core.models import ModeloTrazable


class Notificacion(ModeloTrazable):
    class Estados(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ENVIADO = "ENVIADO", "Enviado"
        ERROR = "ERROR", "Error"
        CANCELADO = "CANCELADO", "Cancelado"

    tipo = models.CharField(max_length=30)
    destinatario = models.CharField(max_length=255)
    asunto = models.CharField(max_length=255, blank=True)
    mensaje = models.TextField()
    estado_envio = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
    )
    fecha_envio = models.DateTimeField(blank=True, null=True)
    referencia_entidad = models.CharField(max_length=100, blank=True)
    referencia_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "notificaciones"
        ordering = ["-creado"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado_envio__in=["PENDIENTE", "ENVIADO", "ERROR", "CANCELADO"]),
                name="chk_notificaciones_estado",
            )
        ]
        indexes = [
            models.Index(fields=["estado_envio"], name="idx_notificaciones_estado"),
        ]
        verbose_name = "notificacion"
        verbose_name_plural = "notificaciones"

    def __str__(self) -> str:
        return f"{self.tipo} -> {self.destinatario}"
