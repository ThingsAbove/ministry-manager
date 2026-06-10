from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from apps.accounts.demo_volunteers import (
    DEFAULT_DEMO_PASSWORD,
    all_demo_volunteers,
)
from apps.accounts.models import User
from apps.campuses.models import ServiceOccurrence, ServiceTime
from apps.communications.models import RSVP, RSVPStatus
from apps.communications.tasks import notify_assignment
from apps.scheduling.models import Assignment, BlockOutDate
from apps.scheduling.scheduler import run_auto_schedule_date_range
from apps.scheduling.signals import suppress_assignment_notifications
from apps.teams.models import Team, TeamMembership


class Command(BaseCommand):
    help = "Seed demo volunteers, team rosters, and a multi-week schedule for demonstrations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing test users (is_test_user=True) before seeding",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_DEMO_PASSWORD,
            help=f"Password for demo accounts (default: {DEFAULT_DEMO_PASSWORD})",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            default=13,
            help="Weeks of service occurrences to generate (~3 months, default: 13)",
        )
        parser.add_argument(
            "--no-schedule",
            action="store_true",
            help="Create users and rosters only; skip auto-schedule",
        )
        parser.add_argument(
            "--no-notifications",
            action="store_true",
            help="Skip sending sample assignment notifications after scheduling",
        )

    def handle(self, *args, **options):
        password = options["password"]
        weeks = options["weeks"]

        team_names = {spec["team_name"] for spec in all_demo_volunteers()}
        teams = {t.name: t for t in Team.objects.filter(name__in=team_names, is_active=True)}
        missing = team_names - set(teams.keys())
        if missing:
            self.stderr.write(
                self.style.ERROR(
                    f"Missing teams: {', '.join(sorted(missing))}. "
                    "Run `python manage.py setup_groups` first."
                )
            )
            return

        if options["reset"]:
            deleted, _ = User.objects.filter(is_test_user=True).delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} test user record(s)."))

        leader_group, _ = Group.objects.get_or_create(name=settings.GROUP_TEAM_LEADER)
        service_times = list(ServiceTime.objects.filter(is_active=True))

        created_users = []
        for spec in all_demo_volunteers():
            user, was_created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "email": spec["email"],
                    "is_test_user": True,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            if not was_created:
                user.first_name = spec["first_name"]
                user.last_name = spec["last_name"]
                user.email = spec["email"]
                user.is_test_user = True
                user.is_staff = False
                user.is_superuser = False
                user.save()

            user.set_password(password)
            user.save(update_fields=["password"])

            profile = user.volunteer_profile
            profile.serving_frequency = spec["serving_frequency"]
            profile.email_opt_in = True
            profile.sms_opt_in = False
            profile.save()

            if service_times:
                profile.preferred_service_times.set(service_times[:1])

            team = teams[spec["team_name"]]
            TeamMembership.objects.get_or_create(team=team, volunteer=profile)

            if spec["is_team_lead"]:
                user.groups.add(leader_group)
                team.leaders.add(user)

            created_users.append(
                {
                    "username": user.username,
                    "name": user.display_name,
                    "team": team.name,
                    "role": "Team Lead" if spec["is_team_lead"] else "Volunteer",
                }
            )

        self._seed_block_outs(created_users)

        if not options["no_schedule"]:
            self._ensure_occurrences(weeks)
            start = timezone.localdate()
            end = start + timedelta(weeks=weeks)
            self.stdout.write(f"Auto-scheduling {start} through {end}...")
            with suppress_assignment_notifications():
                result = run_auto_schedule_date_range(start, end)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Scheduled {result['occurrences']} occurrence(s): "
                    f"{result['filled']} filled, {result['unfilled']} unfilled."
                )
            )
            self._leave_unfilled_demo_slots(teams["Tech"])
            if not options["no_notifications"]:
                self._seed_sample_notifications()
            self._seed_sample_rsvps()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo volunteers ready:"))
        self.stdout.write(f"  Password: {password}")
        self.stdout.write(f"  Email routing: {settings.TEST_EMAIL_ADDRESS}")
        self.stdout.write("")
        for row in created_users:
            self.stdout.write(
                f"  {row['username']:22} {row['name']:22} {row['team']:14} {row['role']}"
            )

    def _seed_block_outs(self, created_users):
        today = timezone.localdate()
        usernames = [row["username"] for row in created_users[:6]]
        profiles = list(
            User.objects.filter(username__in=usernames).select_related("volunteer_profile")
        )
        offsets = [14, 21, 28, 35, 42, 49]
        for user, offset in zip(profiles, offsets):
            BlockOutDate.objects.get_or_create(
                volunteer=user.volunteer_profile,
                date=today + timedelta(days=offset),
            )

    def _ensure_occurrences(self, weeks):
        latest = ServiceOccurrence.objects.aggregate(last=Max("date"))["last"]
        today = timezone.localdate()
        target_end = today + timedelta(weeks=weeks)
        if not latest or latest < target_end:
            call_command("generate_occurrences", weeks=weeks)

    def _leave_unfilled_demo_slots(self, team):
        """Clear a few Tech team assignments in the next two weeks for unfilled alerts."""
        today = timezone.localdate()
        end = today + timedelta(days=14)
        assignments = Assignment.objects.filter(
            team_role__team=team,
            service_occurrence__date__gte=today,
            service_occurrence__date__lte=end,
            volunteer__isnull=False,
        ).order_by("service_occurrence__date")[:3]
        with suppress_assignment_notifications():
            for assignment in assignments:
                assignment.volunteer = None
                assignment.save()

    def _seed_sample_notifications(self):
        today = timezone.localdate()
        assignments = (
            Assignment.objects.filter(
                volunteer__user__is_test_user=True,
                service_occurrence__date__gte=today,
                service_occurrence__date__lte=today + timedelta(days=14),
            )
            .select_related("volunteer")
            .order_by("service_occurrence__date")[:3]
        )
        for assignment in assignments:
            notify_assignment(assignment)

    def _seed_sample_rsvps(self):
        today = timezone.localdate()
        assignments = list(
            Assignment.objects.filter(
                volunteer__user__is_test_user=True,
                service_occurrence__date__gte=today,
            )
            .select_related("volunteer", "team_role__team")
            .order_by("service_occurrence__date")[:5]
        )
        if not assignments:
            return

        for assignment in assignments[:2]:
            rsvp, _ = RSVP.objects.get_or_create(assignment=assignment)
            rsvp.status = RSVPStatus.ACCEPTED
            rsvp.responded_at = timezone.now()
            rsvp.save()

        declined = assignments[2] if len(assignments) > 2 else assignments[0]
        rsvp, _ = RSVP.objects.get_or_create(assignment=declined)
        rsvp.status = RSVPStatus.DECLINED
        rsvp.responded_at = timezone.now()
        rsvp.save()

        team = declined.team_role.team
        for leader in team.leaders.filter(is_test_user=True):
            from apps.communications.rsvp_service import notify_leaders_of_decline

            notify_leaders_of_decline(declined)
