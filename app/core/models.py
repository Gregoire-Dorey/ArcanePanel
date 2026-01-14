from django.db import models
from django.utils import timezone

class Asset(models.Model):
    TYPE_CHOICES = [
        ("vm", "VM"),
        ("server", "Serveur"),
        ("nas", "NAS/Storage"),
        ("network", "Réseau"),
        ("other", "Autre"),
    ]
    name = models.CharField(max_length=120, unique=True)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="server")
    ip_or_host = models.CharField(max_length=255, help_text="IP ou hostname")
    tags = models.CharField(max_length=255, blank=True, help_text="Ex: prod,pve,pbs,site-a")
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __str__(self):
        return f"{self.name} ({self.ip_or_host})"


class Check(models.Model):
    KIND_CHOICES = [
        ("ping", "Ping (ICMP)"),
        ("tcp_port", "TCP Port"),
        ("http", "HTTP/HTTPS"),
        ("ssl_expiry", "SSL Expiry"),
    ]
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="checks")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    interval_seconds = models.PositiveIntegerField(default=60)

    # params génériques (selon kind)
    target = models.CharField(max_length=255, blank=True, help_text="Ex: https://site.tld ou hostname")
    port = models.PositiveIntegerField(null=True, blank=True)
    timeout_seconds = models.PositiveIntegerField(default=3)
    expected_status = models.PositiveIntegerField(default=200)
    ssl_days_threshold = models.PositiveIntegerField(default=14)

    is_enabled = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.asset.name} - {self.name} ({self.kind})"


class CheckResult(models.Model):
    check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="results")
    ok = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    latency_ms = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["recorded_at"]),
            models.Index(fields=["check", "recorded_at"]),
        ]


class Alert(models.Model):
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="alerts")
    is_open = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="critical")
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True)

    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    ack_by = models.CharField(max_length=150, blank=True)
    ack_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{'OPEN' if self.is_open else 'CLOSED'}] {self.title}"


class Job(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="jobs", null=True, blank=True)
    name = models.CharField(max_length=150)
    action = models.CharField(max_length=150, help_text="Ex: restart_service, proxmox_stop_vm, etc.")
    payload_json = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

class JobLog(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="logs")
    line = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
