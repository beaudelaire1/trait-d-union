"""
Document Generator Service
Génère les PDFs pour les devis et factures avec la charte graphique TUS.
"""
import logging
from io import BytesIO
from typing import TYPE_CHECKING

from django.conf import settings
from django.template.loader import render_to_string

if TYPE_CHECKING:
    from apps.devis.models import Quote
    from apps.factures.models import Invoice

logger = logging.getLogger(__name__)


# Branding par défaut pour TUS
DEFAULT_BRANDING = {
    'name': 'Trait d\'Union Studio',
    'tagline': 'Architecture Digitale & Design',
    'address': '258 Av Justin Catayée Rte de la Madeleine',
    'city': 'Cayenne',
    'zip_code': '97300',
    'region': 'Guyane française',
    'country': 'Guyane française',
    'phone': '+594 695 35 80 41',
    'email': 'contact@traitdunion.it',
    'website': 'https://traitdunion.it',
    'siret': '908 264 112 00016',
    'tva_intra': '',
    'iban': 'FR76 1980 6001 8940 2584 2883 094',
    'bic': 'AGRIMQMX',
    'logo_url': '/static/img/tus-logo.png',
}


class DocumentGenerator:
    """Service de génération de documents PDF."""
    
    @classmethod
    def get_branding(cls) -> dict:
        """Récupère les informations de branding depuis settings ou défaut."""
        return getattr(settings, 'INVOICE_BRANDING', DEFAULT_BRANDING)
    
    @classmethod
    def _render_pdf(cls, html_content: str) -> bytes:
        """Convertit du HTML en PDF avec fallback pour les fonts offline."""
        try:
            from weasyprint import HTML, CSS
        except Exception as exc:
            raise ImportError(
                "WeasyPrint n'est pas installé. "
                "Installez-le avec: pip install weasyprint"
            ) from exc

        # Remplacer Google Fonts par fallback CSS local pour éviter timeouts sur Render
        html_content = cls._patch_fonts(html_content)
        
        try:
            html = HTML(string=html_content, base_url=settings.BASE_DIR)
            pdf_bytes = html.write_pdf(timeout=30)  # 30s timeout pour Render
            return pdf_bytes
        except Exception as e:
            logger.error(f"Erreur WeasyPrint: {e}", exc_info=True)
            raise RuntimeError(f"Erreur lors de la génération du PDF: {str(e)}") from e
    
    @classmethod
    def _patch_fonts(cls, html_content: str) -> str:
        """Remplace les imports Google Fonts par CSS avec fallbacks locaux."""
        # Remplacer l'import Google Fonts par un CSS local
        google_fonts_import = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');"
        
        # CSS fallback utilisant des fonts système
        local_fonts_css = """
        @font-face {
            font-family: 'Inter';
            font-weight: 400;
            src: local('Inter'), local('Helvetica Neue'), system-ui, -apple-system, sans-serif;
        }
        @font-face {
            font-family: 'Space Grotesk';
            font-weight: 600;
            font-weight: 700;
            src: local('Space Grotesk'), local('Arial'), system-ui, -apple-system, sans-serif;
        }
        """
        
        html_content = html_content.replace(
            google_fonts_import,
            local_fonts_css
        )
        return html_content
    
    @classmethod
    def generate_quote_pdf(cls, quote: "Quote", attach: bool = True) -> bytes:
        """Génère le PDF d'un devis.
        
        Args:
            quote: Instance du devis
            attach: Si True, attache le PDF au devis
            
        Returns:
            Contenu PDF en bytes
        """
        from django.core.files.base import ContentFile
        
        branding = cls.get_branding()
        
        # Recalculer les totaux si nécessaire
        if hasattr(quote, 'compute_totals'):
            try:
                quote.compute_totals()
            except Exception:
                pass
        
        # Préparer les informations de signature si le devis est signé
        signature_info = None
        if quote.signed_at and quote.signature_audit_trail:
            audit = quote.signature_audit_trail
            signature_info = {
                'signed_at': quote.signed_at,
                'signer_name': audit.get('signer', {}).get('name', 'N/A'),
                'signer_email': audit.get('signer', {}).get('email', 'N/A'),
                'ip_address': audit.get('technical', {}).get('ip_address', 'N/A'),
                'user_agent': audit.get('technical', {}).get('user_agent', 'N/A'),
                'signature_hash': audit.get('technical', {}).get('signature_hash', 'N/A')[:16] + '...' if audit.get('technical', {}).get('signature_hash') else 'N/A',
                'integrity_hash': audit.get('integrity_hash', 'N/A')[:16] + '...' if audit.get('integrity_hash') else 'N/A',
                'legal_statement': audit.get('legal', {}).get('statement', ''),
                'has_signature_image': bool(quote.signature_image),
            }
        
        # Préparer le contexte
        context = {
            'quote': quote,
            'branding': branding,
            'items': list(quote.quote_items.all()) if hasattr(quote, 'quote_items') else [],
            'total_lettres': quote.amount_letter() if hasattr(quote, 'amount_letter') else None,
            'signature_info': signature_info,
        }
        
        # Render le template
        html_content = render_to_string('devis/quote_pdf.html', context)
        
        # Générer le PDF
        pdf_bytes = cls._render_pdf(html_content)
        
        # Attacher au devis si demandé
        if attach:
            filename = f"devis_{quote.number}.pdf"
            quote.pdf.save(filename, ContentFile(pdf_bytes), save=True)
        
        return pdf_bytes
    
    @classmethod
    def generate_invoice_pdf(cls, invoice: "Invoice", attach: bool = True) -> bytes:
        """Génère le PDF d'une facture.
        
        Args:
            invoice: Instance de la facture
            attach: Si True, attache le PDF à la facture
            
        Returns:
            Contenu PDF en bytes
        """
        from django.core.files.base import ContentFile
        
        branding = cls.get_branding()
        
        # Recalculer les totaux si nécessaire
        if hasattr(invoice, 'compute_totals'):
            try:
                invoice.compute_totals()
            except Exception:
                pass
        
        # Préparer le contexte
        context = {
            'invoice': invoice,
            'branding': branding,
            'items': list(invoice.invoice_items.all()) if hasattr(invoice, 'invoice_items') else [],
            'total_lettres': invoice.amount_letter() if hasattr(invoice, 'amount_letter') else None,
        }
        
        # Render le template
        html_content = render_to_string('factures/invoice_pdf.html', context)
        
        # Générer le PDF
        pdf_bytes = cls._render_pdf(html_content)
        
        # Attacher à la facture si demandé
        if attach:
            filename = f"facture_{invoice.number}.pdf"
            invoice.pdf.save(filename, ContentFile(pdf_bytes), save=True)
        
        return pdf_bytes
