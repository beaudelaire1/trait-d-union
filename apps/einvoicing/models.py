"""
Modèles de l'app `einvoicing`.

Phase 1 — un seul modèle critique :
- `InvoiceLifecycleEvent` : journal append-only des transitions de cycle de vie
  d'une facture côté PDP. Rendu immuable au niveau Python (raise sur UPDATE) et
  signé par hash chaîné SHA-256 pour détecter toute altération.

Phases ultérieures : `PDPSubmission`, `PeppolDirectoryEntry`, `EReportingBatch`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone as dt_timezone
from typing import Any, Optional

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .codelists import LifecycleState


# ---------------------------------------------------------------------------
# Helpers (sortis du modèle pour testabilité unitaire)
# ---------------------------------------------------------------------------
GENESIS_HASH = "0" * 64  # hash "racine" pour le tout premier événement


def _serialize_payload(payload: Any) -> str:
    """Sérialise un payload JSON de manière déterministe (clés triées, no whitespace)."""
    if payload is None:
        return ""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_event_hash(
    *,
    invoice_id: int,
    state: str,
    occurred_at: datetime,
    payload: Any,
    previous_hash: str,
) -> str:
    """Calcule le hash chaîné SHA-256 d'un événement.

    Le hash dépend du hash précédent → toute modification rétroactive d'un
    événement antérieur invalide la chaîne (détection de tampering).
    """
    parts = [
        str(invoice_id),
        str(state),
        # ISO 8601 stable, microsecondes incluses, fuseau préservé
        occurred_at.astimezone(dt_timezone.utc).isoformat() if occurred_at.tzinfo else occurred_at.isoformat(),
        _serialize_payload(payload),
        previous_hash or GENESIS_HASH,
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest


# ---------------------------------------------------------------------------
# InvoiceLifecycleEvent — journal append-only
# ---------------------------------------------------------------------------
class InvoiceLifecycleEvent(models.Model):
    """Événement de cycle de vie immuable pour une facture.

    INVARIANTS :
    - Une fois enregistré (pk défini), aucun champ n'est modifiable (raise).
    - Suppression refusée (raise sur delete()).
    - `previous_hash` pointe sur le hash de l'événement précédent de la
      même facture (ou GENESIS_HASH si premier événement).
    - `event_hash` calculé en `save()` à partir des autres champs + previous_hash.

    Usage :
        InvoiceLifecycleEvent.record(
            invoice=invoice,
            state=LifecycleState.SUBMITTED,
            actor=request.user,
            payload={"pdp": "b2brouter", "external_id": "xyz"},
        )
    """

    invoice = models.ForeignKey(
        "factures.Invoice",
        on_delete=models.PROTECT,  # PROTECT pour empêcher la perte d'audit si suppression cascade
        related_name="lifecycle_events",
        verbose_name=_("Facture"),
    )
    state = models.CharField(
        _("État"),
        max_length=20,
        choices=LifecycleState.choices,
    )
    occurred_at = models.DateTimeField(
        _("Survenu le"),
        default=timezone.now,
        editable=False,
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Acteur"),
        help_text=_("Utilisateur Django à l'origine de l'événement, si applicable."),
    )
    source = models.CharField(
        _("Source"),
        max_length=40,
        default="system",
        help_text=_("Origine de l'événement (admin, api, webhook, system, dunning, etc.)"),
    )
    payload = models.JSONField(
        _("Données"),
        default=dict,
        blank=True,
        help_text=_("Métadonnées libres (ID PDP externe, motif rejet, etc.) — pas de PII inutile."),
    )
    previous_hash = models.CharField(
        _("Hash précédent"),
        max_length=64,
        editable=False,
        help_text=_("Hash de l'événement précédent de la même facture (ou genesis)."),
    )
    event_hash = models.CharField(
        _("Hash de l'événement"),
        max_length=64,
        editable=False,
        unique=True,  # collision SHA-256 = facture brisée
        help_text=_("SHA-256 chaîné garantissant l'intégrité de l'historique."),
    )

    class Meta:
        verbose_name = _("Événement cycle de vie facture")
        verbose_name_plural = _("Événements cycle de vie factures")
        ordering = ("invoice_id", "occurred_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "previous_hash"],
                name="uniq_lifecycle_invoice_prev_hash",
            ),
        ]
        indexes = [
            models.Index(fields=["invoice", "state"], name="idx_lc_invoice_state"),
            models.Index(fields=["state", "occurred_at"], name="idx_lc_state_time"),
        ]

    # ---- Représentations -------------------------------------------------
    def __str__(self) -> str:  # pragma: no cover
        return f"{self.invoice_id} · {self.state} · {self.occurred_at:%Y-%m-%d %H:%M:%S}"

    # ---- Immuabilité runtime --------------------------------------------
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is not None:
            # Tentative d'UPDATE bloquée : la chaîne d'audit doit rester intacte.
            raise PermissionError(
                "InvoiceLifecycleEvent est append-only : un événement existant ne peut être modifié."
            )
        # Calcul du previous_hash : dernier événement enregistré pour cette facture
        if not self.previous_hash:
            last = (
                InvoiceLifecycleEvent.objects
                .filter(invoice_id=self.invoice_id)
                .order_by("-occurred_at", "-id")
                .only("event_hash")
                .first()
            )
            self.previous_hash = last.event_hash if last else GENESIS_HASH
        # occurred_at : si l'appelant a fourni une valeur, on la garde, sinon now()
        if self.occurred_at is None:
            self.occurred_at = timezone.now()
        # event_hash : calcul après normalisation des autres champs
        self.event_hash = compute_event_hash(
            invoice_id=self.invoice_id,
            state=self.state,
            occurred_at=self.occurred_at,
            payload=self.payload,
            previous_hash=self.previous_hash,
        )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise PermissionError(
            "InvoiceLifecycleEvent est append-only : la suppression est interdite."
        )

    # ---- Helpers ---------------------------------------------------------
    @classmethod
    def record(
        cls,
        *,
        invoice: "models.Model",
        state: str,
        actor: Optional[Any] = None,
        source: str = "system",
        payload: Optional[dict] = None,
        occurred_at: Optional[datetime] = None,
    ) -> "InvoiceLifecycleEvent":
        """Crée et persiste un événement de cycle de vie.

        Préfère cette méthode au constructeur direct : centralise la création
        et garantit le calcul correct du hash.
        """
        return cls.objects.create(
            invoice=invoice,
            state=state,
            actor=actor,
            source=source,
            payload=payload or {},
            occurred_at=occurred_at or timezone.now(),
        )

    @classmethod
    def verify_chain(cls, invoice_id: int) -> tuple[bool, Optional[int]]:
        """Vérifie l'intégrité de la chaîne d'événements d'une facture.

        Returns
        -------
        (ok, broken_event_id)
            `ok=True` si la chaîne est intacte. Sinon `broken_event_id` pointe
            sur le premier événement dont le hash recalculé ne correspond pas.
        """
        previous = GENESIS_HASH
        events = (
            cls.objects
            .filter(invoice_id=invoice_id)
            .order_by("occurred_at", "id")
            .only("id", "state", "occurred_at", "payload", "previous_hash", "event_hash")
        )
        for ev in events:
            if ev.previous_hash != previous:
                return False, ev.id
            expected = compute_event_hash(
                invoice_id=invoice_id,
                state=ev.state,
                occurred_at=ev.occurred_at,
                payload=ev.payload,
                previous_hash=ev.previous_hash,
            )
            if expected != ev.event_hash:
                return False, ev.id
            previous = ev.event_hash
        return True, None


__all__ = ["InvoiceLifecycleEvent", "compute_event_hash", "GENESIS_HASH"]
