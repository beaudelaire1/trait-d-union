"""Forms for the Simulateur app (email capture)."""
from __future__ import annotations

from django import forms

from .models import SimulatorReport


class SimulatorReportForm(forms.ModelForm):
    """Formulaire de capture email en fin de simulateur.

    Le champ `website` est un honeypot anti-bot (doit rester vide).
    """

    # Budget global des graphiques (base64) transmis au PDF. Les graphiques
    # exportés en haute résolution pèsent 100-500KB pièce : au-delà du budget
    # on écarte les excédentaires plutôt que de refuser tout le rapport.
    MAX_CHARTS_BYTES = 4_000_000
    # Cap du snapshot réellement persisté en base (graphiques déjà retirés).
    MAX_SNAPSHOT_BYTES = 1_000_000

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
        # Les graphiques sont extraits AVANT tout contrôle de taille : ils ne
        # sont pas persistés en DB (transient, passés au service PDF) et ne
        # doivent donc jamais faire échouer la demande de rapport. C'était la
        # cause de l'erreur générique au téléchargement : 4 graphiques haute
        # résolution suffisaient à dépasser le cap et à rejeter la requête.
        charts = snapshot.pop('_charts', None) or snapshot.pop('charts', None)
        if charts:
            self._transient_charts = self._trim_charts(charts)
        # Ce qui reste (saisies + KPI, du texte) doit rester raisonnable.
        import json
        if len(json.dumps(snapshot)) > self.MAX_SNAPSHOT_BYTES:
            raise forms.ValidationError(
                "Les données du simulateur sont trop volumineuses. "
                "Relancez le calcul puis réessayez."
            )
        return snapshot

    @classmethod
    def _trim_charts(cls, charts: object) -> list:
        """Tronque la liste de graphiques à ``MAX_CHARTS_BYTES``.

        Conserve les graphiques dans l'ordre tant que le budget cumulé n'est
        pas dépassé ; les suivants sont ignorés silencieusement. Le rapport
        est ainsi toujours généré, éventuellement avec moins de visuels.
        """
        if not isinstance(charts, list):
            return []
        kept: list = []
        total = 0
        for chart in charts:
            if not isinstance(chart, dict):
                continue
            data_url = chart.get('data_url')
            weight = len(data_url) if isinstance(data_url, str) else 0
            if total + weight > cls.MAX_CHARTS_BYTES:
                continue
            total += weight
            kept.append(chart)
        return kept
