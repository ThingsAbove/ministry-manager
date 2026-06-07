from django.urls import path

from . import views

app_name = "campuses"

urlpatterns = [
    path("", views.campus_list, name="list"),
    path("new/", views.campus_create, name="create"),
    path("<int:pk>/edit/", views.campus_edit, name="edit"),
    path("service-times/new/", views.service_time_create, name="service_time_create"),
    path("service-times/<int:pk>/edit/", views.service_time_edit, name="service_time_edit"),
]
