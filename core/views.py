from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import FieldDoesNotExist
from django.db import DatabaseError, IntegrityError, models
from django.db.models.deletion import ProtectedError, RestrictedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import formats, timezone
from django.views import View
from django.views.generic import TemplateView

from academics.models import Alumno, AlumnoCurso, Curso, ProfesorCurso
from accounts.models import Profesor, Rol, Usuario
from attendance.models import Asistencia, AsistenciaDetalle
from auditing.models import Auditoria
from communications.models import Notificacion
from core.forms import get_crud_form_class
from pdf_imports.forms import PdfImportForm
from pdf_imports.models import ImportacionPDF, ImportacionPDFDetalle
from pdf_imports.services import (
    build_import_report,
    discard_pdf_import,
    get_import_program,
    process_pdf_import,
)


@dataclass(frozen=True)
class CrudDefinition:
    key: str
    section_title: str
    title: str
    menu_description: str
    page_description: str
    model: type[models.Model]
    columns: tuple[str, ...]
    empty_message: str
    allow_create: bool = True


CRUD_DEFINITIONS: dict[str, CrudDefinition] = {
    "roles": CrudDefinition(
        key="roles",
        section_title="Gestion de cuentas",
        title="Roles",
        menu_description="Define perfiles de acceso para el personal.",
        page_description="Crea y consulta los perfiles que ordenan los permisos dentro del sistema.",
        model=Rol,
        columns=("nombre", "descripcion", "activo"),
        empty_message="Aun no hay roles registrados.",
    ),
    "usuarios": CrudDefinition(
        key="usuarios",
        section_title="Gestion de cuentas",
        title="Usuarios",
        menu_description="Administra las cuentas de acceso del personal.",
        page_description="Registra usuarios para que cada persona ingrese con su cuenta y su perfil asignado.",
        model=Usuario,
        columns=("username", "email", "rol", "activo"),
        empty_message="Aun no hay usuarios registrados.",
    ),
    "profesores": CrudDefinition(
        key="profesores",
        section_title="Gestion de cuentas",
        title="Profesores",
        menu_description="Mantiene actualizado el plantel docente.",
        page_description="Carga y consulta la informacion principal de cada docente.",
        model=Profesor,
        columns=("cedula", "nombres", "apellidos", "activo"),
        empty_message="Aun no hay profesores registrados.",
    ),
    "cursos": CrudDefinition(
        key="cursos",
        section_title="Gestion academica",
        title="Cursos",
        menu_description="Organiza cursos, secciones y turnos.",
        page_description="Registra los cursos disponibles para cada periodo lectivo.",
        model=Curso,
        columns=("codigo", "nombre", "seccion", "turno"),
        empty_message="Aun no hay cursos registrados.",
    ),
    "asignaciones-profesor": CrudDefinition(
        key="asignaciones-profesor",
        section_title="Gestion academica",
        title="Asignaciones profesor-curso",
        menu_description="Relaciona docentes con los cursos que atienden.",
        page_description="Asigna cada docente a los cursos que tiene a cargo.",
        model=ProfesorCurso,
        columns=("profesor", "curso", "titular", "fecha_desde"),
        empty_message="Aun no hay asignaciones registradas.",
    ),
    "alumnos": CrudDefinition(
        key="alumnos",
        section_title="Gestion academica",
        title="Alumnos",
        menu_description="Registra y consulta a los estudiantes.",
        page_description="Mantiene actualizado el listado general de alumnos.",
        model=Alumno,
        columns=("documento", "nombres", "apellidos", "activo"),
        empty_message="Aun no hay alumnos registrados.",
    ),
    "matriculas": CrudDefinition(
        key="matriculas",
        section_title="Gestion academica",
        title="Matriculas",
        menu_description="Gestiona la inscripcion de alumnos por curso.",
        page_description="Registra el ingreso, la salida y el estado de cada matricula.",
        model=AlumnoCurso,
        columns=("alumno", "curso", "estado", "fecha_ingreso"),
        empty_message="Aun no hay matriculas registradas.",
    ),
    "asistencias": CrudDefinition(
        key="asistencias",
        section_title="Asistencia",
        title="Asistencias",
        menu_description="Registra la asistencia diaria por curso.",
        page_description="Carga y consulta el control diario de asistencia.",
        model=Asistencia,
        columns=("curso", "profesor", "fecha", "estado_control"),
        empty_message="Aun no hay asistencias registradas.",
    ),
    "detalle-asistencia": CrudDefinition(
        key="detalle-asistencia",
        section_title="Asistencia",
        title="Detalle de asistencia",
        menu_description="Consulta la asistencia individual por alumno.",
        page_description="Revisa el detalle de presencia, ausencia o justificacion de cada estudiante.",
        model=AsistenciaDetalle,
        columns=("asistencia", "alumno", "estado", "corregido"),
        empty_message="Aun no hay detalles de asistencia registrados.",
    ),
    "importaciones-pdf": CrudDefinition(
        key="importaciones-pdf",
        section_title="Importaciones",
        title="Importaciones PDF",
        menu_description="Controla cargas de archivos y su seguimiento.",
        page_description="Registra importaciones y revisa su estado de procesamiento.",
        model=ImportacionPDF,
        columns=("nombre_archivo", "tipo_importacion", "estado", "total_ok"),
        empty_message="Aun no hay importaciones registradas.",
    ),
    "detalle-importacion": CrudDefinition(
        key="detalle-importacion",
        section_title="Importaciones",
        title="Detalle de importacion",
        menu_description="Muestra el resultado detallado de cada importacion.",
        page_description="Consulta las lineas procesadas y las observaciones de cada importacion.",
        model=ImportacionPDFDetalle,
        columns=("importacion", "nro_linea", "tipo_registro", "procesado_ok"),
        empty_message="Aun no hay detalles de importacion registrados.",
    ),
    "notificaciones": CrudDefinition(
        key="notificaciones",
        section_title="Comunicaciones",
        title="Notificaciones",
        menu_description="Gestiona avisos y mensajes enviados.",
        page_description="Registra y consulta las comunicaciones dirigidas a la comunidad educativa.",
        model=Notificacion,
        columns=("tipo", "destinatario", "estado_envio", "fecha_envio"),
        empty_message="Aun no hay notificaciones registradas.",
    ),
    "auditoria": CrudDefinition(
        key="auditoria",
        section_title="Auditoria",
        title="Auditoria",
        menu_description="Consulta el historial de movimientos del sistema.",
        page_description="Revisa cambios importantes y acciones realizadas en la plataforma.",
        model=Auditoria,
        columns=("entidad", "accion", "usuario", "fecha_hora"),
        empty_message="Aun no hay movimientos registrados.",
    ),
}


