from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

from .models import ImportacionPDF, ImportacionPDFDetalle

EXCLUDED_IMPORT_FIELDS = {"creado", "modificado", "fecha_hora", "last_login", "creado_por", "usuario"}


@dataclass(frozen=True)
class ImportPreviewRow:
    line_number: int | None
    values_to_save: dict[str, str]
    report_data: dict[str, str]
    ok: bool
    message: str = ""


@dataclass(frozen=True)
class ImportProcessResult:
    file_name: str
    entity_label: str
    target_fields: tuple[str, ...]
    report_fields: tuple[str, ...]
    imported_rows: list[ImportPreviewRow] = field(default_factory=list)
    error_rows: list[ImportPreviewRow] = field(default_factory=list)


class EntityPdfImportProgram:
    def __init__(
        self,
        *,
        entity_key: str,
        entity_label: str,
        target_model: type[models.Model],
        report_fields: tuple[str, ...],
    ):
        self.entity_key = entity_key
        self.entity_label = entity_label
        self.report_fields = report_fields
        self.target_fields = tuple(
            field.name
            for field in target_model._meta.fields
            if (
                field.editable
                and not isinstance(field, models.AutoField)
                and field.name not in EXCLUDED_IMPORT_FIELDS
            )
        )

    def process(self, file_name: str, file_bytes: bytes) -> ImportProcessResult:
        return ImportProcessResult(
            file_name=file_name,
            entity_label=self.entity_label,
            target_fields=self.target_fields,
            report_fields=self.report_fields,
            imported_rows=[],
            error_rows=[
                ImportPreviewRow(
                    line_number=None,
                    values_to_save={field: "" for field in self.target_fields},
                    report_data={field: "" for field in self.report_fields},
                    ok=False,
                    message=(
                        f"El importador PDF de {self.entity_label.lower()} aun no fue implementado. "
                        "Aqui se conectara el parser especifico de esta entidad."
                    ),
                )
            ],
        )


def get_import_program(
    *,
    entity_key: str,
    entity_label: str,
    target_model: type[models.Model],
    report_fields: tuple[str, ...],
) -> EntityPdfImportProgram:
    return EntityPdfImportProgram(
        entity_key=entity_key,
        entity_label=entity_label,
        target_model=target_model,
        report_fields=report_fields,
    )


def process_pdf_import(
    *,
    entity_key: str,
    entity_label: str,
    target_model: type[models.Model],
    report_fields: tuple[str, ...],
    uploaded_file,
    usuario,
):
    file_bytes = uploaded_file.read()
    program = get_import_program(
        entity_key=entity_key,
        entity_label=entity_label,
        target_model=target_model,
        report_fields=report_fields,
    )
    result = program.process(uploaded_file.name, file_bytes)

    storage_path = default_storage.save(
        f"imports/{entity_key}/{uuid4().hex}_{Path(uploaded_file.name).name}",
        ContentFile(file_bytes),
    )
    importacion = ImportacionPDF.objects.create(
        nombre_archivo=uploaded_file.name,
        ruta_archivo=storage_path,
        tipo_importacion=entity_key,
        estado=ImportacionPDF.Estados.PROCESADO,
        total_registros=len(result.imported_rows) + len(result.error_rows),
        total_ok=len(result.imported_rows),
        total_error=len(result.error_rows),
        usuario=usuario,
        fecha_proceso=timezone.now(),
    )

    detalles = []
    for row in result.imported_rows:
        detalles.append(
            ImportacionPDFDetalle(
                importacion=importacion,
                nro_linea=row.line_number,
                tipo_registro="OK",
                dato_original=json.dumps(
                    {
                        "values_to_save": row.values_to_save,
                        "report_data": row.report_data,
                    },
                    ensure_ascii=False,
                ),
                mensaje_error=row.message,
                procesado_ok=True,
            )
        )
    for row in result.error_rows:
        detalles.append(
            ImportacionPDFDetalle(
                importacion=importacion,
                nro_linea=row.line_number,
                tipo_registro="ERROR",
                dato_original=json.dumps(
                    {
                        "values_to_save": row.values_to_save,
                        "report_data": row.report_data,
                    },
                    ensure_ascii=False,
                ),
                mensaje_error=row.message,
                procesado_ok=False,
            )
        )
    if detalles:
        ImportacionPDFDetalle.objects.bulk_create(detalles)

    return program, importacion


def discard_pdf_import(importacion: ImportacionPDF) -> None:
    storage_path = importacion.ruta_archivo
    importacion.delete()
    if storage_path and default_storage.exists(storage_path):
        default_storage.delete(storage_path)


def _preview_to_text(data: dict[str, str]) -> str:
    if not data:
        return "Sin datos"
    return " | ".join(f"{key}: {value or '-'}" for key, value in data.items())


def build_import_report(importacion: ImportacionPDF, program: EntityPdfImportProgram) -> dict:
    ok_rows = []
    error_rows = []

    for detalle in importacion.detalles.all().order_by("id"):
        payload = json.loads(detalle.dato_original or "{}")
        row = {
            "line_number": detalle.nro_linea or "-",
            "values_preview": _preview_to_text(payload.get("values_to_save", {})),
            "report_preview": _preview_to_text(payload.get("report_data", {})),
            "message": detalle.mensaje_error or "Sin observaciones.",
        }
        if detalle.procesado_ok:
            ok_rows.append(row)
        else:
            error_rows.append(row)

    return {
        "importacion": importacion,
        "program": program,
        "target_fields": program.target_fields,
        "report_fields": program.report_fields,
        "ok_rows": ok_rows,
        "error_rows": error_rows,
        "can_accept": importacion.total_ok > 0 and importacion.total_error == 0,
    }
