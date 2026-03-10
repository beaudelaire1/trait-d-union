"""Forms for the client portal."""
import re

from django import forms
from django.core.validators import RegexValidator

from .models import ClientProfile, ClientDocument


# 🛡️ BANK-GRADE: Server-side SIRET / TVA intra validators
_SIRET_VALIDATOR = RegexValidator(
    regex=r'^\d{14}$',
    message="Le SIRET doit contenir exactement 14 chiffres.",
)
_TVA_INTRA_VALIDATOR = RegexValidator(
    regex=r'^FR\d{11}$',
    message="Le numéro de TVA intracommunautaire doit être au format FR + 11 chiffres (ex: FR12345678901).",
)


class ClientProfileForm(forms.ModelForm):
    """Form for editing client profile."""
    
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre prénom'
        })
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre nom'
        })
    )
    
    class Meta:
        model = ClientProfile
        fields = [
            'company_name', 'phone', 'address',
            'siret', 'tva_number', 'avatar', 'email_notifications'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom de votre entreprise'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+33 6 12 34 56 78'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Votre adresse complète'
            }),
            'siret': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '12345678900012',
                'maxlength': '14',
                'pattern': r'\d{14}',
            }),
            'tva_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'FR12345678901',
                'maxlength': '13',
                'pattern': r'FR\d{11}',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_siret(self):
        """🛡️ BANK-GRADE: Validate SIRET format (14 digits, strip spaces)."""
        value = self.cleaned_data.get('siret', '').strip()
        if not value:
            return value
        # Strip spaces/dashes for user convenience
        value = re.sub(r'[\s\-.]', '', value)
        _SIRET_VALIDATOR(value)
        return value

    def clean_avatar(self):
        """🛡️ BANK-GRADE: Validate avatar file (type, size, magic bytes, Pillow verify)."""
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar

        # 1) Taille max 2 Mo
        if hasattr(avatar, 'size') and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError("L'avatar ne doit pas dépasser 2 Mo.")

        # 2) Extension autorisée
        import os
        ext = os.path.splitext(avatar.name)[1].lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.webp'}:
            raise forms.ValidationError(
                f"Extension non autorisée ({ext}). "
                "Formats acceptés : .jpg, .jpeg, .png, .webp"
            )

        # 3) Magic bytes
        _MAGIC = {
            '.jpg': [b'\xff\xd8\xff'],
            '.jpeg': [b'\xff\xd8\xff'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.webp': [b'RIFF'],
        }
        avatar.seek(0)
        header = avatar.read(12)
        avatar.seek(0)
        signatures = _MAGIC.get(ext, [])
        if signatures and not any(header.startswith(sig) for sig in signatures):
            raise forms.ValidationError(
                "Le contenu du fichier ne correspond pas au format déclaré."
            )

        # 4) Vérification Pillow (détecte les fichiers tronqués/malveillants)
        try:
            from PIL import Image
            img = Image.open(avatar)
            img.verify()
            avatar.seek(0)
        except Exception:
            raise forms.ValidationError(
                "Le fichier ne semble pas être une image valide."
            )

        return avatar

    def clean_tva_number(self):
        """🛡️ BANK-GRADE: Validate TVA intracommunautaire format (FR + 11 digits)."""
        value = self.cleaned_data.get('tva_number', '').strip()
        if not value:
            return value
        value = re.sub(r'[\s\-.]', '', value).upper()
        _TVA_INTRA_VALIDATOR(value)
        return value
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        # Update User model fields
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        if commit:
            profile.user.save()
            profile.save()
            self._save_m2m()
        else:
            # Expose save_m2m so callers (e.g. Django admin) can call it later
            old_save_m2m = self.save_m2m

            def save_m2m():
                old_save_m2m()
                profile.user.save()

            self.save_m2m = save_m2m
        return profile


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""

    # Limites de sécurité
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.zip', '.svg', '.ai', '.psd'}

    # 🛡️ SECURITY: Magic bytes signatures for file type validation (anti content-type spoofing)
    _MAGIC_SIGNATURES = {
        '.pdf': [b'%PDF'],
        '.doc': [b'\xd0\xcf\x11\xe0'],  # OLE2 compound document
        '.docx': [b'PK\x03\x04'],  # ZIP (OOXML)
        '.png': [b'\x89PNG\r\n\x1a\n'],
        '.jpg': [b'\xff\xd8\xff'],
        '.jpeg': [b'\xff\xd8\xff'],
        '.zip': [b'PK\x03\x04', b'PK\x05\x06'],
        '.svg': [b'<?xml', b'<svg'],
        # .ai and .psd have complex headers — skip magic check for these
    }

    class Meta:
        model = ClientDocument
        fields = ['title', 'document_type', 'file', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du document'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.png,.jpg,.jpeg,.zip,.svg,.ai,.psd'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Notes additionnelles (optionnel)'
            }),
        }

    def clean_file(self):
        """Valide le type, la taille et les magic bytes du fichier uploadé."""
        import os
        from core.utils import validate_file_magic
        uploaded = self.cleaned_data.get('file')
        if not uploaded:
            return uploaded
        # Vérifier la taille
        max_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if uploaded.size > max_bytes:
            raise forms.ValidationError(
                f"Le fichier dépasse la taille maximale de {self.MAX_FILE_SIZE_MB} Mo."
            )
        # Vérifier l'extension
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"Type de fichier non autorisé ({ext}). "
                f"Extensions acceptées : {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # 🛡️ SECURITY: Validate magic bytes to prevent content-type spoofing
        if not validate_file_magic(uploaded, ext):
            raise forms.ValidationError(
                'Le contenu du fichier ne correspond pas à son type déclaré.'
            )

        return uploaded



class ClientRequestForm(forms.Form):
    """Formulaire simplifié pour les demandes client (devis/facture)."""
    
    REQUEST_TYPES = [
        ('quote', 'Demande de devis'),
        ('invoice', 'Question sur une facture'),
        ('project', 'Suivi de projet'),
        ('other', 'Autre demande'),
    ]
    
    request_type = forms.ChoiceField(
        label="Type de demande",
        choices=REQUEST_TYPES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio'
        })
    )
    subject = forms.CharField(
        label="Sujet",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Décrivez brièvement votre demande'
        })
    )
    description = forms.CharField(
        label="Description",
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 5,
            'placeholder': 'Détaillez votre demande...'
        })
    )
    budget_range = forms.ChoiceField(
        label="Budget estimé (optionnel)",
        required=False,
        choices=[
            ('', 'Non spécifié'),
            ('500-1500', '500€ - 1 500€'),
            ('1500-3000', '1 500€ - 3 000€'),
            ('3000-5000', '3 000€ - 5 000€'),
            ('5000-10000', '5 000€ - 10 000€'),
            ('10000+', '10 000€+'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    deadline = forms.DateField(
        label="Échéance souhaitée (optionnel)",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )
    attachment = forms.FileField(
        label="Pièce jointe (optionnel)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.pdf,.doc,.docx,.png,.jpg,.jpeg,.zip'
        })
    )


class NewClientRequestForm(forms.Form):
    """Formulaire validé pour les nouvelles demandes client (QuoteRequest)."""

    phone = forms.CharField(
        label="Téléphone",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+33 6 12 34 56 78'
        })
    )
    address = forms.CharField(
        label="Adresse",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre adresse'
        })
    )
    message = forms.CharField(
        label="Description de votre besoin",
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 5,
            'placeholder': 'Décrivez votre projet…'
        })
    )
    preferred_date = forms.DateField(
        label="Date souhaitée (optionnel)",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )
