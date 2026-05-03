from django.urls import path

from . import views

app_name = "aa_dscan_share"

urlpatterns = [
    path("", views.submit_dscan, name="submit"),
    path("systems/search/", views.system_search, name="system_search"),
    path("systems/<int:solar_system_id>/structures/", views.structure_data, name="structure_data"),
    path("systems/<int:solar_system_id>/", views.system_timeline, name="system_timeline"),
    path("<uuid:public_id>/", views.view_dscan, name="view"),
]
