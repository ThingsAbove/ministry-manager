from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import VolunteerProfile

from .models import Team, TeamMembership, TeamRole


def is_leader_or_staff(user):
    return user.is_staff or user.is_team_leader()


def user_can_manage_team(user, team):
    if user.is_staff:
        return True
    return team.leaders.filter(pk=user.pk).exists()


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "campus", "leaders", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3, "class": "input"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "description":
                field.widget.attrs.setdefault("class", "input")


class TeamRoleForm(forms.ModelForm):
    class Meta:
        model = TeamRole
        fields = [
            "name",
            "description",
            "required_skills",
            "required_certifications",
            "slots_per_service",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2, "class": "input"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ("required_skills", "required_certifications", "description"):
                field.widget.attrs.setdefault("class", "input")


@login_required
@user_passes_test(is_leader_or_staff)
def team_list(request):
    teams = Team.objects.select_related("campus").prefetch_related("leaders", "roles")
    if not request.user.is_staff:
        teams = teams.filter(leaders=request.user)
    return render(request, "teams/team_list.html", {"teams": teams})


@login_required
@user_passes_test(is_leader_or_staff)
def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            if not request.user.is_staff:
                team.leaders.add(request.user)
            return redirect("teams:list")
    else:
        form = TeamForm()
    return render(request, "teams/team_form.html", {"form": form, "title": "Add Team"})


@login_required
@user_passes_test(is_leader_or_staff)
def team_edit(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if not user_can_manage_team(request.user, team):
        return redirect("teams:list")
    if request.method == "POST":
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect("teams:list")
    else:
        form = TeamForm(instance=team)
    return render(request, "teams/team_form.html", {"form": form, "title": "Edit Team"})


@login_required
@user_passes_test(is_leader_or_staff)
def team_roster(request, pk):
    team = get_object_or_404(
        Team.objects.prefetch_related(
            Prefetch(
                "memberships",
                queryset=TeamMembership.objects.select_related(
                    "volunteer__user"
                ).filter(is_active=True),
            ),
            "roles__required_skills",
            "roles__required_certifications",
        ),
        pk=pk,
    )
    if not user_can_manage_team(request.user, team):
        return redirect("teams:list")

    if request.method == "POST" and request.htmx:
        action = request.POST.get("action")
        volunteer_id = request.POST.get("volunteer_id")
        if action == "add" and volunteer_id:
            volunteer = get_object_or_404(VolunteerProfile, pk=volunteer_id)
            TeamMembership.objects.get_or_create(team=team, volunteer=volunteer)
        elif action == "remove" and volunteer_id:
            TeamMembership.objects.filter(team=team, volunteer_id=volunteer_id).delete()
        memberships = team.memberships.filter(is_active=True)
        return render(
            request,
            "teams/partials/roster_table.html",
            {"team": team, "memberships": memberships},
        )

    available = VolunteerProfile.objects.exclude(
        pk__in=team.memberships.filter(is_active=True).values_list("volunteer_id", flat=True)
    ).select_related("user")
    return render(
        request,
        "teams/team_roster.html",
        {
            "team": team,
            "memberships": team.memberships.filter(is_active=True),
            "available_volunteers": available,
        },
    )


@login_required
@user_passes_test(is_leader_or_staff)
def team_role_create(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    if not user_can_manage_team(request.user, team):
        return redirect("teams:list")
    if request.method == "POST":
        form = TeamRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.team = team
            role.save()
            form.save_m2m()
            return redirect("teams:roster", pk=team.pk)
    else:
        form = TeamRoleForm()
    return render(
        request,
        "teams/team_role_form.html",
        {"form": form, "team": team, "title": "Add Role"},
    )
