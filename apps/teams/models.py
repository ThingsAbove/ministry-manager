from django.conf import settings
from django.db import models
from django.utils import timezone


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Certification(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    validity_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Months until expiry; blank if no expiry",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    campus = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams",
    )
    leaders = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="led_teams",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeamRole(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    required_skills = models.ManyToManyField(Skill, blank=True, related_name="roles")
    required_certifications = models.ManyToManyField(
        Certification,
        blank=True,
        related_name="roles",
    )
    slots_per_service = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["team", "name"]
        unique_together = [("team", "name")]

    def __str__(self):
        return f"{self.team.name} — {self.name}"


class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    volunteer = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("team", "volunteer")]
        ordering = ["team", "volunteer"]

    def __str__(self):
        return f"{self.volunteer} on {self.team}"


class VolunteerSkill(models.Model):
    volunteer = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="volunteer_skills")

    class Meta:
        unique_together = [("volunteer", "skill")]

    def __str__(self):
        return f"{self.volunteer} — {self.skill}"


class VolunteerCertification(models.Model):
    volunteer = models.ForeignKey(
        "accounts.VolunteerProfile",
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    certification = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name="volunteer_certifications",
    )
    issued_at = models.DateField(default=timezone.localdate)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [("volunteer", "certification")]
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.volunteer} — {self.certification}"

    @property
    def is_valid(self):
        if self.expires_at is None:
            return True
        return self.expires_at >= timezone.localdate()
