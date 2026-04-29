"""Signal handlers for automatic client notifications."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.devis.models import Quote
from apps.factures.models import Invoice
from apps.clients.models import ClientNotification, ClientProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Quote)
def notify_quote_created(sender, instance, created, **kwargs):
    """Send notification when a new quote is created."""
    if not (created and instance.status == 'sent'):
        return
    try:
        profile = instance.client  # Quote.client IS a ClientProfile now
        if profile and profile.has_portal_access:
            ClientNotification.objects.create(
                client=profile,
                notification_type='quote',
                title='Nouveau devis disponible',
                message=f'Un nouveau devis #{instance.number} a été créé pour vous.',
                related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification création devis %s", instance.pk)


@receiver(post_save, sender=Quote)
def notify_quote_accepted(sender, instance, created, **kwargs):
    """Send notification when a quote is accepted (only once)."""
    if created:
        return
    if not (instance.status == 'accepted' and instance.signed_at):
        return
    try:
        profile = instance.client
        if profile and profile.has_portal_access and not ClientNotification.objects.filter(
            client=profile, notification_type='quote',
            title='Devis accepté', related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
        ).exists():
            ClientNotification.objects.create(
                client=profile,
                notification_type='quote',
                title='Devis accepté',
                message=f'Votre devis #{instance.number} a été accepté. Nous commençons votre projet !',
                related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification acceptation devis %s", instance.pk)


def _resolve_invoice_profile(invoice):
    """Retourne le ClientProfile de la facture (direct ou via devis)."""
    return invoice.client or (invoice.quote.client if invoice.quote else None)


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance, created, **kwargs):
    """Send notification when a new invoice is created."""
    if not (created and instance.status == 'sent'):
        return
    try:
        profile = _resolve_invoice_profile(instance)
        if profile and profile.has_portal_access:
            ClientNotification.objects.create(
                client=profile,
                notification_type='invoice',
                title='Nouvelle facture disponible',
                message=f'La facture #{instance.number} est disponible pour un montant de {instance.total_ttc}€.',
                related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification création facture %s", instance.pk)


@receiver(post_save, sender=Invoice)
def notify_invoice_paid(sender, instance, created, **kwargs):
    """Send notification when an invoice is paid (only once)."""
    if created:
        return
    if not (instance.status == 'paid' and instance.paid_at):
        return
    try:
        profile = _resolve_invoice_profile(instance)
        if profile and profile.has_portal_access and not ClientNotification.objects.filter(
            client=profile, notification_type='invoice',
            title='Paiement reçu', related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
        ).exists():
            ClientNotification.objects.create(
                client=profile,
                notification_type='invoice',
                title='Paiement reçu',
                message=f'Votre paiement pour la facture #{instance.number} a été reçu. Merci !',
                related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification paiement facture %s", instance.pk)


# ==============================================================================
# MILESTONE NOTIFICATIONS (in-app + email)
# ==============================================================================

from apps.clients.models import ProjectMilestone


@receiver(post_save, sender=ProjectMilestone)
def notify_milestone_completed(sender, instance, created, **kwargs):
    """Notify client when a milestone is completed (in-app + email)."""
    if created:
        return
    if instance.status != 'completed':
        return

    project = instance.project
    profile = project.client
    if not profile or not profile.has_portal_access:
        return

    # Avoid duplicate notifications
    notif_url = f'/ecosysteme-tus/projets/{project.pk}/'
    notif_title = f'Jalon terminé : {instance.title}'
    if ClientNotification.objects.filter(
        client=profile, title=notif_title, related_url=notif_url,
    ).exists():
        return

    try:
        # In-app notification
        ClientNotification.objects.create(
            client=profile,
            notification_type='project',
            title=notif_title,
            message=f'Le jalon « {instance.title} » de votre projet {project.name} est terminé.',
            related_url=notif_url,
        )

        # Email notification (async, best-effort)
        if profile.email_notifications and profile.user:
            _send_milestone_email(profile, project, instance)

    except Exception:
        logger.exception("Erreur notification jalon %s", instance.pk)


def _send_milestone_email(profile, project, milestone):
    """Send milestone completion email to client (best-effort)."""
    from django.conf import settings

    site_url = str(getattr(settings, 'SITE_URL', 'https://www.traitdunion.it')).rstrip('/')
    if 'localhost' in site_url or '127.0.0.1' in site_url:
        site_url = 'https://www.traitdunion.it'

    user = profile.user
    first_name = user.first_name or profile.full_name.split()[0] if profile.full_name else 'Bonjour'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
    project_url = f"{site_url}/ecosysteme-tus/projets/{project.pk}/"

    # Count progress
    total = project.milestones.count()
    done = project.milestones.filter(status='completed').count()
    pct = int((done / total) * 100) if total > 0 else 0

    subject = f"✅ Jalon terminé — {project.name}"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#07080A;font-family:'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#07080A;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#0D1016;border:1px solid rgba(246,247,251,0.08);border-radius:16px;overflow:hidden;">
  <tr><td style="height:4px;background:linear-gradient(135deg,#0B2DFF,#22C55E);"></td></tr>
  <tr><td style="padding:32px 40px 16px;text-align:center;">
    <span style="font-size:1.4rem;font-weight:700;color:#F6F7FB;">Trait d'Union Studio</span>
  </td></tr>
  <tr><td style="padding:0 40px 24px;text-align:center;">
    <div style="display:inline-block;width:64px;height:64px;line-height:64px;font-size:2rem;background:rgba(34,197,94,0.12);border-radius:50%;">✅</div>
    <h1 style="margin:16px 0 0;font-size:1.4rem;font-weight:700;color:#F6F7FB;">Jalon terminé</h1>
    <p style="margin:8px 0 0;font-size:0.95rem;color:rgba(246,247,251,0.7);">
      {first_name}, votre projet <strong style="color:#4D6FFF;">{project.name}</strong> avance.
    </p>
  </td></tr>
  <tr><td style="padding:0 40px 24px;">
    <table width="100%" style="background:#111827;border:1px solid rgba(34,197,94,0.25);border-radius:12px;">
      <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 8px;font-size:0.8rem;color:rgba(246,247,251,0.5);text-transform:uppercase;letter-spacing:0.1em;">Jalon complété</p>
        <p style="margin:0;font-size:1.1rem;font-weight:600;color:#F6F7FB;">{milestone.title}</p>
        <div style="margin-top:16px;background:rgba(246,247,251,0.05);border-radius:8px;height:8px;overflow:hidden;">
          <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#0B2DFF,#22C55E);border-radius:8px;"></div>
        </div>
        <p style="margin:8px 0 0;font-size:0.85rem;color:rgba(246,247,251,0.5);">{done}/{total} jalons — {pct}%</p>
      </td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:0 40px 32px;text-align:center;">
    <a href="{project_url}" style="display:inline-block;background:linear-gradient(135deg,#0B2DFF,#22C55E);color:#fff;text-decoration:none;padding:14px 40px;border-radius:8px;font-weight:700;font-size:0.95rem;">
      Voir mon projet →
    </a>
  </td></tr>
  <tr><td style="padding:24px 40px;border-top:1px solid rgba(246,247,251,0.08);text-align:center;">
    <p style="margin:0;font-size:0.78rem;color:rgba(246,247,251,0.35);">
      Trait d'Union Studio · Guyane<br>
      <a href="mailto:contact@traitdunion.it" style="color:#4D6FFF;text-decoration:none;">contact@traitdunion.it</a>
    </p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

    try:
        from core.services.email_backends import brevo_service
        if brevo_service.is_configured():
            brevo_service.send_email(
                to_email=user.email,
                to_name=first_name,
                subject=subject,
                html_content=html,
                from_email=from_email,
                from_name=getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio"),
                tags=['milestone', 'project', 'notification'],
            )
            logger.info("Email jalon envoyé à %s pour projet %s", user.email, project.name)
            return
    except Exception as exc:
        logger.warning("Brevo indisponible pour notif jalon: %s", exc)

    from django.core.mail import EmailMultiAlternatives
    msg = EmailMultiAlternatives(subject, f"Jalon terminé: {milestone.title}", from_email, [user.email])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)
