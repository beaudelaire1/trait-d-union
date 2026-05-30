"""Vues du diagnostic — outil interne staff uniquement.

Deux familles de diagnostic :
  • Numérique : analyse automatique d'une URL (SiteDiagnostic).
  • Terrain : entretien client structuré et scoré (FieldDiagnostic).
"""
import math

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from .service import run_diagnostic
from .models import SiteDiagnostic, FieldDiagnostic
from .field_questions import (
    PROFILES, SECTORS, sections_for_profile, questions_for_profile,
)
from .field_scoring import analyze
from apps.audit.models import AuditLog


def _gauge(score, radius=64):
    """Géométrie d'un cercle de progression SVG fiable.

    Utilise la technique ``stroke-dashoffset`` : le tracé occupe toute la
    circonférence (``dasharray``) et l'``offset`` masque la part non atteinte.
    """
    score = max(0, min(100, int(score or 0)))
    circ = 2 * math.pi * radius
    return {
        "r": radius,
        "circ": round(circ, 1),
        "offset": round(circ * (1 - score / 100), 1),
        "score": score,
    }


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


# ══════════════════════════════════════════════════════════════════════
#  DIAGNOSTIC TERRAIN — entretien client structuré et scoré
# ══════════════════════════════════════════════════════════════════════

@staff_member_required
def diagnostic_home(request):
    """Page de choix : diagnostic Numérique (URL) ou Terrain (entretien)."""
    return render(request, "diagnostic/diagnostic_home.html")


@staff_member_required
def field_list(request):
    """Historique des diagnostics terrain."""
    diagnostics = FieldDiagnostic.objects.select_related("created_by").all()[:50]
    return render(request, "diagnostic/field_list.html", {
        "diagnostics": diagnostics,
        "profiles": PROFILES,
    })


@staff_member_required
def field_new(request):
    """Étape 1 — Choix du profil d'entreprise et identité du client.

    Le profil sélectionné oriente le questionnaire de l'étape suivante.
    """
    if request.method == "POST":
        profile = request.POST.get("profile", "")
        company = request.POST.get("company_name", "").strip()
        if profile not in PROFILES or not company:
            return render(request, "diagnostic/field_new.html", {
                "profiles": PROFILES, "sectors": SECTORS,
                "error": "Le nom de l'entreprise et le profil sont requis.",
                "posted": request.POST,
            })
        diag = FieldDiagnostic.objects.create(
            company_name=company,
            sector=request.POST.get("sector", ""),
            profile=profile,
            contact_name=request.POST.get("contact_name", "").strip(),
            contact_email=request.POST.get("contact_email", "").strip(),
            created_by=request.user,
        )
        return redirect("diagnostic:field_form", pk=diag.pk)

    return render(request, "diagnostic/field_new.html", {
        "profiles": PROFILES, "sectors": SECTORS,
    })


@staff_member_required
def field_form(request, pk):
    """Étape 2 — Questionnaire orienté profil + secteur, scoring à la soumission."""
    diag = get_object_or_404(FieldDiagnostic, pk=pk)
    sections = sections_for_profile(diag.profile, diag.sector)

    if request.method == "POST":
        answers = {}
        for q in questions_for_profile(diag.profile, diag.sector):
            raw = request.POST.get(q.id, "").strip()
            if raw != "":
                answers[q.id] = raw
        diag.answers = answers
        diag.notes = request.POST.get("notes", "").strip()
        results = analyze(answers, diag.profile, sector=diag.sector or None)
        diag.results = results
        diag.overall_score = results["global_score"]
        diag.save()

        AuditLog.log_action(
            action_type="admin_action",
            actor=request.user,
            content_type="diagnostic.FieldDiagnostic",
            object_id=diag.pk,
            description=(
                f"Diagnostic terrain « {diag.company_name} » → "
                f"score {diag.overall_score}/100"
            ),
            metadata={"profile": diag.profile, "score": diag.overall_score},
        )
        return redirect("diagnostic:field_detail", pk=diag.pk)

    return render(request, "diagnostic/field_form.html", {
        "diag": diag,
        "sections": sections,
        "profile_meta": PROFILES.get(diag.profile, {}),
        "sector_label": dict(SECTORS).get(diag.sector, ""),
    })


