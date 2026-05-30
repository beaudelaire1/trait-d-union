"""
Synchronisation Stripe → ClientProfile pour la collecte des identifiants fiscaux.

Stripe **n'est pas une PDP agréée** par la DGFiP. Cette intégration sert
uniquement à **enrichir** les fiches clients en récupérant SIREN/SIRET/TVA
collectés via :

- Stripe Checkout avec `tax_id_collection.enabled = true`
- Création/MAJ d'un `Customer` côté Stripe (manuelle ou par webhook)
- Création d'un `tax_id` sur un `Customer` existant

Périmètre :
- B2B FR : on extrait `fr_vat` (SIRET 14 chiffres OU n° TVA intra) + `eu_vat`
- B2B UE : on extrait `eu_vat` (préfixe pays + numéro)

Aucune transmission de facture vers Stripe (les factures partent vers la PDP).

Usage :
    from apps.einvoicing.stripe_sync import sync_client_to_stripe_customer
    sync_client_to_stripe_customer(client_profile)

Robustesse :
- Idempotent : ne crée pas de doublons (`stripe_customer_id` sert de clé).
- Tolérant aux pannes : log + raise StripeSyncError (jamais d'exception silencieuse
  côté métier mais l'appelant peut décider d'ignorer).
- Aucun secret loggué.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from apps.clients.models import ClientProfile


class StripeSyncError(RuntimeError):
    """Erreur de synchronisation Stripe (à logger côté appelant)."""


# Préfixes pays pour les `eu_vat` Stripe
_EU_COUNTRY_PREFIX = re.compile(r"^[A-Z]{2}")


def _stripe_or_none():
    """Retourne le module stripe configuré ou None si indisponible."""
    try:
        import stripe  # type: ignore
    except ImportError:  # pragma: no cover
        return None
    secret = getattr(settings, "STRIPE_SECRET_KEY", "") or ""
    if not secret:
        # Compat avec stripe_service.get_stripe_keys (env var)
        import os
        secret = os.environ.get("STRIPE_SECRET_KEY", "")
    if not secret:
        return None
    stripe.api_key = secret
    return stripe


def _detect_tax_id_type(value: str, country_code: str) -> Optional[str]:
    """Détermine le type de tax_id Stripe à partir de la valeur fournie.

    - "FR12345678901" (TVA intra FR)             → eu_vat
    - "DE123456789"                              → eu_vat
    - "12345678901234" (SIRET 14 chiffres FR)    → fr_vat (Stripe accepte le SIREN/SIRET ici)
    - autre                                       → None (on ne devine pas)
    """
    v = (value or "").strip().upper().replace(" ", "")
    if not v:
        return None
    if _EU_COUNTRY_PREFIX.match(v):
        return "eu_vat"
    digits = re.sub(r"\D", "", v)
    if (country_code or "").upper() == "FR" and len(digits) in (9, 14):
        return "fr_vat"
    return None


def sync_client_to_stripe_customer(client: "ClientProfile") -> Optional[str]:
    """Pousse les identifiants fiscaux du `ClientProfile` vers Stripe.

    - Crée le Customer Stripe si nécessaire (idempotent via `stripe_customer_id`).
    - Met à jour `name`, `email`, `address` côté Stripe.
    - Ajoute les `tax_ids` (un par valeur connue).

    Returns
    -------
    Stripe Customer id ou None si Stripe n'est pas configuré.
    """
    sk = _stripe_or_none()
    if sk is None:
        logger.info("Stripe non configuré : sync ignoré pour client #%s", client.pk)
        return None

    try:
        customer_id = getattr(client, "stripe_customer_id", "") or ""
        addr = client.effective_delivery_address if hasattr(client, "effective_delivery_address") else {}
        common = {
            "name": client.full_name or client.company_name or client.email,
            "email": client.email or None,
            "metadata": {
                "client_profile_id": str(client.pk),
                "is_business": "true" if client.is_business else "false",
            },
        }
        if addr:
            common["address"] = {
                "line1": addr.get("line", "") or client.address_line or "",
                "city": addr.get("city", "") or client.city or "",
                "postal_code": addr.get("zip", "") or client.zip_code or "",
                "country": (addr.get("country") or client.country_code or "FR")[:2],
            }

        if customer_id:
            sk.Customer.modify(customer_id, **common)
        else:
            customer = sk.Customer.create(**common)
            customer_id = customer["id"]
            client.stripe_customer_id = customer_id
            client.save(update_fields=["stripe_customer_id"])

        # Synchroniser les tax_ids (créés à la demande, jamais supprimés ici).
        existing = sk.Customer.list_tax_ids(customer_id, limit=20)
        existing_values = {row["value"] for row in existing.get("data", [])}
        candidates = []
        if client.tva_number:
            candidates.append((client.tva_number, _detect_tax_id_type(client.tva_number, client.country_code)))
        if client.siret:
            candidates.append((client.siret, "fr_vat"))
        elif client.siren:
            candidates.append((client.siren, "fr_vat"))
        for raw_value, tax_type in candidates:
            value = (raw_value or "").strip().upper().replace(" ", "")
            if not value or not tax_type or value in existing_values:
                continue
            try:
                sk.Customer.create_tax_id(customer_id, type=tax_type, value=value)
            except Exception as exc:  # noqa: BLE001
                # On ne bloque pas la synchro pour un tax_id rejeté par Stripe.
                logger.warning(
                    "Stripe a refusé le tax_id (%s) pour client #%s : %s",
                    tax_type, client.pk, str(exc)[:120],
                )
        return customer_id
    except Exception as exc:  # noqa: BLE001
        logger.exception("Échec sync Stripe pour client #%s", client.pk)
        raise StripeSyncError(str(exc)) from exc


def ingest_stripe_customer_tax_ids(stripe_customer_id: str) -> Optional["ClientProfile"]:
    """Récupère les tax_ids d'un `Customer` Stripe et les pousse dans le ClientProfile.

    Utile pour le webhook `customer.updated` / `customer.tax_id.created`.
    """
    from apps.clients.models import ClientProfile

    sk = _stripe_or_none()
    if sk is None or not stripe_customer_id:
        return None

    client = ClientProfile.objects.filter(stripe_customer_id=stripe_customer_id).first()
    if client is None:
        return None

    try:
        tax_ids = sk.Customer.list_tax_ids(stripe_customer_id, limit=20).get("data", [])
    except Exception:
        logger.exception("Stripe: échec récupération tax_ids pour customer=%s", stripe_customer_id)
        return client

    updated = False
    for row in tax_ids:
        ttype = row.get("type")
        value = (row.get("value") or "").strip().upper().replace(" ", "")
        if not value:
            continue
        if ttype == "fr_vat":
            digits = re.sub(r"\D", "", value)
            if len(digits) == 14 and not client.siret:
                client.siret = digits
                if not client.siren:
                    client.siren = digits[:9]
                updated = True
            elif len(digits) == 9 and not client.siren:
                client.siren = digits
                updated = True
        elif ttype == "eu_vat" and not client.tva_number:
            client.tva_number = value
            updated = True
    if updated:
        client.is_business = True
        client.save(update_fields=["siret", "siren", "tva_number", "is_business"])
    return client


__all__ = [
    "StripeSyncError",
    "sync_client_to_stripe_customer",
    "ingest_stripe_customer_tax_ids",
]
