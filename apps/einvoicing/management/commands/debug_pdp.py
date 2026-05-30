"""Debug brut de la connexion PDP — affiche la requete et la reponse.

Usage : python manage.py debug_pdp
"""
from __future__ import annotations

import os

import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Debug brut de la connexion PDP (HTTP brut)."

    def handle(self, *args, **options):
        api_key = os.environ.get("EINVOICING_PDP_API_KEY", "")
        version = os.environ.get("EINVOICING_PDP_API_VERSION", "2026-03-02")
        sandbox = os.environ.get("EINVOICING_PDP_SANDBOX", "1") == "1"
        base = "https://api-staging.b2brouter.net" if sandbox else "https://api.b2brouter.net"

        self.stdout.write(f"Base URL : {base}")
        self.stdout.write(f"Key (first 10) : {api_key[:10]}... (len={len(api_key)})")
        self.stdout.write(f"Version : {version}")

        for path in ("/accounts", "/groups"):
            url = f"{base}{path}"
            self.stdout.write(f"\n--- GET {url} ---")
            try:
                resp = requests.get(
                    url,
                    headers={
                        "Accept": "application/json",
                        "X-B2B-API-Key": api_key,
                        "X-B2B-API-Version": version,
                        "User-Agent": "TUS-eInvoicing-debug/1.0",
                    },
                    timeout=20,
                )
                self.stdout.write(f"Status   : {resp.status_code}")
                # Afficher quelques headers utiles
                for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After", "Content-Type"):
                    if h in resp.headers:
                        self.stdout.write(f"  {h}: {resp.headers[h]}")
                body = resp.text or ""
                # Limiter l'affichage
                self.stdout.write(f"Body (1000c) : {body[:1000]}")
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  Exception : {exc!r}")
