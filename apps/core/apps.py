from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "Ministry Manager"
        admin.site.site_title = "Ministry Manager"
        admin.site.index_title = "Administration"
