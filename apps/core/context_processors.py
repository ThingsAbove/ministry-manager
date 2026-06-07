from django.conf import settings


def church_settings(request):
    return {
        "church_name": settings.CHURCH_NAME,
    }
