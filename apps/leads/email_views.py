"""Views for email composition."""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView
from django.views import View

from .email_models import EmailComposition, EmailTemplate
from .email_forms import EmailCompositionForm

logger = logging.getLogger(__name__)


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin requiring staff status."""
    def test_func(self):
        return self.request.user.is_staff


class EmailComposeView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """View for composing a new email."""
    
    model = EmailComposition
    form_class = EmailCompositionForm
    template_name = 'leads/email_compose.html'
    
    def get_success_url(self):
        # Try admin_emails first, fallback to leads
        try:
            return reverse('admin_emails:email_list')
        except:
            return reverse('leads:email_list')
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['templates'] = EmailTemplate.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form: EmailCompositionForm) -> HttpResponse:
        form.instance.created_by = self.request.user
        
        # Check if we should send or save as draft
        if 'send' in self.request.POST:
            form.instance.is_draft = False
            form.instance.sent_at = timezone.now()
            
            # Save first to get the instance
            response = super().form_valid(form)
            
            # Actually send the email
            success = self._send_email(self.object)
            if success:
                messages.success(self.request, f"✅ Email envoyé avec succès à {self.object.to_emails}")
            else:
                messages.warning(self.request, "⚠️ Email marqué comme envoyé mais l'envoi a peut-être échoué. Vérifiez les logs.")
            
            return response
        else:
            form.instance.is_draft = True
            messages.info(self.request, "📝 Brouillon enregistré")
            return super().form_valid(form)
    
    def _send_email(self, email_composition: EmailComposition) -> bool:
        """Actually send the email using Brevo or fallback Django."""
        try:
            from core.services.email_backends import brevo_service, send_simple_email
            
            # Build HTML with premium template
            branding = getattr(settings, 'INVOICE_BRANDING', {})
            site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.it').rstrip('/')
            
            html_body = render_to_string('emails/modele_email_premium.html', {
                'subject': email_composition.subject,
                'body_content': email_composition.body_html,
                'branding': branding,
                'site_url': site_url,
            })
            
            # Send to each recipient
            to_list = email_composition.get_to_list()
            cc_list = email_composition.get_cc_list()
            bcc_list = email_composition.get_bcc_list()
            
            success = True
            
            # Use Brevo if configured
            if brevo_service.is_configured():
                for recipient in to_list:
                    result = brevo_service.send_email(
                        to_email=recipient,
                        subject=email_composition.subject,
                        html_content=html_body,
                        tags=['premium-email', 'manual-send']
                    )
                    if not result.get('success'):
                        success = False
                        logger.error(f"Failed to send to {recipient}: {result.get('error')}")
                    else:
                        logger.info(f"Email sent to {recipient} via Brevo")
                
                # Send CC copies
                for cc in cc_list:
                    brevo_service.send_email(
                        to_email=cc,
                        subject=f"[CC] {email_composition.subject}",
                        html_content=html_body,
                        tags=['premium-email', 'cc-copy']
                    )
                
                # Send BCC copies
                for bcc in bcc_list:
                    brevo_service.send_email(
                        to_email=bcc,
                        subject=email_composition.subject,
                        html_content=html_body,
                        tags=['premium-email', 'bcc-copy']
                    )
            else:
                # Fallback Django
                logger.warning("Brevo non configuré, utilisation du fallback Django")
                for recipient in to_list:
                    result = send_simple_email(
                        to_email=recipient,
                        subject=email_composition.subject,
                        text_body=email_composition.body_html,
                        html_body=html_body,
                        bcc=bcc_list if recipient == to_list[0] else None,
                    )
                    if not result:
                        success = False
                        logger.error(f"Failed to send to {recipient} via Django")
                    else:
                        logger.info(f"Email sent to {recipient} via Django fallback")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False


class EmailListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """View for listing all emails (drafts and sent)."""
    
    model = EmailComposition
    template_name = 'leads/email_list.html'
    context_object_name = 'emails'
    paginate_by = 20
    
    def get_queryset(self):
        # Staff can see all emails
        if self.request.user.is_superuser:
            return EmailComposition.objects.all()
        return EmailComposition.objects.filter(created_by=self.request.user)


class EmailDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View for viewing a single email."""
    
    model = EmailComposition
    template_name = 'leads/email_detail.html'
    context_object_name = 'email'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return EmailComposition.objects.all()
        return EmailComposition.objects.filter(created_by=self.request.user)


class EmailTemplateAPIView(View):
    """API endpoint to get template content via AJAX."""
    
    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        try:
            template = EmailTemplate.objects.get(pk=pk, is_active=True)
            return JsonResponse({
                'success': True,
                'subject': template.subject,
                'body_html': template.body_html,
            })
        except EmailTemplate.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Template non trouvé'
            }, status=404)


