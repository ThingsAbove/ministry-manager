import pytest

from apps.core.branding import DEFAULT_BRANDING_CSS
from apps.core.models import ChurchSettings


@pytest.mark.django_db
def test_church_settings_default_branding():
    church = ChurchSettings.load()
    assert church.branding_css == DEFAULT_BRANDING_CSS
    assert church.logo_url.endswith("be-renewed-logo.jpg")


@pytest.mark.django_db
def test_branding_in_template_context(client):
    ChurchSettings.objects.update_or_create(
        pk=1,
        defaults={"name": "Test Church", "branding_css": "body { color: red; }"},
    )
    response = client.get("/accounts/login/")
    assert response.status_code == 200
    assert b'id="church-branding"' in response.content
    assert b"body { color: red; }" in response.content
    assert b"Test Church" in response.content
