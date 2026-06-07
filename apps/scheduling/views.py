from datetime import date, timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import VolunteerProfile
from apps.campuses.models import ServiceOccurrence

from .calendar_utils import month_calendar_weeks, shift_month
from .models import Assignment, BlockOutDate
from .scheduler import ensure_assignment_slots
from .tasks import run_auto_schedule


def is_leader_or_staff(user):
    return user.is_staff or user.is_team_leader()


class AutoScheduleForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "input"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "input"}))

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date must be on or after start date.")
        return cleaned


def _block_out_context(profile, year, month):
    first_of_month = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_of_month = next_month - timedelta(days=1)
    blocked = set(
        BlockOutDate.objects.filter(
            volunteer=profile,
            date__gte=first_of_month,
            date__lte=last_of_month,
        ).values_list("date", flat=True)
    )
    prev_year, prev_month = shift_month(year, month, -1)
    next_year, next_month = shift_month(year, month, 1)
    return {
        "year": year,
        "month": month,
        "blocked_dates": blocked,
        "first_of_month": first_of_month,
        "last_of_month": last_of_month,
        "weeks": month_calendar_weeks(first_of_month, last_of_month),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }


@login_required
def my_schedule(request):
    today = timezone.localdate()
    assignments = (
        Assignment.objects.filter(
            volunteer__user=request.user,
            service_occurrence__date__gte=today - timedelta(days=7),
        )
        .select_related(
            "service_occurrence__service_time__campus",
            "team_role__team",
            "rsvp",
        )
        .order_by("service_occurrence__date", "service_occurrence__start_time")
    )
    return render(request, "scheduling/my_schedule.html", {"assignments": assignments})


@login_required
def block_out_calendar(request):
    profile = request.user.volunteer_profile
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    feedback = None

    if request.method == "POST":
        toggle_date = date.fromisoformat(request.POST["date"])
        existing = BlockOutDate.objects.filter(volunteer=profile, date=toggle_date)
        if existing.exists():
            existing.delete()
            feedback = f"Removed block-out for {toggle_date.strftime('%B %d, %Y')}."
        else:
            BlockOutDate.objects.create(volunteer=profile, date=toggle_date)
            feedback = f"Blocked {toggle_date.strftime('%B %d, %Y')}."
        year = toggle_date.year
        month = toggle_date.month
        context = _block_out_context(profile, year, month)
        context["feedback"] = feedback
        if request.htmx:
            return render(request, "scheduling/partials/calendar_grid.html", context)
        return render(request, "scheduling/block_out_calendar.html", context)

    return render(
        request,
        "scheduling/block_out_calendar.html",
        _block_out_context(profile, year, month),
    )


@login_required
@user_passes_test(is_leader_or_staff)
def rota_grid(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    if start_param := request.GET.get("week"):
        week_start = date.fromisoformat(start_param)
    week_end = week_start + timedelta(days=6)

    occurrences = ServiceOccurrence.objects.filter(
        date__gte=week_start,
        date__lte=week_end,
    ).select_related("service_time__campus").order_by("date", "start_time")

    for occ in occurrences:
        ensure_assignment_slots(occ)

    assignments = (
        Assignment.objects.filter(service_occurrence__in=occurrences)
        .select_related("team_role__team", "volunteer__user", "service_occurrence")
        .order_by("service_occurrence__date", "team_role__team__name", "team_role__name")
    )

    if request.method == "POST" and request.htmx:
        assignment_id = request.POST.get("assignment_id")
        volunteer_id = request.POST.get("volunteer_id") or None
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        try:
            assignment.volunteer_id = int(volunteer_id) if volunteer_id else None
            assignment.save()
            conflict = None
        except IntegrityError:
            conflict = "This volunteer is already assigned during this service."
            assignment.refresh_from_db()
        except ValidationError as exc:
            conflict = exc.messages[0] if exc.messages else str(exc)
            assignment.refresh_from_db()

        volunteers = VolunteerProfile.objects.filter(
            team_memberships__team=assignment.team_role.team,
            team_memberships__is_active=True,
        ).select_related("user")
        return render(
            request,
            "scheduling/partials/rota_cell.html",
            {
                "assignment": assignment,
                "volunteers": volunteers,
                "conflict": conflict,
            },
        )

    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    return render(
        request,
        "scheduling/rota_grid.html",
        {
            "week_start": week_start,
            "week_end": week_end,
            "prev_week": prev_week,
            "next_week": next_week,
            "occurrences": occurrences,
            "assignments": assignments,
        },
    )


@login_required
@user_passes_test(is_leader_or_staff)
def auto_schedule_view(request):
    today = timezone.localdate()
    initial = {
        "start_date": today,
        "end_date": today + timedelta(weeks=4),
    }
    result = None
    if request.method == "POST":
        form = AutoScheduleForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"].isoformat()
            end = form.cleaned_data["end_date"].isoformat()
            result = run_auto_schedule.delay(start_date=start, end_date=end)
            if request.htmx:
                return render(
                    request,
                    "scheduling/partials/auto_schedule_started.html",
                    {"task_id": result.id},
                )
            messages.success(request, "Auto-schedule started. Refresh shortly for results.")
            return redirect("scheduling:auto_schedule")
    else:
        form = AutoScheduleForm(initial=initial)
    return render(
        request,
        "scheduling/auto_schedule.html",
        {"form": form, "result": result},
    )
