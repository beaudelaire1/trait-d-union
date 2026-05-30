"""Génère une démo Factur-X complète sur disque pour audit visuel.

Usage :
    python manage.py demo_facturx --out .dist/demo

Produit dans le dossier de sortie :
- factur-x.xml          ← XML CII (lisible par humain)
- demo-invoice.pdf      ← PDF/A-3 hybride (Factur-X)
- extracted.xml         ← XML CII RE-extrait depuis le PDF (preuve d'embed)
- report.txt            ← Vérifications automatiques

Aucune écriture en base : crée des objets en transaction qui est rollback
à la sortie, donc aucun effet de bord sur les données réelles.
"""

from __future__ import annotations

import os
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pikepdf
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Génère une démo Factur-X (PDF/A-3 + XML CII) pour audit."

    def add_arguments(self, parser):
        parser.add_argument("--out", default=".dist/demo_facturx", help="Dossier de sortie.")

    def handle(self, *args, **options):
        from apps.clients.models import ClientProfile
        from apps.einvoicing.builders.cii import build_cii_xml
        from apps.einvoicing.builders.facturx import (
            FACTURX_FILENAME,
            build_facturx_pdf,
        )
        from apps.factures.models import Invoice, InvoiceItem

        out_dir = Path(options["out"]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # On utilise une transaction qui sera rollback : zéro pollution DB.
        with transaction.atomic():
            sid = transaction.savepoint()
            client = ClientProfile.objects.create(
                full_name="Maxime Dupont",
                company_name="Mairie de Cayenne",
                email="commande@mairie-cayenne.fr",
                is_business=True,
                country_code="FR",
                siren="218000037",  # SIRET réel ville de Cayenne (test)
                siret="21800003700017",
                tva_number="",
                address_line="1 rue de Rémire",
                city="Cayenne",
                zip_code="97300",
                peppol_id="0009:21800003700017",
            )

            # 1. Créer un Quote accepté (chaîne réelle TUS : devis → facture).
            from apps.devis.models import Quote, QuoteItem
            from apps.devis.services import create_invoice_from_quote
            quote = Quote.objects.create(
                client=client,
                status=Quote.QuoteStatus.ACCEPTED,
            )
            QuoteItem.objects.create(
                quote=quote,
                description="Refonte du site institutionnel — phase design",
                quantity=Decimal("1"),
                unit_price=Decimal("4500.00"),
                tax_rate=Decimal("0"),
            )
            QuoteItem.objects.create(
                quote=quote,
                description="Accompagnement éditorial",
                quantity=Decimal("8"),
                unit_price=Decimal("125.00"),
                tax_rate=Decimal("0"),
            )
            quote.compute_totals()

            # 2. Convertir en facture via le service métier — lie quote → invoice.
            result = create_invoice_from_quote(quote)
            invoice = result.invoice
            invoice.buyer_reference = "MARCHE-2026-WEB-042"
            invoice.purchase_order_ref = "BC-CAY-2026-018"
            invoice.contract_ref = "CONV-CAY-2026-12"
            invoice.transaction_type = "SERVICES"
            invoice.vat_payment_basis = "NA"
            invoice.save()

            # 3. Aligner les codes EN 16931 sur le régime Guyane (art. 294)
            from apps.einvoicing.legal import (
                get_active_regime,
                get_default_vat_category,
                get_default_vatex_code,
                get_legal_tva_mention,
            )
            invoice.invoice_items.update(
                vat_category_code=get_default_vat_category(),
                vat_exemption_reason_code=get_default_vatex_code(),
                unit_code="LS",
            )
            invoice.compute_totals()
            legal_mention = get_legal_tva_mention()
            regime = get_active_regime()

            # 1. XML CII pur
            xml_bytes = build_cii_xml(invoice)
            xml_path = out_dir / "factur-x.xml"
            xml_path.write_bytes(xml_bytes)

            # 2. PDF/A-3 hybride. Pipeline réel : WeasyPrint rend le PDF visuel
            #    (template factures/invoice_pdf.html avec la charte TUS), puis
            #    on embarque le XML CII pour produire le Factur-X.
            facturx_bytes = invoice.generate_pdf(attach=False, format="facturx")
            pdf_path = out_dir / "demo-invoice.pdf"
            pdf_path.write_bytes(facturx_bytes)

            # 3. Extraction du XML embarqué — preuve d'intégrité round-trip
            with pikepdf.open(BytesIO(facturx_bytes)) as pdf:
                if FACTURX_FILENAME not in pdf.attachments:
                    raise RuntimeError("Le PDF/A-3 ne contient pas factur-x.xml")
                extracted_xml = pdf.attachments[FACTURX_FILENAME].get_file().read_bytes()
                metadata_obj = pdf.Root.get("/Metadata")
                xmp = bytes(metadata_obj.read_bytes()) if metadata_obj else b""
                af_obj = pdf.attachments[FACTURX_FILENAME].obj
                af_relationship = str(af_obj.get("/AFRelationship", ""))
            (out_dir / "extracted.xml").write_bytes(extracted_xml)

            # 4. Rapport texte
            report = [
                "=== Démo Factur-X — Trait d'Union Studio ===",
                f"Régime fiscal   : {regime}",
                f"Mention légale  : {legal_mention}",
                f"Devis source    : {quote.number} (statut : {quote.status})",
                f"Numéro facture  : {invoice.number}",
                f"Date émission   : {invoice.issue_date}",
                f"Client          : {client.company_name} (SIRET {client.siret})",
                f"Acheteur ref    : {invoice.buyer_reference}",
                f"PO ref          : {invoice.purchase_order_ref}",
                f"Total HT        : {invoice.total_ht} EUR",
                f"TVA             : {invoice.tva} EUR ({legal_mention or 'TVA collectée'})",
                f"Total TTC       : {invoice.total_ttc} EUR",
                "",
                "=== Vérifications PDF/A-3 + Factur-X ===",
                f"AFRelationship  : {af_relationship}",
                f"XML attaché     : factur-x.xml ({len(extracted_xml)} octets)",
                f"XMP métadonnées : {len(xmp)} octets — pdfaid:part=3 présent : {b'pdfaid:part>3' in xmp}",
                f"XML round-trip  : identique entre source et extraction : {extracted_xml == xml_bytes}",
                f"Réf devis (BT-14) dans XML : {('SellerOrderReferencedDocument' in extracted_xml.decode('utf-8'))}",
                "",
                f"Fichiers générés dans : {out_dir}",
            ]
            (out_dir / "report.txt").write_text("\n".join(report), encoding="utf-8")

            self.stdout.write("\n".join(report))
            self.stdout.write(self.style.SUCCESS(f"\nOK — {out_dir}"))

            transaction.savepoint_rollback(sid)
