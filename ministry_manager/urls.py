from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("campuses/", include("apps.campuses.urls")),
    path("teams/", include("apps.teams.urls")),
    path("scheduling/", include("apps.scheduling.urls")),
    path("communications/", include("apps.communications.urls")),
]
