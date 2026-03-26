from django.conf import settings


def runtime_flags(request):
    return {
        "pwa_enabled": settings.PWA_ENABLED,
    }
