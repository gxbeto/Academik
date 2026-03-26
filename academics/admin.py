from django.contrib import admin

from .models import Alumno, AlumnoCurso, Curso, ProfesorCurso


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "seccion", "turno", "periodo_lectivo", "activo")
    search_fields = ("codigo", "nombre", "seccion", "turno", "periodo_lectivo")
    list_filter = ("activo", "periodo_lectivo", "turno")


@admin.register(ProfesorCurso)
class ProfesorCursoAdmin(admin.ModelAdmin):
    list_display = ("profesor", "curso", "titular", "activo", "fecha_desde", "fecha_hasta")
    list_filter = ("titular", "activo")
    search_fields = ("profesor__nombres", "profesor__apellidos", "curso__nombre", "curso__codigo")


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("documento", "apellidos", "nombres", "sexo", "activo")
    search_fields = ("documento", "nombres", "apellidos")
    list_filter = ("activo", "sexo")


@admin.register(AlumnoCurso)
class AlumnoCursoAdmin(admin.ModelAdmin):
    list_display = ("alumno", "curso", "estado", "fecha_ingreso", "fecha_salida")
    list_filter = ("estado",)
    search_fields = ("alumno__documento", "alumno__nombres", "alumno__apellidos", "curso__nombre")
