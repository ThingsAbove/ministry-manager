from django.contrib import admin

from .models import RSVP, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["notification_type", "channel", "status", "recipient", "created_at"]
    list_filter = ["notification_type", "channel", "status"]
    readonly_fields = ["created_at", "sent_at"]


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ["assignment", "status", "responded_at"]
