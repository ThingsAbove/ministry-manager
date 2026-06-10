from django.conf import settings

from apps.core.models import ChurchSettings


def church_settings(request):
    church = ChurchSettings.load()
    return {
        "church_name": church.name or settings.CHURCH_NAME,
        "church_logo_url": church.logo_url,
        "church_branding_css": church.branding_css,
    }
