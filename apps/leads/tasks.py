"""Async tasks for the leads app (Django-Q2)."""
from __future__ import annotations

import logging
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_bulk_emails_task(
    emails: list[str],
    subject: str,
    html_body: str,
    delay_seconds: float,
    body_html_raw: str,
    template_id: str | None,
    user_id: int,
) -> dict:
    """Send bulk emails one by one with a delay between each.

    This function is designed to be called via ``django_q.tasks.async_task``
    so that the HTTP request returns immediately while emails are sent in the
    background by a Django-Q2 worker.

    Returns a summary dict with success/failure counts.
    """
    from core.services.email_backends import brevo_service
    from .email_models import EmailComposition
    from django.contrib.auth import get_user_model

    User = get_user_model()

    success_count = 0
    failed_emails: list[str] = []

    for i, recipient in enumerate(emails):
        try:
            result = brevo_service.send_email(
                to_email=recipient,
                subject=subject,
                html_content=html_body,
                tags=['bulk-email', 'prospection'],
            )

            if result.get('success'):
                success_count += 1
                logger.info("[%d/%d] Email envoyé à %s", i + 1, len(emails), recipient)
            else:
                failed_emails.append(recipient)
                logger.error(
                    "[%d/%d] Échec envoi à %s: %s",
                    i + 1, len(emails), recipient, result.get('error'),
                )

            # Delay between sends to avoid rate limits
            if i < len(emails) - 1 and delay_seconds > 0:
                time.sleep(delay_seconds)

        except Exception as e:
            failed_emails.append(recipient)
            logger.error("Erreur envoi à %s: %s", recipient, e)

    # Record campaign in EmailComposition for history
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        user = None

    EmailComposition.objects.create(
        to_emails=', '.join(emails[:10]) + (f'... (+{len(emails) - 10})' if len(emails) > 10 else ''),
        subject=f"[BULK x{len(emails)}] {subject}",
        body_html=body_html_raw,
        template_id=template_id if template_id else None,
        is_draft=False,
        sent_at=timezone.now(),
        created_by=user,
    )

    logger.info(
        "Bulk email terminé: %d/%d envoyés, %d échecs",
        success_count, len(emails), len(failed_emails),
    )

    return {
        'total': len(emails),
        'success': success_count,
        'failed': failed_emails,
    }


def send_newsletter_campaign_task(campaign_id: int) -> dict:
    """Envoie une campagne newsletter à tous les abonnés actifs.

    Appelé via django-q2 async_task depuis l'admin.
    Chaque abonné reçoit un email individuel avec lien de désinscription.
    Délai de 1s entre chaque envoi pour respecter les limites Brevo.
    """
    from core.services.email_backends import brevo_service
    from .models import EmailSubscriber, NewsletterCampaign

    try:
        campaign = NewsletterCampaign.objects.get(pk=campaign_id)
    except NewsletterCampaign.DoesNotExist:
        logger.error("Campagne newsletter #%d introuvable", campaign_id)
        return {'error': 'Campaign not found'}

    campaign.status = NewsletterCampaign.Status.SENDING
    campaign.save(update_fields=['status'])

    subscribers = EmailSubscriber.objects.filter(is_active=True).values_list('email', flat=True)
    emails = list(subscribers)
    campaign.recipients_count = len(emails)
    campaign.save(update_fields=['recipients_count'])

    if not emails:
        campaign.status = NewsletterCampaign.Status.SENT
        campaign.sent_at = timezone.now()
        campaign.save(update_fields=['status', 'sent_at'])
        return {'total': 0, 'success': 0, 'failed': []}

    # Build HTML with premium template + unsubscribe link
    branding = getattr(settings, 'INVOICE_BRANDING', {})
    site_url = str(getattr(settings, 'SITE_URL', 'https://www.traitdunion.it')).rstrip('/')
    if 'localhost' in site_url or '127.0.0.1' in site_url:
        site_url = 'https://www.traitdunion.it'

    success_count = 0
    failed_emails = []

    for i, email in enumerate(emails):
        # Personalized unsubscribe link per recipient (HMAC-signed)
        from .models import make_unsubscribe_url
        unsub_url = make_unsubscribe_url(email)

        html_body = render_to_string('emails/newsletter_campaign.html', {
            'subject': campaign.subject,
            'body_content': campaign.body_html,
            'branding': branding,
            'site_url': site_url,
            'unsubscribe_url': unsub_url,
            'email': email,
        })

        try:
            result = brevo_service.send_email(
                to_email=email,
                subject=campaign.subject,
                html_content=html_body,
                tags=['newsletter', f'campaign-{campaign.pk}'],
            )
            if result.get('success'):
                success_count += 1
            else:
                failed_emails.append(email)
                logger.error("Newsletter #%d: échec envoi à %s: %s", campaign.pk, email, result.get('error'))
        except Exception as e:
            failed_emails.append(email)
            logger.error("Newsletter #%d: erreur envoi à %s: %s", campaign.pk, email, e)

        # Throttle
        if i < len(emails) - 1:
            time.sleep(0.2)

    # Update campaign
    campaign.sent_count = success_count
    campaign.failed_count = len(failed_emails)
    campaign.status = NewsletterCampaign.Status.SENT if not failed_emails else NewsletterCampaign.Status.SENT
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])

    logger.info(
        "Newsletter #%d envoyée: %d/%d OK, %d échecs",
        campaign.pk, success_count, len(emails), len(failed_emails),
    )

    return {
        'total': len(emails),
        'success': success_count,
        'failed': failed_emails,
    }