@method_decorator(staff_member_required, name='dispatch')
class SendEmailView(View):
    """View to send or re-send an email."""
    
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        email_obj = get_object_or_404(EmailComposition, pk=pk)
        
        # Use the same send logic as EmailComposeView
        try:
            from core.services.email_backends import brevo_service, send_transactional_email
            
            branding = getattr(settings, 'INVOICE_BRANDING', {})
            site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.it').rstrip('/')
            
            html_body = render_to_string('emails/modele_email_premium.html', {
                'subject': email_obj.subject,
                'body_content': email_obj.body_html,
                'branding': branding,
                'site_url': site_url,
            })
            
            to_list = email_obj.get_to_list()
            success = True
            
            for recipient in to_list:
                result = send_transactional_email(
                    to_email=recipient,
                    subject=email_obj.subject,
                    html_content=html_body,
                    tags=['premium-email', 'manual-send']
                )
                if not result.get('success'):
                    success = False
            
            if success:
                email_obj.is_draft = False
                email_obj.sent_at = timezone.now()
                email_obj.save()
                messages.success(request, f"✅ Email envoyé avec succès à {email_obj.to_emails}")
            else:
                messages.error(request, "❌ Erreur lors de l'envoi de l'email")
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            messages.error(request, f"❌ Erreur: {e}")
        
        try:
            return redirect('admin_emails:email_list')
        except:
            return redirect('leads:email_list')


@method_decorator(staff_member_required, name='dispatch')
class BulkEmailView(View):
    """Vue pour l'envoi en masse d'emails (chaque destinataire reçoit un email individuel)."""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        templates = EmailTemplate.objects.filter(is_active=True)
        return render(request, 'leads/email_bulk.html', {
            'templates': templates,
        })
    
    def post(self, request: HttpRequest) -> HttpResponse:
        import time
        from core.services.email_backends import brevo_service
        
        # Récupérer les données du formulaire
        emails_raw = request.POST.get('emails', '')
        subject = request.POST.get('subject', '')
        body_html = request.POST.get('body_html', '')
        template_id = request.POST.get('template')
        delay_seconds = float(request.POST.get('delay', 1))  # Délai entre chaque envoi
        
        # Nettoyer et parser les emails
        emails = []
        for line in emails_raw.replace(',', '\n').replace(';', '\n').split('\n'):
            email = line.strip()
            if email and '@' in email:
                emails.append(email)
        
        # Supprimer les doublons tout en préservant l'ordre
        emails = list(dict.fromkeys(emails))
        
        if not emails:
            messages.error(request, "❌ Aucune adresse email valide fournie")
            return redirect('admin_emails:bulk_email')
        
        if not subject or not body_html:
            messages.error(request, "❌ Sujet et contenu requis")
            return redirect('admin_emails:bulk_email')
        
        # Préparer le HTML avec le template premium
        branding = getattr(settings, 'INVOICE_BRANDING', {})
        site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.it').rstrip('/')
        
        html_body = render_to_string('emails/modele_email_premium.html', {
            'subject': subject,
            'body_content': body_html,
            'branding': branding,
            'site_url': site_url,
        })
        
        # Envoyer les emails un par un
        success_count = 0
        failed_emails = []
        
        for i, recipient in enumerate(emails):
            try:
                result = brevo_service.send_email(
                    to_email=recipient,
                    subject=subject,
                    html_content=html_body,
                    tags=['bulk-email', 'prospection']
                )
                
                if result.get('success'):
                    success_count += 1
                    logger.info(f"[{i+1}/{len(emails)}] Email envoyé à {recipient}")
                else:
                    failed_emails.append(recipient)
                    logger.error(f"[{i+1}/{len(emails)}] Échec envoi à {recipient}: {result.get('error')}")
                
                # Délai entre chaque envoi pour éviter les limites de taux
                if i < len(emails) - 1 and delay_seconds > 0:
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                failed_emails.append(recipient)
                logger.error(f"Erreur envoi à {recipient}: {e}")
        
        # Enregistrer la campagne dans EmailComposition pour historique
        EmailComposition.objects.create(
            to_emails=', '.join(emails[:10]) + (f'... (+{len(emails)-10})' if len(emails) > 10 else ''),
            subject=f"[BULK x{len(emails)}] {subject}",
            body_html=body_html,
            template_id=template_id if template_id else None,
            is_draft=False,
            sent_at=timezone.now(),
            created_by=request.user,
        )
        
        # Messages de feedback
        if success_count == len(emails):
            messages.success(request, f"✅ {success_count} emails envoyés avec succès !")
        elif success_count > 0:
            messages.warning(
                request, 
                f"⚠️ {success_count}/{len(emails)} emails envoyés. "
                f"Échecs: {', '.join(failed_emails[:5])}{'...' if len(failed_emails) > 5 else ''}"
            )
        else:
            messages.error(request, f"❌ Échec de l'envoi. Vérifiez la configuration Brevo.")
        
        try:
            return redirect('admin_emails:email_list')
        except:
            return redirect('leads:email_list')
