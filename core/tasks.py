"""
Tâches asynchrones TUS — django-q2.

Ce module centralise toutes les tâches exécutées en arrière-plan :
- Envoi d'emails (bienvenue, devis, factures, notifications)
- Génération de PDF
- Notifications portail client

Usage :
    from core.tasks import async_send_email, async_send_welcome_email
    async_send_welcome_email(user_id, temporary_password)

Worker :
    python manage.py qcluster
"""
import logging

from django_q.tasks import async_task

logger = logging.getLogger(__name__)


# ==============================================================================
# HELPERS / DISPATCHERS
# ==============================================================================

def _is_qcluster_running() -> bool:
    """Vérifie si au moins un worker qcluster est actif.

    On regarde les Stat objects de django-q2.  S'il n'y en a aucun
    ou si la table n'existe pas, on considère le cluster inactif.
    """
    try:
        from django_q.monitor import Stat
        return len(Stat.get_all()) > 0
    except Exception:
        return False


def _run_sync(func_path: str, *args):
    """Importe et exécute la fonction de manière synchrone."""
    from importlib import import_module
    module_path, func_name = func_path.rsplit('.', 1)
    module = import_module(module_path)
    func = getattr(module, func_name)
    return func(*args)


def _dispatch(func_path: str, *args, **kwargs):
    """Dispatch une tâche asynchrone via django-q2.

    Si le cluster n'est pas actif (dev local sans qcluster),
    exécute la tâche de manière synchrone en fallback.
    """
    task_name = kwargs.pop('task_name', func_path.split('.')[-1])

    # En dev sans worker actif → exécution synchrone immédiate
    if not _is_qcluster_running():
        logger.info(f"qcluster inactif — exécution synchrone : {task_name}")
        return _run_sync(func_path, *args)

    try:
        return async_task(
            func_path,
            *args,
            task_name=task_name,
            **kwargs,
        )
    except Exception as e:
        logger.warning(f"django-q2 erreur, exécution synchrone: {e}")
        return _run_sync(func_path, *args)


# ==============================================================================
# DISPATCHERS PUBLICS (appelés depuis les vues/admin/signals)
# ==============================================================================

def async_send_welcome_email(user_id: int, temporary_password: str, context_label: str = ''):
    """Envoie l'email de bienvenue en arrière-plan."""
    return _dispatch(
        'core.tasks._task_send_welcome_email',
        user_id,
        temporary_password,
        context_label,
        task_name=f'welcome_email_user_{user_id}',
    )


def async_reset_password_notify(user_id: int):
    """Réinitialise le mot de passe et envoie la notification en arrière-plan."""
    return _dispatch(
        'core.tasks._task_reset_password_notify',
        user_id,
        task_name=f'reset_password_user_{user_id}',
    )


def async_send_quote_email(quote_id: int):
    """Envoie le devis par email en arrière-plan."""
    return _dispatch(
        'core.tasks._task_send_quote_email',
        quote_id,
        task_name=f'send_quote_{quote_id}',
    )


def async_send_quote_pdf_email(quote_id: int):
    """Génère le PDF du devis et l'envoie par email."""
    return _dispatch(
        'core.tasks._task_send_quote_pdf_email',
        quote_id,
        task_name=f'send_quote_pdf_{quote_id}',
    )


def async_notify_quote_request(quote_request_id: int):
    """Envoie la notification de demande de devis (client + admin)."""
    return _dispatch(
        'core.tasks._task_notify_quote_request',
        quote_request_id,
        task_name=f'notify_quote_request_{quote_request_id}',
    )


def async_notify_invoice_created(invoice_id: int):
    """Notifie l'admin de la création d'une facture."""
    return _dispatch(
        'core.tasks._task_notify_invoice_created',
        invoice_id,
        task_name=f'notify_invoice_{invoice_id}',
    )


def async_send_payment_confirmation(quote_id: int = None, invoice_id: int = None, is_partial: bool = False):
    """Envoie la confirmation de paiement (devis ou facture)."""
    return _dispatch(
        'core.tasks._task_send_payment_confirmation',
        quote_id,
        invoice_id,
        is_partial,
        task_name=f'payment_confirmation_{quote_id or invoice_id}',
    )