NAVIGATION_SECTIONS = (
    {
        "title": "Principal",
        "subtitle": "Inicio y accesos rapidos",
        "items": (
            {
                "key": "inicio",
                "label": "Inicio",
                "description": "Resumen de tareas y accesos a cada area.",
            },
        ),
    },
    {
        "title": "Gestion de cuentas",
        "subtitle": "Usuarios, roles y docentes",
        "items": (
            {"key": "roles", "label": "Roles"},
            {"key": "usuarios", "label": "Usuarios"},
            {"key": "profesores", "label": "Profesores"},
        ),
    },
    {
        "title": "Gestion academica",
        "subtitle": "Cursos, alumnos y matriculas",
        "items": (
            {"key": "cursos", "label": "Cursos"},
            {"key": "asignaciones-profesor", "label": "Asignaciones"},
            {"key": "alumnos", "label": "Alumnos"},
            {"key": "matriculas", "label": "Matriculas"},
        ),
    },
    {
        "title": "Asistencia",
        "subtitle": "Registro diario por curso",
        "items": (
            {"key": "asistencias", "label": "Asistencias"},
            {"key": "detalle-asistencia", "label": "Detalle"},
        ),
    },
    {
        "title": "Importaciones",
        "subtitle": "Archivos y seguimiento",
        "items": (
            {"key": "importaciones-pdf", "label": "Importaciones PDF"},
            {"key": "detalle-importacion", "label": "Detalle PDF"},
        ),
    },
    {
        "title": "Comunicaciones",
        "subtitle": "Mensajeria operativa",
        "items": (
            {"key": "notificaciones", "label": "Notificaciones"},
        ),
    },
    {
        "title": "Auditoria",
        "subtitle": "Historial del sistema",
        "items": (
            {"key": "auditoria", "label": "Auditoria"},
        ),
    },
)


PROFESOR_HIDDEN_ENTITY_KEYS = {
    "roles",
    "usuarios",
    "profesores",
    "matriculas",
    "importaciones-pdf",
    "detalle-importacion",
    "auditoria",
}

PROFESOR_CREATE_BLOCKED_ENTITY_KEYS = {
    "alumnos",
    "cursos",
    "asignaciones-profesor",
}

