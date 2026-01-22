"""Forms for email composition."""
from __future__ import annotations

from django import forms
from .email_models import EmailComposition, EmailTemplate


class EmailCompositionForm(forms.ModelForm):
    """Form for composing emails with rich text editor."""
    
    class Meta:
        model = EmailComposition
        fields = ['to_emails', 'cc_emails', 'bcc_emails', 'subject', 'body_html', 'template_used']
        widgets = {
            'to_emails': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-3 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white placeholder-tus-white/40 focus:border-tus-blue focus:ring-2 focus:ring-tus-blue/20 transition-all',
                'placeholder': 'destinataire@example.com, autre@example.com'
            }),
            'cc_emails': forms.Textarea(attrs={
                'rows': 1,
                'class': 'w-full px-4 py-2 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white placeholder-tus-white/40 focus:border-tus-blue focus:ring-2 focus:ring-tus-blue/20 transition-all',
                'placeholder': 'copie@example.com (optionnel)'
            }),
            'bcc_emails': forms.Textarea(attrs={
                'rows': 1,
                'class': 'w-full px-4 py-2 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white placeholder-tus-white/40 focus:border-tus-blue focus:ring-2 focus:ring-tus-blue/20 transition-all',
                'placeholder': 'copie.cachee@example.com (optionnel)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white placeholder-tus-white/40 focus:border-tus-blue focus:ring-2 focus:ring-tus-blue/20 transition-all',
                'placeholder': 'Sujet de l\'email'
            }),
            'body_html': forms.Textarea(attrs={
                'rows': 15,
                'class': 'tinymce w-full px-4 py-3 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white',
            }),
            'template_used': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-tus-white/5 border border-tus-white/10 rounded-xl text-tus-white focus:border-tus-blue focus:ring-2 focus:ring-tus-blue/20 transition-all',
            }),
        }
        labels = {
            'to_emails': 'Destinataires',
            'cc_emails': 'CC (Copie)',
            'bcc_emails': 'BCC (Copie cachée)',
            'subject': 'Sujet',
            'body_html': 'Message',
            'template_used': 'Template pré-défini (optionnel)',
        }
