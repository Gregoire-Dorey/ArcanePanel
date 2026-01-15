from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Asset, Check, Alert, CheckResult


def _bucket_time(dt, minutes=10):
    return dt.replace(minute=(dt.minute // minutes) * minutes, second=0, microsecond=0)


@login_required
def dashboard(request):
    now = timezone.now()
    since_24h = now - timedelta(hours=24)
    since_1h = now - timedelta(hours=1)

    assets_total = Asset.objects.count()
    checks_total = Check.objects.count()
    alerts_open = Alert.objects.filter(is_open=True).count()

    latest_alerts = (
        Alert.objects.select_related("monitor_check", "monitor_check__asset")
        .order_by("-opened_at")[:10]
    )

    # Uptime 24h (tous checks)
    total_results_24h = CheckResult.objects.filter(recorded_at__gte=since_24h).count()
    ok_results_24h = CheckResult.objects.filter(recorded_at__gte=since_24h, ok=True).count()
    uptime_24h = (ok_results_24h / total_results_24h * 100.0) if total_results_24h else 100.0

    # Latence moyenne 24h
    avg_latency_24h = (
        CheckResult.objects.filter(recorded_at__gte=since_24h, latency_ms__isnull=False)
        .aggregate(v=Avg("latency_ms"))["v"]
    ) or 0.0

    # Checks failing (dernière heure): top checks avec le + de fails
    failing_checks_1h = (
        CheckResult.objects.filter(recorded_at__gte=since_1h, ok=False)
        .values("monitor_check__asset__name", "monitor_check__name")
        .annotate(fails=Count("id"))
        .order_by("-fails")[:8]
    )

    # Top assets en alerte (open)
    top_alert_assets = (
        Alert.objects.filter(is_open=True)
        .values("monitor_check__asset__name")
        .annotate(c=Count("id"))
        .order_by("-c")[:5]
    )

    return render(
        request,
        "core/dashboard_v2_1.html",
        {
            "now": now,
            "assets_total": assets_total,
            "checks_total": checks_total,
            "alerts_open": alerts_open,
            "latest_alerts": latest_alerts,
            "uptime_24h": round(uptime_24h, 2),
            "avg_latency_24h": round(avg_latency_24h, 1),
            "total_results_24h": total_results_24h,
            "failing_checks_1h": failing_checks_1h,
            "top_alert_assets": top_alert_assets,
        },
    )


@login_required
def assets(request):
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip().lower()

    qs = Asset.objects.all().order_by("name")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))
    if tag:
        # filtre naïf mais efficace: match substring
        qs = qs.filter(tags__icontains=tag)

    assets_list = list(qs)

    # stats rapides par asset (open alerts + checks)
    asset_ids = [a.id for a in assets_list]
    open_alerts_map = {
        row["monitor_check__asset"]: row["c"]
        for row in Alert.objects.filter(is_open=True, monitor_check__asset_id__in=asset_ids)
        .values("monitor_check__asset")
        .annotate(c=Count("id"))
    }
    checks_map = {
        row["asset"]: row["c"]
        for row in Check.objects.filter(asset_id__in=asset_ids)
        .values("asset")
        .annotate(c=Count("id"))
    }

    # tags “top” (facilite le filtrage)
    all_tags = []
    for a in Asset.objects.all().only("tags"):
        all_tags.extend(a.tag_list())
    tag_cloud = sorted(list(set([t.lower() for t in all_tags])))[:30]

    # enrichit les assets sans casser tes modèles
    enriched = []
    for a in assets_list:
        enriched.append({
            "obj": a,
            "checks": checks_map.get(a.id, 0),
            "open_alerts": open_alerts_map.get(a.id, 0),
            "tags": a.tag_list(),
        })

    return render(
        request,
        "core/assets_v2_1.html",
        {
            "now": timezone.now(),
            "assets": enriched,
            "q": q,
            "tag": tag,
            "tag_cloud": tag_cloud,
        },
    )


@login_required
def asset_detail(request, asset_id: int):
    asset = get_object_or_404(Asset, id=asset_id)
    now = timezone.now()
    since_7d = now - timedelta(days=7)

    checks = list(asset.checks.all().order_by("name"))

    # Uptime 7j pour l’asset
    total = CheckResult.objects.filter(monitor_check__asset=asset, recorded_at__gte=since_7d).count()
    ok = CheckResult.objects.filter(monitor_check__asset=asset, recorded_at__gte=since_7d, ok=True).count()
    uptime_7d = (ok / total * 100.0) if total else 100.0

    # Latence moyenne 7j
    avg_latency_7d = (
        CheckResult.objects.filter(monitor_check__asset=asset, recorded_at__gte=since_7d, latency_ms__isnull=False)
        .aggregate(v=Avg("latency_ms"))["v"]
    ) or 0.0

    open_alerts = (
        Alert.objects.filter(is_open=True, monitor_check__asset=asset)
        .select_related("monitor_check")
        .order_by("-opened_at")[:20]
    )

    last_results = (
        CheckResult.objects.filter(monitor_check__asset=asset)
        .select_related("monitor_check")
        .order_by("-recorded_at")[:30]
    )

    return render(
        request,
        "core/asset_detail_v2_1.html",
        {
            "now": now,
            "asset": asset,
            "checks": checks,
            "uptime_7d": round(uptime_7d, 2),
            "avg_latency_7d": round(avg_latency_7d, 1),
            "open_alerts": open_alerts,
            "last_results": last_results,
        },
    )


