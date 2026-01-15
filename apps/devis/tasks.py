"""
Celery tasks for devis (quote) emails.

- Envoi asynchrone d'un devis au client en HTML brandé + PDF en pièce jointe.
"""

from __future__ import annotations

try:
    from celery import shared_task  # type: ignore
except Exception:  # Celery non installé -> fallback
    def shared_task(*dargs, **dkwargs):  # type: ignore
        def _decorator(fn):
            return fn
        return _decorator

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from core.services.pdf_generator import render_quote_pdf


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_quote_pdf_email(self, quote_id: int) -> None:
    from devis.models import Quote  # local import

    quote = Quote.objects.select_related("client").prefetch_related("quote_items").get(pk=quote_id)

    # Ensure totals + PDF
    try:
        quote.compute_totals()
    except Exception:
        pass

    pdf_res = render_quote_pdf(quote)

    # Build email html
    context = {
        "quote": quote,
        "branding": getattr(settings, "INVOICE_BRANDING", {}) or {},
        "cta_url": getattr(settings, "SITE_URL", "").rstrip("/") + f"/devis/{quote.pk}/" if getattr(settings, "SITE_URL", None) else None,
    }
    html = render_to_string("emails/new_quote_pdf.html", context)

    to_email = getattr(quote.client, "email", None) or getattr(quote, "email", None)
    if not to_email:
        return

    subject = f"Votre devis {quote.number}"
    email = EmailMessage(
        subject=subject,
        body=html,
        to=[to_email],
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
    )
    email.content_subtype = "html"
    email.attach(pdf_res.filename, pdf_res.content, "application/pdf")

    # Optional admin copy
    admin_email = getattr(settings, "TASK_NOTIFICATION_EMAIL", None)
    if admin_email:
        email.bcc = [admin_email]

    email.send(fail_silently=False)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_quote_request_received(self, quote_request_id: int) -> None:
    """Confirme au client + notifie l'admin (template premium)."""
    from devis.models import QuoteRequest

    qr = QuoteRequest.objects.get(pk=quote_request_id)
    branding = getattr(settings, "INVOICE_BRANDING", {}) or {}

    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    admin_dashboard_url = site_url + "/dashboard/"
    admin_request_url = site_url + "/admin/devis/quoterequest/"

    # -------------------------
    # 1) Email client (confirmation)
    # -------------------------
    if qr.email:
        context = {
            "quote_request": qr,
            "branding": branding,
            "cta_url": site_url + "/devis/nouveau/",
        }
        html = render_to_string("emails/new_quote.html", context)
        email = EmailMessage(
            subject="Votre demande de devis a bien été reçue",
            body=html,
            to=[qr.email],
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

    # -------------------------
    # 2) Email admin (notification premium)
    # -------------------------
    admin_email = getattr(settings, "TASK_NOTIFICATION_EMAIL", None)
    if not admin_email:
        return

    rows = [
        {"label": "Type de service", "value": getattr(qr, "topic", None) or "Demande de devis"},
        {"label": "Client", "value": getattr(qr, "client_name", None) or "—"},
        {"label": "Téléphone", "value": getattr(qr, "phone", None) or "—"},
        {"label": "Email", "value": getattr(qr, "email", None) or "—"},
        {"label": "Commune", "value": f"{getattr(qr, 'zip_code', '')} {getattr(qr, 'city', '')}".strip() or "—"},
    ]

    ctx_admin = {
        "brand": branding.get("name", "NETTOYAGE EXPRESS"),
        "title": "Nouvelle demande de devis",
        "headline": "Nouvelle demande de devis reçue",
        "intro": "Une nouvelle demande a été soumise via le formulaire du site. Voici le récapitulatif.",
        "rows": rows,
        "action_url": admin_request_url,
        "action_label": "Ouvrir dans l'admin",
        "reference": f"REQ-{qr.pk}",
    }
    html_admin = render_to_string("emails/notification_generic.html", ctx_admin)
    em = EmailMessage(
        subject=f"[NetExpress] Nouvelle demande de devis (REQ-{qr.pk})",
        body=html_admin,
        to=[admin_email],
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
    )
    em.content_subtype = "html"
    em.send(fail_silently=False)
