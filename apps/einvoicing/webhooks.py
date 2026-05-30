"""Vérification de signature pour les webhooks PDP entrants.

Format commun à toutes les Plateformes Agréées que TUS supporte :

    <X-PA-Signature>: t=<unix_ts>,s=<hmac_sha256(secret, "t.body")>

Headers concrets selon le provider :
- B2BRouter : ``X-B2Brouter-Signature``
- IOPOLE    : ``X-Iopole-Signature``

Le couple (timestamp, hex_sig) est extrait par `parse_pdp_signature`, validé
en temps constant pour éviter les attaques par timing side-channel et anti-
replay (tolérance 5 min par défaut).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import time
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


_HEADER_RE = re.compile(r"t=([^,]+),\s*s=([0-9a-fA-F]+)")
DEFAULT_TOLERANCE_SECONDS = 5 * 60  # rejet des replays > 5 min


def _get_webhook_secret(secret_key: str = "WEBHOOK_SECRET") -> str:
    cfg = getattr(settings, "INVOICING", {}) or {}
    pdp_cfg = cfg.get("PDP") or {}
    return (pdp_cfg.get(secret_key) or "")


def parse_pdp_signature(header: str) -> tuple[Optional[int], Optional[str]]:
    """Parse `t=...,s=...` et retourne `(timestamp, hex_sig)` ou `(None, None)`."""
    if not header:
        return None, None
    match = _HEADER_RE.search(header)
    if not match:
        return None, None
    try:
        ts = int(match.group(1))
    except (TypeError, ValueError):
        return None, None
    return ts, match.group(2)


# Alias rétrocompatible — l'ancien nom est conservé pour ne pas casser les
# imports existants (tests, vues).
parse_b2brouter_signature = parse_pdp_signature


def _verify_signature(
    *,
    body: bytes,
    header: str,
    secret_value: str,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[int] = None,
    provider_label: str = "PDP",
) -> bool:
    if not secret_value:
        logger.warning("Webhook %s: secret manquant — rejet par défaut.", provider_label)
        return False
    ts, sig = parse_pdp_signature(header)
    if ts is None or sig is None:
        return False
    current = int(now if now is not None else time.time())
    if abs(current - ts) > tolerance_seconds:
        logger.info("Webhook %s: signature périmée (delta=%ss).", provider_label, current - ts)
        return False
    payload = f"{ts}.".encode("utf-8") + body
    expected = hmac.new(secret_value.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig.lower())


def verify_b2brouter_signature(
    *,
    body: bytes,
    header: str,
    secret: Optional[str] = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[int] = None,
) -> bool:
    """Renvoie True si la signature B2Brouter est valide ET non périmée."""
    secret_value = secret if secret is not None else _get_webhook_secret("WEBHOOK_SECRET")
    return _verify_signature(
        body=body,
        header=header,
        secret_value=secret_value or "",
        tolerance_seconds=tolerance_seconds,
        now=now,
        provider_label="B2Brouter",
    )


def verify_iopole_signature(
    *,
    body: bytes,
    header: str,
    secret: Optional[str] = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[int] = None,
) -> bool:
    """Renvoie True si la signature IOPOLE est valide ET non périmée.

    Le secret est lu dans ``settings.INVOICING['PDP']['WEBHOOK_SECRET']`` (clé
    partagée par tous les adapters). Si vous utilisez plusieurs PA en parallèle
    et que les secrets diffèrent, override via le paramètre `secret`.
    """
    secret_value = secret if secret is not None else _get_webhook_secret("WEBHOOK_SECRET")
    return _verify_signature(
        body=body,
        header=header,
        secret_value=secret_value or "",
        tolerance_seconds=tolerance_seconds,
        now=now,
        provider_label="IOPOLE",
    )


__all__ = [
    "verify_b2brouter_signature",
    "verify_iopole_signature",
    "parse_pdp_signature",
    "parse_b2brouter_signature",
    "DEFAULT_TOLERANCE_SECONDS",
]
