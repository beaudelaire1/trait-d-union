"""Renvoie les rapports simulateur dont l'email n'est jamais parti.

Filet de sécurité de la livraison : l'envoi du rapport se fait normalement dans
un thread d'arrière-plan côté web (réponse non bloquante). Si ce thread est tué
(recyclage de worker, déploiement, crash) avant d'avoir envoyé l'email, le
rapport reste avec ``pdf_sent_at = NULL``. Ce cron le détecte et le renvoie,
garantissant la livraison.

Planifié via render.yaml (toutes les 15 min environ).
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.simulateur.models import SimulatorReport
from apps.simulateur.services import SimulatorReportService

# Garde-fous : on ne renvoie pas indéfiniment ni trop vieux.
MAX_ATTEMPTS = 5
MAX_AGE_DAYS = 3
BATCH_SIZE = 50


class Command(BaseCommand):
    help = "Renvoie les rapports simulateur dont l'email n'a pas pu partir."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--max-attempts", type=int, default=MAX_ATTEMPTS,
            help=f"Nombre maxi de tentatives par rapport (défaut {MAX_ATTEMPTS}).",
        )
        parser.add_argument(
            "--max-age-days", type=int, default=MAX_AGE_DAYS,
            help=f"Ne traite que les rapports récents (défaut {MAX_AGE_DAYS} j).",
        )
        parser.add_argument(
            "--limit", type=int, default=BATCH_SIZE,
            help=f"Nombre maxi de rapports par exécution (défaut {BATCH_SIZE}).",
        )

    def handle(self, *args, **options) -> None:
        max_attempts = options["max_attempts"]
        cutoff = timezone.now() - timedelta(days=options["max_age_days"])
        limit = options["limit"]

        pending = (
            SimulatorReport.objects
            .filter(
                pdf_sent_at__isnull=True,
                send_attempts__lt=max_attempts,
                created_at__gte=cutoff,
            )
            .order_by("created_at")[:limit]
        )

        total = sent = failed = 0
        for report in pending:
            total += 1
            # charts non persistés : le PDF de renvoi est généré sans les
            # graphiques transitoires (acceptable pour un fallback).
            if SimulatorReportService.deliver(report):
                sent += 1
            else:
                failed += 1

        if total:
            self.stdout.write(
                f"Rapports en attente traités : {total} "
                f"(envoyés : {sent}, échecs : {failed})"
            )
        else:
            self.stdout.write("Aucun rapport en attente d'envoi.")