IMPORT_ENABLED_ENTITY_KEYS = {
    "profesores",
    "alumnos",
}


def is_profesor_user(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "rol_id", None)
        and user.rol.nombre == Rol.Nombres.PROFESOR
    )


def user_can_access_entity(user, entity_key: str) -> bool:
    if not is_profesor_user(user):
        return True
    return entity_key not in PROFESOR_HIDDEN_ENTITY_KEYS


def user_can_create_entity(user, entity_key: str) -> bool:
    if not is_profesor_user(user):
        return True
    return entity_key not in PROFESOR_CREATE_BLOCKED_ENTITY_KEYS


def user_can_import_entity(user, entity_key: str) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and user.is_staff
        and entity_key in IMPORT_ENABLED_ENTITY_KEYS
    )


def get_accessible_queryset(definition: CrudDefinition, user):
    queryset = definition.model._default_manager.all()
    if not is_profesor_user(user):
        return queryset

    profesor = getattr(user, "profesor", None)
    if profesor is None:
        return queryset.none()

    if definition.key == "asignaciones-profesor":
        return queryset.filter(profesor=profesor)

    if definition.key == "alumnos":
        return queryset.filter(
            cursos__curso__profesores__profesor=profesor,
            cursos__curso__profesores__activo=True,
        ).distinct()

    return queryset


def build_sidebar(active_key: str, user) -> list[dict]:
    sections = []
    for section in NAVIGATION_SECTIONS[1:]:
        items = []
        for item in section["items"]:
            item_key = item["key"]
            if not user_can_access_entity(user, item_key):
                continue
            definition = CRUD_DEFINITIONS[item_key]
            description = definition.menu_description
            url = reverse("crud-entidad", kwargs={"entity_key": item_key})
            items.append(
                {
                    "key": item_key,
                    "label": item["label"],
                    "description": description,
                    "url": url,
                    "active": item_key == active_key,
                }
            )
        if not items:
            continue
        sections.append(
            {
                "title": section["title"],
                "subtitle": section["subtitle"],
                "items": items,
            }
        )
    return sections


def build_home_sections(user) -> list[dict]:
    sections = []
    for section in NAVIGATION_SECTIONS[1:]:
        items = []
        for item in section["items"]:
            if not user_can_access_entity(user, item["key"]):
                continue
            definition = CRUD_DEFINITIONS[item["key"]]
            items.append(
                {
                    "label": item["label"],
                    "description": definition.menu_description,
                    "url": reverse("crud-entidad", kwargs={"entity_key": item["key"]}),
                }
            )
        if not items:
            continue
        sections.append(
            {
                "title": section["title"],
                "subtitle": section["subtitle"],
                "items": items,
            }
        )
    return sections


def get_active_nav_label(active_key: str) -> str:
    if active_key == "inicio":
        return "Inicio"

    definition = CRUD_DEFINITIONS.get(active_key)
    if definition is not None:
        return definition.title

    return "Menu"


def format_value(value) -> str:
    if value in (None, ""):
        return "Sin dato"
    if isinstance(value, bool):
        return "Si" if value else "No"
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return formats.date_format(value, "SHORT_DATETIME_FORMAT")
    if isinstance(value, date):
        return formats.date_format(value, "SHORT_DATE_FORMAT")
    if isinstance(value, time):
        return formats.time_format(value, "TIME_FORMAT")
    return str(value)


def get_column_label(model: type[models.Model], field_name: str) -> str:
    try:
        return str(model._meta.get_field(field_name).verbose_name).capitalize()
    except FieldDoesNotExist:
        return field_name.replace("_", " ").capitalize()


def get_entity_name(definition: CrudDefinition) -> str:
    return str(definition.model._meta.verbose_name)


