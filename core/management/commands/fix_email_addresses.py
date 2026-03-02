"""
Management command to fix existing client accounts missing allauth EmailAddress.
Marks their email as verified so ACCOUNT_EMAIL_VERIFICATION='mandatory' won't block login.

Usage:
    python manage.py fix_email_addresses          # dry-run
    python manage.py fix_email_addresses --apply   # apply changes
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Create verified EmailAddress records for users missing one (fixes allauth mandatory verification)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually create the EmailAddress records (default: dry-run)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        fixed = 0

        users = User.objects.filter(is_active=True).exclude(email="")
        for user in users:
            has_email = EmailAddress.objects.filter(user=user, email__iexact=user.email).exists()
            if not has_email:
                if apply:
                    EmailAddress.objects.create(
                        user=user,
                        email=user.email,
                        verified=True,
                        primary=True,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {user.username} ({user.email})"))
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  {user.username} ({user.email}) — missing"))
                fixed += 1

        if fixed == 0:
            self.stdout.write(self.style.SUCCESS("All users already have a verified EmailAddress."))
        elif apply:
            self.stdout.write(self.style.SUCCESS(f"\n{fixed} EmailAddress record(s) created."))
        else:
            self.stdout.write(self.style.WARNING(
                f"\n{fixed} user(s) missing EmailAddress. Re-run with --apply to fix."
            ))
