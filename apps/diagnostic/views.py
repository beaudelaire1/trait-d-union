"""Vues du diagnostic de site — outil interne staff uniquement."""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .service import run_diagnostic
from .models import SiteDiagnostic
from apps.audit.models import AuditLog


@staff_member_required
def diagnostic_list(request):
    """Historique des diagnostics."""
    diagnostics = SiteDiagnostic.objects.select_related("created_by").all()[:50]
    return render(request, "diagnostic/diagnostic_list.html", {"diagnostics": diagnostics})


@staff_member_required
def diagnostic_new(request):
    """Formulaire + lancement d'un nouveau diagnostic."""
    if request.method == "POST":
        url = request.POST.get("url", "").strip()
        if not url:
            return render(request, "diagnostic/diagnostic_new.html", {"error": "URL requise."})

        diag = SiteDiagnostic.objects.create(
            url=url,
            created_by=request.user,
            status=SiteDiagnostic.Status.RUNNING,
        )

        try:
            results = run_diagnostic(url)
            diag.status = SiteDiagnostic.Status.COMPLETED
            diag.overall_score = results.get("overall_score", 0)
            diag.results = results
            diag.duration_seconds = results.get("duration", 0)
        except Exception as exc:
            diag.status = SiteDiagnostic.Status.FAILED
            diag.error_message = str(exc)
        diag.save()

        AuditLog.log_action(
            action_type="admin_action",
            actor=request.user,
            content_type="diagnostic.SiteDiagnostic",
            object_id=diag.pk,
            description=f"Diagnostic lancé pour {url} → score {diag.overall_score}/100",
            metadata={"url": url, "score": diag.overall_score},
        )

        return redirect("diagnostic:diagnostic_detail", pk=diag.pk)

    return render(request, "diagnostic/diagnostic_new.html")


@staff_member_required
def diagnostic_detail(request, pk):
    """Résultats détaillés d'un diagnostic."""
    diag = get_object_or_404(SiteDiagnostic, pk=pk)
    return render(request, "diagnostic/diagnostic_detail.html", {"diag": diag})


@staff_member_required
@require_POST
def diagnostic_rerun(request, pk):
    """Relancer un diagnostic existant avec la même URL."""
    old = get_object_or_404(SiteDiagnostic, pk=pk)
    diag = SiteDiagnostic.objects.create(
        url=old.url,
        created_by=request.user,
        status=SiteDiagnostic.Status.RUNNING,
    )
    try:
        results = run_diagnostic(old.url)
        diag.status = SiteDiagnostic.Status.COMPLETED
        diag.overall_score = results.get("overall_score", 0)
        diag.results = results
        diag.duration_seconds = results.get("duration", 0)
    except Exception as exc:
        diag.status = SiteDiagnostic.Status.FAILED
        diag.error_message = str(exc)
    diag.save()
    return redirect("diagnostic:diagnostic_detail", pk=diag.pk)


@staff_member_required
def diagnostic_api_json(request, pk):
    """Export JSON brut d'un diagnostic (pour intégration API)."""
    diag = get_object_or_404(SiteDiagnostic, pk=pk)
    return JsonResponse({
        "id": diag.pk,
        "url": diag.url,
        "score": diag.overall_score,
        "status": diag.status,
        "created_at": diag.created_at.isoformat(),
        "results": diag.results,
    })
