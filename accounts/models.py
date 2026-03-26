from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from core.models import ModeloTrazable


class Rol(ModeloTrazable):
    class Nombres(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        PROFESOR = "PROFESOR", "Profesor"

    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "roles"
        ordering = ["nombre"]
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self) -> str:
        return self.nombre


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username: str, password: str | None = None, **extra_fields):
        if not username:
            raise ValueError("El username es obligatorio.")
        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)
        usuario = self.model(username=username, **extra_fields)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username: str, password: str, **extra_fields):
        extra_fields.setdefault("activo", True)
        if extra_fields.get("rol") is None:
            rol, _ = Rol.objects.get_or_create(
                nombre=Rol.Nombres.ADMINISTRADOR,
                defaults={
                    "descripcion": (
                        "Administra alumnos, cursos, profesores, importaciones, "
                        "reportes y correcciones"
                    )
                },
            )
            extra_fields["rol"] = rol
        return self.create_user(username=username, password=password, **extra_fields)


class Usuario(AbstractBaseUser, ModeloTrazable):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255, db_column="password_hash")
    email = models.EmailField(max_length=255, blank=True, null=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name="usuarios")
    activo = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True, db_column="ultimo_login")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    objects = UsuarioManager()

    class Meta:
        db_table = "usuarios"
        ordering = ["username"]
        indexes = [
            models.Index(fields=["rol"], name="idx_usuarios_rol_id"),
        ]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.username

    @property
    def is_active(self) -> bool:
        return self.activo

    @property
    def is_staff(self) -> bool:
        return bool(self.rol_id and self.rol.nombre == Rol.Nombres.ADMINISTRADOR)

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_staff

    def has_module_perms(self, app_label) -> bool:
        return self.is_staff

    def get_full_name(self) -> str:
        profesor = getattr(self, "profesor", None)
        if profesor is not None:
            return profesor.nombre_completo
        return self.username

    def get_short_name(self) -> str:
        return self.username


class Profesor(ModeloTrazable):
    usuario = models.OneToOneField(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="profesor",
    )
    cedula = models.CharField(max_length=30, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "profesores"
        ordering = ["apellidos", "nombres"]
        verbose_name = "profesor"
        verbose_name_plural = "profesores"

    def __str__(self) -> str:
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()
