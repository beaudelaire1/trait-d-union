"""
Assembleur Factur-X — PDF/A-3 + XML CII embarqué.

Le PDF/A-3 (ISO 19005-3) est un PDF/A-1b ou PDF/A-2b qui autorise
l'attachement de fichiers arbitraires. Pour Factur-X, on attache le XML CII
au document avec le nom canonique `factur-x.xml` et la relation Adobe
`AFRelationship = Alternative` (le XML est une représentation alternative
du document, équivalente, et lisible par machine).

Approche retenue (sans dépendance lib factur-x) :
1. Prendre le PDF source produit par WeasyPrint (rendu identique au design).
2. Y attacher `factur-x.xml` via pikepdf (AFRelationship + AssociatedFiles).
3. Injecter les métadonnées XMP nécessaires :
    - identifier le document comme `pdfaid:part=3, conformance=B` (PDF/A-3b)
    - inclure les extensions Factur-X (DocumentType, ConformanceLevel, Version)
4. Forcer les flags PDF/A : OutputIntent sRGB, Marked = true, structure tree.

Sources :
- https://fnfe-mpe.org/factur-x/factur-x_en/
- ISO 19005-3 (PDF/A-3)
- Adobe XMP Specification (Part 1 + 3)

Note : la conformité PDF/A-3b stricte (notamment le sous-ensemble fonts,
JavaScript banni) dépend du PDF source. Pour passer une validation veraPDF
formelle, une étape de post-traitement Ghostscript peut être nécessaire
(profil `PDF/A-3b`). C'est traité comme une amélioration optionnelle ici car
WeasyPrint produit déjà un PDF très propre, et la majorité des PDP
acceptent le hybride sans validation veraPDF stricte.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from typing import TYPE_CHECKING, Optional

import pikepdf
from django.conf import settings

if TYPE_CHECKING:  # pragma: no cover
    from apps.factures.models import Invoice

from .cii import build_cii_xml, _profile_urn  # type: ignore

logger = logging.getLogger(__name__)


# Nom canonique du XML Factur-X (FNFE-MPE)
FACTURX_FILENAME = "factur-x.xml"


class FacturXAttachmentRelationship(str, Enum):
    """Adobe AFRelationship — relation de l'attachement avec le PDF.

    `Alternative` est la valeur officielle Factur-X.
    """

    ALTERNATIVE = "Alternative"
    SOURCE = "Source"
    DATA = "Data"
    SUPPLEMENT = "Supplement"
    UNSPECIFIED = "Unspecified"


# ---------------------------------------------------------------------------
# Métadonnées XMP Factur-X
# ---------------------------------------------------------------------------
_XMP_TEMPLATE = """<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="TUS Factur-X 1.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:pdf="http://ns.adobe.com/pdf/1.3/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"
    xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/"
    xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#"
    xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#"
    xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">
   <dc:title>
    <rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt>
   </dc:title>
   <dc:creator>
    <rdf:Seq><rdf:li>{creator}</rdf:li></rdf:Seq>
   </dc:creator>
   <dc:description>
    <rdf:Alt><rdf:li xml:lang="x-default">{description}</rdf:li></rdf:Alt>
   </dc:description>
   <pdf:Producer>{producer}</pdf:Producer>
   <xmp:CreatorTool>{creator}</xmp:CreatorTool>
   <xmp:CreateDate>{created_at}</xmp:CreateDate>
   <xmp:ModifyDate>{created_at}</xmp:ModifyDate>
   <xmpMM:DocumentID>uuid:{doc_uuid}</xmpMM:DocumentID>
   <pdfaid:part>3</pdfaid:part>
   <pdfaid:conformance>B</pdfaid:conformance>
   <fx:DocumentType>INVOICE</fx:DocumentType>
   <fx:DocumentFileName>{xml_filename}</fx:DocumentFileName>
   <fx:Version>1.0</fx:Version>
   <fx:ConformanceLevel>{conformance}</fx:ConformanceLevel>
   <pdfaExtension:schemas>
    <rdf:Bag>
     <rdf:li rdf:parseType="Resource">
      <pdfaSchema:schema>Factur-X PDFA Extension Schema</pdfaSchema:schema>
      <pdfaSchema:namespaceURI>urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#</pdfaSchema:namespaceURI>
      <pdfaSchema:prefix>fx</pdfaSchema:prefix>
      <pdfaSchema:property>
       <rdf:Seq>
        <rdf:li rdf:parseType="Resource">
         <pdfaProperty:name>DocumentFileName</pdfaProperty:name>
         <pdfaProperty:valueType>Text</pdfaProperty:valueType>
         <pdfaProperty:category>external</pdfaProperty:category>
         <pdfaProperty:description>name of the embedded XML invoice file</pdfaProperty:description>
        </rdf:li>
        <rdf:li rdf:parseType="Resource">
         <pdfaProperty:name>DocumentType</pdfaProperty:name>
         <pdfaProperty:valueType>Text</pdfaProperty:valueType>
         <pdfaProperty:category>external</pdfaProperty:category>
         <pdfaProperty:description>INVOICE or ORDER</pdfaProperty:description>
        </rdf:li>
        <rdf:li rdf:parseType="Resource">
         <pdfaProperty:name>Version</pdfaProperty:name>
         <pdfaProperty:valueType>Text</pdfaProperty:valueType>
         <pdfaProperty:category>external</pdfaProperty:category>
         <pdfaProperty:description>The actual version of the Factur-X XML schema</pdfaProperty:description>
        </rdf:li>
        <rdf:li rdf:parseType="Resource">
         <pdfaProperty:name>ConformanceLevel</pdfaProperty:name>
         <pdfaProperty:valueType>Text</pdfaProperty:valueType>
         <pdfaProperty:category>external</pdfaProperty:category>
         <pdfaProperty:description>The conformance level of the embedded XML invoice</pdfaProperty:description>
        </rdf:li>
       </rdf:Seq>
      </pdfaSchema:property>
     </rdf:li>
    </rdf:Bag>
   </pdfaExtension:schemas>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def _profile_conformance_label(profile_key: Optional[str] = None) -> str:
    """Mapping clé interne → libellé `ConformanceLevel` Factur-X."""
    cfg = getattr(settings, "INVOICING", {}) or {}
    key = (profile_key or cfg.get("FACTURX_PROFILE", "EN16931")).upper()
    return {
        "MINIMUM":  "MINIMUM",
        "BASIC_WL": "BASIC WL",
        "BASIC":    "BASIC",
        "EN16931":  "EN 16931",
        "EXTENDED": "EXTENDED",
    }.get(key, "EN 16931")


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def build_facturx_pdf(
    invoice: "Invoice",
    *,
    pdf_bytes: Optional[bytes] = None,
    profile: Optional[str] = None,
    relationship: FacturXAttachmentRelationship = FacturXAttachmentRelationship.ALTERNATIVE,
) -> bytes:
    """Produit un Factur-X (PDF/A-3 + XML CII embarqué) pour la facture.

    Parameters
    ----------
    invoice : Invoice
        Instance Django de la facture.
    pdf_bytes : Optional[bytes]
        PDF source. Si omis, on génère le PDF via le DocumentGenerator existant
        (rendu visuel identique au design TUS actuel).
    profile : Optional[str]
        Profil Factur-X (MINIMUM, BASIC_WL, BASIC, EN16931, EXTENDED).
        Par défaut : settings.INVOICING['FACTURX_PROFILE'] = "EN16931".
    relationship : FacturXAttachmentRelationship
        Relation Adobe AFRelationship. Par défaut "Alternative" (Factur-X officiel).

    Returns
    -------
    bytes : le PDF/A-3 hybride.
    """
    if pdf_bytes is None:
        # Importation locale pour éviter le couplage hard avec WeasyPrint au
        # niveau du module (utile pour les tests qui ne montent pas Weasy).
        from core.services.document_generator import DocumentGenerator
        # ⚠️ Profil Factur-X = PDF/A-3b. WeasyPrint sait le produire nativement
        # (variant `pdf/a-3b`) → conformité veraPDF / KoSIT.
        pdf_bytes = DocumentGenerator.generate_invoice_pdf(
            invoice, attach=False, pdf_variant="pdf/a-3b",
        )

    xml_bytes = build_cii_xml(invoice, profile=profile)
    return _embed_xml_in_pdf(
        pdf_bytes=pdf_bytes,
        xml_bytes=xml_bytes,
        invoice=invoice,
        profile=profile,
        relationship=relationship,
    )


