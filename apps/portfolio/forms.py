"""Forms pour le portfolio admin."""
from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from .models import Project

# Widget TinyMCE réutilisable pour les champs de chapitre
_tinymce_widget = TinyMCE(attrs={'cols': 80, 'rows': 20})


class ProjectAdminForm(forms.ModelForm):
    """Form custom pour l'admin avec TinyMCE sur les chapitres."""

    objective = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 20}),
        label='Objectif',
        help_text='Ch.01 — Pourquoi : contexte et objectif du projet',
    )
    solution = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 20}),
        label='Solution',
        help_text='Ch.02 — Défi technique : problème résolu et approche',
    )
    strategy = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 20}),
        required=False,
        label='Stratégie',
        help_text='Ch.03 — Stratégie : méthodologie et processus. Laissez vide = timeline par défaut.',
    )
    result = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 20}),
        label='Résultat',
        help_text='Ch.04 — Résultat : impact et livrables',
    )

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
