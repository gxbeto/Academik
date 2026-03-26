from django.db import models
from django.db.models import Q

from core.models import ModeloTrazable


class Asistencia(ModeloTrazable):
    class Estados(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        CONTROLADA = "CONTROLADA", "Controlada"
        CORREGIDA = "CORREGIDA", "Corregida"

    curso = models.ForeignKey("academics.Curso", on_delete=models.RESTRICT, related_name="asistencias")
    profesor = models.ForeignKey(
        "accounts.Profesor",
        on_delete=models.RESTRICT,
        related_name="asistencias",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_confirmacion = models.DateTimeField(blank=True, null=True)
    estado_control = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.BORRADOR,
    )
    observacion = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="asistencias_creadas",
    )

    class Meta:
        db_table = "asistencias"
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado_control__in=["BORRADOR", "CONTROLADA", "CORREGIDA"]),
                name="chk_asistencias_estado",
            ),
            models.UniqueConstraint(
                fields=["curso", "profesor", "fecha"],
                name="uq_asis_cur_prof_fecha",
            ),
        ]
        indexes = [
            models.Index(fields=["fecha"], name="idx_asistencias_fecha"),
            models.Index(fields=["curso", "fecha"], name="idx_asistencias_curso_fecha"),
        ]
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"

    def __str__(self) -> str:
        return f"{self.curso} - {self.fecha}"


class AsistenciaDetalle(ModeloTrazable):
    class Estados(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        AUSENTE = "AUSENTE", "Ausente"
        JUSTIFICADO = "JUSTIFICADO", "Justificado"

    asistencia = models.ForeignKey(
        Asistencia,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    alumno = models.ForeignKey(
        "academics.Alumno",
        on_delete=models.RESTRICT,
        related_name="asistencias",
    )
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.PRESENTE)
    observacion = models.TextField(blank=True)
    corregido = models.BooleanField(default=False)

    class Meta:
        db_table = "asistencia_detalle"
        ordering = ["alumno__apellidos", "alumno__nombres"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=["PRESENTE", "AUSENTE", "JUSTIFICADO"]),
                name="chk_asistencia_detalle_estado",
            ),
            models.UniqueConstraint(
                fields=["asistencia", "alumno"],
                name="uq_asistencia_detalle",
            ),
        ]
        indexes = [
            models.Index(fields=["alumno"], name="idx_asistencia_detalle_alumno"),
        ]
        verbose_name = "detalle de asistencia"
        verbose_name_plural = "detalles de asistencia"

    def __str__(self) -> str:
        return f"{self.alumno} - {self.estado}"
