"""Views for email composition."""
from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView
from django.views import View

from .email_models import EmailComposition, EmailTemplate
from .email_forms import EmailCompositionForm

logger = logging.getLogger(__name__)


class EmailComposeView(LoginRequiredMixin, CreateView):
    """View for composing a new email."""
    
    model = EmailComposition
    form_class = EmailCompositionForm
    template_name = 'leads/email_compose.html'
    success_url = reverse_lazy('leads:email_list')
    
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
            # TODO: Actually send the email here using the email service
            # For now, we just mark it as sent
            # Future implementation should integrate with core.services.email_backends
            logger.info(f"Email marked for sending to: {form.instance.to_emails}")
        else:
            form.instance.is_draft = True
        
        return super().form_valid(form)


class EmailListView(LoginRequiredMixin, ListView):
    """View for listing all emails (drafts and sent)."""
    
    model = EmailComposition
    template_name = 'leads/email_list.html'
    context_object_name = 'emails'
    paginate_by = 20
    
    def get_queryset(self):
        return EmailComposition.objects.filter(created_by=self.request.user)


class EmailDetailView(LoginRequiredMixin, DetailView):
    """View for viewing a single email."""
    
    model = EmailComposition
    template_name = 'leads/email_detail.html'
    context_object_name = 'email'
    
    def get_queryset(self):
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
