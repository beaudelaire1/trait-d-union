"""Inspect or re-enrol one admin TOTP factor from a trusted server console.

A reset is an exceptional, audited recovery operation. It never prints a
confirmed factor's secret to logs or exposes the secret over the login page.
The pending factor must be confirmed with a valid code from the authenticator.

    python manage.py setup_totp admin_tus               # inspect only
    python manage.py setup_totp admin_tus --reset       # operator-authorized recovery
"""
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = 'Inspect staff TOTP devices, or explicitly reset them for secure re-enrolment.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument(
            '--reset', action='store_true',
            help='Remove all factors for this user and create one unconfirmed factor.',
        )

    def handle(self, *args, **options):
        username = options['username']
        reset = options['reset']
        User = get_user_model()

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(username=username)
            except User.DoesNotExist:
                raise CommandError('Compte introuvable.')

            if not user.is_active or not user.is_staff:
                raise CommandError('Ce compte ne dispose pas d’un accès administrateur actif.')

            devices = TOTPDevice.objects.filter(user=user)
            if not reset:
                self.stdout.write(
                    f'Compte {username}: {devices.filter(confirmed=True).count()} '
                    f'appareil(s) actif(s), {devices.filter(confirmed=False).count()} en attente.'
                )
                for device in devices:
                    current_t = int((time.time() - device.t0) // device.step)
                    blocked = device.verify_is_allowed()[0] is False
                    self.stdout.write(
                        f'  id={device.pk} confirmed={device.confirmed} '
                        f'drift={device.drift} last_t_ahead={device.last_t > current_t + device.tolerance} '
                        f'throttled={blocked} failures={device.throttling_failure_count}'
                    )
                self.stdout.write('Aucun secret TOTP n’est affiché. Utilisez --reset seulement si nécessaire.')
                return

            deleted, _ = devices.delete()
            new_device = TOTPDevice.objects.create(
                user=user,
                name='Microsoft Authenticator (en attente)',
                confirmed=False,
                tolerance=1,
            )
            self.stdout.write(
                self.style.WARNING(
                    f'RECOVERY user={username}: {deleted} ancien(s) appareil(s) supprimé(s), '
                    f'nouvel appareil id={new_device.pk} EN ATTENTE de confirmation.'
                )
            )
            self.stdout.write(
                'Sur la page de connexion, saisissez vos identifiants, choisissez '
                '« Configurer Microsoft Authenticator », scannez le QR code et '
                'validez un code dans la fenêtre. Ne diffusez pas le QR code.'
            )
