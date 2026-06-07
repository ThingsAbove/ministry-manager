from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.scheduling.models import Assignment


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

    unfilled_count = 0
    if request.user.is_staff or request.user.groups.filter(name="TeamLeader").exists():
        unfilled_count = (
            Assignment.objects.filter(
                volunteer__isnull=True,
                service_occurrence__date__gte=today,
            ).count()
        )

    context = {
        "upcoming_assignments": upcoming,
        "unfilled_count": unfilled_count,
    }
    return render(request, "core/dashboard.html", context)
