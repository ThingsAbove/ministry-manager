from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("", views.team_list, name="list"),
    path("new/", views.team_create, name="create"),
    path("<int:pk>/edit/", views.team_edit, name="edit"),
    path("<int:pk>/roster/", views.team_roster, name="roster"),
    path("<int:team_pk>/roles/new/", views.team_role_create, name="role_create"),
]
