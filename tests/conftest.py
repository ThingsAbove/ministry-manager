from datetime import date, time

import pytest
from django.conf import settings
from django.contrib.auth.models import Group

from apps.accounts.models import ServingFrequency, User
from apps.campuses.models import Campus, ServiceOccurrence, ServiceTime, Weekday
from apps.teams.models import Team, TeamMembership, TeamRole


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
def team(campus):
    return Team.objects.create(name="Greeters", campus=campus)


@pytest.fixture
def role(team):
    return TeamRole.objects.create(team=team, name="Door Greeter", slots_per_service=1)


@pytest.fixture
def make_volunteer(db):
    def _make_volunteer(
        username="volunteer",
        password="pass",
        email=None,
        is_test_user=False,
        **user_kwargs,
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email or f"{username}@test.com",
            is_test_user=is_test_user,
            **user_kwargs,
        )
        return user

    return _make_volunteer


@pytest.fixture
def make_team_leader(db):
    def _make_team_leader(
        team,
        username="leader",
        password="pass",
        is_test_user=False,
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@test.com",
            is_test_user=is_test_user,
        )
        leader_group, _ = Group.objects.get_or_create(name=settings.GROUP_TEAM_LEADER)
        user.groups.add(leader_group)
        team.leaders.add(user)
        TeamMembership.objects.get_or_create(team=team, volunteer=user.volunteer_profile)
        return user

    return _make_team_leader


@pytest.fixture
def volunteer(make_volunteer):
    user = make_volunteer(username="vol1", email="v@test.com")
    return user.volunteer_profile


@pytest.fixture
def volunteer_client(make_volunteer, client):
    user = make_volunteer(username="volunteer1")
    client.force_login(user)
    return client, user


@pytest.fixture
def leader_client(make_team_leader, team, client):
    user = make_team_leader(team, username="teamlead")
    client.force_login(user)
    return client, user, team
