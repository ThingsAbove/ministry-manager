import pytest
from django.urls import reverse

from apps.accounts.models import User
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


@pytest.mark.django_db
def test_church_branding_admin_live_preview(client):
    ChurchSettings.load()
    admin = User.objects.create_superuser(username="branding-admin", password="pass")
    client.force_login(admin)
    response = client.get(reverse("admin:core_churchbranding_change", args=[1]))
    assert response.status_code == 200
    assert b"branding-preview-css" in response.content
    assert b"church_branding_preview.js" in response.content


@pytest.mark.django_db
def test_church_logo_admin_live_preview(client):
    ChurchSettings.load()
    admin = User.objects.create_superuser(username="logo-admin", password="pass")
    client.force_login(admin)
    response = client.get(reverse("admin:core_churchlogo_change", args=[1]))
    assert response.status_code == 200
    assert b"data-logo-preview-sidebar" in response.content
    assert b"church_logo_preview.js" in response.content


@pytest.mark.django_db
def test_church_settings_admin_redirects_to_singleton(client):
    ChurchSettings.load()
    admin = User.objects.create_superuser(username="settings-admin", password="pass")
    client.force_login(admin)
    response = client.get(reverse("admin:core_churchbranding_changelist"))
    assert response.status_code == 302
    assert response.url == reverse("admin:core_churchbranding_change", args=[1])
