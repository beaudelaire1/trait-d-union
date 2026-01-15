"""
Service dédié à la génération de factures PDF pour l'application
``factures``.  Cette implémentation reprend la logique auparavant
présente dans le modèle ``Invoice`` et la déplace dans une classe
distincte pour respecter le principe de responsabilité unique.

La classe ``PDFInvoiceGenerator`` prend une instance d'``Invoice`` en
paramètre et expose une méthode ``generate_pdf`` qui renvoie le PDF
sous forme d'octets et, si souhaité, l'attache au modèle.

Les fonctions utilitaires comme ``_wrap_text`` ou ``_resolve_logo_path``
sont déclarées en haut du module afin de ne plus encombrer le modèle.
La résolution du logo est simplifiée : si le chemin est relatif,
il est résolu par rapport au répertoire ``static`` via ``Path``.  Si
``settings.INVOICE_BRANDING['logo_path']`` fournit un chemin absolu,
celui‑ci est utilisé tel quel.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings
from django.core.files.base import ContentFile


def _num2words_fr(v: Decimal) -> str:
    """Import tardif de .utils.num2words_fr, repli numérique FR si absent."""
    try:
        from ..utils import num2words_fr as _n2w  # type: ignore
        return _n2w(v)
    except Exception:
        return str(v).replace(".", ",")


def _money(value: Decimal) -> str:
    return f"{value:.2f} €".replace(".", ",")


def _safe_get(obj, attr, default=""):
    try:
        val = getattr(obj, attr)
        return val if val is not None else default
    except Exception:
        return default


def _wrap_text(text: str, max_width: float, pdfmetrics, font_name: str, font_size: int) -> List[str]:
    words = (text or "").split()
    if not words:
        return [""]
    lines: List[str] = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _resolve_logo_path(path: Optional[str]) -> Optional[str]:
    """
    Résout le chemin du logo en utilisant ``pathlib``.  Si le chemin
    fourni est absolu et existe, il est retourné tel quel.  Sinon on
    suppose qu'il est relatif au dossier ``static`` du projet (défini
    par ``STATICFILES_DIRS`` ou ``STATIC_ROOT``) et on renvoie le
    chemin absolu correspondant si le fichier existe.  Cette fonction
    ne tente plus de deviner le logo dans ``MEDIA_ROOT``.
    """
    if not path:
        return None
    try:
        p = Path(path)
        # Chemin absolu
        if p.is_absolute():
            return str(p) if p.exists() else None
        # Si le chemin commence par "static:", retirer ce préfixe
        rel = path.replace("static:", "").lstrip("/\\")
        # Dossier static
        static_dirs = []
        # Préférer STATICFILES_DIRS si défini, sinon STATIC_ROOT
        if hasattr(settings, "STATICFILES_DIRS") and settings.STATICFILES_DIRS:
            static_dirs.extend([Path(d) for d in settings.STATICFILES_DIRS])
        if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
            static_dirs.append(Path(settings.STATIC_ROOT))
        for directory in static_dirs:
            candidate = directory / rel
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass
    return None


def _get_branding() -> dict:
    cfg = getattr(settings, "INVOICE_BRANDING", {}) or {}
    addr_lines = cfg.get("address_lines")
    if not addr_lines:
        addr = cfg.get("address")
        if addr:
            addr_lines = [line.strip() for line in str(addr).splitlines() if line.strip()]
        else:
            addr_lines = []

    return {
        "name": cfg.get("name", "Nettoyage Express"),
        "tagline": cfg.get("tagline", "Espaces verts, nettoyage, peinture, bricolage"),
        "email": cfg.get("email", "contact@exemple.fr"),
        "phone": cfg.get("phone", ""),
        "website": cfg.get("website", ""),
        "address_lines": addr_lines,
        "siret": cfg.get("siret", ""),
        "tva_intra": cfg.get("tva_intra", ""),
        "iban": cfg.get("iban", ""),
        "bic": cfg.get("bic", ""),
        "logo_path": cfg.get("logo_path", None),
        "font_path": cfg.get("font_path", None),
        "font_bold_path": cfg.get("font_bold_path", None),
        "payment_qr_data_template": cfg.get("payment_qr_data_template", ""),
        "default_notes": cfg.get("default_notes", ""),
        "payment_terms": cfg.get("payment_terms", ""),
    }


class PDFInvoiceGenerator:
    """Générateur de PDF pour les instances de ``Invoice``."""

    def __init__(self, invoice: "Invoice") -> None:
        self.invoice = invoice

    def generate_pdf(self, attach: bool = True) -> bytes:
        """
        Générez un PDF professionnel à partir de l'instance d'``Invoice``.

        Cette méthode est une adaptation de l'ancienne méthode
        ``Invoice.generate_pdf``.  Elle réutilise les instructions et
        fonctions internes en réaffectant la variable ``self`` à
        l'instance de facture afin de conserver la compatibilité avec
        les variables ``self.number``, ``self.total_ht``, etc.  Le
        paramètre ``attach`` permet, comme auparavant, de sauvegarder le
        fichier dans le champ ``pdf`` de l'instance.

        Parameters
        ----------
        attach : bool
            Si ``True``, le PDF sera enregistré dans
            ``invoice.pdf``.  Sinon seuls les octets sont retournés.

        Returns
        -------
        bytes
            Le contenu binaire du PDF généré.
        """
        invoice = self.invoice
        # Rediriger ``self`` vers l'objet facture pour conserver la
        # compatibilité des références dans le code hérité.  Toute
        # variable "self" dans le code copié ci‑dessous désigne donc
        # l'instance ``Invoice`` plutôt que le générateur.
        self = invoice  # type: ignore
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.graphics.barcode import qr as qrmod
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF
        except ImportError as exc:
            raise ImportError("ReportLab n'est pas installé. `pip install reportlab`") from exc

        branding = _get_branding()

        # Polices (optionnel)
        font_main = "Helvetica"
        font_bold = "Helvetica-Bold"
        if branding.get("font_path"):
            try:
                pdfmetrics.registerFont(TTFont("Brand-Regular", branding["font_path"]))
                font_main = "Brand-Regular"
            except Exception:
                pass
        if branding.get("font_bold_path"):
            try:
                pdfmetrics.registerFont(TTFont("Brand-Bold", branding["font_bold_path"]))
                font_bold = "Brand-Bold"
            except Exception:
                pass

        # Canvas + couleurs
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        c.setTitle(f"Facture {self.number}")  # type: ignore
        c.setAuthor(branding["name"])
        c.setSubject("Facture")

        COLOR_PRIMARY = colors.HexColor("#0B5D46")
        COLOR_ACCENT = colors.HexColor("#F5F7F9")
        COLOR_BORDER = colors.HexColor("#E5E7EB")
        COLOR_TEXT = colors.black
        COLOR_MUTED = colors.HexColor("#6B7280")

        # Marges & interlignes
        M_LEFT, M_RIGHT, M_BOTTOM = 20 * mm, 20 * mm, 18 * mm
        CONTENT_W = width - M_LEFT - M_RIGHT
        LINE_H_TABLE = 5.5 * mm
        LINE_H_TEXT = 5.0 * mm

        # Tableau (170 mm total = 210-20-20)
        x0 = M_LEFT
        col_w_desc = 90 * mm
        col_w_qty = 18 * mm
        col_w_unit = 24 * mm
        col_w_tax = 18 * mm
        col_w_ttc = 20 * mm
        x1 = x0 + col_w_desc
        x2 = x1 + col_w_qty
        x3 = x2 + col_w_unit
        x4 = x3 + col_w_tax
        x5 = x4 + col_w_ttc
        TABLE_W = x5 - x0

        # --- Filigrane de statut
        def _wm():
            label_map = {
                "paid": "PAYÉE",
                "draft": "BROUILLON",
                "overdue": "EN RETARD",
                "partial": "PARTIELLE",
                "sent": "ENVOYÉE",
                "demo": "DEVIS",
            }
            label = label_map.get(self.status, "FACTURE")  # type: ignore
            c.saveState()
            c.setFillColor(colors.HexColor("#EEEEEE"))
            c.setFont(font_bold, 60)
            c.translate(width / 2, height / 2)
            c.rotate(35)
            c.drawCentredString(0, 0, label)
            c.restoreState()

        # --- Bandeau haut + logo + cartouche Total TTC (ABAISSÉ)
        def _topbar(include_total_card: bool):
            c.setFillColor(COLOR_PRIMARY)
            c.rect(0, height - 6 * mm, width, 6 * mm, fill=1, stroke=0)

            # Logo fiable
            logo_path = _resolve_logo_path(branding.get("logo_path"))
            logo_ok, logo_w = False, 0
            if logo_path:
                try:
                    if logo_path.lower().endswith(".svg"):
                        from svglib.svglib import svg2rlg  # type: ignore
                        drawing = svg2rlg(logo_path)
                        max_h = 30 * mm
                        scale = max_h / max(drawing.height or 1, 1)
                        drawing.scale(scale, scale)
                        renderPDF.draw(drawing, c, M_LEFT, height - (max_h + 8 * mm))
                        logo_w = drawing.width * scale
                        logo_ok = True
                    else:
                        img = ImageReader(logo_path)
                        iw, ih = img.getSize()
                        max_h = 30 * mm
                        w = max_h * (iw / max(ih, 1))
                        c.drawImage(
                            img,
                            M_LEFT,
                            height - (max_h + 8 * mm),
                            width=w,
                            height=max_h,
                            mask="auto",
                            preserveAspectRatio=True,
                        )
                        logo_w = w
                        logo_ok = True
                except Exception:
                    logo_ok = False

            # Marque + tagline + email
            tx = M_LEFT + (logo_w + 8 * mm if logo_ok else 0)
            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 16)
            c.drawString(tx, height - 20 * mm, branding["name"])
            c.setFont(font_main, 10)
            c.setFillColor(COLOR_MUTED)
            c.drawString(tx, height - 26 * mm, branding["tagline"])
            if branding["email"]:
                c.drawString(tx, height - 26 * mm - LINE_H_TEXT, branding["email"])

            # Bloc facture (droite)
            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 12)
            c.drawRightString(width - M_RIGHT, height - 19 * mm, f"Facture {self.number}")  # type: ignore
            c.setFont(font_main, 9)
            c.drawRightString(width - M_RIGHT, height - 25 * mm, f"Date : {self.issue_date.strftime('%d/%m/%Y')}")  # type: ignore
            if self.due_date:  # type: ignore
                c.drawRightString(
                    width - M_RIGHT,
                    height - 25 * mm - LINE_H_TEXT,
                    f"Échéance : {self.due_date.strftime('%d/%m/%Y')}",
                )
            if self.quote:  # type: ignore
                qn = getattr(self.quote, "number", None) or getattr(self.quote, "reference", None) or "—"  # type: ignore
                c.drawRightString(
                    width - M_RIGHT,
                    height - 25 * mm - 2 * LINE_H_TEXT,
                    f"Devis : {qn}",
                )

            # Cartouche Total TTC ABBAISSÉ (cy = height - 72*mm)
            if include_total_card:
                c.setFillColor(COLOR_ACCENT)
                cw, ch = 64 * mm, 20 * mm
                cx, cy = width - M_RIGHT - cw, height - 65 * mm  # << abaissé pour ne pas recouvrir le header
                c.roundRect(cx, cy, cw, ch, 3 * mm, fill=1, stroke=0)
                c.setFillColor(COLOR_TEXT)
                c.setFont(font_main, 9)
                c.drawString(cx + 4 * mm, cy + ch - 7 * mm, "Total TTC")
                c.setFont(font_bold, 16)
                c.drawRightString(cx + cw - 4 * mm, cy + 7 * mm, _money(self.total_ttc))  # type: ignore

        # --- Panneaux Émetteur / Client
        def _parties(y: float) -> float:
            ch = 30 * mm
            colw = (CONTENT_W - 6 * mm) / 2

            # Émetteur
            c.setFillColor(COLOR_ACCENT)
            c.roundRect(M_LEFT, y - ch, colw, ch, 2 * mm, fill=1, stroke=0)
            c.setFillColor(COLOR_TEXT)
            # Section title
            c.setFont(font_bold, 12)
            c.drawString(M_LEFT + 4 * mm, y - 6 * mm, "Émetteur")
            # Branding details
            brand = _get_branding()
            yy = y - 11 * mm
            # Nom de l'entreprise (si disponible)
            if brand.get("name"):
                c.setFont(font_bold, 11)
                c.drawString(M_LEFT + 4 * mm, yy, brand["name"])
                yy -= LINE_H_TEXT
                c.setFont(font_main, 11)
            # Adresse (chaque ligne)
            for line in brand.get("address_lines", []):
                c.drawString(M_LEFT + 4 * mm, yy, line)
                yy -= LINE_H_TEXT
            # Coordonnées de contact
            if brand.get("phone"):
                c.drawString(M_LEFT + 4 * mm, yy, brand["phone"])
                yy -= LINE_H_TEXT
            # Ne pas afficher l'e‑mail par défaut, sauf si aucune autre
            # coordonnée n'est fournie.
            if brand.get("email") and not brand.get("phone"):
                c.drawString(M_LEFT + 4 * mm, yy, brand["email"])
                yy -= LINE_H_TEXT
            if brand.get("website"):
                c.drawString(M_LEFT + 4 * mm, yy, brand["website"])
                yy -= LINE_H_TEXT
            c.setFillColor(COLOR_MUTED)
            if brand.get("tva_intra"):
                c.drawString(M_LEFT + 4 * mm, yy, f"TVA {brand['tva_intra']}")

            # Client
            cx = M_LEFT + colw + 6 * mm
            c.setFillColor(COLOR_ACCENT)
            c.roundRect(cx, y - ch, colw, ch, 2 * mm, fill=1, stroke=0)
            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 12)
            c.drawString(cx + 4 * mm, y - 6 * mm, "Client")
            c.setFont(font_main, 11)
            yy = y - 11 * mm
            cli = self.quote.client if self.quote else None  # type: ignore
            if cli:
                c.drawString(cx + 4 * mm, yy, _safe_get(cli, "full_name", "Client"))  # type: ignore
                yy -= LINE_H_TEXT
                em = _safe_get(cli, "email", "")  # type: ignore
                ph = _safe_get(cli, "phone", "")  # type: ignore
                if em:
                    c.drawString(cx + 4 * mm, yy, em)
                    yy -= LINE_H_TEXT
                if ph:
                    c.drawString(cx + 4 * mm, yy, ph)
                    yy -= LINE_H_TEXT
                addr = ", ".join(
                    s
                    for s in [
                        _safe_get(cli, "address_line1", ""),  # type: ignore
                        _safe_get(cli, "address_line2", ""),  # type: ignore
                        _safe_get(cli, "postal_code", ""),  # type: ignore
                        _safe_get(cli, "city", ""),  # type: ignore
                    ]
                    if s
                )
                if addr:
                    c.drawString(cx + 4 * mm, yy, addr)
            else:
                c.drawString(cx + 4 * mm, yy, "Client inconnu")

            return y - ch - 10 * mm

        # --- En-tête tableau
        def _thead(y: float) -> float:
            c.setFillColor(colors.HexColor("#F3F4F6"))
            c.rect(x0, y - 8 * mm, TABLE_W, 8 * mm, fill=1, stroke=0)
            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 11)
            c.drawString(x0 + 2 * mm, y - 5.5 * mm, "Description")
            c.drawRightString(x2 - 2 * mm, y - 5.5 * mm, "Quantité")
            c.drawRightString(x3 - 2 * mm, y - 5.5 * mm, "PU HT")
            c.drawRightString(x4 - 2 * mm, y - 5.5 * mm, "TVA %")
            c.drawRightString(x5 - 2 * mm, y - 5.5 * mm, "Montant TTC")
            c.setStrokeColor(COLOR_BORDER)
            c.setLineWidth(0.3)
            c.line(x0, y - 8 * mm, x5, y - 8 * mm)
            return y - 8 * mm

        # --- Footer (par page)
        def _footer():
            c.setFont(font_main, 7)
            c.setFillColor(COLOR_MUTED)
            left = branding["name"]
            if branding.get("tva_intra"):
                left += f" • TVA {branding['tva_intra']}"
            c.drawString(M_LEFT, M_BOTTOM - 2 * mm, left)
            right = []
            if branding.get("iban"):
                right.append(f"IBAN {branding['iban']}")
            if branding.get("bic"):
                right.append(f"BIC {branding['bic']}")
            right.append(f"Page {c.getPageNumber()}")
            c.drawRightString(width - M_RIGHT, M_BOTTOM - 2 * mm, " • ".join(right))

        # --- Saut de page
        def _maybe_new(y: float, need: float, repeat_header: bool = True) -> float:
            if y - need < M_BOTTOM + 34 * mm:
                _footer()
                c.showPage()
                _wm()
                _topbar(include_total_card=False)
                y2 = height - 60 * mm
                if repeat_header:
                    y2 = _thead(y2)
                return y2
            return y

        # --- Corps du tableau
        def _tbody(y: float) -> float:
            from reportlab.pdfbase import pdfmetrics as _pm  # type: ignore
            c.setFont(font_main, 9)
            zebra = False

            for it in self.items:  # type: ignore
                desc = (it.description or "").strip()
                lines = _wrap_text(desc, (x1 - x0) - 4 * mm, _pm, font_main, 9)
                row_h = max(LINE_H_TABLE * max(1, len(lines)), 7 * mm)
                y = _maybe_new(y, row_h, True)

                if zebra:
                    c.setFillColor(COLOR_ACCENT)
                    c.rect(x0, y - row_h, TABLE_W, row_h, fill=1, stroke=0)

                c.setFillColor(COLOR_TEXT)
                base_y = y - 3.6 * mm
                cy = base_y
                for ln in lines:
                    c.drawString(x0 + 2 * mm, cy, ln)
                    cy -= LINE_H_TABLE

                c.drawRightString(x2 - 2 * mm, base_y, str(it.quantity))
                c.drawRightString(x3 - 2 * mm, base_y, f"{it.unit_price:.2f}")
                c.drawRightString(x4 - 2 * mm, base_y, f"{it.tax_rate:.2f}")
                c.drawRightString(x5 - 2 * mm, base_y, f"{it.total_ttc:.2f}")

                c.setStrokeColor(COLOR_BORDER)
                c.setLineWidth(0.25)
                c.line(x0, y - row_h, x5, y - row_h)
                for xv in (x0, x1, x2, x3, x4, x5):
                    if xv in (x0, x5):
                        c.setStrokeColor(COLOR_TEXT)
                    else:
                        c.setStrokeColor(COLOR_PRIMARY)
                    c.setLineWidth(0.3)
                    c.line(xv, y, xv, y - row_h)

                y -= row_h
                zebra = not zebra
            return y

        # --- Récap + décomposition TVA + QR + montant en lettres
        def _vat_and_summary(y: float) -> float:
            vat_map: Dict[Decimal, Dict[str, Decimal]] = {}
            total_ht_pre_discount = Decimal("0.00")
            for it in self.items:  # type: ignore
                r = it.tax_rate
                vat_map.setdefault(r, {"base": Decimal("0.00"), "vat": Decimal("0.00")})
                vat_map[r]["base"] += it.total_ht
                vat_map[r]["vat"] += it.total_tva
                total_ht_pre_discount += it.total_ht

            y = _maybe_new(y, 42 * mm, False)

            rl, rv = x4 - 8 * mm, x5 - 2 * mm
            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 9)
            if self.discount and total_ht_pre_discount > 0:  # type: ignore
                c.drawRightString(rl, y, "Sous-total HT :")
                c.drawRightString(rv, y, _money(total_ht_pre_discount))
                y -= LINE_H_TEXT
                c.setFont(font_main, 9)
                c.drawRightString(rl, y, "Remise :")
                c.drawRightString(rv, y, f"- {_money(self.discount)}")  # type: ignore
                y -= LINE_H_TEXT
                c.setFont(font_main, 9)
                c.drawRightString(rl, y, "Net HT :")
                c.drawRightString(rv, y, _money(self.total_ht))  # type: ignore
                y -= LINE_H_TEXT
            else:
                c.drawRightString(rl, y, "Sous-total HT :")
                c.drawRightString(rv, y, _money(self.total_ht))  # type: ignore
                y -= LINE_H_TEXT

            c.setFont(font_main, 9)
            c.drawRightString(rl, y, "TVA :")
            c.drawRightString(rv, y, _money(self.tva))  # type: ignore
            y -= LINE_H_TEXT

            for rate, comp in sorted(vat_map.items(), key=lambda x: x[0], reverse=True):
                c.setFillColor(COLOR_MUTED)
                c.setFont(font_main, 8)
                c.drawRightString(rl, y, f"• TVA {rate:.2f}% sur {_money(comp['base'])} :")
                c.drawRightString(rv, y, _money(comp["vat"]))
                y -= (LINE_H_TEXT - 0.8 * mm)

            c.setFillColor(COLOR_TEXT)
            c.setFont(font_bold, 10)
            c.drawRightString(rl, y, "TOTAL TTC :")
            c.drawRightString(rv, y, _money(self.total_ttc))  # type: ignore
            y -= (LINE_H_TEXT + 2 * mm)

            tmpl = branding.get("payment_qr_data_template", "")
            if tmpl:
                try:
                    payload = tmpl.format(
                        number=self.number,  # type: ignore
                        total=str(self.total_ttc),  # type: ignore
                        iban=branding.get("iban", ""),
                        bic=branding.get("bic", ""),
                    )
                    w = 26 * mm
                    widget = qrmod.QrCodeWidget(payload)
                    b = widget.getBounds()
                    ww, hh = b[2] - b[0], b[3] - b[1]
                    d = Drawing(w, w, transform=[w / ww, 0, 0, w / hh, 0, 0])
                    d.add(widget)
                    renderPDF.draw(d, c, x0, y - w + 2 * mm)
                    c.setFillColor(COLOR_MUTED)
                    c.setFont(font_main, 7)
                    c.drawString(x0 + w + 3 * mm, y - 6 * mm, "Scanner pour payer")
                except Exception:
                    pass

            c.setFillColor(COLOR_PRIMARY)
            c.setFont(font_main, 8)
            try:
                words = _num2words_fr(self.total_ttc)  # type: ignore
                c.drawString(x0, y - 8 * mm, f"Montant en toutes lettres : {words} euros")
                y -= (LINE_H_TEXT + 6 * mm)
            except Exception:
                y -= 4 * mm

            return y

        # --- Notes / Conditions (si présentes)
        def _notes_terms(y: float) -> float:
            notes = (self.notes or "").strip() or branding.get("default_notes", "")  # type: ignore
            terms = (self.payment_terms or "").strip() or branding.get("payment_terms", "")  # type: ignore
            from reportlab.pdfbase import pdfmetrics as _pm  # type: ignore
            for title, text in (("Notes", notes), ("Conditions de paiement", terms)):
                if not text:
                    continue
                y = _maybe_new(y, 18 * mm, False)

                # Encadré premium : Notes (fond subtil) / Conditions de paiement (cadre fin)
                if title == "Conditions de paiement":
                    c.setFillColor(colors.white)
                    c.setStrokeColor(COLOR_BORDER)
                    c.setLineWidth(0.8)
                    c.roundRect(M_LEFT, y - 18 * mm, CONTENT_W, 18 * mm, 2 * mm, fill=0, stroke=1)
                    c.setFillColor(COLOR_PRIMARY)
                else:
                    c.setFillColor(COLOR_ACCENT)
                    c.roundRect(M_LEFT, y - 18 * mm, CONTENT_W, 18 * mm, 2 * mm, fill=1, stroke=0)
                    c.setFillColor(COLOR_TEXT)

                c.setFont(font_bold, 9)
                c.drawString(M_LEFT + 4 * mm, y - 6 * mm, title)
                c.setFont(font_main, 8)
                c.setFillColor(COLOR_TEXT)
                max_w = CONTENT_W - 8 * mm
                line = ""
                yy = y - 11 * mm
                for w in text.split():
                    test = (line + " " + w).strip()
                    if _pm.stringWidth(test, font_main, 8) <= max_w:
                        line = test
                    else:
                        c.drawString(M_LEFT + 4 * mm, yy, line)
                        yy -= (LINE_H_TEXT - 1 * mm)
                        line = w
                if line:
                    c.drawString(M_LEFT + 4 * mm, yy, line)
                    yy -= (LINE_H_TEXT - 1 * mm)
                y = yy - 4 * mm
            return y

        # --- Signature et mention "Bon pour accord" (non utilisée sur les factures)
        def _signature_block(y: float) -> float:
            from reportlab.lib.units import mm  # type: ignore
            height_needed = 25 * mm
            y = _maybe_new(y, height_needed, False)
            box_w, box_h = 60 * mm, 20 * mm
            x_sig = M_LEFT
            c.setStrokeColor(COLOR_BORDER)
            c.setLineWidth(0.5)
            c.rect(x_sig, y - box_h, box_w, box_h, fill=0, stroke=1)
            c.setFont(font_main, 7)
            c.setFillColor(COLOR_MUTED)
            msg = "Veuillez ajouter la mention ‘Bon pour accord’ et signer ci‑dessus."
            c.drawString(x_sig, y - box_h - 3 * mm, msg)
            return y - box_h - 6 * mm

        # --- Rendu final
        _wm()
        _topbar(include_total_card=True)
        y = height - 68 * mm
        y = _parties(y)
        y = _thead(y)
        y = _tbody(y)
        y = _vat_and_summary(y)
        y = _notes_terms(y)
        # Pas de bloc de signature sur les factures
        _footer()
        c.save()

        pdf_bytes = buf.getvalue()
        buf.close()
        if attach:
            filename = f"{self.number}.pdf"  # type: ignore
            if invoice.pdf:
                try:
                    invoice.pdf.delete(save=False)
                except Exception:
                    pass
            invoice.pdf.save(filename, ContentFile(pdf_bytes), save=False)
        return pdf_bytes