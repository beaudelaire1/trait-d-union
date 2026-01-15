"""Formulaires pour la soumission de devis."""

from decimal import Decimal
from typing import Optional

from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from services.models import Service
from .models import Client, Quote, QuoteRequest, QuoteRequestPhoto, QuoteItem


phone_validator = RegexValidator(
    regex=r'^(?:(?:\+|00)594|0)[1-9][0-9]{8}$',
    message="Entrez un numéro de téléphone valide (Guyane)"
)


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class DevisForm(forms.Form):
    """Formulaire simple pour demander un devis."""

    full_name = forms.CharField(
        label="Nom complet",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Nom complet",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "input",
                "placeholder": "Email",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    phone = forms.CharField(
        label="Téléphone",
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Téléphone",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Ville",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    zip_code = forms.CharField(
        label="Code postal",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Code postal",
                "required": True,
                "aria-required": "true",
            }
        ),
    )

    address = forms.CharField(
        label="Adresse",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Adresse (quartier, rue, ...)",
            }
        ),
    )

    preferred_date = forms.DateField(
        label="Date souhaitée (optionnel)",
        required=False,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
    )

    service = forms.ModelChoiceField(
        label="Service souhaité",
        queryset=Service.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.Select(attrs={"class": "select"}),
    )

    message = forms.CharField(
        label="Votre demande",
        widget=forms.Textarea(
            attrs={
                "class": "textarea",
                "placeholder": "Décrivez votre besoin (surface, fréquence, contraintes...) ",
                "rows": 4,
            }
        ),
    )

    SERVICE_TYPES = [
        ("nettoyage", "Nettoyage"),
        ("espaces_verts", "Espaces verts"),
        ("renovation", "Rénovation"),
    ]

    URGENCY_LEVELS = [
        ("standard", "Standard (sous 1 semaine)"),
        ("express", "Express (48 h)"),
        ("immediat", "Immédiat (24 h)"),
    ]

    service_type = forms.ChoiceField(
        label="Type de service",
        choices=SERVICE_TYPES,
        widget=forms.Select(attrs={"class": "select", "required": True}),
    )

    surface = forms.IntegerField(
        label="Surface (m²)",
        min_value=1,
        widget=forms.HiddenInput(),
        required=False,
    )

    urgency = forms.ChoiceField(
        label="Urgence",
        choices=URGENCY_LEVELS,
        widget=forms.Select(attrs={"class": "select", "required": True}),
    )

    images = forms.FileField(
        label="Photos (optionnel)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"multiple": False}),
    )

    def save(self) -> Quote:
        cleaned = self.cleaned_data
        service: Optional[Service] = cleaned.get("service")

        message = cleaned.get("message", "")
        extra_lines = []

        if cleaned.get("surface"):
            extra_lines.append(f"Surface : {cleaned['surface']} m²")

        if cleaned.get("urgency"):
            extra_lines.append(
                f"Urgence : {dict(self.URGENCY_LEVELS).get(cleaned['urgency'])}"
            )

        if cleaned.get("service_type"):
            extra_lines.append(
                f"Type de service : {dict(self.SERVICE_TYPES).get(cleaned['service_type'])}"
            )

        if extra_lines:
            message = "\n".join(extra_lines) + "\n\n" + message

        client = Client.objects.create(
            full_name=cleaned["full_name"],
            email=cleaned["email"],
            phone=cleaned["phone"],
            city=cleaned["city"],
            zip_code=cleaned["zip_code"],
        )

        quote = Quote.objects.create(
            client=client,
            service=service,
            message=message,
            total_ht=Decimal("0.00"),
            tva=Decimal("0.00"),
            total_ttc=Decimal("0.00"),
        )

        return quote


class QuoteRequestForm(forms.ModelForm):
    """Formulaire public pour déposer une demande de devis."""

    photos = forms.FileField(
        label=_("Photos (optionnel)"),
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
    )

    def clean_photos(self):
        files = self.files.getlist("photos")
        if not files:
            return None

        if len(files) > 5:
            raise forms.ValidationError("Maximum 5 fichiers.")

        for f in files:
            if f.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Chaque fichier doit faire au maximum 5 Mo.")

        self.cleaned_data["photos_list"] = files
        # conserve une valeur compat (ModelForm) même si on utilise photos_list
        return files[0]

    class Meta:
        model = QuoteRequest
        fields = ["client_name", "email", "phone", "address", "message", "preferred_date"]


class QuoteAdminForm(forms.ModelForm):
    """Formulaire d'édition des métadonnées d'un devis côté back-office."""

    class Meta:
        model = Quote
        fields = [
            "client",
            "quote_request",
            "status",
            "issue_date",
            "valid_until",
            "message",
            "notes",
        ]


class QuoteItemForm(forms.ModelForm):
    """Formulaire pour une ligne de devis dans l'éditeur dynamique."""

    class Meta:
        model = QuoteItem
        fields = ["service", "description", "quantity", "unit_price", "tax_rate"]


class QuoteValidationCodeForm(forms.Form):
    code = forms.CharField(
        label="Code de confirmation",
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Ex : 123456",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        ),
    )