def async_send_generic_email(to_email: str, subject: str, html_content: str, from_email: str = None):
    """Envoie un email générique en arrière-plan."""
    return _dispatch(
        'core.tasks._task_send_generic_email',
        to_email,
        subject,
        html_content,
        from_email,
        task_name=f'generic_email_{to_email}',
    )


def async_send_password_changed_email(user_id: int):
    """Envoie l'email de confirmation de changement de mot de passe."""
    return _dispatch(
        'core.tasks._task_send_password_changed_email',
        user_id,
        task_name=f'password_changed_email_{user_id}',
    )


def async_notify_admin_new_comment(comment_id: int):
    """Notifie l'admin qu'un client a posté un commentaire sur un projet."""
    return _dispatch(
        'core.tasks._task_notify_admin_new_comment',
        comment_id,
        task_name=f'admin_comment_notif_{comment_id}',
    )


# ==============================================================================
# WORKERS (fonctions exécutées par le cluster django-q2)
# ==============================================================================

def _task_send_welcome_email(user_id: int, temporary_password: str, context_label: str = ''):
    """Worker : envoie l'email de bienvenue."""
    from django.contrib.auth.models import User
    from apps.clients.services import send_welcome_email

    user = User.objects.get(pk=user_id)
    send_welcome_email(user, temporary_password, context_label=context_label)
    logger.info(f"[ASYNC] Email bienvenue envoyé à {user.email}")


def _task_reset_password_notify(user_id: int):
    """Worker : réinitialise le mot de passe et notifie."""
    from django.contrib.auth.models import User
    from apps.clients.services import reset_password_and_notify

    user = User.objects.get(pk=user_id)
    reset_password_and_notify(user)
    logger.info(f"[ASYNC] Password reset + email envoyé à {user.email}")


def _task_send_password_changed_email(user_id: int):
    """Worker : envoie l'email de confirmation de changement de mot de passe."""
    from django.contrib.auth.models import User
    from apps.clients.services import send_password_changed_email

    user = User.objects.get(pk=user_id)
    send_password_changed_email(user)
    logger.info(f"[ASYNC] Email confirmation changement mdp envoyé à {user.email}")


def _task_notify_admin_new_comment(comment_id: int):
    """Worker : notifie l'admin qu'un client a posté un commentaire."""
    from apps.clients.models import ProjectComment
    from apps.clients.services import send_new_comment_notification_to_admin

    comment = ProjectComment.objects.select_related('project', 'author').get(pk=comment_id)
    send_new_comment_notification_to_admin(comment)
    logger.info(f"[ASYNC] Notification admin commentaire #{comment_id} envoyée")


def _task_send_quote_email(quote_id: int):
    """Worker : envoie le devis par email."""
    from apps.devis.email_service import send_quote_email
    from apps.devis.models import Quote

    quote = Quote.objects.select_related('client').get(pk=quote_id)
    send_quote_email(quote)
    logger.info(f"[ASYNC] Devis {quote.number} envoyé par email")


def _task_send_quote_pdf_email(quote_id: int):
    """Worker : génère le PDF et envoie le devis.

    Délègue à send_quote_email (email_service.py) qui gère
    correctement les URLs (SITE_URL), le PDF, et l'envoi Brevo.
    """
    from apps.devis.email_service import send_quote_email
    from apps.devis.models import Quote

    quote = Quote.objects.select_related('client').prefetch_related('quote_items').get(pk=quote_id)
    if not quote.pdf:
        quote.generate_pdf(attach=True)
    send_quote_email(quote)
    logger.info(f"[ASYNC] PDF devis {quote.number} envoyé par email")


