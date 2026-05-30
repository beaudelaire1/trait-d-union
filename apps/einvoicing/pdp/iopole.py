"""Adapter IOPOLE — Plateforme Agréée DGFiP (réforme FR 2026/2027).

IOPOLE (https://iopole.fr) est une PA française enregistrée par la DGFiP.
Comme toutes les PA, son API se conforme au standard **AFNOR XP Z12-013** qui
définit les échanges ERP ↔ PA et PA ↔ PA.

Caractéristiques retenues (overridables par variables d'environnement, à caler
sur la documentation développeur IOPOLE communiquée à l'inscription) :

- **Authentification**  : OAuth2 client_credentials (POST `/oauth/token`),
  Bearer Token avec refresh automatique avant expiration.
- **Base URL**          :
    * production : ``https://api.iopole.fr`` (override via env `EINVOICING_PDP_BASE_URL`)
    * sandbox    : ``https://sandbox.iopole.fr``
- **Endpoints**         :
    * POST `/v1/invoices`                          → soumission d'une facture
    * GET  `/v1/invoices/{id}/lifecycle_events`    → cycle de vie XP Z12-013
    * GET  `/v1/directory?identifier=...`          → annuaire SIREN/SIRET
- **Format**            : Factur-X PDF/A-3 (champ `attachment` base64) ou CII XML
  brut (champ `cii_xml` base64). Profil EN 16931 par défaut.
- **Cycle de vie**      : codes CDAR DGFiP (Déposée, Reçue, Approuvée, Refusée,
  Encaissée…) — normalisés vers `apps.einvoicing.codelists.LifecycleState`.
- **Rate limit**        : retries exponentiels sur 429 / 5xx
  (`urllib3.util.Retry`).
- **Webhook**           : signature HMAC-SHA256 sur `t=<unix_ts>,s=<hex>` portée
  par l'en-tête `X-Iopole-Signature` (cf. `apps.einvoicing.webhooks`).

Ne JAMAIS importer cet adapter directement depuis le code métier : passer par
``apps.einvoicing.pdp.get_pdp_client()`` pour bénéficier du swap d'adapter.
"""

from __future__ import annotations

import base64
import logging
import threading
import time
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


PRODUCTION_BASE = "https://api.iopole.fr"
SANDBOX_BASE = "https://sandbox.iopole.fr"
DEFAULT_TOKEN_PATH = "/oauth/token"
DEFAULT_API_PREFIX = "/v1"
DEFAULT_TIMEOUT = 20
TOKEN_REFRESH_LEEWAY_SECONDS = 30  # on rafraîchit 30s avant expiration


