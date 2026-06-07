from django.core.exceptions import ValidationError
from django.db import models


class BlockOutDate(models.Model):
    volunteer = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.CASCADE,
        related_name="block_out_dates",
    )
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("volunteer", "date")]
        ordering = ["date"]
        indexes = [models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.volunteer} blocked {self.date}"


class AssignmentStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    UNFILLED = "unfilled", "Unfilled"
    CONFIRMED = "confirmed", "Confirmed"
    DECLINED = "declined", "Declined"


class Assignment(models.Model):
    service_occurrence = models.ForeignKey(
        "campuses.ServiceOccurrence",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    team_role = models.ForeignKey(
        "teams.TeamRole",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    volunteer = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
    )
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.SCHEDULED,
    )
    slot_index = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service_occurrence", "team_role", "slot_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["service_occurrence", "team_role", "slot_index"],
                name="unique_role_slot_per_occurrence",
            ),
            models.UniqueConstraint(
                fields=["service_occurrence", "volunteer"],
                condition=models.Q(volunteer__isnull=False),
                name="unique_volunteer_per_occurrence",
            ),
        ]

    def __str__(self):
        name = self.volunteer or "Unfilled"
        return f"{self.team_role} @ {self.service_occurrence} — {name}"

    def clean(self):
        if not self.volunteer_id:
            return
        conflict = Assignment.objects.filter(
            service_occurrence=self.service_occurrence,
            volunteer=self.volunteer,
        ).exclude(pk=self.pk)
        if conflict.exists():
            raise ValidationError(
                "This volunteer is already assigned to another team during this service."
            )

    def save(self, *args, **kwargs):
        if self.volunteer_id:
            self.status = AssignmentStatus.SCHEDULED
        else:
            self.status = AssignmentStatus.UNFILLED
        self.full_clean()
        super().save(*args, **kwargs)
