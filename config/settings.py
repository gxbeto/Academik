import os
from pathlib import Path

from core.runtime_config import (
    build_local_dev_csrf_trusted_origins,
    expand_local_dev_hosts,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def cargar_env(ruta: Path) -> None:
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def env_bool(clave: str, default: bool = False) -> bool:
    valor = os.environ.get(clave)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "t", "yes", "y", "on", "si"}


def env_list(clave: str, default: str = "") -> list[str]:
    valor = os.environ.get(clave, default)
    if not valor:
        return []
    return [item.strip() for item in valor.split(",") if item.strip()]


cargar_env(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "academik-dev-secret-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = expand_local_dev_hosts(
    env_list("ALLOWED_HOSTS", "127.0.0.1,localhost"),
    debug=DEBUG,
)
CSRF_TRUSTED_ORIGINS = build_local_dev_csrf_trusted_origins(
    env_list("CSRF_TRUSTED_ORIGINS"),
    allowed_hosts=ALLOWED_HOSTS,
    debug=DEBUG,
)
PWA_ENABLED = env_bool("PWA_ENABLED", not DEBUG)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pwa",
    "core",
    "accounts",
    "academics",
    "attendance",
    "pdf_imports",
    "communications",
    "auditing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.runtime_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "Academik"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.Usuario"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "es"

TIME_ZONE = "America/Asuncion"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

PWA_APP_NAME = "Academi-k"
PWA_APP_DESCRIPTION = "Control de asistencia escolar para docentes y administracion."
PWA_APP_THEME_COLOR = "#114b5f"
PWA_APP_BACKGROUND_COLOR = "#f5fbff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "portrait-primary"
PWA_APP_START_URL = "/"
PWA_APP_STATUS_BAR_COLOR = "default"
PWA_APP_DIR = "ltr"
PWA_APP_LANG = "es-PY"
PWA_APP_DEBUG_MODE = DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