class IopoleClient(PDPClient):
    """Adapter REST IOPOLE.

    Le client est paresseux (`requests.Session` instancié à la première
    requête) et thread-safe pour le refresh du jeton OAuth2.
    """

    provider = "iopole"

    def __init__(
        self,
        *,
        sandbox: bool = True,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        token_path: Optional[str] = None,
        api_prefix: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        self.client_id = client_id or cfg.get("OAUTH_CLIENT_ID", "")
        self.client_secret = client_secret or cfg.get("OAUTH_CLIENT_SECRET", "")
        self.base_url = (
            base_url
            or cfg.get("BASE_URL")
            or (SANDBOX_BASE if sandbox else PRODUCTION_BASE)
        ).rstrip("/")
        self.token_path = token_path or cfg.get("TOKEN_PATH", DEFAULT_TOKEN_PATH)
        self.api_prefix = (api_prefix or cfg.get("API_PREFIX", DEFAULT_API_PREFIX)).rstrip("/")
        self.timeout = timeout or int(cfg.get("TIMEOUT_SECONDS", DEFAULT_TIMEOUT))

        self._session = None
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._token_lock = threading.Lock()

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
                "Le package `requests` est requis pour l'adapter IOPOLE."
            ) from exc

        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        session = requests.Session()
        retry = Retry(
            total=int(cfg.get("RETRY_MAX_ATTEMPTS", 5)),
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
            "User-Agent": "TUS-eInvoicing/1.0 (+https://traitdunion.it)",
        })
        self._session = session
        return session

    # ─── OAuth2 ───────────────────────────────────────────────────────
    def _get_access_token(self) -> str:
        """Retourne un Bearer token valide (cache + refresh transparent)."""
        with self._token_lock:
            now = time.time()
            if self._token and now < (self._token_expires_at - TOKEN_REFRESH_LEEWAY_SECONDS):
                return self._token
            if not (self.client_id and self.client_secret):
                raise PDPAuthError(
                    "IOPOLE: client_id/client_secret OAuth2 non configurés.",
                    provider=self.provider,
                )
            url = f"{self.base_url}{self.token_path}"
            try:
                resp = self._get_session().post(
                    url,
                    data={"grant_type": "client_credentials"},
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.timeout,
                )
            except Exception as exc:  # noqa: BLE001
                raise PDPTransportError(
                    f"IOPOLE: impossible d'obtenir un token OAuth2 ({exc}).",
                    provider=self.provider,
                ) from exc
            if resp.status_code in (401, 403):
                raise PDPAuthError(
                    "IOPOLE: identifiants OAuth2 refusés.",
                    provider=self.provider,
                    status_code=resp.status_code,
                    payload=self._safe_json(resp),
                )
            if resp.status_code >= 400:
                raise PDPTransportError(
                    f"IOPOLE: échec OAuth2 ({resp.status_code}).",
                    provider=self.provider,
                    status_code=resp.status_code,
                    payload=self._safe_json(resp),
                )
            data = self._safe_json(resp)
            token = data.get("access_token")
            if not token:
                raise PDPAuthError(
                    "IOPOLE: réponse OAuth2 sans access_token.",
                    provider=self.provider,
                    payload=data,
                )
            expires_in = self._safe_int(data.get("expires_in")) or 3600
            self._token = token
            self._token_expires_at = now + expires_in
            return token

    def _request(self, method: str, path: str, *, json: Any = None, params: dict | None = None):
        url = f"{self.base_url}{self.api_prefix}{path}"
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = self._get_session().request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as exc:  # noqa: BLE001
            raise PDPTransportError(
                f"Échec réseau IOPOLE sur {method} {path}: {exc}",
                provider=self.provider,
            ) from exc

        # Si le token a expiré côté serveur entre deux refresh, on retente une
        # fois après ré-émission explicite du jeton.
        if resp.status_code == 401 and self._token is not None:
            self._token = None
            token = self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            try:
                resp = self._get_session().request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
            except Exception as exc:  # noqa: BLE001
                raise PDPTransportError(
                    f"Échec réseau IOPOLE (retry) sur {method} {path}: {exc}",
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
        if sc in (401, 403):
            raise PDPAuthError(
                "IOPOLE: authentification refusée.",
                provider=self.provider, status_code=sc, payload=body,
            )
        if sc == 404:
            raise PDPNotFoundError(
                "IOPOLE: ressource introuvable.",
                provider=self.provider, status_code=sc, payload=body,
            )
        if sc in (400, 422):
            raise PDPValidationError(
                f"IOPOLE: validation échouée ({sc}).",
                provider=self.provider, status_code=sc, payload=body,
            )
        if sc == 429:
            retry_after = self._safe_int(resp.headers.get("Retry-After"))
            raise PDPRateLimitError(
                "IOPOLE: rate limit dépassé.",
                provider=self.provider, status_code=sc,
                retry_after=retry_after, payload=body,
            )
        if 500 <= sc < 600:
            raise PDPTransportError(
                f"IOPOLE: erreur serveur ({sc}).",
                provider=self.provider, status_code=sc, payload=body,
            )
        raise PDPError(
            f"IOPOLE: réponse inattendue ({sc}) sur {method} {path}.",
            provider=self.provider, status_code=sc, payload=body,
        )

    @staticmethod
    def _safe_json(resp) -> dict:
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {"text": (getattr(resp, "text", "") or "")[:2000]}

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
        """Soumet une facture à IOPOLE.

        On envoie de préférence le Factur-X complet (PDF/A-3 + XML CII embarqué)
        pour profiter de la double représentation visuelle/machine. Si seul le
        XML est disponible, il est passé en `cii_xml`.
        """
        if facturx_pdf is None and cii_xml is None:
            facturx_pdf = build_facturx_pdf(invoice)

        payload: dict[str, Any] = {
            "external_reference": invoice.number,
            "format": "facturx" if facturx_pdf else "cii",
        }
        if facturx_pdf:
            payload["attachment"] = {
                "filename": f"{invoice.number}.pdf",
                "content_type": "application/pdf",
                "data": base64.b64encode(facturx_pdf).decode("ascii"),
            }
        if cii_xml:
            payload["cii_xml"] = base64.b64encode(cii_xml).decode("ascii")

        body = self._request("POST", "/invoices", json=payload)
        return self._parse_submission(body)

    def get_lifecycle(self, external_id: str) -> list[PDPLifecycleEvent]:
        body = self._request("GET", f"/invoices/{external_id}/lifecycle_events") or {}
        events_raw = (
            body.get("lifecycle_events")
            or body.get("data")
            or body.get("events")
            or []
        )
        return [self._parse_lifecycle(e) for e in events_raw if isinstance(e, dict)]

    def lookup_directory(self, siren_or_siret: str) -> Optional[dict[str, Any]]:
        body = self._request("GET", "/directory", params={"identifier": siren_or_siret}) or {}
        records = body.get("records") or body.get("data") or []
        if not records:
            return None
        first = records[0]
        return {
            "name": first.get("name") or first.get("legal_name", ""),
            "siret": first.get("siret") or first.get("tin_value", ""),
            "peppol_id": first.get("peppol_id") or first.get("schema_id", ""),
            "country_code": first.get("country") or first.get("country_code") or "FR",
            "raw": first,
        }

    def verify_webhook_signature(self, *, body: bytes, signature_header: str) -> bool:
        """Webhook IOPOLE — HMAC-SHA256 ``t=...,s=...`` (cf. webhooks.py)."""
        from ..webhooks import verify_iopole_signature

        return verify_iopole_signature(body=body, header=signature_header)

    # ─── helpers internes ─────────────────────────────────────────────
    def _parse_submission(self, body: dict) -> PDPSubmission:
        invoice_node = body.get("invoice") if isinstance(body, dict) else None
        node = invoice_node or body or {}
        external_id = str(node.get("id") or node.get("invoice_id") or "")
        if not external_id:
            raise PDPValidationError(
                "IOPOLE: réponse sans identifiant — soumission rejetée.",
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
        """Mappe un état IOPOLE / DGFiP CDAR vers `LifecycleState`."""
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


__all__ = ["IopoleClient", "PRODUCTION_BASE", "SANDBOX_BASE"]
