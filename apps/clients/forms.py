"""Forms for the client portal."""
from django import forms
from .models import ClientProfile, ClientDocument


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
                'placeholder': '123 456 789 00012'
            }),
            'tva_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'FR12345678901'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
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
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        # Update User model fields
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        if commit:
            profile.user.save()
            profile.save()
        return profile


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    
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
