"""Adapter B2Brouter — Plateforme Agréée certifiée DGFiP.

Documentation source : https://developer.b2brouter.net/

Caractéristiques :
- Auth par header `X-B2B-API-Key` + `X-B2B-API-Version`
- Base URL :
    * production : https://api.b2brouter.net
    * staging    : https://api-staging.b2brouter.net
- Format réponse : JSON uniquement (depuis 2025-10-13)
- Soumission de facture : POST `/invoices` (champ `original_attachment` pour
  passer un Factur-X PDF/A-3 en base64)
- Cycle de vie (DGFiP Flux 6) : GET `/invoices/{id}/lifecycle_events` (champs
  CDAR : Déposée, Reçue, Approuvée, Refusée, Encaissée).
- Annuaire : GET `/directory?identifier=...`
- Rate limit : 1000 req/min prod, 600 staging → exponential backoff sur 429
- Webhook : signature HMAC-SHA256 (cf. apps.einvoicing.webhooks)

L'adapter cache UN unique objet `requests.Session` (pour le keep-alive HTTP)
et réinitialise les retries via `urllib3.util.Retry`.
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from django.conf import settings

from ..builders.facturx import build_facturx_pdf
from .base import PDPClient, PDPLifecycleEvent, PDPSubmission
from .exceptions import (
    PDPAuthError,
    PDPError,
    PDPNotFoundError,
    PDPRateLimitError,
    PDPTransportError,
    PDPValidationError,
)

logger = logging.getLogger(__name__)


PRODUCTION_BASE = "https://api.b2brouter.net"
STAGING_BASE = "https://api-staging.b2brouter.net"
DEFAULT_API_VERSION = "2026-03-02"
DEFAULT_TIMEOUT = 20


class B2BrouterClient(PDPClient):
    """Adapter REST B2Brouter."""

    provider = "b2brouter"

    def __init__(
        self,
        *,
        sandbox: bool = True,
        api_version: str = DEFAULT_API_VERSION,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        self.api_key = api_key or cfg.get("API_KEY", "")
        self.account_id = account_id or cfg.get("ACCOUNT_ID", "")
        self.base_url = (base_url or (STAGING_BASE if sandbox else PRODUCTION_BASE)).rstrip("/")
        self.api_version = api_version
        self.timeout = timeout or int(cfg.get("TIMEOUT_SECONDS", DEFAULT_TIMEOUT))
        self._session = None  # paresseux : pas d'import requests si pas appelé

    # ─── HTTP plumbing ────────────────────────────────────────────────
    def _get_session(self):
        if self._session is not None:
            return self._session
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
        except ImportError as exc:  # pragma: no cover
            raise PDPTransportError(
                "Le package `requests` est requis pour l'adapter B2Brouter."
            ) from exc

        session = requests.Session()
        # Retries automatiques uniquement sur les codes transitoires (5xx, 429).
        retry = Retry(
            total=int(((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {}).get("RETRY_MAX_ATTEMPTS", 5)),
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "DELETE"),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-B2B-API-Key": self.api_key,
            "X-B2B-API-Version": self.api_version,
            "User-Agent": "TUS-eInvoicing/1.0 (+https://traitdunion.it)",
        })
        self._session = session
        return session

    def _request(self, method: str, path: str, *, json: Any = None, params: dict | None = None):
        if not self.api_key:
            raise PDPAuthError("Aucune clé API B2Brouter configurée.", provider=self.provider)
        url = f"{self.base_url}{path}"
        try:
            resp = self._get_session().request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except Exception as exc:  # noqa: BLE001
            raise PDPTransportError(
                f"Échec réseau B2Brouter sur {method} {path}: {exc}",
                provider=self.provider,
            ) from exc
        return self._handle_response(resp, method=method, path=path)

    def _handle_response(self, resp, *, method: str, path: str) -> Any:
        if 200 <= resp.status_code < 300:
            if resp.status_code == 204 or not resp.content:
                return None
            try:
                return resp.json()
            except ValueError:
                return resp.text

        body = self._safe_json(resp)
        sc = resp.status_code
        if sc == 401 or sc == 403:
            raise PDPAuthError("B2Brouter: authentification refusée.", provider=self.provider, status_code=sc, payload=body)
        if sc == 404:
            raise PDPNotFoundError("B2Brouter: ressource introuvable.", provider=self.provider, status_code=sc, payload=body)
        if sc == 422 or sc == 400:
            raise PDPValidationError(
                f"B2Brouter: validation échouée ({sc}).",
                provider=self.provider, status_code=sc, payload=body,
            )
        if sc == 429:
            retry_after = self._safe_int(resp.headers.get("Retry-After"))
            raise PDPRateLimitError(
                "B2Brouter: rate limit dépassé.",
                provider=self.provider, status_code=sc,
                retry_after=retry_after, payload=body,
            )
        if 500 <= sc < 600:
            raise PDPTransportError(
                f"B2Brouter: erreur serveur ({sc}).",
                provider=self.provider, status_code=sc, payload=body,
            )
        raise PDPError(
            f"B2Brouter: réponse inattendue ({sc}) sur {method} {path}.",
            provider=self.provider, status_code=sc, payload=body,
        )

    @staticmethod
    def _safe_json(resp) -> dict:
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {"text": resp.text[:2000]}

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    # ─── Interface PDPClient ──────────────────────────────────────────
    def submit_invoice(
        self,
        invoice,
        *,
        facturx_pdf: bytes | None = None,
        cii_xml: bytes | None = None,
    ) -> PDPSubmission:
        """Soumet une facture à B2Brouter.

        Stratégie : on privilégie l'envoi du Factur-X complet (PDF/A-3 + XML
        embarqué) pour profiter du visuel + machine. B2Brouter accepte ce
        format en `original_attachment` base64.
        """
        if facturx_pdf is None:
            facturx_pdf = build_facturx_pdf(invoice)

        payload = {
            "invoice": {
                "import_format": "facturx",
                "external_reference": invoice.number,
                "original_attachment": {
                    "filename": f"{invoice.number}.pdf",
                    "content_type": "application/pdf",
                    "data": base64.b64encode(facturx_pdf).decode("ascii"),
                },
            }
        }
        path = self._invoices_path()
        body = self._request("POST", path, json=payload)
        return self._parse_submission(body)

    def get_lifecycle(self, external_id: str) -> list[PDPLifecycleEvent]:
        path = f"{self._invoices_path()}/{external_id}/lifecycle_events"
        body = self._request("GET", path) or {}
        events_raw = body.get("lifecycle_events") or body.get("data") or body.get("events") or []
        return [self._parse_lifecycle(e) for e in events_raw if isinstance(e, dict)]

    def lookup_directory(self, siren_or_siret: str) -> Optional[dict[str, Any]]:
        """B2Brouter Directory : recherche par identifier (SIRET/SIREN)."""
        body = self._request("GET", "/directory", params={"identifier": siren_or_siret}) or {}
        records = body.get("records") or body.get("data") or []
        if not records:
            return None
        first = records[0]
        return {
            "name": first.get("name") or first.get("legal_name", ""),
            "siret": first.get("tin_value") or first.get("siret", ""),
            "peppol_id": first.get("peppol_id") or first.get("schema_id", ""),
            "country_code": first.get("country") or "FR",
            "raw": first,
        }

    # ─── helpers internes ─────────────────────────────────────────────
    def _invoices_path(self) -> str:
        if self.account_id:
            return f"/accounts/{self.account_id}/invoices"
        return "/invoices"

    def _parse_submission(self, body: dict) -> PDPSubmission:
        invoice_node = body.get("invoice") if isinstance(body, dict) else None
        node = invoice_node or body or {}
        external_id = str(node.get("id") or node.get("invoice_id") or "")
        if not external_id:
            raise PDPValidationError(
                "B2Brouter: réponse sans identifiant — soumission rejetée.",
                provider=self.provider,
                payload=body,
            )
        state = (node.get("state") or node.get("status") or "SUBMITTED").upper()
        ts = node.get("created_at") or node.get("submitted_at")
        accepted_at = self._parse_iso(ts) or datetime.now(timezone.utc)
        return PDPSubmission(
            external_id=external_id,
            state=self._normalize_state(state),
            accepted_at=accepted_at,
            raw=node,
        )

    def _parse_lifecycle(self, event: dict) -> PDPLifecycleEvent:
        external_id = str(event.get("invoice_id") or event.get("external_id") or "")
        state = self._normalize_state((event.get("state") or event.get("status") or "").upper())
        occurred = self._parse_iso(event.get("occurred_at") or event.get("created_at")) or datetime.now(timezone.utc)
        reason = event.get("reason") or event.get("rejection_reason") or ""
        return PDPLifecycleEvent(
            external_id=external_id,
            state=state,
            occurred_at=occurred,
            reason=reason,
            raw=event,
        )

    @staticmethod
    def _parse_iso(value) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _normalize_state(state: str) -> str:
        """Mapping vers les codes `apps.einvoicing.codelists.LifecycleState`.

        B2Brouter / DGFiP CDAR utilisent des libellés français
        (Déposée, Reçue, Approuvée, Refusée, Encaissée).
        """
        mapping = {
            "DEPOSEE": "SUBMITTED",
            "DEPOSITED": "SUBMITTED",
            "QUEUED": "QUEUED",
            "RECUE": "DELIVERED",
            "RECEIVED": "DELIVERED",
            "DELIVERED": "DELIVERED",
            "APPROUVEE": "APPROVED",
            "APPROVED": "APPROVED",
            "REFUSEE": "REJECTED",
            "REJECTED": "REJECTED",
            "DISPUTED": "DISPUTED",
            "ENCAISSEE": "PAID",
            "PAID": "PAID",
            "SENT": "SENT",
            "SUBMITTED": "SUBMITTED",
            "CANCELLED": "CANCELLED",
        }
        return mapping.get(state, state or "SUBMITTED")


__all__ = ["B2BrouterClient", "PRODUCTION_BASE", "STAGING_BASE"]
