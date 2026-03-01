"""Forms for the leads app."""
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Lead, ProjectTypeChoice, BudgetRange


class ContactForm(forms.ModelForm):
    """Main contact form with dynamic fields based on project type."""

    # Magic bytes signatures for file type validation
    _MAGIC_SIGNATURES = {
        'application/pdf': [b'%PDF'],
        'application/msword': [b'\xd0\xcf\x11\xe0'],  # OLE2 compound document
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [b'PK\x03\x04'],  # ZIP (OOXML)
    }

    class Meta:
        model = Lead
        fields = [
            'name',
            'email',
            'project_type',
            'message',
            'budget',
            'existing_url',
            'attachment',
            'honeypot',
        ]
        widgets = {
            'honeypot': forms.HiddenInput(),
        }

    def clean_honeypot(self) -> str:
        value = self.cleaned_data.get('honeypot', '')
        if value:
            raise ValidationError('Spam détecté.')
        return value

    def clean_attachment(self):  # type: ignore[override]
        file = self.cleaned_data.get('attachment')
        if not file:
            return file
        max_size = 5 * 1024 * 1024  # 5 Mo
        if file.size > max_size:
            raise ValidationError('Le fichier ne doit pas dépasser 5 Mo.')
        allowed_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        if file.content_type not in allowed_types:
            raise ValidationError('Seuls les fichiers PDF, DOC et DOCX sont acceptés.')

        # 🛡️ SECURITY: Validate magic bytes to prevent content-type spoofing
        file.seek(0)
        header = file.read(8)
        file.seek(0)
        signatures = self._MAGIC_SIGNATURES.get(file.content_type, [])
        if signatures and not any(header.startswith(sig) for sig in signatures):
            raise ValidationError('Le contenu du fichier ne correspond pas à son type déclaré.')

        return file


class DynamicFieldsForm(forms.Form):
    """Partial form returned via HTMX to render fields depending on project type."""

    project_type = forms.ChoiceField(choices=ProjectTypeChoice.choices)
    # additional dynamic fields would be defined in the view