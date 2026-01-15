from django.db import models
from django.utils import timezone


class Asset(models.Model):
    name = models.CharField(max_length=120, unique=True)
    address = models.CharField(max_length=255, blank=True)  # ip/host/url
    description = models.TextField(blank=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Tags séparés par des virgules (ex: prod, web, paris)",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def tag_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    def __str__(self):
        return self.name


class Check(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="checks")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=32, default="ping")  # ping/http/tcp/etc
    target = models.CharField(max_length=255, blank=True)
    interval_seconds = models.PositiveIntegerField(default=60)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("asset", "name")

    def __str__(self):
        return f"{self.asset.name} / {self.name}"


class CheckResult(models.Model):
    monitor_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="results")
    ok = models.BooleanField(default=False)
    status_code = models.IntegerField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["recorded_at"]),
            models.Index(fields=["monitor_check", "recorded_at"]),
            models.Index(fields=["monitor_check", "ok", "recorded_at"]),
        ]

    def __str__(self):
        return f"{self.monitor_check} ok={self.ok} @ {self.recorded_at}"


class Alert(models.Model):
    monitor_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="alerts")
    is_open = models.BooleanField(default=True)
    severity = models.CharField(max_length=16, default="warning")  # info/warning/critical
    title = models.CharField(max_length=160, blank=True)
    details = models.TextField(blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_open", "opened_at"]),
            models.Index(fields=["monitor_check", "is_open"]),
        ]

    def __str__(self):
        st = "OPEN" if self.is_open else "CLOSED"
        return f"[{st}] {self.monitor_check} ({self.severity})"


class MetricSample(models.Model):
    """
    Time-series générique (V2.1). Utile si tu ajoutes agent/proxmox/pbs plus tard.
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="metrics", null=True, blank=True)
    key = models.CharField(max_length=64)  # ex: cpu_percent, ram_percent, disk_percent
    value = models.FloatField()
    unit = models.CharField(max_length=24, blank=True)  # ex: "%", "ms"
    labels = models.CharField(max_length=255, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["key", "recorded_at"]),
            models.Index(fields=["asset", "key", "recorded_at"]),
        ]

    def __str__(self):
        return f"{self.key}={self.value}{self.unit}"
