from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, VolunteerProfile


class VolunteerProfileInline(admin.StackedInline):
    model = VolunteerProfile
    can_delete = False
    filter_horizontal = ["preferred_service_times"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [VolunteerProfileInline]
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_test_user",
    ]
    list_filter = BaseUserAdmin.list_filter + ("is_test_user",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Contact", {"fields": ("phone",)}),
        ("Demo", {"fields": ("is_test_user",)}),
    )


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "serving_frequency", "email_opt_in", "sms_opt_in"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email"]
    filter_horizontal = ["preferred_service_times"]
