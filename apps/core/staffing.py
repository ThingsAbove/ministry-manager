from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.communications.models import RSVP, RSVPStatus
from apps.scheduling.models import Assignment

STAFFING_WINDOW_WEEKS = 4


def build_staffing_overview(user, weeks=STAFFING_WINDOW_WEEKS):
    today = timezone.localdate()
    end = today + timedelta(weeks=weeks)

    assignments = (
        Assignment.objects.filter(
            service_occurrence__date__gte=today,
            service_occurrence__date__lte=end,
        )
        .select_related(
            "team_role__team",
            "team_role",
            "volunteer__user",
            "service_occurrence__service_time",
            "rsvp",
        )
        .order_by(
            "team_role__team__name",
            "service_occurrence__date",
            "service_occurrence__start_time",
            "team_role__name",
            "slot_index",
        )
    )

    if not user.is_staff:
        assignments = assignments.filter(team_role__team__leaders=user)

    teams = defaultdict(
        lambda: {
            "team": None,
            "assignments": [],
            "unfilled": 0,
            "filled": 0,
            "accepted": 0,
            "declined": 0,
            "pending_rsvp": 0,
        }
    )

    for assignment in assignments:
        team = assignment.team_role.team
        entry = teams[team.pk]
        entry["team"] = team
        entry["assignments"].append(assignment)

        if assignment.volunteer_id is None:
            entry["unfilled"] += 1
            continue

        entry["filled"] += 1
        try:
            rsvp_status = assignment.rsvp.status
        except RSVP.DoesNotExist:
            rsvp_status = None

        if rsvp_status == RSVPStatus.ACCEPTED:
            entry["accepted"] += 1
        elif rsvp_status == RSVPStatus.DECLINED:
            entry["declined"] += 1
        else:
            entry["pending_rsvp"] += 1

    team_list = sorted(teams.values(), key=lambda item: item["team"].name)
    totals = {
        "unfilled": sum(item["unfilled"] for item in team_list),
        "filled": sum(item["filled"] for item in team_list),
        "accepted": sum(item["accepted"] for item in team_list),
        "declined": sum(item["declined"] for item in team_list),
        "pending_rsvp": sum(item["pending_rsvp"] for item in team_list),
    }

    return {
        "window_start": today,
        "window_end": end,
        "teams": team_list,
        "totals": totals,
    }
