from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from .models import ChurchBranding, ChurchLogo, ChurchSettings

_CHURCH_SETTINGS_PERM = "core.change_churchsettings"


class ChurchSettingsSingletonAdmin(admin.ModelAdmin):
    """Redirect list view to the singleton change form."""

    def has_module_permission(self, request):
        return request.user.has_perm(_CHURCH_SETTINGS_PERM)

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm(_CHURCH_SETTINGS_PERM)

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm(_CHURCH_SETTINGS_PERM)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        return HttpResponseRedirect(
            reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[1])
        )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        ChurchSettings.load()
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(ChurchSettings)
class ChurchSettingsAdmin(ChurchSettingsSingletonAdmin):
    fieldsets = (
        (
            "Church",
            {"fields": ("name",)},
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


@admin.register(ChurchLogo)
class ChurchLogoAdmin(ChurchSettingsSingletonAdmin):
    change_form_template = "admin/core/churchlogo/change_form.html"
    fieldsets = (
        (
            "Logo",
            {
                "fields": ("logo", "logo_preview"),
                "description": (
                    "Upload a logo for the app sidebar and admin header. "
                    "Leave blank to use the default. Changes preview live below."
                ),
            },
        ),
    )
    readonly_fields = ("logo_preview",)

    @admin.display(description="Current logo")
    def logo_preview(self, obj):
        return format_html(
            '<img src="{}" alt="" class="mm-admin-logo-preview-thumb" data-logo-preview />',
            obj.logo_url,
        )


@admin.register(ChurchBranding)
class ChurchBrandingAdmin(ChurchSettingsSingletonAdmin):
    change_form_template = "admin/core/churchbranding/change_form.html"
    fieldsets = (
        (
            "Branding CSS",
            {
                "fields": ("branding_css",),
                "description": (
                    "Custom CSS applied to the main app and admin. Use CSS variables such as "
                    "<code>--mm-brand</code> or target classes like "
                    "<code>.mm-sidebar</code> and <code>.btn-primary</code>. "
                    "The preview below updates as you type."
                ),
            },
        ),
    )
