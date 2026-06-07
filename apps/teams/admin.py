from django.contrib import admin

from .models import (
    Certification,
    Skill,
    Team,
    TeamMembership,
    TeamRole,
    VolunteerCertification,
    VolunteerSkill,
)


class TeamRoleInline(admin.TabularInline):
    model = TeamRole
    extra = 0
    filter_horizontal = ["required_skills", "required_certifications"]


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "campus", "is_active"]
    list_filter = ["campus", "is_active"]
    filter_horizontal = ["leaders"]
    inlines = [TeamRoleInline, TeamMembershipInline]


@admin.register(TeamRole)
class TeamRoleAdmin(admin.ModelAdmin):
    list_display = ["name", "team", "slots_per_service"]
    list_filter = ["team"]
    filter_horizontal = ["required_skills", "required_certifications"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(VolunteerSkill)
class VolunteerSkillAdmin(admin.ModelAdmin):
    list_display = ["volunteer", "skill"]


@admin.register(VolunteerCertification)
class VolunteerCertificationAdmin(admin.ModelAdmin):
    list_display = ["volunteer", "certification", "issued_at", "expires_at"]
