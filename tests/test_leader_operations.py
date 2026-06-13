from datetime import timedelta

import pytest

from apps.accounts.models import User
from apps.scheduling.models import Assignment
from apps.scheduling.scheduler import ensure_assignment_slots
from apps.scheduling.signals import suppress_assignment_notifications
from apps.teams.models import Team, TeamMembership, TeamRole


@pytest.mark.django_db
class TestLeaderTeamList:
    def test_leader_sees_only_led_teams(self, make_team_leader, campus, client):
        led_team = Team.objects.create(name="Led Team", campus=campus)
        Team.objects.create(name="Other Team", campus=campus)
        leader = make_team_leader(led_team, username="scoped-leader")
        client.force_login(leader)

        response = client.get("/teams/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Led Team" in response.content
        assert b"Other Team" not in response.content

    def test_staff_sees_all_teams(self, campus, client):
        Team.objects.create(name="Team A", campus=campus)
        Team.objects.create(name="Team B", campus=campus)
        admin = User.objects.create_user(
            username="staffadmin",
            password="pass",
            is_staff=True,
        )
        client.force_login(admin)

        response = client.get("/teams/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Team A" in response.content
        assert b"Team B" in response.content


@pytest.mark.django_db
class TestLeaderRoster:
    def test_roster_add_and_remove(self, leader_client, make_volunteer):
        client, leader, team = leader_client
        volunteer = make_volunteer(username="roster-vol")

        response = client.post(
            f"/teams/{team.pk}/roster/",
            {
                "action": "add",
                "volunteer_id": volunteer.volunteer_profile.pk,
            },
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert TeamMembership.objects.filter(
            team=team,
            volunteer=volunteer.volunteer_profile,
        ).exists()

        response = client.post(
            f"/teams/{team.pk}/roster/",
            {
                "action": "remove",
                "volunteer_id": volunteer.volunteer_profile.pk,
            },
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert not TeamMembership.objects.filter(
            team=team,
            volunteer=volunteer.volunteer_profile,
        ).exists()

    def test_leader_cannot_manage_other_team_roster(
        self, make_team_leader, campus, make_volunteer, client
    ):
        led_team = Team.objects.create(name="My Team", campus=campus)
        other_team = Team.objects.create(name="Not My Team", campus=campus)
        leader = make_team_leader(led_team, username="other-leader")
        make_volunteer(username="extra-vol")
        client.force_login(leader)

        response = client.get(f"/teams/{other_team.pk}/roster/", HTTP_HOST="localhost")
        assert response.status_code == 302
        assert response.url.endswith("/teams/")


@pytest.mark.django_db
class TestLeaderRota:
    def test_rota_manual_assign(self, leader_client, make_volunteer, occurrence, role):
        client, leader, team = leader_client
        volunteer = make_volunteer(username="rota-vol")
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        ensure_assignment_slots(occurrence)
        assignment = Assignment.objects.filter(
            service_occurrence=occurrence,
            team_role=role,
        ).first()

        with suppress_assignment_notifications():
            response = client.post(
                "/scheduling/rota/",
                {
                    "assignment_id": assignment.pk,
                    "volunteer_id": volunteer.volunteer_profile.pk,
                },
                HTTP_HOST="localhost",
                HTTP_HX_REQUEST="true",
            )
        assert response.status_code == 200
        assignment.refresh_from_db()
        assert assignment.volunteer_id == volunteer.volunteer_profile.pk

    def test_rota_conflict_returns_error(
        self, leader_client, make_volunteer, occurrence, team
    ):
        client, leader, team = leader_client
        volunteer = make_volunteer(username="conflict-vol")
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        role_a = TeamRole.objects.create(team=team, name="Role A", slots_per_service=1)
        role_b = TeamRole.objects.create(team=team, name="Role B", slots_per_service=1)
        ensure_assignment_slots(occurrence)
        assignment_a = Assignment.objects.get(service_occurrence=occurrence, team_role=role_a)
        assignment_b = Assignment.objects.get(service_occurrence=occurrence, team_role=role_b)

        with suppress_assignment_notifications():
            assignment_a.volunteer = volunteer.volunteer_profile
            assignment_a.save()
            response = client.post(
                "/scheduling/rota/",
                {
                    "assignment_id": assignment_b.pk,
                    "volunteer_id": volunteer.volunteer_profile.pk,
                },
                HTTP_HOST="localhost",
                HTTP_HX_REQUEST="true",
            )
        assert response.status_code == 200
        assert b"already assigned" in response.content.lower()
        assignment_b.refresh_from_db()
        assert assignment_b.volunteer_id is None

    def test_rota_shows_only_led_teams(
        self, make_team_leader, campus, service_time, client
    ):
        from django.utils import timezone

        from apps.campuses.models import ServiceOccurrence
        from apps.teams.models import Team, TeamRole

        led_team = Team.objects.create(name="Led Team", campus=campus)
        other_team = Team.objects.create(name="Other Team", campus=campus)
        TeamRole.objects.create(team=led_team, name="Greeter", slots_per_service=1)
        TeamRole.objects.create(team=other_team, name="Barista", slots_per_service=1)
        leader = make_team_leader(led_team, username="rota-scoped-lead")
        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=14),
            start_time=service_time.start_time,
        )
        ensure_assignment_slots(occurrence)
        client.force_login(leader)
        week_start = occurrence.date - timedelta(days=occurrence.date.weekday())

        response = client.get(
            f"/scheduling/rota/?week={week_start.isoformat()}",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200
        assert b"Led Team" in response.content
        assert b"Other Team" not in response.content

    def test_rota_shows_rsvp_status(
        self, leader_client, make_volunteer, service_time, role, team
    ):
        from django.utils import timezone

        from apps.campuses.models import ServiceOccurrence
        from apps.communications.models import RSVP, RSVPStatus

        client, leader, team = leader_client
        volunteer = make_volunteer(username="declined-vol")
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=14),
            start_time=service_time.start_time,
        )
        ensure_assignment_slots(occurrence)
        assignment = Assignment.objects.filter(
            service_occurrence=occurrence,
            team_role=role,
        ).first()
        with suppress_assignment_notifications():
            assignment.volunteer = volunteer.volunteer_profile
            assignment.save()
        RSVP.objects.create(assignment=assignment, status=RSVPStatus.DECLINED)
        week_start = occurrence.date - timedelta(days=occurrence.date.weekday())

        response = client.get(
            f"/scheduling/rota/?week={week_start.isoformat()}",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200
        assert b"Declined" in response.content
        assert b"bg-red-50" in response.content

    def test_rota_assign_requires_csrf_token(
        self, make_team_leader, team, role, service_time, occurrence
    ):
        from django.test import Client

        leader = make_team_leader(team, username="csrf-leader")
        client = Client(enforce_csrf_checks=True)
        client.force_login(leader)
        ensure_assignment_slots(occurrence)
        assignment = Assignment.objects.filter(
            service_occurrence=occurrence,
            team_role=role,
        ).first()

        response = client.post(
            "/scheduling/rota/",
            {
                "assignment_id": assignment.pk,
                "volunteer_id": "",
            },
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403

        client.get("/scheduling/rota/", HTTP_HOST="localhost")
        csrf = client.cookies["csrftoken"].value
        response = client.post(
            "/scheduling/rota/",
            {
                "assignment_id": assignment.pk,
                "volunteer_id": "",
            },
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 200

    def test_rota_assign_sends_assignment_email(
        self, leader_client, make_volunteer, service_time, role, team
    ):
        from django.core import mail
        from django.utils import timezone

        from apps.campuses.models import ServiceOccurrence

        client, leader, team = leader_client
        volunteer = make_volunteer(username="email-rota-vol")
        volunteer.volunteer_profile.email_opt_in = True
        volunteer.volunteer_profile.save()
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=14),
            start_time=service_time.start_time,
        )
        ensure_assignment_slots(occurrence)
        assignment = Assignment.objects.filter(
            service_occurrence=occurrence,
            team_role=role,
        ).first()

        mail.outbox.clear()
        response = client.post(
            "/scheduling/rota/",
            {
                "assignment_id": assignment.pk,
                "volunteer_id": volunteer.volunteer_profile.pk,
            },
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert b"/communications/rsvp/" in mail.outbox[0].body.encode()


@pytest.mark.django_db
class TestLeaderAutoSchedule:
    def test_auto_schedule_trigger(self, leader_client, occurrence):
        client, leader, team = leader_client
        response = client.post(
            "/scheduling/auto-schedule/",
            {
                "start_date": occurrence.date.isoformat(),
                "end_date": occurrence.date.isoformat(),
            },
            HTTP_HOST="localhost",
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestLeaderMassMessage:
    def test_mass_message_creates_notifications(self, leader_client, make_volunteer):
        from apps.communications.models import Notification

        client, leader, team = leader_client
        volunteer = make_volunteer(username="mass-vol")
        volunteer.volunteer_profile.email_opt_in = True
        volunteer.volunteer_profile.save()
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)

        response = client.post(
            "/communications/mass-message/",
            {
                "team": team.pk,
                "message": "Team meeting this Wednesday at 7pm.",
                "channels": ["email"],
            },
            HTTP_HOST="localhost",
        )
        assert response.status_code == 302
        assert Notification.objects.filter(
            recipient=volunteer.volunteer_profile,
            body__contains="Team meeting",
        ).exists()
