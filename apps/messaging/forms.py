"""Forms for the messaging app."""
from django import forms
from .models import Prospect, EmailCampaign, EmailTemplate


class ProspectForm(forms.ModelForm):
    """Form for creating/editing prospects."""
    
    class Meta:
        model = Prospect
        fields = [
            'contact_name',
            'company_name',
            'email',
            'phone',
            'website',
            'sector',
            'activity_description',
            'pain_points',
            'status',
            'source',
            'priority',
            'notes',
            'tags',
            'next_follow_up',
        ]
        widgets = {
            'contact_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom complet du contact'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': "Nom de l'entreprise"
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@exemple.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+594 694 XX XX XX'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://www.exemple.com'
            }),
            'sector': forms.Select(attrs={'class': 'form-select'}),
            'activity_description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': "Décrivez l'activité du prospect..."
            }),
            'pain_points': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Points de douleur identifiés, besoins...'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 5
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Notes internes...'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'guyane, btp, urgent'
            }),
            'next_follow_up': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            }),
        }


class ProspectQuickEmailForm(forms.Form):
    """Quick email form for prospect detail page."""
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="Template par défaut",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 4,
            'placeholder': 'Message personnalisé (optionnel)...'
        })
    )


class CampaignForm(forms.ModelForm):
    """Form for creating email campaigns."""
    
    class Meta:
        model = EmailCampaign
        fields = ['name', 'template', 'scheduled_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom de la campagne'
            }),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_at': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            }),
        }


class ProspectImportForm(forms.Form):
    """Form for importing prospects from CSV."""
    
    csv_file = forms.FileField(
        label='Fichier CSV',
        help_text='Format: email, contact_name, company_name, phone, sector, source',
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.csv'
        })
    )
