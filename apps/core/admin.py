from django.contrib import admin

from .models import ChurchSettings


@admin.register(ChurchSettings)
class ChurchSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ChurchSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
