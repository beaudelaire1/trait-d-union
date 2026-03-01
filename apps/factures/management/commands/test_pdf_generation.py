"""
Commande pour tester la génération de PDF en local.
Usage: python manage.py test_pdf_generation
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from decimal import Decimal
from datetime import date

from apps.devis.models import Client, Quote, QuoteItem
from apps.factures.models import Invoice, InvoiceItem
from services.models import Service


class Command(BaseCommand):
    help = "Teste la génération de PDFs pour devis et factures."
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--quote',
            action='store_true',
            help='Génère un PDF de devis test.',
        )
        parser.add_argument(
            '--invoice',
            action='store_true',
            help='Génère un PDF de facture test.',
        )
        parser.add_argument(
            '--both',
            action='store_true',
            help='Génère les deux PDFs (devis et facture).',
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        run_quote = options.get('quote', False)
        run_invoice = options.get('invoice', False)
        run_both = options.get('both', False)
        
        if run_both:
            run_quote = run_invoice = True
        
        if not run_quote and not run_invoice:
            self.stdout.write(
                self.style.WARNING(
                    "Usage: python manage.py test_pdf_generation [--quote|--invoice|--both]"
                )
            )
            return
        
        # Créer client test
        client = self._create_test_client()
        
        if run_quote:
            self.test_quote_pdf(client)
        
        if run_invoice:
            self.test_invoice_pdf(client)
        
        self.stdout.write(
            self.style.SUCCESS("✓ Tests de PDFs terminés avec succès !")
        )
    
    def _create_test_client(self):
        """Crée un client de test."""
        client, created = Client.objects.get_or_create(
            email="test@traitdunion.it",
            defaults={
                "full_name": "Test Client",
                "phone": "+594695358041",
                "address_line": "Test Address",
                "city": "Test City",
                "zip_code": "97300",
            }
        )
        return client
    
    def test_quote_pdf(self, client):
        """Teste la génération d'un PDF de devis."""
        self.stdout.write("\n📄 Test: Génération PDF Devis...")
        
        try:
            # Créer ou récupérer un service
            service, _ = Service.objects.get_or_create(
                title="Test Service",
                defaults={
                    "description": "Service de test",
                    "price": Decimal("1000.00")
                }
            )
            
            # Créer un devis
            quote = Quote.objects.create(
                client=client,
                service=service,
                message="Devis de test pour vérifier la génération PDF",
                issue_date=date.today(),
                status=Quote.QuoteStatus.DRAFT,
            )
            
            # Ajouter une ligne
            QuoteItem.objects.create(
                quote=quote,
                service=service,
                description="Service de test",
                quantity=Decimal("2.00"),
                unit_price=Decimal("500.00"),
                tax_rate=Decimal("20.00")
            )
            
            quote.compute_totals()
            
            # Générer le PDF
            pdf_bytes = quote.generate_pdf(attach=False)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Devis #{quote.number}: PDF généré ({len(pdf_bytes)} bytes)"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur lors de la génération du PDF devis: {str(e)}")
            )
            raise
    
    def test_invoice_pdf(self, client):
        """Teste la génération d'un PDF de facture."""
        self.stdout.write("\n💵 Test: Génération PDF Facture...")
        
        try:
            # Créer une facture
            invoice = Invoice.objects.create(
                number="FAC-TEST-001",
                issue_date=date.today(),
                status=Invoice.InvoiceStatus.DRAFT,
                total_ht=Decimal("1000.00"),
                tva=Decimal("200.00"),
                total_ttc=Decimal("1200.00"),
            )
            
            # Ajouter une ligne
            InvoiceItem.objects.create(
                invoice=invoice,
                description="Ligne de facture de test",
                quantity=2,
                unit_price=Decimal("500.00"),
                tax_rate=Decimal("20.00")
            )
            
            # Générer le PDF
            pdf_bytes = invoice.generate_pdf(attach=False)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Facture #{invoice.number}: PDF généré ({len(pdf_bytes)} bytes)"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur lors de la génération du PDF facture: {str(e)}")
            )
            raise
