import socket
import ssl
import subprocess
import time
from datetime import datetime, timezone as dt_timezone

import requests
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import Check, CheckResult, Alert

def _tcp_check(host: str, port: int, timeout: int):
    t0 = time.time()
    with socket.create_connection((host, port), timeout=timeout):
        pass
    return (time.time() - t0) * 1000.0

def _ping_check(host: str, timeout: int):
    # ping binaire Debian souvent setuid -> OK sans capabilities custom
    t0 = time.time()
    proc = subprocess.run(["ping", "-c", "1", "-W", str(timeout), host], capture_output=True, text=True)
    ms = (time.time() - t0) * 1000.0
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Ping failed")
    return ms

def _http_check(url: str, timeout: int, expected_status: int):
    t0 = time.time()
    r = requests.get(url, timeout=timeout, allow_redirects=True)
    ms = (time.time() - t0) * 1000.0
    if r.status_code != expected_status:
        raise RuntimeError(f"HTTP {r.status_code} (expected {expected_status})")
    return ms

def _ssl_expiry_check(host: str, port: int, timeout: int, days_threshold: int):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    # notAfter ex: 'Jun 15 12:00:00 2027 GMT'
    not_after = cert.get("notAfter")
    if not not_after:
        raise RuntimeError("No notAfter in certificate")
    exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=dt_timezone.utc)
    remaining_days = (exp - datetime.now(dt_timezone.utc)).days
    if remaining_days < days_threshold:
        raise RuntimeError(f"SSL expires in {remaining_days} days (threshold {days_threshold})")
    return remaining_days

def _open_or_update_alert(check: Check, severity: str, title: str, details: str):
    alert = Alert.objects.filter(check=check, is_open=True).first()
    if alert:
        alert.severity = severity
        alert.title = title
        alert.details = details
        alert.save(update_fields=["severity", "title", "details"])
        return alert, False
    return Alert.objects.create(check=check, is_open=True, severity=severity, title=title, details=details), True

def _resolve_alerts(check: Check):
    qs = Alert.objects.filter(check=check, is_open=True)
    now = timezone.now()
    qs.update(is_open=False, closed_at=now)

def _maybe_email(subject: str, body: str):
    try:
        send_mail(subject, body, None, [], fail_silently=True)
    except Exception:
        # ignore hard errors in v1
        pass

@shared_task
def run_check(check_id: int):
    check = Check.objects.select_related("asset").get(id=check_id)
    if not check.is_enabled or not check.asset.is_enabled:
        return

    host = check.target.strip() or check.asset.ip_or_host.strip()

    ok = False
    message = ""
    latency_ms = None

    try:
        if check.kind == "ping":
            latency_ms = _ping_check(host, check.timeout_seconds)
            ok = True
            message = "Ping OK"

        elif check.kind == "tcp_port":
            if not check.port:
                raise RuntimeError("Missing port")
            latency_ms = _tcp_check(host, int(check.port), check.timeout_seconds)
            ok = True
            message = f"TCP {check.port} OK"

        elif check.kind == "http":
            url = host
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "http://" + url
            latency_ms = _http_check(url, check.timeout_seconds, check.expected_status)
            ok = True
            message = "HTTP OK"

        elif check.kind == "ssl_expiry":
            p = int(check.port or 443)
            remaining_days = _ssl_expiry_check(host, p, check.timeout_seconds, check.ssl_days_threshold)
            ok = True
            message = f"SSL OK (expires in {remaining_days} days)"

        else:
            raise RuntimeError(f"Unknown kind: {check.kind}")

    except Exception as e:
        ok = False
        message = str(e)[:2000]

    CheckResult.objects.create(check=check, ok=ok, message=message, latency_ms=latency_ms)
    Check.objects.filter(id=check.id).update(last_run_at=timezone.now())

    if ok:
        _resolve_alerts(check)
    else:
        title = f"{check.asset.name}: {check.name} FAILED"
        details = f"Asset: {check.asset.name}\nHost: {host}\nKind: {check.kind}\nMessage: {message}"
        alert, created = _open_or_update_alert(check, "critical", title, details)
        if created:
            _maybe_email(f"[ArcanePanel] {title}", details)

@shared_task
def run_all_checks():
    now = timezone.now()
    checks = Check.objects.select_related("asset").filter(is_enabled=True, asset__is_enabled=True)

    for c in checks:
        # Respect interval
        if c.last_run_at and (now - c.last_run_at).total_seconds() < c.interval_seconds:
            continue
        run_check.delay(c.id)
