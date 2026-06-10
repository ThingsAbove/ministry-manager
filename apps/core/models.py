from django.db import models
from django.templatetags.static import static

from .branding import DEFAULT_BRANDING_CSS


class ChurchSettings(models.Model):
    """Singleton-style church configuration."""

    name = models.CharField(max_length=200, default="Be Renewed Church")
    logo = models.ImageField(
        upload_to="church/",
        blank=True,
        help_text="Church logo shown in the app sidebar and admin. Leave blank to use the default.",
    )
    branding_css = models.TextField(
        blank=True,
        default=DEFAULT_BRANDING_CSS,
        help_text="Custom CSS for app branding (colors, fonts, sidebar, buttons).",
    )
    timezone = models.CharField(max_length=63, default="America/New_York")
    reminder_days_before = models.CharField(
        max_length=50,
        default="7,1",
        help_text="Comma-separated days before shift to send reminders",
    )
    default_serving_frequency_weeks = models.PositiveSmallIntegerField(
        default=4,
        help_text="Target weeks between assignments for a volunteer",
    )

    class Meta:
        verbose_name_plural = "church settings"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @property
    def logo_url(self):
        if self.logo:
            return self.logo.url
        return static("img/be-renewed-logo.jpg")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Be Renewed Church",
                "branding_css": DEFAULT_BRANDING_CSS,
            },
        )
        return obj


class ChurchLogo(ChurchSettings):
    """Proxy for logo settings in admin."""

    class Meta:
        proxy = True
        verbose_name = "church logo"
        verbose_name_plural = "church logos"


class ChurchBranding(ChurchSettings):
    """Proxy for branding CSS settings in admin."""

    class Meta:
        proxy = True
        verbose_name = "church branding"
        verbose_name_plural = "church branding"
