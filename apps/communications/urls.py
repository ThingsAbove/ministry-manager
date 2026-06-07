from django.urls import path

from . import views

app_name = "communications"

urlpatterns = [
    path("rsvp/<str:token>/accept/", views.rsvp_accept, name="rsvp_accept"),
    path("rsvp/<str:token>/decline/", views.rsvp_decline, name="rsvp_decline"),
    path("mass-message/", views.mass_message, name="mass_message"),
]
