from django.contrib import admin

from .models import Assignment, BlockOutDate


@admin.register(BlockOutDate)
class BlockOutDateAdmin(admin.ModelAdmin):
    list_display = ["volunteer", "date", "reason"]
    list_filter = ["date"]
    date_hierarchy = "date"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["service_occurrence", "team_role", "volunteer", "status"]
    list_filter = ["status", "service_occurrence__date", "team_role__team"]
    date_hierarchy = "service_occurrence__date"
    raw_id_fields = ["volunteer"]
