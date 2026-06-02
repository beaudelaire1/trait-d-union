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

    # ── Ch.05 — note UI/UX manuelle ────────────────────────────────────
    # Champ proxy non persistant : il lit / écrit dans Project.audit_results['ui_ux']
    # via `__init__` et `save()` ci-dessous, pour ne pas créer une colonne dédiée
    # alors que le JSONField existe déjà.
    ui_ux_score = forms.IntegerField(
        required=False, min_value=0, max_value=100,
        label='Ch.05 — Note UI/UX TUS (sur 100)',
        help_text=(
            'Note attribuée par l\'équipe TUS sur la qualité design (hiérarchie, '
            'lisibilité, parcours, cohérence). Laissez vide tant qu\'aucune note '
            'n\'a été déterminée — la carte affichera "en cours d\'évaluation".'
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir le champ depuis audit_results['ui_ux']['score']
        if self.instance and self.instance.pk:
            ui_ux = (self.instance.audit_results or {}).get('ui_ux') or {}
            self.fields['ui_ux_score'].initial = ui_ux.get('score')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Synchroniser le score saisi avec audit_results['ui_ux']
        score = self.cleaned_data.get('ui_ux_score')
        results = dict(instance.audit_results or {})
        if score is not None:
            from datetime import datetime, timezone as _tz
            results['ui_ux'] = {
                'score': int(score),
                'measured_at': datetime.now(_tz.utc).isoformat(timespec='seconds'),
            }
        else:
            results.pop('ui_ux', None)
        instance.audit_results = results
        if commit:
            instance.save()
        return instance

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
