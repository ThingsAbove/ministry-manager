from django.contrib import admin

from .models import Campus, ServiceOccurrence, ServiceTime


class ServiceTimeInline(admin.TabularInline):
    model = ServiceTime
    extra = 0


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    inlines = [ServiceTimeInline]


@admin.register(ServiceTime)
class ServiceTimeAdmin(admin.ModelAdmin):
    list_display = ["name", "campus", "weekday", "start_time", "is_active"]
    list_filter = ["campus", "weekday", "is_active"]


@admin.register(ServiceOccurrence)
class ServiceOccurrenceAdmin(admin.ModelAdmin):
    list_display = ["service_time", "date", "start_time"]
    list_filter = ["date", "service_time__campus"]
    date_hierarchy = "date"
