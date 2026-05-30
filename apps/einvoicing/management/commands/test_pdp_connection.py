"""Test de connectivité avec la PDP configurée (B2BRouter sandbox).

Vérifie en lecture seule (GET /accounts) que la clé API fonctionne, sans
créer de ressource côté PDP. Ne loggue ni la clé, ni les tokens.

Usage :
    python manage.py test_pdp_connection
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Teste la connectivité avec la PDP configurée (lecture seule)."

    def handle(self, *args, **options):
        from apps.einvoicing.pdp import get_pdp_client
        from apps.einvoicing.pdp.exceptions import (
            PDPAuthError,
            PDPError,
            PDPRateLimitError,
            PDPTransportError,
        )

        cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
        provider = cfg.get("PROVIDER", "?")
        sandbox = cfg.get("SANDBOX", True)
        env_label = "SANDBOX (staging)" if sandbox else "PRODUCTION"
        api_key = cfg.get("API_KEY", "") or ""
        masked_key = (api_key[:8] + "…") if api_key else "(vide)"
        account_id = cfg.get("ACCOUNT_ID", "") or "(non defini)"

        self.stdout.write("-" * 60)
        self.stdout.write(f"  Provider     : {provider}")
        self.stdout.write(f"  Environment  : {env_label}")
        self.stdout.write(f"  API key      : {masked_key} (longueur {len(api_key)})")
        self.stdout.write(f"  Account ID   : {account_id}")
        self.stdout.write("-" * 60)

        client = get_pdp_client(provider)

        # Test 1 : GET /accounts -- ne cree rien, valide juste la cle.
        self.stdout.write("\n[1/2] Test authentification (GET /accounts)...")
        try:
            body = client._request("GET", "/accounts")
        except PDPAuthError as exc:
            self.stderr.write(self.style.ERROR(
                f"  [KO] Authentification refusee par la PDP : {exc}\n"
                f"       Verifie EINVOICING_PDP_API_KEY dans .env."
            ))
            return
        except PDPRateLimitError as exc:
            self.stderr.write(self.style.WARNING(
                f"  [WARN] Rate limit atteint : retry dans {exc.retry_after or '?'}s."
            ))
            return
        except PDPTransportError as exc:
            self.stderr.write(self.style.ERROR(
                f"  [KO] Erreur reseau / serveur PDP : {exc}"
            ))
            return
        except PDPError as exc:
            self.stderr.write(self.style.ERROR(
                f"  [KO] Erreur PDP : {exc} (status={exc.status_code})"
            ))
            return

        if isinstance(body, dict):
            accounts = body.get("accounts") or body.get("data") or []
        elif isinstance(body, list):
            accounts = body
        else:
            accounts = []

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] Authentification reussie -- {len(accounts)} compte(s) accessible(s)."
        ))
        for acc in accounts[:5]:
            ident = acc.get("identifier") or acc.get("id") or "?"
            name = acc.get("name") or acc.get("legal_name") or ""
            self.stdout.write(f"      - {ident} -- {name}")

        # Test 2 : Si un account_id est fourni, on recupere ses details.
        if account_id and account_id != "(non defini)":
            self.stdout.write(f"\n[2/2] Test compte specifique (GET /accounts/{account_id})...")
            try:
                detail = client._request("GET", f"/accounts/{account_id}")
                if isinstance(detail, dict):
                    name = detail.get("name") or detail.get("legal_name") or ""
                    country = detail.get("country") or "?"
                    tin = detail.get("tin_value") or "?"
                    self.stdout.write(self.style.SUCCESS(
                        f"  [OK] Compte recupere -- {name} ({country}, TIN {tin})"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS("  [OK] Compte trouve."))
            except PDPError as exc:
                self.stderr.write(self.style.WARNING(
                    f"  [WARN] Lecture compte echouee : {exc} (status={exc.status_code})"
                ))
        else:
            self.stdout.write("\n[2/2] EINVOICING_PDP_ACCOUNT_ID non defini -- etape ignoree.")

        self.stdout.write("-" * 60)
        self.stdout.write(self.style.SUCCESS("[OK] Connectivite PDP fonctionnelle."))
