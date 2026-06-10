from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group
from django.conf import settings

from apps.accounts.models import ServingFrequency
from apps.communications.models import RSVP, RSVPStatus
from apps.communications.tokens import generate_rsvp_token
from apps.scheduling.models import Assignment, BlockOutDate
from apps.scheduling.signals import suppress_assignment_notifications
from apps.teams.models import TeamMembership


@pytest.mark.django_db
class TestVolunteerRegistration:
    def test_register_creates_user_profile_and_volunteer_group(self, client):
        response = client.post(
            "/accounts/register/",
            {
                "username": "newvol",
                "email": "newvol@example.com",
                "first_name": "New",
                "last_name": "Volunteer",
                "phone": "",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            HTTP_HOST="localhost",
        )
        assert response.status_code == 302

        from apps.accounts.models import User

        user = User.objects.get(username="newvol")
        assert hasattr(user, "volunteer_profile")
        volunteer_group = Group.objects.get(name=settings.GROUP_VOLUNTEER)
        assert user.groups.filter(pk=volunteer_group.pk).exists()


@pytest.mark.django_db
class TestVolunteerProfile:
    def test_profile_update_saves_preferences(self, volunteer_client):
        client, user = volunteer_client
        response = client.post(
            "/accounts/profile/",
            {
                "first_name": "Volunteer",
                "last_name": "One",
                "email": user.email,
                "phone": "555-0100",
                "email_opt_in": "on",
                "sms_opt_in": "",
                "serving_frequency": ServingFrequency.WEEKLY,
                "notes": "Available most Sundays",
            },
            HTTP_HOST="localhost",
        )
        assert response.status_code == 302
        user.volunteer_profile.refresh_from_db()
        user.refresh_from_db()
        assert user.volunteer_profile.serving_frequency == ServingFrequency.WEEKLY
        assert user.volunteer_profile.notes == "Available most Sundays"


@pytest.mark.django_db
class TestVolunteerBlockOuts:
    def test_block_out_toggle(self, volunteer_client):
        client, user = volunteer_client
        response = client.post(
            "/scheduling/block-outs/?year=2026&month=6",
            {"date": "2026-06-15"},
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert BlockOutDate.objects.filter(
            volunteer=user.volunteer_profile,
            date=date(2026, 6, 15),
        ).exists()

        response = client.post(
            "/scheduling/block-outs/?year=2026&month=6",
            {"date": "2026-06-15"},
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert not BlockOutDate.objects.filter(
            volunteer=user.volunteer_profile,
            date=date(2026, 6, 15),
        ).exists()


@pytest.mark.django_db
class TestVolunteerSchedule:
    def test_my_schedule_shows_assignment(
        self, volunteer_client, team, role, occurrence, make_volunteer
    ):
        client, user = volunteer_client
        TeamMembership.objects.create(team=team, volunteer=user.volunteer_profile)
        with suppress_assignment_notifications():
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=user.volunteer_profile,
                slot_index=0,
            )

        response = client.get("/scheduling/my-schedule/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Door Greeter" in response.content
        assert b"Greeters" in response.content

    def test_dashboard_shows_upcoming_assignment(
        self, volunteer_client, team, role, occurrence
    ):
        from django.utils import timezone

        client, user = volunteer_client
        occurrence.date = timezone.localdate() + timedelta(days=7)
        occurrence.save()
        TeamMembership.objects.create(team=team, volunteer=user.volunteer_profile)
        with suppress_assignment_notifications():
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=user.volunteer_profile,
                slot_index=0,
            )

        response = client.get("/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Door Greeter" in response.content


@pytest.mark.django_db
class TestVolunteerRSVP:
    def test_rsvp_accept(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer,
                slot_index=0,
            )

        token = generate_rsvp_token(assignment.pk)
        from django.test import Client

        client = Client()
        response = client.get(
            f"/communications/rsvp/{token}/accept/",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200
        rsvp = RSVP.objects.get(assignment=assignment)
        assert rsvp.status == RSVPStatus.ACCEPTED

    def test_rsvp_decline(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer,
                slot_index=0,
            )

        token = generate_rsvp_token(assignment.pk)
        from django.test import Client

        client = Client()
        response = client.get(
            f"/communications/rsvp/{token}/decline/",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200
        rsvp = RSVP.objects.get(assignment=assignment)
        assert rsvp.status == RSVPStatus.DECLINED

    def test_rsvp_accept_in_app(self, volunteer_client, team, role, occurrence):
        client, user = volunteer_client
        TeamMembership.objects.create(team=team, volunteer=user.volunteer_profile)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=user.volunteer_profile,
                slot_index=0,
            )

        response = client.post(
            f"/scheduling/assignments/{assignment.pk}/rsvp/",
            {"response": "accept"},
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"Accepted" in response.content
        rsvp = RSVP.objects.get(assignment=assignment)
        assert rsvp.status == RSVPStatus.ACCEPTED

    def test_rsvp_decline_in_app(self, volunteer_client, team, role, occurrence):
        client, user = volunteer_client
        TeamMembership.objects.create(team=team, volunteer=user.volunteer_profile)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=user.volunteer_profile,
                slot_index=0,
            )

        response = client.post(
            f"/scheduling/assignments/{assignment.pk}/rsvp/",
            {"response": "decline"},
            HTTP_HOST="localhost",
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"Declined" in response.content
        rsvp = RSVP.objects.get(assignment=assignment)
        assert rsvp.status == RSVPStatus.DECLINED

    def test_rsvp_in_app_rejects_other_users_assignment(
        self, volunteer_client, make_volunteer, team, role, occurrence
    ):
        client, user = volunteer_client
        other = make_volunteer(username="other-vol")
        TeamMembership.objects.create(team=team, volunteer=other.volunteer_profile)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=other.volunteer_profile,
                slot_index=0,
            )

        response = client.post(
            f"/scheduling/assignments/{assignment.pk}/rsvp/",
            {"response": "accept"},
            HTTP_HOST="localhost",
        )
        assert response.status_code == 404