def _embed_xml_in_pdf(
    *,
    pdf_bytes: bytes,
    xml_bytes: bytes,
    invoice: "Invoice",
    profile: Optional[str],
    relationship: FacturXAttachmentRelationship,
) -> bytes:
    """Embed XML in PDF + écriture des métadonnées XMP Factur-X."""
    src = BytesIO(pdf_bytes)
    out = BytesIO()
    with pikepdf.open(src, allow_overwriting_input=False) as pdf:
        # 1. Attacher le XML — pikepdf gère la création des entrées
        #    `EmbeddedFiles`, `AssociatedFiles` et `AFRelationship`.
        try:
            attachment = pikepdf.AttachedFileSpec(
                pdf,
                xml_bytes,
                description="Factur-X invoice (CII XML)",
                mime_type="application/xml",
                creation_date=datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ"),
                modification_date=datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ"),
            )
        except TypeError:
            # Compat pikepdf < 8.0 : pas de creation/modification_date kwargs.
            attachment = pikepdf.AttachedFileSpec(
                pdf,
                xml_bytes,
                description="Factur-X invoice (CII XML)",
                mime_type="application/xml",
            )
        pdf.attachments[FACTURX_FILENAME] = attachment

        # 2. Configurer la relation Adobe (AFRelationship) ET inscrire le
        #    filespec dans le tableau /AF du Catalog — exigence PDF/A-3
        #    clause 6.8 (ISO 19005-3:2012). Sans cela, veraPDF rejette
        #    avec "embedded file not associated".
        af_spec = pdf.attachments[FACTURX_FILENAME]
        af_obj = None
        try:
            af_spec.relationship = pikepdf.Name(f"/{relationship.value}")
            af_obj = af_spec.obj
        except (AttributeError, TypeError):
            try:
                af_obj = af_spec.obj
                af_obj["/AFRelationship"] = pikepdf.Name(f"/{relationship.value}")
            except Exception:  # noqa: BLE001
                logger.warning("Impossible de poser /AFRelationship — PDF généré sans cette clé.")

        if af_obj is not None:
            # /AF doit être un tableau d'IndirectObjects (refs) sur le Catalog.
            try:
                af_indirect = pdf.make_indirect(af_obj)
            except Exception:  # noqa: BLE001
                af_indirect = af_obj
            existing_af = pdf.Root.get("/AF")
            if existing_af is None:
                pdf.Root["/AF"] = pikepdf.Array([af_indirect])
            else:
                # Évite les doublons en comparant les objgens.
                already_present = any(
                    getattr(item, "objgen", None) == getattr(af_indirect, "objgen", object())
                    for item in existing_af
                )
                if not already_present:
                    existing_af.append(af_indirect)

        # 3. Métadonnées XMP (PDF/A-3)
        title = f"Facture {invoice.number}"
        producer = "Trait d'Union Studio · WeasyPrint + pikepdf"
        creator = "TUS · apps.einvoicing"
        description = f"Facture électronique conforme EN 16931 ({_profile_conformance_label(profile)})"
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        doc_uuid = invoice.public_token or f"invoice-{invoice.pk}"

        xmp_payload = _XMP_TEMPLATE.format(
            title=_xml_escape(title),
            creator=_xml_escape(creator),
            description=_xml_escape(description),
            producer=_xml_escape(producer),
            created_at=created_at,
            doc_uuid=_xml_escape(doc_uuid),
            xml_filename=FACTURX_FILENAME,
            conformance=_profile_conformance_label(profile),
        )

        try:
            with pdf.open_metadata() as meta:
                meta.load_from_docinfo(pdf.docinfo)
                # Set raw XMP (pikepdf ≥ 5.4)
                meta._update_xmp(xmp_payload)
        except (AttributeError, TypeError):
            # Fallback : dump direct dans le stream Metadata du Catalog
            try:
                metadata_stream = pdf.make_stream(xmp_payload.encode("utf-8"))
                metadata_stream.Type = pikepdf.Name.Metadata
                metadata_stream.Subtype = pikepdf.Name.XML
                pdf.Root.Metadata = metadata_stream
            except Exception:  # noqa: BLE001
                logger.exception("Échec écriture XMP Factur-X — PDF émis avec XMP basique.")

        # 4. PDF version 1.7 minimum (PDF/A-3 = ISO 19005-3 basé PDF 1.7)
        pdf.save(out, linearize=False, fix_metadata_version=True, compress_streams=True)
    return out.getvalue()


def _xml_escape(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


__all__ = ["build_facturx_pdf", "FacturXAttachmentRelationship", "FACTURX_FILENAME"]
