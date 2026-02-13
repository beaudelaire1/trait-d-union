"""
Tests pour la génération de PDFs (devis / factures).
Valide que les templates et le service DocumentGenerator fonctionnent.
"""
import pytest
from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User

from apps.devis.models import Client, Quote, QuoteItem
from apps.factures.models import Invoice, InvoiceItem
from services.models import Service
from core.services.document_generator import DocumentGenerator


@pytest.mark.django_db
class TestQuotePDFGeneration(TestCase):
    """Test la génération de PDF pour les devis."""
    
    def setUp(self):
        """Crée les données de test."""
        self.client_obj = Client.objects.create(
            full_name="John Doe",
            email="john@example.com",
            phone="0612345678",
            address_line="123 Rue de la Paix",
            city="Cayenne",
            zip_code="97300"
        )
        
        self.service = Service.objects.create(
            title="Développement Web",
            description="Service de développement web",
            price=Decimal("1000.00")
        )
        
        self.quote = Quote.objects.create(
            client=self.client_obj,
            service=self.service,
            message="Devis pour projet web",
            issue_date=date.today(),
            status=Quote.QuoteStatus.DRAFT,
        )
        
        # Ajouter un item
        self.quote_item = QuoteItem.objects.create(
            quote=self.quote,
            service=self.service,
            description="Développement de site web responsive",
            quantity=Decimal("1.00"),
            unit_price=Decimal("2500.00"),
            tax_rate=Decimal("20.00")
        )
        
        self.quote.compute_totals()
    
    def test_quote_pdf_generation_success(self):
        """Teste que le PDF du devis est généré sans erreur."""
        try:
            pdf_bytes = self.quote.generate_pdf(attach=False)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert b"PDF" in pdf_bytes[:10] or b"%" in pdf_bytes[:10]  # Vérifier que c'est du PDF
        except Exception as e:
            self.fail(f"PDF generation failed: {str(e)}")
    
    def test_quote_pdf_with_missing_data(self):
        """Teste la génération avec données partielles (branding None)."""
        # Même avec des données incomplètes, le PDF doit générer
        quote = Quote.objects.create(
            client=self.client_obj,
            number="DEV-2026-TESTX",
            issue_date=date.today(),
            status=Quote.QuoteStatus.DRAFT,
        )
        
        try:
            pdf_bytes = quote.generate_pdf(attach=False)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
        except Exception as e:
            self.fail(f"PDF generation with missing data failed: {str(e)}")


@pytest.mark.django_db
class TestInvoicePDFGeneration(TestCase):
    """Test la génération de PDF pour les factures."""
    
    def setUp(self):
        """Crée les données de test."""
        self.client_obj = Client.objects.create(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="0687654321",
            address_line="456 Avenue des Arts",
            city="Toulouse",
            zip_code="31000"
        )
        
        self.invoice = Invoice.objects.create(
            number="FAC-2026-001",
            issue_date=date.today(),
            status=Invoice.InvoiceStatus.DRAFT,
            total_ht=Decimal("2500.00"),
            tva=Decimal("500.00"),
            total_ttc=Decimal("3000.00"),
        )
        
        # Ajouter un item
        self.invoice_item = InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service de développement",
            quantity=1,
            unit_price=Decimal("2500.00"),
            tax_rate=Decimal("20.00")
        )
    
    def test_invoice_pdf_generation_success(self):
        """Teste que le PDF de la facture est généré sans erreur."""
        try:
            pdf_bytes = self.invoice.generate_pdf(attach=False)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert b"PDF" in pdf_bytes[:10] or b"%" in pdf_bytes[:10]
        except Exception as e:
            self.fail(f"Invoice PDF generation failed: {str(e)}")
    
    def test_invoice_pdf_with_quote_reference(self):
        """Teste la génération avec référence de devis."""
        quote = Quote.objects.create(
            client=self.client_obj,
            number="DEV-2026-001",
            issue_date=date.today(),
            status=Quote.QuoteStatus.INVOICED,
            total_ttc=Decimal("3000.00")
        )
        
        invoice = Invoice.objects.create(
            quote=quote,
            number="FAC-2026-002",
            issue_date=date.today(),
            status=Invoice.InvoiceStatus.SENT,
            total_ht=Decimal("2500.00"),
            tva=Decimal("500.00"),
            total_ttc=Decimal("3000.00"),
        )
        
        try:
            pdf_bytes = invoice.generate_pdf(attach=False)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
        except Exception as e:
            self.fail(f"Invoice with quote reference PDF generation failed: {str(e)}")


@pytest.mark.django_db
class TestDocumentGeneratorFontPatching(TestCase):
    """Test que le patch des fonts Google fonctionne."""
    
    def test_font_patching_removes_google_import(self):
        """Teste que _patch_fonts supprime l'import Google Fonts."""
        html = """
        <html>
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;....');
        body { font-family: 'Inter'; }
        </style>
        </html>
        """
        
        patched = DocumentGenerator._patch_fonts(html)
        assert "fonts.googleapis.com" not in patched
        assert "@font-face" in patched
        assert "Inter" in patched
    
    def test_font_patching_preserves_content(self):
        """Teste que patch_fonts préserve le contenu HTML."""
        html = "<html><body>Test content</body></html>"
        patched = DocumentGenerator._patch_fonts(html)
        assert "Test content" in patched
