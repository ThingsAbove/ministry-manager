from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("my-schedule/", views.my_schedule, name="my_schedule"),
    path("block-outs/", views.block_out_calendar, name="block_outs"),
    path("rota/", views.rota_grid, name="rota"),
    path("auto-schedule/", views.auto_schedule_view, name="auto_schedule"),
]
