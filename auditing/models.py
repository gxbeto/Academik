from django.db import models

from core.models import ModeloCreado


class Auditoria(ModeloCreado):
    usuario = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="auditorias",
    )
    entidad = models.CharField(max_length=100)
    entidad_id = models.BigIntegerField(blank=True, null=True)
    accion = models.CharField(max_length=50)
    valor_anterior = models.JSONField(blank=True, null=True)
    valor_nuevo = models.JSONField(blank=True, null=True)
    ip = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auditoria"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["entidad", "entidad_id"], name="idx_audit_entidad_ent_id"),
            models.Index(fields=["fecha_hora"], name="idx_auditoria_fecha_hora"),
        ]
        verbose_name = "auditoria"
        verbose_name_plural = "auditoria"

    def __str__(self) -> str:
        return f"{self.entidad} - {self.accion}"