def build_table_context(definition: CrudDefinition, user) -> dict:
    model = definition.model
    related_fields = [
        field_name
        for field_name in definition.columns
        if (
            (field := model._meta.get_field(field_name)).is_relation
            and not field.many_to_many
            and not field.one_to_many
        )
    ]
    queryset = get_accessible_queryset(definition, user)
    if related_fields:
        queryset = queryset.select_related(*related_fields)

    headers = [get_column_label(model, field_name) for field_name in definition.columns]

    try:
        records = list(queryset)
    except DatabaseError as exc:
        return {
            "headers": headers,
            "rows": [],
            "error": str(exc),
        }

    rows = []
    entity_name = get_entity_name(definition)
    for record in records:
        rows.append(
            {
                "pk": record.pk,
                "label": str(record),
                "edit_url": reverse(
                    "crud-entidad-editar",
                    kwargs={"entity_key": definition.key, "pk": record.pk},
                ),
                "delete_url": reverse(
                    "crud-entidad-eliminar",
                    kwargs={"entity_key": definition.key, "pk": record.pk},
                ),
                "delete_confirm": (
                    f'Se eliminara {entity_name} "{record}". Deseas continuar?'
                ),
                "cells": [
                    format_value(getattr(record, field_name)) for field_name in definition.columns
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
        "error": "",
    }


class ShellContextMixin:
    active_nav_key = "inicio"

    def get_sidebar_sections(self) -> list[dict]:
        return build_sidebar(self.active_nav_key, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sidebar_sections"] = self.get_sidebar_sections()
        context["app_title"] = "Academi-k"
        context["active_nav_label"] = get_active_nav_label(self.active_nav_key)
        context["is_home_shell"] = self.active_nav_key == "inicio"
        return context


class InicioView(LoginRequiredMixin, ShellContextMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["home_sections"] = build_home_sections(self.request.user)
        return context


class CrudDefinitionMixin(LoginRequiredMixin, ShellContextMixin):
    definition: CrudDefinition
    object = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.definition = CRUD_DEFINITIONS.get(kwargs["entity_key"])
        if self.definition is None:
            raise Http404("La entidad solicitada no existe.")
        if not user_can_access_entity(request.user, self.definition.key):
            raise Http404("La entidad solicitada no esta disponible para tu perfil.")
        self.active_nav_key = self.definition.key
        if "pk" in kwargs:
            self.object = get_object_or_404(self.get_accessible_queryset(), pk=kwargs["pk"])

    def get_entity_name(self) -> str:
        return get_entity_name(self.definition)

    def get_accessible_queryset(self):
        return get_accessible_queryset(self.definition, self.request.user)

    def get_list_url(self) -> str:
        return reverse("crud-entidad", kwargs={"entity_key": self.definition.key})

    def get_create_url(self) -> str:
        return reverse("crud-entidad-nuevo", kwargs={"entity_key": self.definition.key})

    def get_import_url(self) -> str:
        return reverse("crud-entidad-importar", kwargs={"entity_key": self.definition.key})

    def get_form_class(self):
        return get_crud_form_class(
            self.definition.key,
            self.definition.model,
            instance=self.object,
        )

    def get_form(self):
        form_class = self.get_form_class()
        if self.request.method == "POST":
            return form_class(self.request.POST, instance=self.object)
        return form_class(instance=self.object)

    def save_form(self, form):
        try:
            instance = form.save(commit=False)
            if self.definition.key == "asistencias" and not instance.creado_por_id:
                instance.creado_por = self.request.user
            if self.definition.key == "importaciones-pdf" and not instance.usuario_id:
                instance.usuario = self.request.user
            instance.save()
            if hasattr(form, "save_m2m"):
                form.save_m2m()
        except IntegrityError:
            form.add_error(
                None,
                "No pudimos guardar los datos. Revisa si ya existe un registro igual o si falta informacion obligatoria.",
            )
            return None
        return instance


class CrudEntidadListView(CrudDefinitionMixin, TemplateView):
    template_name = "core/crud_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["crud"] = self.definition
        context["table"] = build_table_context(self.definition, self.request.user)
        context["entity_name"] = self.get_entity_name()
        context["create_url"] = self.get_create_url()
        context["import_url"] = self.get_import_url()
        context["can_import"] = user_can_import_entity(self.request.user, self.definition.key)
        context["can_create"] = self.definition.allow_create and user_can_create_entity(
            self.request.user,
            self.definition.key,
        )
        return context


class CrudEntidadFormView(CrudDefinitionMixin, TemplateView):
    template_name = "core/crud_form.html"

    def dispatch(self, request, *args, **kwargs):
        if self.object is None and not user_can_create_entity(request.user, self.definition.key):
            raise Http404("No puedes crear registros en esta seccion con tu perfil actual.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_mode(self) -> str:
        return "create" if self.object is None else "update"

    def get_form_title(self) -> str:
        entity_name = self.get_entity_name()
        if self.get_form_mode() == "create":
            return f"Nuevo {entity_name}"
        return f"Editar {entity_name}"

    def get_form_description(self) -> str:
        entity_name = self.get_entity_name()
        if self.get_form_mode() == "create":
            return f"Completa la informacion para registrar {entity_name}."
        return f"Actualiza la informacion guardada para {entity_name}."

    def get_submit_label(self) -> str:
        if self.get_form_mode() == "create":
            return "Guardar registro"
        return "Guardar cambios"

    def get_submit_copy(self) -> str:
        if self.get_form_mode() == "create":
            return "Crea un nuevo registro con los datos cargados."
        return "Aplica los cambios realizados a este registro."

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            instance = self.save_form(form)
            if instance is not None:
                if self.get_form_mode() == "create":
                    messages.success(self.request, "El registro fue creado correctamente.")
                else:
                    messages.success(self.request, "Los cambios se guardaron correctamente.")
                return redirect("crud-entidad", entity_key=self.definition.key)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["crud"] = self.definition
        context["form"] = kwargs.get("form") or self.get_form()
        context["form_mode"] = self.get_form_mode()
        context["form_title"] = self.get_form_title()
        context["form_description"] = self.get_form_description()
        context["submit_label"] = self.get_submit_label()
        context["submit_copy"] = self.get_submit_copy()
        context["list_url"] = self.get_list_url()
        context["record_label"] = str(self.object) if self.object is not None else ""
        return context


class CrudEntidadDeleteView(CrudDefinitionMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            self.object.delete()
        except (ProtectedError, RestrictedError):
            messages.error(
                self.request,
                "No se puede eliminar este registro porque esta siendo usado en otros datos relacionados.",
            )
        except IntegrityError:
            messages.error(
                self.request,
                "No pudimos eliminar el registro por una restriccion de integridad.",
            )
        else:
            messages.success(self.request, "El registro fue eliminado correctamente.")

        return redirect("crud-entidad", entity_key=self.definition.key)


class CrudEntidadImportView(CrudDefinitionMixin, TemplateView):
    template_name = "core/crud_import.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_import_entity(request.user, self.definition.key):
            raise Http404("La importacion no esta disponible para esta seccion.")
        return super().dispatch(request, *args, **kwargs)

    def get_program(self):
        return get_import_program(
            entity_key=self.definition.key,
            entity_label=self.definition.title,
            target_model=self.definition.model,
            report_fields=self.definition.columns,
        )

    def get_current_import(self):
        import_id = self.request.GET.get("import_id")
        if not import_id:
            return None
        return get_object_or_404(
            ImportacionPDF.objects.prefetch_related("detalles"),
            pk=import_id,
            tipo_importacion=self.definition.key,
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "process")

        if action == "process":
            form = PdfImportForm(request.POST, request.FILES)
            if form.is_valid():
                _, importacion = process_pdf_import(
                    entity_key=self.definition.key,
                    entity_label=self.definition.title,
                    target_model=self.definition.model,
                    report_fields=self.definition.columns,
                    uploaded_file=form.cleaned_data["archivo"],
                    usuario=request.user,
                )
                messages.success(
                    request,
                    "El archivo fue procesado. Revisa el informe antes de aceptarlo o descartarlo.",
                )
                return redirect(f"{self.get_import_url()}?import_id={importacion.pk}")
            return self.render_to_response(self.get_context_data(import_form=form))

        importacion = get_object_or_404(
            ImportacionPDF,
            pk=request.POST.get("import_id"),
            tipo_importacion=self.definition.key,
        )

        if action == "accept":
            if importacion.total_ok == 0 or importacion.total_error > 0:
                messages.error(
                    request,
                    "No se puede aceptar la importacion mientras existan errores o no haya registros listos.",
                )
                return redirect(f"{self.get_import_url()}?import_id={importacion.pk}")
            importacion.estado = ImportacionPDF.Estados.VALIDADO
            importacion.save(update_fields=["estado"])
            messages.success(request, "La importacion fue marcada como valida.")
            return redirect(f"{self.get_import_url()}?import_id={importacion.pk}")

        if action == "discard":
            discard_pdf_import(importacion)
            messages.success(request, "La importacion fue descartada.")
            return redirect(self.get_import_url())

        raise Http404("La accion solicitada no existe.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_import = self.get_current_import()
        program = self.get_program()
        context["crud"] = self.definition
        context["list_url"] = self.get_list_url()
        context["import_form"] = kwargs.get("import_form") or PdfImportForm()
        context["program"] = program
        context["report"] = build_import_report(current_import, program) if current_import else None
        return context
