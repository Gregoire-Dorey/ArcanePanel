from django.contrib import admin
from .models import Asset, Check, CheckResult, Alert, Job, JobLog


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "asset_type", "ip_or_host", "tags", "is_enabled", "created_at")
    search_fields = ("name", "ip_or_host", "tags")
    list_filter = ("asset_type", "is_enabled")


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ("name", "asset", "kind", "interval_seconds", "is_enabled", "last_run_at")
    search_fields = ("name", "asset__name", "kind")
    list_filter = ("kind", "is_enabled")


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ("monitor_check", "ok", "latency_ms", "recorded_at")
    list_filter = ("ok", "recorded_at")
    search_fields = ("monitor_check__name", "monitor_check__asset__name")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "monitor_check", "severity", "is_open", "opened_at", "closed_at", "ack_by")
    list_filter = ("severity", "is_open")
    search_fields = ("title", "monitor_check__name", "monitor_check__asset__name")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("name", "action", "asset", "status", "created_at", "started_at", "finished_at")
    list_filter = ("status",)
    search_fields = ("name", "action", "asset__name")


@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ("job", "created_at")
    search_fields = ("job__name", "line")