# --- placeholder views (si tu as déjà des versions, garde les tiennes et adapte juste les templates)
@login_required
def checks(request):
    # garde ta logique actuelle si tu l’as
    checks_list = Check.objects.select_related("asset").order_by("asset__name", "name")
    return render(request, "core/checks.html", {"checks": checks_list, "now": timezone.now()})


@login_required
def alerts(request):
    alerts_list = Alert.objects.select_related("monitor_check", "monitor_check__asset").order_by("-opened_at")[:200]
    return render(request, "core/alerts.html", {"alerts": alerts_list, "now": timezone.now()})


@login_required
def asset_create(request):
    # garde ton form actuel si tu en as un
    return redirect("/assets/")


# ------------------ API METRICS ------------------

@login_required
def metrics_latency_series_24h(request):
    now = timezone.now()
    since = now - timedelta(hours=24)

    qs = (
        CheckResult.objects.filter(recorded_at__gte=since, latency_ms__isnull=False)
        .order_by("recorded_at")
        .values("recorded_at", "latency_ms")
    )

    bucket = {}
    for row in qs:
        t = _bucket_time(row["recorded_at"], minutes=10)
        bucket.setdefault(t, []).append(float(row["latency_ms"]))

    labels, values = [], []
    for t in sorted(bucket.keys()):
        labels.append(t.strftime("%H:%M"))
        values.append(sum(bucket[t]) / len(bucket[t]))

    return JsonResponse({"labels": labels, "values": values})


@login_required
def metrics_uptime_series_24h(request):
    now = timezone.now()
    since = now - timedelta(hours=24)

    qs = CheckResult.objects.filter(recorded_at__gte=since).values("recorded_at", "ok").order_by("recorded_at")

    bucket_ok = {}
    bucket_total = {}

    for row in qs:
        t = row["recorded_at"].replace(minute=0, second=0, microsecond=0)
        bucket_total[t] = bucket_total.get(t, 0) + 1
        if row["ok"]:
            bucket_ok[t] = bucket_ok.get(t, 0) + 1

    labels, values = [], []
    for t in sorted(bucket_total.keys()):
        total = bucket_total[t]
        ok = bucket_ok.get(t, 0)
        pct = (ok / total * 100.0) if total else 100.0
        labels.append(t.strftime("%H:%M"))
        values.append(round(pct, 2))

    return JsonResponse({"labels": labels, "values": values})


@login_required
def metrics_asset_latency_7d(request, asset_id: int):
    asset = get_object_or_404(Asset, id=asset_id)
    now = timezone.now()
    since = now - timedelta(days=7)

    qs = (
        CheckResult.objects.filter(monitor_check__asset=asset, recorded_at__gte=since, latency_ms__isnull=False)
        .order_by("recorded_at")
        .values("recorded_at", "latency_ms")
    )

    bucket = {}
    for row in qs:
        # bucket 1h sur 7j
        t = row["recorded_at"].replace(minute=0, second=0, microsecond=0)
        bucket.setdefault(t, []).append(float(row["latency_ms"]))

    labels, values = [], []
    for t in sorted(bucket.keys()):
        labels.append(t.strftime("%d/%m %Hh"))
        values.append(sum(bucket[t]) / len(bucket[t]))

    return JsonResponse({"labels": labels, "values": values, "asset": asset.name})


@login_required
def metrics_asset_uptime_7d(request, asset_id: int):
    asset = get_object_or_404(Asset, id=asset_id)
    now = timezone.now()
    since = now - timedelta(days=7)

    qs = (
        CheckResult.objects.filter(monitor_check__asset=asset, recorded_at__gte=since)
        .values("recorded_at", "ok")
        .order_by("recorded_at")
    )

    bucket_ok = {}
    bucket_total = {}

    for row in qs:
        t = row["recorded_at"].replace(minute=0, second=0, microsecond=0)
        bucket_total[t] = bucket_total.get(t, 0) + 1
        if row["ok"]:
            bucket_ok[t] = bucket_ok.get(t, 0) + 1

    labels, values = [], []
    for t in sorted(bucket_total.keys()):
        total = bucket_total[t]
        ok = bucket_ok.get(t, 0)
        pct = (ok / total * 100.0) if total else 100.0
        labels.append(t.strftime("%d/%m %Hh"))
        values.append(round(pct, 2))

    return JsonResponse({"labels": labels, "values": values, "asset": asset.name})
