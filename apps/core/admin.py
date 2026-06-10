from django.contrib import admin
from django.utils.html import format_html

from .models import ChurchSettings


@admin.register(ChurchSettings)
class ChurchSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Church",
            {
                "fields": ("name", "logo", "logo_preview"),
            },
        ),
        (
            "Branding",
            {
                "fields": ("branding_css",),
                "description": (
                    "Custom CSS applied to the main app. Use CSS variables such as "
                    "<code>--mm-brand</code> or target classes like "
                    "<code>.mm-sidebar</code> and <code>.btn-primary</code>."
                ),
            },
        ),
        (
            "Scheduling",
            {
                "fields": (
                    "timezone",
                    "reminder_days_before",
                    "default_serving_frequency_weeks",
                ),
            },
        ),
    )
    readonly_fields = ("logo_preview",)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return format_html(
            '<img src="{}" alt="" style="max-height: 80px; max-width: 200px;" />',
            obj.logo_url,
        )

    def has_add_permission(self, request):
        return not ChurchSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
