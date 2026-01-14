from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Asset, Check, Alert

@login_required
def dashboard(request):
    assets_total = Asset.objects.count()
    checks_total = Check.objects.count()
    alerts_open = Alert.objects.filter(is_open=True).count()
    latest_alerts = Alert.objects.select_related("check", "check__asset").order_by("-opened_at")[:10]

    return render(request, "core/dashboard.html", {
        "assets_total": assets_total,
        "checks_total": checks_total,
        "alerts_open": alerts_open,
        "latest_alerts": latest_alerts,
        "now": timezone.now(),
    })

@login_required
def assets(request):
    items = Asset.objects.order_by("name")
    return render(request, "core/assets.html", {"items": items})

@login_required
def asset_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        asset_type = request.POST.get("asset_type", "server")
        ip_or_host = request.POST.get("ip_or_host", "").strip()
        tags = request.POST.get("tags", "").strip()
        if name and ip_or_host:
            Asset.objects.create(name=name, asset_type=asset_type, ip_or_host=ip_or_host, tags=tags)
            return redirect("assets")
    return render(request, "core/asset_create.html")

@login_required
def checks(request):
    items = Check.objects.select_related("asset").order_by("asset__name", "name")
    return render(request, "core/checks.html", {"items": items})

@login_required
def alerts(request):
    items = Alert.objects.select_related("check", "check__asset").order_by("-opened_at")[:200]
    return render(request, "core/alerts.html", {"items": items})
