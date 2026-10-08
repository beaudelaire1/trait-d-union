"""Container-startup TOTP maintenance for Coolify (no terminal needed).

Always clears failed-attempt lockouts. When both variables are set in Coolify,
also performs a one-shot ``setup_totp --reset`` for that user:

    TOTP_RESET_USER=admin_tus
    TOTP_RESET_DATE=2026-10-08 15:00     # Europe/Paris, "now" when you set it

The reset only happens if every TOTP device of the user was created before
TOTP_RESET_DATE. The new pending device is created after it, so later restarts
do nothing even if the variables are left in place (remove them anyway).
"""
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = 'Clear TOTP lockouts and apply a one-shot reset requested via environment variables.'

    def handle(self, *args, **options):
        unlocked = TOTPDevice.objects.filter(throttling_failure_count__gt=0).update(
            throttling_failure_count=0,
            throttling_failure_timestamp=None,
        )
        self.stdout.write(f'[TUS] TOTP throttling reset: {unlocked}')

        username = os.environ.get('TOTP_RESET_USER', '').strip()
        raw_date = os.environ.get('TOTP_RESET_DATE', '').strip()
        if not username:
            return
        try:
            requested_at = timezone.make_aware(datetime.strptime(raw_date, '%Y-%m-%d %H:%M'))
        except ValueError:
            self.stderr.write(
                '[TUS] TOTP_RESET_USER is set but TOTP_RESET_DATE is missing or not '
                '"YYYY-MM-DD HH:MM"; no reset performed.'
            )
            return

        user = get_user_model().objects.filter(username=username).first()
        if user is None:
            self.stderr.write(f'[TUS] TOTP reset: user {username!r} not found.')
            return
        if TOTPDevice.objects.filter(user=user, created_at__gte=requested_at).exists():
            self.stdout.write(f'[TUS] TOTP reset for {username} already applied; skipping.')
            return

        call_command('setup_totp', username, reset=True, stdout=self.stdout, stderr=self.stderr)
