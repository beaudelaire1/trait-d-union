#!/usr/bin/env python
"""
Génère les PDFs de devis et facture en local
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

import django
django.setup()

from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from apps.devis.models import Quote
from apps.factures.models import Invoice
from decimal import Decimal

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'pdfs_test_v2')


def nombre_en_lettres(n):
    """Convertit un nombre en lettres (français)"""
    unites = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
              'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf']
    dizaines = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 'soixante', 'quatre-vingt', 'quatre-vingt']
    
    def _convert_moins_de_100(n):
        if n < 20:
            return unites[n]
        dizaine, unite = divmod(n, 10)
        if dizaine == 7 or dizaine == 9:
            # 70-79 et 90-99
            base = dizaines[dizaine]
            reste = (10 if dizaine == 7 else 10) + unite
            if reste == 11:
                return base + '-et-onze' if dizaine == 7 else base + '-onze'
            return base + '-' + unites[reste]
        if unite == 0:
            return dizaines[dizaine] + ('s' if dizaine == 8 else '')
        if unite == 1 and dizaine < 8:
            return dizaines[dizaine] + '-et-un'
        return dizaines[dizaine] + '-' + unites[unite]
    
    def _convert_moins_de_1000(n):
        if n < 100:
            return _convert_moins_de_100(n)
        centaine, reste = divmod(n, 100)
        if centaine == 1:
            prefix = 'cent'
        else:
            prefix = unites[centaine] + ' cent'
        if reste == 0:
            return prefix + ('s' if centaine > 1 else '')
        return prefix + ' ' + _convert_moins_de_100(reste)
    
    def _convert(n):
        if n == 0:
            return 'zéro'
        if n < 1000:
            return _convert_moins_de_1000(n)
        if n < 1000000:
            millier, reste = divmod(n, 1000)
            if millier == 1:
                prefix = 'mille'
            else:
                prefix = _convert_moins_de_1000(millier) + ' mille'
            if reste == 0:
                return prefix
            return prefix + ' ' + _convert_moins_de_1000(reste)
        if n < 1000000000:
            million, reste = divmod(n, 1000000)
            if million == 1:
                prefix = 'un million'
            else:
                prefix = _convert_moins_de_1000(million) + ' millions'
            if reste == 0:
                return prefix
            return prefix + ' ' + _convert(reste)
        return str(n)
    
    return _convert(int(n))


def montant_en_lettres(montant):
    """Convertit un montant en euros en lettres"""
    if isinstance(montant, Decimal):
        montant = float(montant)
    
    euros = int(montant)
    centimes = int(round((montant - euros) * 100))
    
    result = nombre_en_lettres(euros) + ' euro' + ('s' if euros > 1 else '')
    
    if centimes > 0:
        result += ' et ' + nombre_en_lettres(centimes) + ' centime' + ('s' if centimes > 1 else '')
    
    return result.capitalize()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'pdfs_test_v2')

# Informations de branding Trait d'Union Studio
BRANDING = {
    'name': "Trait d'Union Studio",
    'tagline': 'Design & Développement',
    'address': '123 Rue de la Création',
    'zip_code': '75001',
    'city': 'Paris',
    'region': 'France',
    'phone': '+33 1 23 45 67 89',
    'email': 'contact@traitdunion.studio',
    'siret': '123 456 789 00012',
    'siren': '123 456 789',
    'tva_intra': 'FR12 123456789',
    'rcs': 'Paris B 123 456 789',
    'bank_name': 'Banque Nationale de Paris',
    'iban': 'FR76 1234 5678 9012 3456 7890 123',
    'bic': 'BNPAFRPP',
}

def generate_quote_pdf():
    """Génère le PDF du dernier devis"""
    quote = Quote.objects.last()
    if not quote:
        print("❌ Aucun devis trouvé")
        return None
    
    print(f"📄 Génération PDF Devis: {quote.number}")
    
    # Contexte pour le template
    context = {
        'quote': quote,
        'items': quote.items.all(),
        'client': quote.client,
        'branding': BRANDING,
        'total_lettres': montant_en_lettres(quote.total_ttc),
    }
    
    # Rendu HTML
    html_content = render_to_string('devis/quote_pdf.html', context)
    
    # Génération PDF
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f'{quote.number}_v6.pdf')
    
    HTML(string=html_content).write_pdf(output_path)
    
    print(f"   ✅ Sauvegardé: {output_path}")
    return output_path


def generate_invoice_pdf():
    """Génère le PDF de la dernière facture"""
    invoice = Invoice.objects.last()
    if not invoice:
        print("❌ Aucune facture trouvée")
        return None
    
    print(f"📄 Génération PDF Facture: {invoice.number}")
    
    # Le client vient du devis lié
    client = invoice.quote.client if invoice.quote else None
    
    # Contexte pour le template
    context = {
        'invoice': invoice,
        'items': invoice.invoice_items.all(),
        'client': client,
        'branding': BRANDING,
        'total_lettres': montant_en_lettres(invoice.total_ttc),
    }
    
    # Rendu HTML
    html_content = render_to_string('factures/invoice_pdf.html', context)
    
    # Génération PDF
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f'{invoice.number}_v6.pdf')
    
    HTML(string=html_content).write_pdf(output_path)
    
    print(f"   ✅ Sauvegardé: {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("📁 GÉNÉRATION PDFs EN LOCAL")
    print("=" * 60)
    print(f"\n📂 Dossier de sortie: {OUTPUT_DIR}\n")
    
    quote_path = generate_quote_pdf()
    print()
    invoice_path = generate_invoice_pdf()
    
    print("\n" + "=" * 60)
    print("✅ TERMINÉ!")
    print("=" * 60)
    
    if quote_path or invoice_path:
        print(f"\n📂 Ouvrez le dossier: {OUTPUT_DIR}")
        
        # Ouvrir le dossier automatiquement sur Windows
        import subprocess
        subprocess.Popen(f'explorer "{OUTPUT_DIR}"')
