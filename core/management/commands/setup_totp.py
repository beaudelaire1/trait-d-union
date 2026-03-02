"""
Management command to create/reset a TOTP device for a user.
Useful when deploying for the first time or when locked out.

Usage (Render shell / production console):
    python manage.py setup_totp admin_tus
    python manage.py setup_totp admin_tus --reset   # delete existing device first
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()


class Command(BaseCommand):
    help = "Create (or reset) a TOTP device for a user and display the provisioning secret."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username of the target user")
        parser.add_argument(
            "--reset",
            action="store_true",
            default=False,
            help="Delete all existing TOTP devices before creating a new one",
        )

    def handle(self, *args, **options):
        username = options["username"]
        reset = options["reset"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist.")

        if reset:
            deleted, _ = TOTPDevice.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing device(s)."))

        existing = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if existing and not reset:
            self.stdout.write(self.style.WARNING(
                f"User '{username}' already has a confirmed device: {existing.name}"
            ))
            self.stdout.write(f"Secret (base32) : {existing.bin_key.hex()}")
            self.stdout.write(f"Config URL       : {existing.config_url}")
            self.stdout.write(
                "\nUse --reset to delete it and create a fresh device."
            )
            return

        device = TOTPDevice.objects.create(
            user=user,
            name=f"CLI-provisioned ({username})",
            confirmed=True,
            tolerance=2,  # ±60s — compense le décalage d'horloge cloud
        )

        self.stdout.write(self.style.SUCCESS(f"\nTOTP device created for '{username}'."))
        self.stdout.write(f"  Device name : {device.name}")
        self.stdout.write(f"  Config URL  : {device.config_url}")
        self.stdout.write(
            "\nCopy the Config URL into your authenticator app "
            "(or use the QR code from the admin login page)."
        )
