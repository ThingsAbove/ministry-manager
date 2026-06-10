from datetime import timedelta

import pytest
from django.utils import timezone

from apps.communications.models import RSVP, RSVPStatus
from apps.core.staffing import build_staffing_overview
from apps.scheduling.models import Assignment
from apps.scheduling.signals import suppress_assignment_notifications
from apps.teams.models import TeamMembership


@pytest.mark.django_db
class TestStaffingOverview:
    def test_admin_sees_all_teams_with_details(
        self, client, campus, make_volunteer, make_team_leader, service_time, role, team
    ):
        from apps.accounts.models import User
        from apps.campuses.models import ServiceOccurrence
        from apps.teams.models import Team, TeamRole

        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=7),
            start_time=service_time.start_time,
        )
        admin = User.objects.create_user(
            username="admin-dash",
            password="pass",
            is_staff=True,
        )
        volunteer = make_volunteer(username="assigned-vol", first_name="Sam", last_name="River")
        other_team = Team.objects.create(name="Coffee", campus=campus)
        other_role = TeamRole.objects.create(team=other_team, name="Barista", slots_per_service=1)
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)

        with suppress_assignment_notifications():
            filled = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer.volunteer_profile,
                slot_index=0,
            )
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=other_role,
                volunteer=None,
                slot_index=0,
            )
        RSVP.objects.create(assignment=filled, status=RSVPStatus.ACCEPTED)

        client.force_login(admin)
        response = client.get("/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Team Staffing Overview" in response.content
        assert b"Greeters" in response.content
        assert b"Coffee" in response.content
        assert b"Sam River" in response.content
        assert b"Needs volunteer" in response.content
        assert b"Accepted" in response.content
        assert b"Unfilled" in response.content

    def test_team_leader_sees_only_led_teams(
        self, make_team_leader, campus, service_time, role, team
    ):
        from apps.campuses.models import ServiceOccurrence
        from apps.teams.models import Team, TeamRole

        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=7),
            start_time=service_time.start_time,
        )
        led_team = team
        other_team = Team.objects.create(name="Roadies", campus=campus)
        TeamRole.objects.create(team=other_team, name="Runner", slots_per_service=1)
        leader = make_team_leader(led_team, username="dash-leader")
        with suppress_assignment_notifications():
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=None,
                slot_index=0,
            )

        overview = build_staffing_overview(leader)
        team_names = [item["team"].name for item in overview["teams"]]
        assert "Greeters" in team_names
        assert "Roadies" not in team_names

    def test_rsvp_accept_does_not_reduce_unfilled_count(
        self, make_volunteer, team, role, service_time
    ):
        from apps.accounts.models import User
        from apps.campuses.models import ServiceOccurrence

        occurrence = ServiceOccurrence.objects.create(
            service_time=service_time,
            date=timezone.localdate() + timedelta(days=7),
            start_time=service_time.start_time,
        )
        admin = User.objects.create_user(username="admin-count", is_staff=True)
        volunteer = make_volunteer(username="rsvp-vol")
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer.volunteer_profile,
                slot_index=0,
            )
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=None,
                slot_index=1,
            )

        before = build_staffing_overview(admin)
        assert before["totals"]["unfilled"] == 1
        assert before["totals"]["filled"] == 1

        RSVP.objects.create(assignment=assignment, status=RSVPStatus.ACCEPTED)
        after = build_staffing_overview(admin)
        assert after["totals"]["unfilled"] == 1
        assert after["totals"]["accepted"] == 1
        assert after["totals"]["filled"] == 1

    def test_volunteer_does_not_see_staffing_overview(self, volunteer_client):
        client, user = volunteer_client
        response = client.get("/", HTTP_HOST="localhost")
        assert response.status_code == 200
        assert b"Team Staffing Overview" not in response.content
