from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.scheduling.models import Assignment

from .staffing import build_staffing_overview


@login_required
def dashboard(request):
    today = timezone.localdate()
    upcoming = (
        Assignment.objects.filter(
            volunteer__user=request.user,
            service_occurrence__date__gte=today,
        )
        .select_related(
            "service_occurrence__service_time__campus",
            "team_role__team",
            "rsvp",
        )
        .order_by("service_occurrence__date", "service_occurrence__start_time")[:10]
    )

    is_leader = request.user.is_staff or request.user.groups.filter(name="TeamLeader").exists()
    staffing = build_staffing_overview(request.user) if is_leader else None

    context = {
        "upcoming_assignments": upcoming,
        "staffing": staffing,
        "is_leader": is_leader,
    }
    return render(request, "core/dashboard.html", context)
