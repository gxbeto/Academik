from django.contrib import admin

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Profesor, Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "creado", "modificado")
    search_fields = ("nombre", "descripcion")
    list_filter = ("activo",)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    list_display = ("username", "email", "rol", "activo", "last_login")
    search_fields = ("username", "email")
    list_filter = ("activo", "rol")
    ordering = ("username",)
    readonly_fields = ("creado", "modificado", "last_login")
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Acceso", {"fields": ("rol", "activo", "last_login")}),
        ("Auditoria", {"fields": ("creado", "modificado")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "rol", "activo", "password1", "password2"),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = self.add_form if obj is None else self.form
        return super().get_form(request, obj, **kwargs)


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ("cedula", "apellidos", "nombres", "email", "activo")
    search_fields = ("cedula", "nombres", "apellidos", "email")
    list_filter = ("activo",)
