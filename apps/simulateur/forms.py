"""Forms for the Simulateur app (email capture)."""
from __future__ import annotations

from django import forms

from .models import SimulatorReport


class SimulatorReportForm(forms.ModelForm):
    """Formulaire de capture email en fin de simulateur.

    Le champ `website` est un honeypot anti-bot (doit rester vide).
    """

    website = forms.CharField(required=False, widget=forms.HiddenInput)
    consent = forms.BooleanField(required=True, error_messages={
        'required': "Vous devez accepter de recevoir le rapport.",
    })

    class Meta:
        model = SimulatorReport
        fields = ['email', 'name', 'company', 'tool_slug', 'tool_name', 'snapshot']
        widgets = {
            'snapshot': forms.HiddenInput(),
            'tool_slug': forms.HiddenInput(),
            'tool_name': forms.HiddenInput(),
        }

    def clean_website(self) -> str:
        value = self.cleaned_data.get('website', '')
        if value:
            raise forms.ValidationError("Spam détecté.")
        return value

    def clean_email(self) -> str:
        email = self.cleaned_data['email'].strip().lower()
        # Bloquer les domaines jetables les plus évidents.
        disposable_suffixes = (
            'mailinator.com', 'guerrillamail.com', 'tempmail.com',
            'yopmail.com', 'trashmail.com', '10minutemail.com',
        )
        for suffix in disposable_suffixes:
            if email.endswith('@' + suffix):
                raise forms.ValidationError("Merci d'utiliser un email professionnel.")
        return email

    def clean_snapshot(self) -> dict:
        snapshot = self.cleaned_data.get('snapshot') or {}
        if not isinstance(snapshot, dict):
            raise forms.ValidationError("Format de données invalide.")
        # Limiter la taille (anti-abus payload).
        import json
        if len(json.dumps(snapshot)) > 20_000:
            raise forms.ValidationError("Données trop volumineuses.")
        return snapshot
