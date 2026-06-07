from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import ServingFrequency
from apps.campuses.models import ServiceOccurrence
from apps.teams.models import TeamMembership, TeamRole, VolunteerCertification

from .models import Assignment, BlockOutDate

FREQUENCY_WEEKS = {
    ServingFrequency.WEEKLY: 1,
    ServingFrequency.BIWEEKLY: 2,
    ServingFrequency.MONTHLY: 4,
    ServingFrequency.QUARTERLY: 12,
    ServingFrequency.AS_NEEDED: 52,
}


def volunteer_has_required_skills(volunteer, role):
    required = set(role.required_skills.values_list("pk", flat=True))
    if not required:
        return True
    held = set(volunteer.skills.values_list("skill_id", flat=True))
    return required.issubset(held)


def volunteer_has_valid_certifications(volunteer, role):
    required = role.required_certifications.all()
    if not required.exists():
        return True
    today = timezone.localdate()
    for cert in required:
        vc = (
            VolunteerCertification.objects.filter(
                volunteer=volunteer,
                certification=cert,
            )
            .order_by("-issued_at")
            .first()
        )
        if not vc:
            return False
        if vc.expires_at and vc.expires_at < today:
            return False
    return True


def volunteer_is_blocked(volunteer, occurrence_date):
    return BlockOutDate.objects.filter(volunteer=volunteer, date=occurrence_date).exists()


def volunteer_over_frequency_cap(volunteer, occurrence, weeks_window=8):
    target_weeks = FREQUENCY_WEEKS.get(volunteer.serving_frequency, 4)
    window_start = occurrence.date - timedelta(weeks=weeks_window)
    recent_count = Assignment.objects.filter(
        volunteer=volunteer,
        service_occurrence__date__gte=window_start,
        service_occurrence__date__lte=occurrence.date,
    ).count()
    max_allowed = max(1, weeks_window // target_weeks)
    return recent_count >= max_allowed


def score_candidate(volunteer, role, occurrence):
    score = 0
    if volunteer.preferred_service_times.filter(pk=occurrence.service_time_id).exists():
        score += 10

    weeks_ago = 12
    since = occurrence.date - timedelta(weeks=weeks_ago)
    recent = Assignment.objects.filter(
        volunteer=volunteer,
        service_occurrence__date__gte=since,
        service_occurrence__date__lt=occurrence.date,
    ).count()
    score -= recent * 2
    return score


def get_candidates(role, occurrence, exclude_volunteer_ids=None):
    exclude_volunteer_ids = exclude_volunteer_ids or set()
    members = TeamMembership.objects.filter(
        team=role.team,
        is_active=True,
    ).select_related("volunteer")

    candidates = []
    for membership in members:
        volunteer = membership.volunteer
        if volunteer.pk in exclude_volunteer_ids:
            continue
        if not volunteer_has_required_skills(volunteer, role):
            continue
        if not volunteer_has_valid_certifications(volunteer, role):
            continue
        if volunteer_is_blocked(volunteer, occurrence.date):
            continue
        if volunteer_over_frequency_cap(volunteer, occurrence):
            continue
        candidates.append(volunteer)
    return candidates


def ensure_assignment_slots(occurrence):
    """Create unfilled assignment rows for each team role slot."""
    roles = TeamRole.objects.filter(team__is_active=True).select_related("team")
    if occurrence.service_time.campus_id:
        roles = roles.filter(
            Q(team__campus_id=occurrence.service_time.campus_id)
            | Q(team__campus__isnull=True)
        )
    created = []
    for role in roles:
        existing = Assignment.objects.filter(
            service_occurrence=occurrence,
            team_role=role,
        ).count()
        for slot in range(role.slots_per_service - existing):
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                slot_index=existing + slot,
                volunteer=None,
            )
            created.append(assignment)
    return created


def run_auto_schedule_for_occurrence(occurrence_id):
    occurrence = ServiceOccurrence.objects.select_related("service_time").get(pk=occurrence_id)
    ensure_assignment_slots(occurrence)

    assigned_volunteers = set()
    results = {"filled": 0, "unfilled": 0, "assignments": []}

    unfilled = (
        Assignment.objects.filter(
            service_occurrence=occurrence,
            volunteer__isnull=True,
        )
        .select_related("team_role")
        .order_by("team_role__team__name", "team_role__name", "slot_index")
    )

    for assignment in unfilled:
        candidates = get_candidates(
            assignment.team_role,
            occurrence,
            exclude_volunteer_ids=assigned_volunteers,
        )
        if not candidates:
            results["unfilled"] += 1
            results["assignments"].append({"assignment_id": assignment.pk, "status": "unfilled"})
            continue

        scored = [(score_candidate(v, assignment.team_role, occurrence), v) for v in candidates]
        scored.sort(key=lambda x: (-x[0], x[1].user.last_name))
        best = scored[0][1]
        assignment.volunteer = best
        assignment.save()
        assigned_volunteers.add(best.pk)
        results["filled"] += 1
        results["assignments"].append(
            {"assignment_id": assignment.pk, "status": "filled", "volunteer_id": best.pk}
        )

    return results


def run_auto_schedule_date_range(start_date, end_date):
    occurrences = ServiceOccurrence.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
    ).values_list("pk", flat=True)
    aggregate = {"filled": 0, "unfilled": 0, "occurrences": 0}
    for occ_id in occurrences:
        result = run_auto_schedule_for_occurrence(occ_id)
        aggregate["filled"] += result["filled"]
        aggregate["unfilled"] += result["unfilled"]
        aggregate["occurrences"] += 1
    return aggregate
