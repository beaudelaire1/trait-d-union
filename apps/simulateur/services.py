"""Services for the Simulateur app.

Génère le rapport PDF d'un simulateur et l'envoie par email au lead.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from core.services.document_generator import DocumentGenerator

from .models import SimulatorReport

logger = logging.getLogger(__name__)


class SimulatorReportService:
    """Génération + envoi du rapport PDF d'un simulateur."""

    @classmethod
    def generate_pdf(cls, report: SimulatorReport) -> bytes:
        """Rend le template PDF générique et produit les bytes."""
        branding = DocumentGenerator.get_branding()
        snapshot = report.snapshot or {}

        context = {
            'report': report,
            'branding': branding,
            'tool_name': report.tool_name,
            'tool_slug': report.tool_slug,
            'snapshot': snapshot,
            # Champs pratiques si fournis par le front.
            'verdict': snapshot.get('verdict'),
            'score': snapshot.get('score'),
            'sections': snapshot.get('sections', []),
            'recommendations': snapshot.get('recommendations', []),
            'generated_at': timezone.now(),
        }

        html = render_to_string('pdf/simulateur_report.html', context)
        return DocumentGenerator._render_pdf(html)

    @classmethod
    def send(cls, report: SimulatorReport) -> None:
        """Génère et envoie le rapport par email au lead."""
        from django.core.mail import EmailMultiAlternatives

        pdf_bytes = cls.generate_pdf(report)

        context = {
            'report': report,
            'tool_name': report.tool_name,
            'site_url': getattr(settings, 'SITE_URL', 'https://traitdunion.it'),
        }
        html_body = render_to_string('emails/simulateur_report.html', context)
        text_body = render_to_string('emails/simulateur_report.txt', context)

        subject = f"Votre rapport : {report.tool_name}"
        from_email = getattr(
            settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it'
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[report.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        filename = f"rapport_{report.tool_slug}.pdf"
        msg.attach(filename, pdf_bytes, 'application/pdf')

        try:
            msg.send(fail_silently=False)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Échec envoi rapport simulateur %s à %s : %s",
                report.tool_slug, report.email, exc, exc_info=True,
            )
            report.send_error = str(exc)[:500]
            report.save(update_fields=['send_error'])
            raise

        report.pdf_sent_at = timezone.now()
        report.save(update_fields=['pdf_sent_at'])

        # Notification interne (best-effort).
        try:
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            if admin_email:
                from django.core.mail import send_mail
                send_mail(
                    subject=f"[Lead simulateur] {report.tool_name} – {report.email}",
                    message=(
                        f"Nouveau rapport demandé\n\n"
                        f"Email : {report.email}\n"
                        f"Nom : {report.name or '—'}\n"
                        f"Entreprise : {report.company or '—'}\n"
                        f"Outil : {report.tool_name}\n"
                        f"IP : {report.ip_address or '—'}\n"
                    ),
                    from_email=from_email,
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
        except Exception:  # noqa: BLE001
            logger.exception("Échec notification admin lead simulateur")
