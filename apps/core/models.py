from django.db import models


class ChurchSettings(models.Model):
    """Singleton-style church configuration."""

    name = models.CharField(max_length=200, default="My Church")
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

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
