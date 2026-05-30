"""Smoke-test du sandbox IOPOLE — Plateforme Agréée DGFiP.

Vérifie en quelques secondes que l'adapter `apps.einvoicing.pdp.iopole`
parle bien à la sandbox IOPOLE :

  1. **Auth OAuth2** (client_credentials) → POST {TOKEN_PATH}
  2. **Annuaire**  (lookup_directory) → GET /directory?identifier=...
  3. **Soumission** (option --submit) → POST /invoices avec un Factur-X
     généré depuis la facture test (la dernière en base, ou celle indiquée
     par --invoice-id, ou la facture de démo via demo_facturx).
  4. **Lifecycle** (option --submit) → GET /invoices/{id}/lifecycle_events.

⚠️ Aucun secret n'est loggué. Les valeurs sensibles sont masquées.

Usage typique :

    # Lecture seule (auth + annuaire) — sûre pour la sandbox
    python manage.py test_iopole_sandbox

    # Soumission complète d'une facture test
    python manage.py test_iopole_sandbox --submit

    # Soumission d'une facture précise déjà en base
    python manage.py test_iopole_sandbox --submit --invoice-id 42

    # Vérification de la chaîne webhook (signature HMAC) en local
    python manage.py test_iopole_sandbox --probe-webhook

Pré-requis (.env) :

    EINVOICING_PDP_PROVIDER=iopole
    EINVOICING_PDP_SANDBOX=1
    EINVOICING_PDP_OAUTH_CLIENT_ID=...
    EINVOICING_PDP_OAUTH_CLIENT_SECRET=...
    EINVOICING_PDP_WEBHOOK_SECRET=...   (pour --probe-webhook)
    # Optionnels si IOPOLE diverge du standard :
    EINVOICING_PDP_BASE_URL=https://sandbox.iopole.fr
    EINVOICING_PDP_TOKEN_PATH=/oauth/token
    EINVOICING_PDP_API_PREFIX=/v1
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


# SIRET réel d'une mairie utilisé uniquement pour tester l'annuaire (lecture).
DEFAULT_DIRECTORY_PROBE = "21800003700017"  # Mairie de Cayenne


class Command(BaseCommand):
    help = "Smoke-test bout-en-bout du sandbox IOPOLE."

    def add_arguments(self, parser):
        parser.add_argument(
            "--submit", action="store_true",
            help="Soumet une facture test à IOPOLE (POST /invoices).",
        )
        parser.add_argument(
            "--invoice-id", type=int, default=None,
            help="ID d'une Invoice existante à soumettre (par défaut : la dernière).",
        )
        parser.add_argument(
            "--directory-probe", default=DEFAULT_DIRECTORY_PROBE,
            help=f"SIREN/SIRET utilisé pour tester l'annuaire (défaut : {DEFAULT_DIRECTORY_PROBE}).",
        )
        parser.add_argument(
            "--probe-webhook", action="store_true",
            help="Génère une signature HMAC test et vérifie qu'elle est acceptée.",
        )

    # ------------------------------------------------------------------ main
    def handle(self, *args, **options):
        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        if cfg.get("PROVIDER", "") != "iopole":
            self._warn(
                f"Provider courant = {cfg.get('PROVIDER', '?')!r}. "
                f"Cette commande va instancier IopoleClient quand même, "
                f"mais pense à passer EINVOICING_PDP_PROVIDER=iopole."
            )

        self._print_config(cfg)
        client = self._get_client()

        ok_auth = self._step_auth(client)
        if not ok_auth:
            return

        self._step_directory(client, options["directory_probe"])

        if options["submit"]:
            invoice = self._resolve_invoice(options["invoice_id"])
            if invoice is not None:
                self._step_submit_and_lifecycle(client, invoice)

        if options["probe_webhook"]:
            self._step_webhook_probe()

        self._stdout("-" * 60)
        self._ok("Smoke-test IOPOLE terminé.")

    # ----------------------------------------------------------- pretty print
    def _print_config(self, cfg: dict):
        sandbox = cfg.get("SANDBOX", True)
        env_label = "SANDBOX (préprod)" if sandbox else "PRODUCTION"
        cid = cfg.get("OAUTH_CLIENT_ID") or ""
        secret = cfg.get("OAUTH_CLIENT_SECRET") or ""
        webhook_secret = cfg.get("WEBHOOK_SECRET") or ""

        self._stdout("-" * 60)
        self._stdout(f"  Provider           : {cfg.get('PROVIDER', '?')}")
        self._stdout(f"  Environnement      : {env_label}")
        self._stdout(f"  Base URL           : {cfg.get('BASE_URL') or '(défaut adapter)'}")
        self._stdout(f"  Token path         : {cfg.get('TOKEN_PATH', '/oauth/token')}")
        self._stdout(f"  API prefix         : {cfg.get('API_PREFIX', '/v1')}")
        self._stdout(f"  Client ID          : {self._mask(cid)}")
        self._stdout(f"  Client secret      : {self._mask(secret)}")
        self._stdout(f"  Webhook secret     : {self._mask(webhook_secret)}")
        self._stdout("-" * 60)

    @staticmethod
    def _mask(value: str) -> str:
        value = value or ""
        if not value:
            return "(vide)"
        if len(value) <= 6:
            return "*" * len(value)
        return f"{value[:4]}…{value[-2:]} (len={len(value)})"

    # --------------------------------------------------------- step accessors
    def _get_client(self):
        from apps.einvoicing.pdp.iopole import IopoleClient
        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        return IopoleClient(sandbox=bool(cfg.get("SANDBOX", True)))

    # --------------------------------------------------------------- step 1
    def _step_auth(self, client) -> bool:
        from apps.einvoicing.pdp.exceptions import (
            PDPAuthError,
            PDPError,
            PDPTransportError,
        )
        self._stdout("\n[1/?] OAuth2 client_credentials …")
        try:
            token = client._get_access_token()
        except PDPAuthError as exc:
            self._error(
                f"  [KO] Authentification refusée : {exc}\n"
                f"       Vérifie EINVOICING_PDP_OAUTH_CLIENT_ID/SECRET dans .env."
            )
            return False
        except PDPTransportError as exc:
            self._error(f"  [KO] Erreur réseau / sandbox indisponible : {exc}")
            return False
        except PDPError as exc:
            self._error(f"  [KO] Erreur PDP : {exc} (status={exc.status_code})")
            return False
        # Token reçu → on n'affiche que les premiers caractères pour audit.
        self._ok(f"  [OK] Access token obtenu — {self._mask(token)}")
        # Affiche aussi quand il expire (pour vérifier le refresh)
        if client._token_expires_at:
            ttl = int(client._token_expires_at - time.time())
            self._stdout(f"       (TTL ~ {ttl}s)")
        return True

    # --------------------------------------------------------------- step 2
    def _step_directory(self, client, probe: str):
        from apps.einvoicing.pdp.exceptions import (
            PDPError,
            PDPNotFoundError,
            PDPValidationError,
        )
        self._stdout(f"\n[2/?] Annuaire — recherche du SIRET {probe} …")
        try:
            result = client.lookup_directory(probe)
        except PDPNotFoundError:
            self._warn(f"  [WARN] Endpoint /directory introuvable (404). "
                       "IOPOLE n'expose peut-être pas cet alias — non bloquant.")
            return
        except PDPValidationError as exc:
            self._warn(f"  [WARN] Annuaire refusé la requête : {exc}")
            return
        except PDPError as exc:
            self._warn(f"  [WARN] Annuaire indisponible : {exc} (status={exc.status_code})")
            return

        if result is None:
            self._warn(f"  [WARN] SIRET {probe} non trouvé dans l'annuaire IOPOLE.")
        else:
            self._ok(
                f"  [OK] {result.get('name', '?')} — SIRET {result.get('siret', '?')} "
                f"({result.get('country_code', '?')})"
            )

    # --------------------------------------------------------------- step 3
    def _resolve_invoice(self, invoice_id: Optional[int]):
        from apps.factures.models import Invoice
        qs = Invoice.objects.all().order_by("-created_at")
        if invoice_id is not None:
            inv = qs.filter(pk=invoice_id).first()
            if inv is None:
                raise CommandError(f"Facture #{invoice_id} introuvable.")
            return inv
        inv = qs.first()
        if inv is None:
            self._warn(
                "  [WARN] Aucune facture en base — exécute "
                "`python manage.py demo_facturx` puis relance avec --submit."
            )
        return inv

    def _step_submit_and_lifecycle(self, client, invoice):
        from apps.einvoicing.pdp.exceptions import PDPError

        self._stdout(f"\n[3/?] Soumission de la facture {invoice.number} (id={invoice.pk}) …")
        try:
            submission = client.submit_invoice(invoice)
        except PDPError as exc:
            self._error(
                f"  [KO] Soumission refusée : {type(exc).__name__} — {exc} "
                f"(status={getattr(exc, 'status_code', '?')})"
            )
            self._stdout(f"       Payload IOPOLE : {json.dumps(getattr(exc, 'payload', {}), indent=2, ensure_ascii=False)[:800]}")
            return

        self._ok(
            f"  [OK] external_id={submission.external_id} "
            f"state={submission.state} accepted_at={submission.accepted_at.isoformat()}"
        )

        self._stdout(f"\n[4/?] Lecture du cycle de vie /invoices/{submission.external_id}/lifecycle_events …")
        try:
            events = client.get_lifecycle(submission.external_id)
        except PDPError as exc:
            self._warn(f"  [WARN] lifecycle indisponible : {exc} (status={exc.status_code})")
            return
        if not events:
            self._stdout("  [..] Aucun événement remonté pour l'instant (normal en sandbox).")
        else:
            for ev in events[:10]:
                self._stdout(f"      - {ev.occurred_at.isoformat()} {ev.state} {ev.reason}")

    # --------------------------------------------------------------- step 5
    def _step_webhook_probe(self):
        from apps.einvoicing.webhooks import verify_iopole_signature
        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        secret = cfg.get("WEBHOOK_SECRET") or ""

        self._stdout("\n[5/?] Probe webhook IOPOLE (signature HMAC locale) …")
        if not secret:
            self._warn("  [WARN] EINVOICING_PDP_WEBHOOK_SECRET vide — étape ignorée.")
            return

        body = json.dumps({
            "event": "lifecycle.deposed",
            "data": {"id": "iop_demo", "state": "DEPOSEE"},
        }, ensure_ascii=False).encode("utf-8")
        ts = int(time.time())
        payload = f"{ts}.".encode("utf-8") + body
        sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        header = f"t={ts},s={sig}"

        if verify_iopole_signature(body=body, header=header):
            self._ok("  [OK] Signature locale acceptée — la chaîne HMAC est correcte.")
        else:
            self._error(
                "  [KO] Signature locale REJETÉE. "
                "Vérifie EINVOICING_PDP_WEBHOOK_SECRET et l'horloge système."
            )

    # ----------------------------------------------------------- helpers UI
    def _stdout(self, msg: str):
        self.stdout.write(msg)

    def _ok(self, msg: str):
        self.stdout.write(self.style.SUCCESS(msg))

    def _warn(self, msg: str):
        self.stdout.write(self.style.WARNING(msg))

    def _error(self, msg: str):
        self.stderr.write(self.style.ERROR(msg))
