from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    @property
    def display_name(self):
        full = self.get_full_name()
        return full if full else self.username

    def is_team_leader(self):
        return self.groups.filter(name="TeamLeader").exists() or self.is_staff

    def is_admin_user(self):
        return self.is_staff or self.groups.filter(name="Admin").exists()


class ServingFrequency(models.TextChoices):
    WEEKLY = "weekly", "Weekly"
    BIWEEKLY = "biweekly", "Every 2 weeks"
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    AS_NEEDED = "as_needed", "As needed"


class VolunteerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    email_opt_in = models.BooleanField(default=True)
    sms_opt_in = models.BooleanField(default=False)
    serving_frequency = models.CharField(
        max_length=20,
        choices=ServingFrequency.choices,
        default=ServingFrequency.MONTHLY,
    )
    preferred_service_times = models.ManyToManyField(
        "campuses.ServiceTime",
        blank=True,
        related_name="preferred_by",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.display_name

    @property
    def contact_phone(self):
        return self.phone or self.user.phone

    @property
    def contact_email(self):
        return self.user.email