@staff_member_required
def field_detail(request, pk):
    """Étape 3 — Tableau de bord des résultats du diagnostic terrain."""
    diag = get_object_or_404(FieldDiagnostic, pk=pk)
    return render(request, "diagnostic/field_detail.html", {
        "diag": diag,
        "r": diag.results,
        "profile_meta": PROFILES.get(diag.profile, {}),
        "gauge": _gauge(diag.overall_score),
    })


@staff_member_required
def field_pdf(request, pk):
    """Génère et télécharge le rapport PDF du diagnostic terrain."""
    diag = get_object_or_404(FieldDiagnostic, pk=pk)
    filename, pdf_bytes = _render_field_pdf(diag)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _render_field_pdf(diag):
    """Rend le rapport PDF d'un diagnostic terrain.

    Retourne ``(filename, pdf_bytes)`` afin d'être réutilisé aussi bien pour
    le téléchargement direct que pour l'envoi par email.
    """
    from core.services.document_generator import DocumentGenerator
    from django.template.loader import render_to_string
    from django.utils import timezone

    branding = DocumentGenerator.get_branding()
    html = render_to_string("diagnostic/field_pdf.html", {
        "diag": diag,
        "r": diag.results,
        "branding": branding,
        "profile_meta": PROFILES.get(diag.profile, {}),
        "generated_at": timezone.now(),
        "gauge": _gauge(diag.overall_score, radius=54),
    })
    pdf_bytes = DocumentGenerator._render_pdf(html)
    filename = f"diagnostic_terrain_{diag.company_name[:30]}.pdf".replace(" ", "_")
    return filename, pdf_bytes


@staff_member_required
@require_POST
def field_send_email(request, pk):
    """Envoie le rapport PDF du diagnostic terrain au contact du client."""
    from django.contrib import messages

    diag = get_object_or_404(FieldDiagnostic, pk=pk)
    back_url = request.POST.get("next") or reverse(
        "diagnostic:field_detail", args=[diag.pk]
    )
    ok, detail = send_field_report(diag, actor=request.user)
    (messages.success if ok else messages.error)(request, detail)
    return redirect(back_url)


def send_field_report(diag, actor=None):
    """Envoie par email le rapport PDF d'un diagnostic terrain au contact.

    Fonction réutilisable par la vue dédiée et par l'action d'administration.
    Retourne ``(ok: bool, detail: str)`` sans lever d'exception.
    """
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    if not diag.results:
        return False, (
            f"{diag.company_name} : diagnostic non complété, envoi impossible."
        )
    if not diag.contact_email:
        return False, (
            f"{diag.company_name} : aucune adresse email de contact."
        )

    filename, pdf_bytes = _render_field_pdf(diag)
    context = {
        "diag": diag,
        "site_url": getattr(settings, "SITE_URL", "https://traitdunion.it"),
    }
    html_body = render_to_string("emails/field_diagnostic_report.html", context)
    text_body = render_to_string("emails/field_diagnostic_report.txt", context)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "contact@traitdunion.it")

    msg = EmailMultiAlternatives(
        subject=f"Votre diagnostic d'entreprise — {diag.company_name}",
        body=text_body,
        from_email=from_email,
        to=[diag.contact_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.attach(filename, pdf_bytes, "application/pdf")

    try:
        msg.send(fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        return False, f"{diag.company_name} : échec de l'envoi ({exc})."

    AuditLog.log_action(
        action_type="admin_action",
        actor=actor,
        content_type="diagnostic.FieldDiagnostic",
        object_id=diag.pk,
        description=(
            f"Rapport diagnostic « {diag.company_name} » envoyé à "
            f"{diag.contact_email}"
        ),
        metadata={"email": diag.contact_email, "score": diag.overall_score},
    )
    return True, f"Rapport envoyé à {diag.contact_email}."


@staff_member_required
@require_POST
def field_delete(request, pk):
    """Supprime un diagnostic terrain."""
    diag = get_object_or_404(FieldDiagnostic, pk=pk)
    diag.delete()
    return redirect("diagnostic:field_list")
