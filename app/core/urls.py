from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("assets/", views.assets, name="assets"),
    path("assets/new/", views.asset_create, name="asset_create"),
    path("checks/", views.checks, name="checks"),
    path("alerts/", views.alerts, name="alerts"),
]
