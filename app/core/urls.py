from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("assets/", views.assets, name="assets"),
    path("assets/new/", views.asset_create, name="asset_create"),
    path("assets/<int:asset_id>/", views.asset_detail, name="asset_detail"),

    path("checks/", views.checks, name="checks"),
    path("alerts/", views.alerts, name="alerts"),

    # API metrics (global)
    path("api/metrics/latency-24h/", views.metrics_latency_series_24h, name="metrics_latency_24h"),
    path("api/metrics/uptime-24h/", views.metrics_uptime_series_24h, name="metrics_uptime_24h"),

    # API metrics (par asset)
    path("api/assets/<int:asset_id>/latency-7d/", views.metrics_asset_latency_7d, name="metrics_asset_latency_7d"),
    path("api/assets/<int:asset_id>/uptime-7d/", views.metrics_asset_uptime_7d, name="metrics_asset_uptime_7d"),
]
