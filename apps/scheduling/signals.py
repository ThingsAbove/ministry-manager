from contextlib import contextmanager

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Assignment

_suppress_assignment_notifications = False
_previous_volunteer_ids = {}


@contextmanager
def suppress_assignment_notifications():
    global _suppress_assignment_notifications
    previous = _suppress_assignment_notifications
    _suppress_assignment_notifications = True
    try:
        yield
    finally:
        _suppress_assignment_notifications = previous


@receiver(pre_save, sender=Assignment)
def cache_previous_volunteer(sender, instance, **kwargs):
    if instance.pk:
        _previous_volunteer_ids[instance.pk] = (
            Assignment.objects.filter(pk=instance.pk)
            .values_list("volunteer_id", flat=True)
            .first()
        )
    else:
        _previous_volunteer_ids[id(instance)] = None


@receiver(post_save, sender=Assignment)
def notify_on_assignment_save(sender, instance, created, **kwargs):
    if _suppress_assignment_notifications:
        return
    if not instance.volunteer_id:
        return

    key = instance.pk if instance.pk else id(instance)
    previous_volunteer_id = _previous_volunteer_ids.pop(key, None)
    if not created and previous_volunteer_id == instance.volunteer_id:
        return

    from apps.communications.tasks import notify_assignment

    notify_assignment(instance)
