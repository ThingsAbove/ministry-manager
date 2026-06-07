from django.db import models


class Campus(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "campuses"

    def __str__(self):
        return self.name


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class ServiceTime(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="service_times")
    name = models.CharField(max_length=100)
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=90)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["campus", "weekday", "start_time"]
        unique_together = [("campus", "weekday", "start_time", "name")]

    def __str__(self):
        return f"{self.name} ({self.get_weekday_display()} {self.start_time:%H:%M})"


class ServiceOccurrence(models.Model):
    service_time = models.ForeignKey(
        ServiceTime,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    date = models.DateField()
    start_time = models.TimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = [("service_time", "date")]
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.service_time.name} — {self.date}"

    @property
    def campus(self):
        return self.service_time.campus