def send_article_as_newsletter_task(article_id: int) -> dict:
    """Envoie un article des Chroniques TUS comme newsletter à tous les abonnés actifs.

    Crée automatiquement une NewsletterCampaign pour le suivi.
    Chaque abonné reçoit un email individuel avec lien de désinscription signé.
    """
    from core.services.email_backends import brevo_service
    from apps.chroniques.models import Article
    from .models import EmailSubscriber, NewsletterCampaign, make_unsubscribe_url

    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error("Article #%d introuvable pour newsletter", article_id)
        return {'error': 'Article not found'}

    # Create campaign for tracking
    campaign = NewsletterCampaign.objects.create(
        subject=f"📰 {article.title}",
        body_html=article.excerpt or article.title,
        status=NewsletterCampaign.Status.SENDING,
    )

    subscribers = list(EmailSubscriber.objects.filter(is_active=True).values_list('email', flat=True))
    campaign.recipients_count = len(subscribers)
    campaign.save(update_fields=['recipients_count'])

    if not subscribers:
        campaign.status = NewsletterCampaign.Status.SENT
        campaign.sent_at = timezone.now()
        campaign.save(update_fields=['status', 'sent_at'])
        return {'total': 0, 'success': 0, 'failed': []}

    site_url = str(getattr(settings, 'SITE_URL', 'https://www.traitdunion.it')).rstrip('/')
    if 'localhost' in site_url or '127.0.0.1' in site_url:
        site_url = 'https://www.traitdunion.it'

    article_url = f"{site_url}{article.get_absolute_url()}"

    # Cover image URL
    cover_image_url = ''
    if article.cover_image:
        cover_url = article.cover_image.url
        if cover_url.startswith('http'):
            cover_image_url = cover_url
        else:
            cover_image_url = f"{site_url}{cover_url}"

    success_count = 0
    failed_emails = []

    for i, email in enumerate(subscribers):
        unsub_url = make_unsubscribe_url(email)

        html_body = render_to_string('emails/newsletter_article.html', {
            'title': article.title,
            'subtitle': article.subtitle or '',
            'category': article.category.name if article.category else '',
            'excerpt': article.excerpt or article.meta_description or article.title,
            'cover_image_url': cover_image_url,
            'article_url': article_url,
            'unsubscribe_url': unsub_url,
            'site_url': site_url,
        })

        try:
            result = brevo_service.send_email(
                to_email=email,
                subject=f"📰 {article.title}",
                html_content=html_body,
                tags=['newsletter', 'article', f'article-{article.slug}'],
            )
            if result.get('success'):
                success_count += 1
            else:
                failed_emails.append(email)
        except Exception as e:
            failed_emails.append(email)
            logger.error("Newsletter article: erreur envoi à %s: %s", email, e)

        if i < len(subscribers) - 1:
            time.sleep(0.2)

    campaign.sent_count = success_count
    campaign.failed_count = len(failed_emails)
    campaign.status = NewsletterCampaign.Status.SENT
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])

    logger.info(
        "Newsletter article '%s': %d/%d OK, %d échecs",
        article.title, success_count, len(subscribers), len(failed_emails),
    )

    return {
        'total': len(subscribers),
        'success': success_count,
        'failed': failed_emails,
        'campaign_id': campaign.pk,
    }
