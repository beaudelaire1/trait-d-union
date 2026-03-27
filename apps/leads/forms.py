"""Forms for the leads app."""
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import SplitPhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from .models import Lead, ProjectTypeChoice, BudgetRange


class ContactForm(forms.ModelForm):
    """Main contact form with dynamic fields based on project type."""

    phone = SplitPhoneNumberField(label="Téléphone", required=False)

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
            'phone',
            'message',
            'budget',
            'existing_url',
            'attachment',
            'honeypot',
        ]
        widgets = {
            'honeypot': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['phone'] = '+33'

        # Styling du champ téléphone (SplitPhoneNumberField utilise 2 sous-widgets)
        common_classes = (
            "bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-xl "
            "px-4 py-3 text-tus-white placeholder-tus-white/50 focus:bg-tus-white/10 "
            "focus:border-tus-blue/50 focus:ring-1 focus:ring-tus-blue/30 "
            "focus:shadow-[0_0_20px_rgba(11,45,255,0.15)] transition-all duration-300"
        )
        # Select indicatif pays
        self.fields['phone'].widget.widgets[0].attrs.update({
            'class': f"{common_classes} cursor-pointer w-[140px] md:w-[160px] flex-shrink-0 text-sm",
        })
        # Champ numéro
        self.fields['phone'].widget.widgets[1].attrs.update({
            'class': f"{common_classes} flex-1 w-full",
            'placeholder': '6 12 34 56 78',
        })

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