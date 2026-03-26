from __future__ import annotations

from functools import lru_cache

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.forms import modelform_factory

from accounts.forms import UsuarioCreationForm
from accounts.models import Usuario

FIELD_INPUT_CLASS = (
    "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 "
    "outline-none transition focus:border-rio focus:ring-0"
)
FIELD_CHECKBOX_CLASS = "h-5 w-5 rounded border-slate-300 text-rio focus:ring-rio"
FIELD_TOOLTIP_EXAMPLES = {
    "username": (
        "Ingresa el nombre de usuario que la persona usara para acceder.",
        "jperez",
    ),
    "email": (
        "Ingresa un correo valido para contacto o acceso.",
        "usuario@colegio.edu.py",
    ),
    "password1": (
        "Escribe una contrasena segura para este registro.",
        "Minimo 8 caracteres",
    ),
    "password2": (
        "Repite la misma contrasena para confirmarla.",
        "Debe coincidir con la anterior",
    ),
    "cedula": (
        "Ingresa el numero de cedula sin puntos ni espacios innecesarios.",
        "1234567",
    ),
    "documento": (
        "Ingresa el numero de documento del alumno.",
        "1234567",
    ),
    "telefono": (
        "Ingresa un telefono de contacto.",
        "0981123456",
    ),
    "telefono_responsable": (
        "Ingresa el telefono de la persona responsable.",
        "0981123456",
    ),
    "codigo": (
        "Ingresa el codigo que identificara este registro.",
        "CUR-001",
    ),
}


def build_field_tooltip(field_name: str, field, model_field=None) -> tuple[str, str]:
    custom_hint = FIELD_TOOLTIP_EXAMPLES.get(field_name)
    if custom_hint is not None:
        description, example = custom_hint
        return f"{description} Ejemplo: {example}.", example

    if isinstance(field, forms.ModelChoiceField):
        return (
            "Selecciona una opcion de la lista para vincular este registro con otro dato existente.",
            "",
        )
    if isinstance(field.widget, forms.CheckboxInput):
        return ("Marca esta opcion solo si corresponde para este registro.", "")
    if isinstance(model_field, models.DateTimeField):
        return (
            "Selecciona la fecha y la hora esperadas para este dato.",
            "2026-03-24T14:30",
        )
    if isinstance(model_field, models.DateField):
        return ("Selecciona la fecha correspondiente en el calendario.", "2026-03-24")
    if isinstance(model_field, models.TimeField):
        return ("Selecciona la hora correspondiente.", "07:30")
    if isinstance(model_field, (models.IntegerField, models.BigIntegerField)):
        return ("Ingresa un numero entero.", "1")
    if isinstance(model_field, models.EmailField):
        return ("Ingresa un correo valido.", "usuario@colegio.edu.py")
    if isinstance(field.widget, forms.Textarea):
        return (
            "Escribe la informacion solicitada de forma breve y clara.",
            "Detalle breve y claro",
        )
    if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
        return ("Selecciona una opcion de la lista.", "")

    label = field.label.lower() if field.label else "el dato solicitado"
    return (f"Ingresa {label}.", field.label or "")


class PortalFormStylingMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_portal_styles()

    def _apply_portal_styles(self) -> None:
        model = getattr(self._meta, "model", None)
        for field_name, field in self.fields.items():
            model_field = None
            if model is not None:
                try:
                    model_field = model._meta.get_field(field_name)
                except FieldDoesNotExist:
                    model_field = None

            if isinstance(model_field, models.DateTimeField):
                field.widget = forms.DateTimeInput(
                    attrs={"type": "datetime-local"},
                    format="%Y-%m-%dT%H:%M",
                )
                field.input_formats = ["%Y-%m-%dT%H:%M"]
            elif isinstance(model_field, models.DateField):
                field.widget = forms.DateInput(
                    attrs={"type": "date"},
                    format="%Y-%m-%d",
                )
                field.input_formats = ["%Y-%m-%d"]
            elif isinstance(model_field, models.TimeField):
                field.widget = forms.TimeInput(
                    attrs={"type": "time"},
                    format="%H:%M",
                )
                field.input_formats = ["%H:%M"]

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = FIELD_CHECKBOX_CLASS
            else:
                field.widget.attrs["class"] = FIELD_INPUT_CLASS

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 4)

            if field_name == "username":
                field.widget.attrs.setdefault("autocomplete", "username")
            elif field_name in {"password1", "password2"}:
                field.widget.attrs.setdefault("autocomplete", "new-password")
            elif field_name == "email":
                field.widget.attrs.setdefault("autocomplete", "email")

            tooltip_text, placeholder = build_field_tooltip(field_name, field, model_field)
            if tooltip_text:
                field.widget.attrs["title"] = tooltip_text
            if placeholder and not isinstance(
                field.widget,
                (forms.CheckboxInput, forms.Select, forms.SelectMultiple),
            ):
                field.widget.attrs.setdefault("placeholder", placeholder)


class BaseCrudModelForm(PortalFormStylingMixin, forms.ModelForm):
    pass


class PortalUsuarioCreationForm(PortalFormStylingMixin, UsuarioCreationForm):
    pass


class PortalUsuarioUpdateForm(PortalFormStylingMixin, forms.ModelForm):
    password1 = forms.CharField(
        label="Nueva contrasena",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirmar nueva contrasena",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Usuario
        fields = ("username", "email", "rol", "activo")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if not password1 or not password2:
                raise forms.ValidationError("Completa ambos campos de contrasena para actualizarla.")
            if password1 != password2:
                raise forms.ValidationError("Las contrasenas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            usuario.set_password(password)
        if commit:
            usuario.save()
        return usuario


ENTITY_FORM_EXCLUDES: dict[str, tuple[str, ...]] = {
    "asistencias": ("creado_por",),
    "importaciones-pdf": ("usuario",),
}

def get_crud_form_class(entity_key: str, model: type[models.Model], *, instance=None):
    if entity_key == "usuarios":
        return PortalUsuarioUpdateForm if instance is not None else PortalUsuarioCreationForm
    return _build_model_form_class(entity_key, model)


@lru_cache(maxsize=None)
def _build_model_form_class(entity_key: str, model: type[models.Model]):
    excluded_fields = set(ENTITY_FORM_EXCLUDES.get(entity_key, ()))
    field_names = [
        field.name
        for field in model._meta.fields
        if field.editable and not isinstance(field, models.AutoField) and field.name not in excluded_fields
    ]
    return modelform_factory(
        model,
        form=BaseCrudModelForm,
        fields=field_names,
    )
