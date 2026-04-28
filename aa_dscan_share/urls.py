from django.urls import path

from . import views

app_name = "aa_dscan_share"

urlpatterns = [
    path("", views.submit_dscan, name="submit"),
    path("systems/<int:solar_system_id>/", views.system_timeline, name="system_timeline"),
    path("<uuid:public_id>/", views.view_dscan, name="view"),
]
