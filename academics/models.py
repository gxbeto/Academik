from django.db import models
from django.db.models import Q

from core.models import ModeloTrazable


class Curso(ModeloTrazable):
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=150)
    seccion = models.CharField(max_length=30)
    turno = models.CharField(max_length=30)
    periodo_lectivo = models.CharField(max_length=30)
    nivel = models.CharField(max_length=50, blank=True)
    grado = models.CharField(max_length=50, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "cursos"
        ordering = ["periodo_lectivo", "nombre", "seccion", "turno"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo", "periodo_lectivo", "seccion", "turno"],
                name="uq_curso_cod_per_sec_turno",
            )
        ]
        indexes = [
            models.Index(fields=["periodo_lectivo"], name="idx_cursos_periodo_lectivo"),
            models.Index(fields=["nombre"], name="idx_cursos_nombre"),
        ]
        verbose_name = "curso"
        verbose_name_plural = "cursos"

    def __str__(self) -> str:
        return f"{self.nombre} {self.seccion} - {self.turno}"


class ProfesorCurso(ModeloTrazable):
    profesor = models.ForeignKey(
        "accounts.Profesor",
        on_delete=models.CASCADE,
        related_name="cursos_asignados",
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="profesores")
    titular = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "profesor_curso"
        ordering = ["-fecha_desde"]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_hasta__isnull=True) | Q(fecha_hasta__gte=models.F("fecha_desde")),
                name="chk_profesor_curso_fechas",
            ),
            models.UniqueConstraint(
                fields=["profesor", "curso", "fecha_desde"],
                name="uq_profesor_curso",
            ),
        ]
        indexes = [
            models.Index(fields=["profesor"], name="idx_profesor_curso_profesor"),
            models.Index(fields=["curso"], name="idx_profesor_curso_curso"),
        ]
        verbose_name = "asignacion profesor-curso"
        verbose_name_plural = "asignaciones profesor-curso"

    def __str__(self) -> str:
        return f"{self.profesor} -> {self.curso}"


class Alumno(ModeloTrazable):
    class Sexo(models.TextChoices):
        M = "M", "Masculino"
        F = "F", "Femenino"
        OTRO = "OTRO", "Otro"

    documento = models.CharField(max_length=30, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=20, choices=Sexo.choices, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono_responsable = models.CharField(max_length=30, blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "alumnos"
        ordering = ["apellidos", "nombres"]
        constraints = [
            models.CheckConstraint(
                condition=Q(sexo__isnull=True) | Q(sexo__in=["M", "F", "OTRO"]),
                name="chk_alumnos_sexo",
            )
        ]
        verbose_name = "alumno"
        verbose_name_plural = "alumnos"

    def __str__(self) -> str:
        return f"{self.apellidos}, {self.nombres}"

    def save(self, *args, **kwargs):
        if self.sexo == "":
            self.sexo = None
        super().save(*args, **kwargs)


class AlumnoCurso(ModeloTrazable):
    class Estados(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        RETIRADO = "RETIRADO", "Retirado"
        TRASLADADO = "TRASLADADO", "Trasladado"
        FINALIZADO = "FINALIZADO", "Finalizado"

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="cursos")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="alumnos")
    fecha_ingreso = models.DateField()
    fecha_salida = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.ACTIVO)

    class Meta:
        db_table = "alumno_curso"
        ordering = ["-fecha_ingreso"]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_salida__isnull=True) | Q(fecha_salida__gte=models.F("fecha_ingreso")),
                name="chk_alumno_curso_fechas",
            ),
            models.CheckConstraint(
                condition=Q(estado__in=["ACTIVO", "RETIRADO", "TRASLADADO", "FINALIZADO"]),
                name="chk_alumno_curso_estado",
            ),
            models.UniqueConstraint(
                fields=["alumno", "curso", "fecha_ingreso"],
                name="uq_alumno_curso",
            ),
        ]
        indexes = [
            models.Index(fields=["alumno"], name="idx_alumno_curso_alumno"),
            models.Index(fields=["curso"], name="idx_alumno_curso_curso"),
        ]
        verbose_name = "matricula de alumno"
        verbose_name_plural = "matriculas de alumnos"

    def __str__(self) -> str:
        return f"{self.alumno} en {self.curso}"
