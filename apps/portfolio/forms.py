"""Forms pour le portfolio admin."""
from django import forms
from django.contrib import admin
from .models import Project


class ProjectAdminForm(forms.ModelForm):
    """Form custom pour l'admin avec aide contextuelle."""
    
    class Meta:
        model = Project
        fields = '__all__'
        help_texts = {
            'technologies': (
                '⚠️ ATTENTION : Saisir les TECHNOLOGIES (langages, frameworks, BDD), '
                'PAS les fonctionnalités métier.<br>'
                'Format JSON liste : <code>["Django", "PostgreSQL", "Tailwind CSS", "HTMX", "Cloudinary"]</code><br>'
                '✅ BON : Django, React, PostgreSQL, Redis, Docker<br>'
                '❌ MAUVAIS : Gestion de stock, Paiement en ligne, Chat en temps réel'
            )
        }
        widgets = {
            'technologies': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '["Django", "PostgreSQL", "Tailwind CSS"]',
                'style': 'font-family: monospace;'
            })
        }
