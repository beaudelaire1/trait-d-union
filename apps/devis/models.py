"""
Modèles pour la gestion des devis.

L'application ``devis`` gère les entités suivantes :

* ``Client`` : représente un contact (particulier ou entreprise) qui demande un devis.
  Les champs incluent nom complet, email, téléphone et adresse.  Cette entité
  peut être enrichie selon les besoins (ex. société, SIREN).

* ``Quote`` : une demande de devis associée à un client.  Elle contient un
  numéro unique, un statut et des champs pour le service souhaité, un message
  libre et des totaux (HT, TVA, TTC) pour préparer la conversion en
  facture.  Les totaux peuvent être calculés via la méthode ``compute_totals``.

* ``QuoteItem`` : une ligne de devis liée à un service ou à une description
  libre, avec quantité, prix unitaire et taux de TVA.

Depuis 2025, les formulaires associés exigent un numéro de téléphone et la
présentation a été améliorée avec des visuels locaux (stockés dans
``static/img``).  Les modèles restent compatibles avec l'interface
d'administration et les actions de génération de factures.  Les
dépendances à Unsplash ont été supprimées pour garantir un rendu fiable.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from services.models import Service
from typing import List


def _num2words_fr(v: Decimal) -> str:
    """Convertit un montant en toutes lettres (fr).

    Utilise num2words (dépendance déjà présente dans requirements/dev.txt).
    En cas d'absence de la lib, renvoie une valeur simple.
    """
    try:
        from num2words import num2words
        # num2words gère les décimales avec to='currency' mais on préfère
        # une sortie simple : "cent vingt-trois".
        return num2words(v, lang='fr')
    except Exception:
        return str(v)


class Client(models.Model):
    """Informations de contact pour une demande de devis."""
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("client")
        verbose_name_plural = _("clients")

    def __str__(self) -> str:
        return self.full_name


class QuoteRequestPhoto(models.Model):
    """Fichier (photo ou document) joint à une demande de devis."""

    image = models.ImageField(_("Fichier"), upload_to="devis/requests/photos")

    class Meta:
        verbose_name = _("photo de demande de devis")
        verbose_name_plural = _("photos de demandes de devis")

    def __str__(self) -> str:
        return self.image.name if self.image else "Pièce jointe"


class QuoteRequest(models.Model):
    """Demande initiale envoyée par un client depuis le site ou l'interface publique."""

    class QuoteRequestStatus(models.TextChoices):
        NEW = "new", _("Nouveau")
        PROCESSED = "processed", _("Traité")
        REJECTED = "rejected", _("Rejeté")

    client_name = models.CharField(_("Nom du client"), max_length=200)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=50)
    address = models.CharField(_("Adresse"), max_length=255)
    message = models.TextField(_("Message"), blank=True)
    preferred_date = models.DateField(_("Date souhaitée"), null=True, blank=True)
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=QuoteRequestStatus.choices,
        default=QuoteRequestStatus.NEW,
    )
    photos = models.ManyToManyField(
        "devis.QuoteRequestPhoto",
        verbose_name=_("Photos"),
        blank=True,
        related_name="quote_requests",
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("demande de devis")
        verbose_name_plural = _("demandes de devis")

    def __str__(self) -> str:
        return f"Demande {self.id} - {self.client_name}"



class Quote(models.Model):
    """Demande de devis.

    Un numéro de devis est généré automatiquement à partir de l'année et de
    l'identifiant.  Le champ ``service`` est optionnel pour permettre des
    demandes libres.  Le statut permet de suivre l'avancement (brouillon,
    envoyé, accepté, rejeté).  Les totaux permettent d'anticiper la facture.
    """

    class QuoteStatus(models.TextChoices):
        DRAFT = "draft", _("Brouillon")
        SENT = "sent", _("Envoyé")
        ACCEPTED = "accepted", _("Accepté")
        REJECTED = "rejected", _("Refusé")
        INVOICED = "invoiced", _("Facturé")


    number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Numéro de devis format DEV-AAAA-XXX, généré automatiquement."
    )

    public_token = models.CharField(max_length=64, unique=True, blank=True, help_text="Jeton public stable pour consulter le PDF du devis.")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="quotes")
    quote_request = models.ForeignKey(
        "QuoteRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotes",
        help_text="Demande d'origine (facultative).",
    )
    # Lorsque plusieurs services sont ajoutés via les items, ce champ reste optionnel
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotes",
        help_text="Service principal demandé (optionnel si plusieurs items)."
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=QuoteStatus.choices, default=QuoteStatus.DRAFT)
    # Date d'émission du devis.  Utilise la date du jour par défaut afin d'éviter les
    # problèmes de migration avec auto_now_add.  La valeur est fixée lors de la création
    # et peut être modifiée par l'administrateur si nécessaire.
    issue_date = models.DateField(default=date.today)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Totaux calculés pour le devis.  Ces champs sont renseignés via compute_totals().
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # PDF file attached to the quote.  When a quote is generated the
    # associated PDF is stored here.  The file is saved under
    # ``media/devis/`` and named after the quote number.  This field
    # allows automated emailing of professional quotes and a central
    # repository of generated documents.
    pdf = models.FileField(upload_to="devis", blank=True, null=True)

    # ===========================================
    # PHASE 3 : Signature électronique & Paiement
    # ===========================================
    # Image de la signature client (base64 PNG stockée en fichier)
    signature_image = models.FileField(
        upload_to="devis/signatures",
        blank=True,
        null=True,
        help_text="Signature électronique du client"
    )
    # Date de signature
    signed_at = models.DateTimeField(null=True, blank=True)
    # Audit trail JSON (IP, UserAgent, etc.)
    signature_audit_trail = models.JSONField(
        blank=True,
        null=True,
        help_text="Informations d'audit de la signature"
    )
    # Stripe Checkout Session ID (acompte)
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID de session Stripe pour le paiement d'acompte"
    )
    # Montant de l'acompte payé
    deposit_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Montant de l'acompte encaissé"
    )
    # Date de paiement de l'acompte
    deposit_paid_at = models.DateTimeField(null=True, blank=True)

    def amount_letter(self):
        """Montant TTC en toutes lettres (affiché sur le PDF devis)."""
        return f"{_num2words_fr(self.total_ttc).title()} euros"

    def __str__(self) -> str:
        return f"Devis {self.number or ''} pour {self.client.full_name}"

    def save(self, *args, **kwargs):
        import secrets
        from django.db import transaction
        
        if not self.public_token:
            # Generate unique public token
            while True:
                token = secrets.token_urlsafe(32)
                if not Quote.objects.filter(public_token=token).exists():
                    self.public_token = token
                    break
        
        # Attribution d'un numéro de devis si nécessaire : DEV-AAAA-XXX
        # Use atomic transaction with select_for_update to avoid race conditions
        if not self.pk and not self.number:
            # l'année est celle de la date d'émission
            year = self.issue_date.year if getattr(self, "issue_date", None) else date.today().year
            prefix = f"DEV-{year}-"
            
            # Use atomic block to avoid race conditions
            with transaction.atomic():
                last = (
                    Quote.objects
                    .select_for_update()
                    .filter(number__startswith=prefix)
                    .order_by("number")
                    .last()
                )
                counter = 0
                if last:
                    try:
                        counter = int(str(last.number).split("-")[-1])
                    except ValueError:
                        counter = 0
                # Use a three‑digit counter (000–999)
                self.number = f"{prefix}{counter + 1:03d}"
        
        # Définir une date de validité par défaut (30 jours) si non
        # renseignée.  Cette logique est placée dans ``save`` afin
        # d'éviter des migrations supplémentaires et de garantir un
        # comportement homogène lors de la création via l'admin ou l'API.
        if not self.valid_until and getattr(self, "issue_date", None):
            from datetime import timedelta
            self.valid_until = self.issue_date + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def items(self) -> List["QuoteItem"]:
        return self.quote_items.all()

    def compute_totals(self):
        """Calcule et met à jour les totaux HT, TVA et TTC à partir des items.

        Implémentation Django "Service Layer" simple (sans couche hexagonale).
        """
        from decimal import Decimal

        total_ht = Decimal("0.00")
        total_tva = Decimal("0.00")

        # quote.items related_name expected
        for item in self.quote_items.all():
            qty = Decimal(str(getattr(item, "quantity", 0) or 0))
            unit = Decimal(str(getattr(item, "unit_price", 0) or 0))
            rate = Decimal(str(getattr(item, "tax_rate", 0) or 0))
            line_ht = qty * unit
            line_tva = (line_ht * rate) / Decimal("100")
            total_ht += line_ht
            total_tva += line_tva

        self.total_ht = total_ht
        self.tva = total_tva
        self.total_ttc = total_ht + total_tva
        self.save(update_fields=["total_ht", "tva", "total_ttc"])

    def amount_letter(self):
        """Montant TTC en toutes lettres (pour le PDF premium)."""
        return f"{_num2words_fr(self.total_ttc).title()} euros"

    def generate_pdf(self, attach: bool = True) -> bytes:
        """Génère un PDF premium pour ce devis via WeasyPrint.

        - Utilise le template ``pdf/quote.html`` (modèle premium).
        - Génère toujours le document à partir des données actuelles.
        - Si ``attach`` est vrai, le fichier est sauvegardé dans ``self.pdf``.

        Returns
        -------
        bytes
            Le contenu binaire du PDF.
        """
        # Toujours recalculer les totaux avant génération
        try:
            self.compute_totals()
        except Exception:
            # ne bloque pas la génération si un item est mal formé
            pass

        from django.core.files.base import ContentFile
        from core.services.document_generator import DocumentGenerator

        return DocumentGenerator.generate_quote_pdf(self, attach=attach)

    def convert_to_invoice(self):
        """Convertit ce devis en facture en utilisant le service dédié."""
        from .services import create_invoice_from_quote
        result = create_invoice_from_quote(self)
        return result.invoice

    def send_email(self, request=None, *, force_pdf: bool = True):
        """Envoie au client un email premium avec le PDF en pièce jointe."""
        if force_pdf and not self.pdf:
            self.generate_pdf(attach=True)
        from .email_service import send_quote_email
        return send_quote_email(self, request=request)