def _task_notify_quote_request(quote_request_id: int):
    """Worker : notification demande de devis (client + admin)."""
    from apps.devis.models import QuoteRequest
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings

    qr = QuoteRequest.objects.get(pk=quote_request_id)
    branding = getattr(settings, 'INVOICE_BRANDING', {}) or {}
    site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.it').rstrip('/')

    # 1) Email client
    if qr.email:
        context = {
            'quote_request': qr,
            'branding': branding,
            'cta_url': site_url + '/devis/nouveau/',
        }
        html = render_to_string('emails/new_quote.html', context)
        email = EmailMessage(
            subject='Votre demande de devis a bien été reçue',
            body=html,
            to=[qr.email],
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    # 2) Email admin
    admin_email = getattr(settings, 'TASK_NOTIFICATION_EMAIL', None)
    if admin_email:
        admin_request_url = site_url + '/tus-gestion-secure/devis/quoterequest/'
        rows = [
            {'label': 'Type de service', 'value': getattr(qr, 'topic', None) or 'Demande de devis'},
            {'label': 'Client', 'value': getattr(qr, 'client_name', None) or '—'},
            {'label': 'Téléphone', 'value': getattr(qr, 'phone', None) or '—'},
            {'label': 'Email', 'value': getattr(qr, 'email', None) or '—'},
            {'label': 'Commune', 'value': f"{getattr(qr, 'zip_code', '')} {getattr(qr, 'city', '')}".strip() or '—'},
        ]
        ctx_admin = {
            'brand': branding.get('name', 'Trait d\'Union Studio'),
            'title': 'Nouvelle demande de devis',
            'headline': 'Nouvelle demande de devis reçue',
            'intro': 'Une nouvelle demande a été soumise via le formulaire du site.',
            'rows': rows,
            'action_url': admin_request_url,
            'action_label': 'Ouvrir dans l\'admin',
            'reference': f'REQ-{qr.pk}',
        }
        html_admin = render_to_string('emails/notification_generic.html', ctx_admin)
        em = EmailMessage(
            subject=f"[TUS] Nouvelle demande de devis (REQ-{qr.pk})",
            body=html_admin,
            to=[admin_email],
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        )
        em.content_subtype = 'html'
        em.send(fail_silently=False)

    logger.info(f"[ASYNC] Notification demande de devis REQ-{qr.pk} envoyée")


def _task_notify_invoice_created(invoice_id: int):
    """Worker : notification création facture."""
    from apps.factures.models import Invoice
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings

    invoice = Invoice.objects.get(pk=invoice_id)
    recipient = getattr(settings, 'TASK_NOTIFICATION_EMAIL', getattr(settings, 'ADMIN_EMAIL', ''))
    if not recipient:
        return

    num = invoice.number or invoice.pk
    total = getattr(invoice, 'total_ttc', None) or getattr(invoice, 'total', 'N/A')
    subject = f"[Trait d'Union Studio] Facture #{num} générée"

    html_body = render_to_string('emails/notification_generic.html', {
        'headline': 'Nouvelle facture générée',
        'intro': 'Une nouvelle facture a été créée dans le système.',
        'rows': [
            {'label': 'Numéro', 'value': str(num)},
            {'label': 'Total TTC', 'value': f'{total} €'},
        ],
    })

    # Essai Brevo puis fallback Django
    try:
        from core.services.email_backends import send_transactional_email, brevo_service
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")

        if brevo_service.is_configured():
            send_transactional_email(
                to_email=recipient,
                subject=subject,
                html_content=html_body,
                from_email=from_email,
                from_name=from_name,
                tags=['facture', 'notification', 'admin'],
            )
            logger.info(f"[ASYNC] Notification facture {num} envoyée via Brevo")
            return
    except Exception:
        pass

    email = EmailMessage(
        subject=subject, body=html_body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it'),
        to=[recipient],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=True)
    logger.info(f"[ASYNC] Notification facture {num} envoyée via Django")


def _task_send_payment_confirmation(quote_id: int = None, invoice_id: int = None, is_partial: bool = False):
    """Worker : confirmation de paiement."""
    if quote_id:
        from core.services.payment_email_service import send_quote_deposit_confirmation_email
        from apps.devis.models import Quote
        quote = Quote.objects.select_related('client').get(pk=quote_id)
        send_quote_deposit_confirmation_email(quote)
        logger.info(f"[ASYNC] Confirmation paiement devis {quote.number}")

    if invoice_id:
        from core.services.payment_email_service import send_invoice_payment_confirmation_email
        from apps.factures.models import Invoice
        invoice = Invoice.objects.select_related('quote__client').get(pk=invoice_id)
        send_invoice_payment_confirmation_email(invoice, is_partial=is_partial)
        logger.info(f"[ASYNC] Confirmation paiement facture {invoice.number}")


def _task_send_generic_email(to_email: str, subject: str, html_content: str, from_email: str = None):
    """Worker : email générique."""
    from django.core.mail import EmailMessage
    from django.conf import settings

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it'),
        to=[to_email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)
    logger.info(f"[ASYNC] Email générique envoyé à {to_email}")
