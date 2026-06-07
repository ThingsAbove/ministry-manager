from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, VolunteerProfile


@receiver(post_save, sender=User)
def create_volunteer_profile(sender, instance, created, **kwargs):
    if created:
        VolunteerProfile.objects.create(user=instance)
        volunteer_group, _ = Group.objects.get_or_create(name=settings.GROUP_VOLUNTEER)
        instance.groups.add(volunteer_group)