class QuoteItem(models.Model):
    """Une ligne de devis liée à un service ou à une description libre."""

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="quote_items")
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quote_items",
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        help_text=_("Libellé de la ligne (prérempli si un service est sélectionné)."),
    )
    quantity = models.DecimalField(
        _("Quantité"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
    )
    unit_price = models.DecimalField(
        _("Prix unitaire HT"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_rate = models.DecimalField(
        _("Taux de TVA"),
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Taux de TVA en pourcentage (ex. 20.00 pour 20 %)."),
    )


    class Meta:
        verbose_name = _("ligne de devis")
        verbose_name_plural = _("lignes de devis")

    def __str__(self) -> str:
        return self.description or (self.service.title if self.service else "Ligne")

    @property
    def total_ht(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_tva(self) -> Decimal:
        return (self.total_ht * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_ttc(self) -> Decimal:
        return (self.total_ht + self.total_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# -----------------------------------------------------------------------------
# Pièces jointes (photos) pour les devis
# -----------------------------------------------------------------------------

class QuotePhoto(models.Model):
    """Image ou document joint à un devis.

    Les clients peuvent fournir des photos de l'état initial avant les
    travaux.  Chaque fichier est relié à un devis via une clé étrangère.
    Les images sont stockées dans ``media/devis/photos``.
    """
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="devis/photos")

    class Meta:
        verbose_name = _("photo du devis")
        verbose_name_plural = _("photos du devis")

    def __str__(self) -> str:
        return f"Photo pour {self.quote.number}"


class QuoteValidation(models.Model):
    """Jeton de validation 2 facteurs pour un devis.

    Flux :
    1) Lien "Valider le devis" -> crée un QuoteValidation (token) et envoie un code.
    2) Le client saisit le code -> on confirme et le devis passe à ACCEPTED.

    Objectif : éviter une simple validation en 1 clic et empêcher les validations
    accidentelles.
    """

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="validations")
    token = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("validation devis")
        verbose_name_plural = _("validations devis")

    def __str__(self) -> str:
        return f"Validation {self.quote.number} ({'OK' if self.confirmed_at else 'EN ATTENTE'})"

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone
        return self.expires_at <= timezone.now()

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None

    @classmethod
    def create_for_quote(cls, quote: "Quote", *, ttl_minutes: int = 15) -> "QuoteValidation":
        """Crée un jeton + code et invalide les précédents jetons non confirmés."""
        import secrets
        from django.utils import timezone
        from datetime import timedelta

        # Invalidate previous pending validations
        cls.objects.filter(quote=quote, confirmed_at__isnull=True).delete()

        token = secrets.token_urlsafe(32)
        # 6 digits (000000-999999)
        code = f"{secrets.randbelow(1_000_000):06d}"
        return cls.objects.create(
            quote=quote,
            token=token,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    def verify(self, submitted_code: str, *, max_attempts: int = 5) -> bool:
        """Valide le code : True si OK (et marque confirmed_at)."""
        from django.utils import timezone

        if self.is_confirmed:
            return True
        if self.is_expired:
            return False
        if self.attempts >= max_attempts:
            return False
        
        # Validate that submitted code is not empty
        if not submitted_code or not submitted_code.strip():
            return False

        self.attempts += 1
        ok = submitted_code.strip() == (self.code or "").strip()
        if ok:
            self.confirmed_at = timezone.now()
            self.save(update_fields=["attempts", "confirmed_at"])
            return True
        self.save(update_fields=["attempts"])
        return False

# === Hexagonal‑friendly signaux pour les emails de devis ===
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver


def _guess_quote_email(quote):
    """Détecte de manière défensive l'email de contact client."""
    for attr in ("email", "client_email", "contact_email"):
        value = getattr(quote, attr, None)
        if value:
            return value
    client = getattr(quote, "client", None)
    if client is not None:
        for attr in ("email", "contact_email"):
            value = getattr(client, attr, None)
            if value:
                return value
    return None


@receiver(post_save, sender=Quote)
def send_quote_created_email(sender, instance: "Quote", created: bool, **kwargs):
    """Envoi d'un email simple lorsqu'un devis est créé.

    - Email au client (si adresse détectée)
    - Email de notification à l'adresse par défaut du projet
    """
    # Désactivé : le projet utilise désormais un email premium envoyé
    # explicitement (admin action / workflow). On évite les emails "en vrac".
    return

    subject = f"Votre demande de devis NetExpress n°{instance.pk}"
    body = (
        "Bonjour,\n\n"
        "Votre demande de devis a bien été enregistrée par NetExpress.\n"
        "Nous reviendrons vers vous avec une proposition détaillée dans les meilleurs délais.\n\n"
        "Ceci est un email automatique, merci de ne pas y répondre."
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@example.com"
    to_email = _guess_quote_email(instance)

    # Email client
    if to_email:
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=True)
        except Exception:
            # On reste silencieux pour ne pas casser le flux applicatif
            pass

    # Notification interne
    internal_email = getattr(settings, "NETEXPRESS_DEVIS_NOTIFICATION", None)
    if internal_email:
        try:
            send_mail(
                f"[NetExpress] Nouveau devis #{instance.pk}",
                f"Un nouveau devis vient d'être créé (ID: {instance.pk}).",
                from_email,
                [internal_email],
                fail_silently=True,
            )
        except Exception:
            pass
