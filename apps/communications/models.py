from django.db import models


class NotificationType(models.TextChoices):
    REMINDER = "reminder", "Reminder"
    ASSIGNMENT = "assignment", "Assignment"
    MASS = "mass", "Mass Message"
    RSVP = "rsvp", "RSVP"
    UNFILLED = "unfilled", "Unfilled Slot Alert"


class NotificationChannel(models.TextChoices):
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class Notification(models.Model):
    recipient = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    recipient_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    assignment = models.ForeignKey(
        "scheduling.Assignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices)
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    external_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} via {self.channel} ({self.status})"


class RSVPStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"


class RSVP(models.Model):
    assignment = models.OneToOneField(
        "scheduling.Assignment",
        on_delete=models.CASCADE,
        related_name="rsvp",
    )
    status = models.CharField(
        max_length=10,
        choices=RSVPStatus.choices,
        default=RSVPStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RSVP {self.status} for {self.assignment}"
