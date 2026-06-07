from datetime import date, time, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.campuses.models import Campus, ServiceOccurrence, ServiceTime, Weekday
from apps.communications.tokens import generate_rsvp_token, verify_rsvp_token
from apps.scheduling.models import Assignment, BlockOutDate
from apps.scheduling.scheduler import (
    get_candidates,
    run_auto_schedule_for_occurrence,
    score_candidate,
    volunteer_is_blocked,
)
from apps.teams.models import Skill, Team, TeamMembership, TeamRole, VolunteerSkill


@pytest.fixture
def campus(db):
    return Campus.objects.create(name="Main Campus")


@pytest.fixture
def service_time(campus):
    return ServiceTime.objects.create(
        campus=campus,
        name="Sunday Morning",
        weekday=Weekday.SUNDAY,
        start_time=time(9, 0),
    )


@pytest.fixture
def occurrence(service_time):
    return ServiceOccurrence.objects.create(
        service_time=service_time,
        date=date(2026, 6, 7),
        start_time=time(9, 0),
    )


@pytest.fixture
def volunteer(db):
    user = User.objects.create_user(username="vol1", password="pass", email="v@test.com")
    return user.volunteer_profile


@pytest.fixture
def team(campus):
    return Team.objects.create(name="Greeters", campus=campus)


@pytest.fixture
def role(team):
    return TeamRole.objects.create(team=team, name="Door", slots_per_service=1)


@pytest.mark.django_db
class TestScheduler:
    def test_block_out_excludes_volunteer(self, volunteer, occurrence):
        BlockOutDate.objects.create(volunteer=volunteer, date=occurrence.date)
        assert volunteer_is_blocked(volunteer, occurrence.date)

    def test_get_candidates_respects_team_membership(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        candidates = get_candidates(role, occurrence)
        assert volunteer in candidates

    def test_skill_requirement_filters_candidates(self, volunteer, team, role, occurrence):
        skill = Skill.objects.create(name="First Aid")
        role.required_skills.add(skill)
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        assert get_candidates(role, occurrence) == []

        VolunteerSkill.objects.create(volunteer=volunteer, skill=skill)
        assert volunteer in get_candidates(role, occurrence)

    def test_auto_schedule_fills_slot(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        result = run_auto_schedule_for_occurrence(occurrence.pk)
        assert result["filled"] == 1
        assignment = Assignment.objects.get(service_occurrence=occurrence, team_role=role)
        assert assignment.volunteer == volunteer

    def test_conflict_prevented_on_assignment(self, volunteer, team, role, occurrence):
        other_role = TeamRole.objects.create(team=team, name="Usher", slots_per_service=1)
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        Assignment.objects.create(
            service_occurrence=occurrence,
            team_role=role,
            volunteer=volunteer,
            slot_index=0,
        )
        second = Assignment(
            service_occurrence=occurrence,
            team_role=other_role,
            volunteer=volunteer,
            slot_index=0,
        )
        with pytest.raises(ValidationError):
            second.save()

    def test_preferred_service_time_increases_score(
        self, volunteer, service_time, role, occurrence
    ):
        volunteer.preferred_service_times.add(service_time)
        score_with = score_candidate(volunteer, role, occurrence)
        other_user = User.objects.create_user(username="v2")
        other = other_user.volunteer_profile
        score_without = score_candidate(other, role, occurrence)
        assert score_with > score_without


@pytest.mark.django_db
class TestBlockOutCalendar:
    def test_block_out_toggle_via_post(self, client):
        user = User.objects.create_user("blockuser", password="pass")
        client.force_login(user)
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
        assert b"Blocked" in response.content

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
        assert b"Removed block-out" in response.content


@pytest.mark.django_db
class TestRSVPTokens:
    def test_token_roundtrip(self, volunteer, team, role, occurrence):
        assignment = Assignment.objects.create(
            service_occurrence=occurrence,
            team_role=role,
            volunteer=volunteer,
            slot_index=0,
        )
        token = generate_rsvp_token(assignment.pk)
        data = verify_rsvp_token(token)
        assert data["assignment_id"] == assignment.pk


@pytest.mark.django_db
class TestCommunications:
    def test_send_shift_reminders_creates_notifications(self, volunteer, team, role, occurrence):
        from apps.communications.models import Notification
        from apps.communications.tasks import send_shift_reminders

        TeamMembership.objects.create(team=team, volunteer=volunteer)
        volunteer.email_opt_in = True
        volunteer.save()
        Assignment.objects.create(
            service_occurrence=occurrence,
            team_role=role,
            volunteer=volunteer,
            slot_index=0,
        )
        occurrence.date = timezone.localdate() + timedelta(days=7)
        occurrence.save()

        result = send_shift_reminders()
        assert result["sent"] >= 1
        assert Notification.objects.filter(recipient=volunteer).exists()
