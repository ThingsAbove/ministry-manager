from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.core.models import ChurchSettings


class Command(BaseCommand):
    help = "Create default auth groups and church settings"

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name=settings.GROUP_ADMIN)
        leader_group, _ = Group.objects.get_or_create(name=settings.GROUP_TEAM_LEADER)
        volunteer_group, _ = Group.objects.get_or_create(name=settings.GROUP_VOLUNTEER)

        ChurchSettings.load()

        from django.core.management import call_command

        call_command("setup_teams")
        call_command("setup_services")

        self.stdout.write(
            self.style.SUCCESS(
                "Groups, church settings, default teams, and service times ready"
            )
        )
