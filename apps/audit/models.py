"""Modèles pour la traçabilité centralisée : journal d'audit des actions critiques."""
import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """Journal d'audit centralisé pour les actions critiques.
    
    Trace les validations de devis, paiements de factures, validations de jalons,
    création de comptes clients, etc. Chaque entrée contient :
    - action_type : type d'action (quote_validated, invoice_paid, milestone_validated, etc.)
    - actor : utilisateur qui a effectué l'action
    - timestamp : moment exact
    - content_type / object_id : lien vers l'objet modifié
    - metadata : données additionnelles (JSON) → {old_value, new_value, ip, user_agent, etc.}
    """
    
    class ActionType(models.TextChoices):
        QUOTE_CREATED = "quote_created", _("Devis créé")
        QUOTE_SENT = "quote_sent", _("Devis envoyé")
        QUOTE_VALIDATED = "quote_validated", _("Devis validé")
        QUOTE_ACCEPTED = "quote_accepted", _("Devis accepté")
        QUOTE_REJECTED = "quote_rejected", _("Devis refusé")
        QUOTE_INVOICED = "quote_invoiced", _("Devis facturé")
        
        INVOICE_CREATED = "invoice_created", _("Facture créée")
        INVOICE_SENT = "invoice_sent", _("Facture envoyée")
        INVOICE_PAID = "invoice_paid", _("Facture payée")
        INVOICE_MARKED_OVERDUE = "invoice_marked_overdue", _("Facture marquée en retard")
        
        MILESTONE_VALIDATED = "milestone_validated", _("Jalon validé")
        MILESTONE_LOCKED = "milestone_locked", _("Jalon verrouillé")
        
        CLIENT_ACCOUNT_CREATED = "client_account_created", _("Compte client créé")
        CLIENT_PASSWORD_RESET_FORCED = "client_password_reset_forced", _("Réinitialisation de mot de passe forcée")
    
    # Champs de base
    action_type = models.CharField(
        _("Type d'action"),
        max_length=50,
        choices=ActionType.choices
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs_created",
        verbose_name=_("Acteur")
    )
    timestamp = models.DateTimeField(
        _("Horodatage"),
        auto_now_add=True,
        db_index=True
    )
    
    # Lien vers l'objet modifié (flexible : Quote, Invoice, ProjectMilestone)
    content_type = models.CharField(
        _("Type de contenu"),
        max_length=50,
        help_text="devis.Quote, factures.Invoice, clients.ProjectMilestone, auth.User, etc."
    )
    object_id = models.PositiveIntegerField(
        _("ID de l'objet"),
        help_text="pk de l'objet modifié"
    )
    
    # Métadonnées supplémentaires
    metadata = models.JSONField(
        _("Métadonnées"),
        default=dict,
        blank=True,
        help_text="Données additionnelles : {old_value, new_value, ip, user_agent, comment, etc.}"
    )
    
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text="Résumé lisible de l'action"
    )
    
    class Meta:
        verbose_name = _("Journal d'audit")
        verbose_name_plural = _("Journaux d'audit")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action_type", "-timestamp"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["actor", "-timestamp"]),
        ]
    
    def __str__(self) -> str:
        return f"[{self.get_action_type_display()}] {self.content_type}#{self.object_id} @ {self.timestamp}"
    
    @classmethod
    def log_action(
        cls,
        action_type: str,
        actor: User = None,
        content_type: str = None,
        object_id: int = None,
        description: str = "",
        metadata: dict = None,
    ) -> "AuditLog":
        """Utilitaire pour enregistrer une action d'audit.
        
        Args:
            action_type: Type d'action (ex: 'quote_validated')
            actor: User qui a effectué l'action
            content_type: Type de l'objet (ex: 'devis.Quote')
            object_id: PK de l'objet
            description: Description lisible
            metadata: Dict additionnelle
        
        Returns:
            AuditLog créée
        """
        if metadata is None:
            metadata = {}
        
        return cls.objects.create(
            action_type=action_type,
            actor=actor,
            content_type=content_type or "",
            object_id=object_id or 0,
            description=description,
            metadata=metadata,
        )
