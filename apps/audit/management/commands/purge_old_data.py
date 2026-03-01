"""🛡️ BANK-GRADE / RGPD: Anonymize PII in audit logs after retention period.

Usage:
    python manage.py purge_old_data              # dry-run (default)
    python manage.py purge_old_data --execute     # actually anonymize
    python manage.py purge_old_data --months 6    # custom retention (default: 12)

What it does:
- Anonymizes IP addresses in AuditLog.metadata older than N months
- Anonymizes user_agent strings in AuditLog.metadata older than N months
- Does NOT delete records (preserves audit trail integrity)
- Logs all operations for compliance reporting
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "RGPD: Anonymize PII (IP, user_agent) in AuditLog entries older than N months."

    def add_arguments(self, parser):
        parser.add_argument(
            '--months', type=int, default=12,
            help='Retention period in months (default: 12)',
        )
        parser.add_argument(
            '--execute', action='store_true',
            help='Actually perform anonymization (default: dry-run)',
        )

    def handle(self, *args, **options):
        from apps.audit.models import AuditLog

        months = options['months']
        execute = options['execute']
        cutoff = timezone.now() - timedelta(days=months * 30)

        old_entries = AuditLog.objects.filter(timestamp__lt=cutoff)
        total = old_entries.count()

        self.stdout.write(f"Found {total} audit entries older than {months} months (before {cutoff.date()})")

        if not execute:
            self.stdout.write(self.style.WARNING("DRY RUN — use --execute to anonymize"))
            return

        anonymized = 0
        for entry in old_entries.iterator(chunk_size=500):
            changed = False
            meta = entry.metadata or {}
            if 'ip' in meta and meta['ip'] not in ('', 'anonymized'):
                meta['ip'] = 'anonymized'
                changed = True
            if 'user_agent' in meta and meta['user_agent'] not in ('', 'anonymized'):
                meta['user_agent'] = 'anonymized'
                changed = True
            if changed:
                entry.metadata = meta
                entry.save(update_fields=['metadata'])
                anonymized += 1

        self.stdout.write(self.style.SUCCESS(
            f"Anonymized {anonymized}/{total} entries (IPs + user agents)"
        ))
        logger.info("RGPD purge: anonymized %d/%d audit entries older than %d months", anonymized, total, months)
