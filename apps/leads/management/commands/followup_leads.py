"""Relance automatique des leads sans réponse.

Usage :
    python manage.py followup_leads          # dry-run (affiche sans envoyer)
    python manage.py followup_leads --send   # envoie les relances

Logique :
- Lead NEW créé il y a 48-72h → relance J+2
- Lead CONTACTED sans activité depuis 7j → relance J+7
- Maximum 1 relance par lead (tracé dans notes)
- Priorise les leads à score élevé

Planification recommandée : cron quotidien à 9h ou django-q2 schedule.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.leads.models import Lead, LeadStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Relance automatique des leads NEW (J+2) et CONTACTED (J+7)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--send', action='store_true',
            help='Envoyer les emails (sinon dry-run)',
        )

    def handle(self, *args, **options):
        send = options['send']
        now = timezone.now()

        # J+2 : leads NEW créés il y a 48-72h
        new_leads = Lead.objects.filter(
            status=LeadStatus.NEW,
            created_at__lte=now - timedelta(hours=48),
            created_at__gte=now - timedelta(hours=72),
        ).exclude(
            notes__icontains='[RELANCE-AUTO]',
        ).order_by('-score')

        # J+7 : leads CONTACTED sans activité depuis 7j
        contacted_leads = Lead.objects.filter(
            status=LeadStatus.CONTACTED,
            created_at__lte=now - timedelta(days=7),
            created_at__gte=now - timedelta(days=10),
        ).exclude(
            notes__icontains='[RELANCE-AUTO-J7]',
        ).order_by('-score')

        self.stdout.write(f"Leads NEW à relancer (J+2) : {new_leads.count()}")
        self.stdout.write(f"Leads CONTACTED à relancer (J+7) : {contacted_leads.count()}")

        count = 0

        for lead in new_leads:
            if send:
                self._send_followup_j2(lead)
                lead.notes = (lead.notes or '') + f"\n[RELANCE-AUTO] {now.strftime('%d/%m/%Y %H:%M')}"
                lead.status = LeadStatus.CONTACTED
                lead.save(update_fields=['notes', 'status'])
            self.stdout.write(f"  → {lead.name} ({lead.email}) score={lead.score}")
            count += 1

        for lead in contacted_leads:
            if send:
                self._send_followup_j7(lead)
                lead.notes = (lead.notes or '') + f"\n[RELANCE-AUTO-J7] {now.strftime('%d/%m/%Y %H:%M')}"
                lead.save(update_fields=['notes'])
            self.stdout.write(f"  → J+7 {lead.name} ({lead.email}) score={lead.score}")
            count += 1

        mode = "ENVOYÉ" if send else "DRY-RUN"
        self.stdout.write(self.style.SUCCESS(f"[{mode}] {count} relance(s) traitée(s)."))

    def _send_followup_j2(self, lead):
        """Email de relance J+2 pour un lead NEW."""
        from core.tasks import async_send_generic_email

        site_url = str(getattr(settings, 'SITE_URL', 'https://www.traitdunion.it')).rstrip('/')
        first_name = lead.name.split()[0] if lead.name else 'Bonjour'

        subject = f"{first_name}, avez-vous des questions sur votre projet ?"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#07080A;font-family:'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#07080A;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#0D1016;border:1px solid rgba(246,247,251,0.08);border-radius:16px;overflow:hidden;">
  <tr><td style="height:4px;background:linear-gradient(135deg,#0B2DFF,#22C55E);"></td></tr>
  <tr><td style="padding:32px 40px 24px;">
    <p style="margin:0;font-size:1rem;color:rgba(246,247,251,0.85);line-height:1.7;">
      Bonjour {first_name},<br><br>
      Vous nous avez contactés il y a quelques jours concernant votre projet.
      Nous voulions simplement nous assurer que vous aviez bien reçu notre réponse
      et savoir si vous aviez des questions.<br><br>
      Si le moment n'est pas le bon, pas de souci — nous restons disponibles quand vous serez prêt.
    </p>
  </td></tr>
  <tr><td style="padding:0 40px 32px;text-align:center;">
    <a href="{site_url}/contact/" style="display:inline-block;background:linear-gradient(135deg,#0B2DFF,#22C55E);color:#fff;text-decoration:none;padding:14px 40px;border-radius:8px;font-weight:700;">
      Reprendre la conversation →
    </a>
  </td></tr>
  <tr><td style="padding:24px 40px;border-top:1px solid rgba(246,247,251,0.08);text-align:center;">
    <p style="margin:0;font-size:0.78rem;color:rgba(246,247,251,0.35);">
      Trait d'Union Studio · Cayenne, Guyane<br>
      <a href="mailto:contact@traitdunion.it" style="color:#4D6FFF;text-decoration:none;">contact@traitdunion.it</a>
    </p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

        async_send_generic_email(lead.email, subject, html)

    def _send_followup_j7(self, lead):
        """Email de relance J+7 pour un lead CONTACTED."""
        from core.tasks import async_send_generic_email

        site_url = str(getattr(settings, 'SITE_URL', 'https://www.traitdunion.it')).rstrip('/')
        first_name = lead.name.split()[0] if lead.name else 'Bonjour'

        subject = f"Dernière relance — votre projet web, {first_name}"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#07080A;font-family:'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#07080A;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#0D1016;border:1px solid rgba(246,247,251,0.08);border-radius:16px;overflow:hidden;">
  <tr><td style="height:4px;background:linear-gradient(135deg,#0B2DFF,#22C55E);"></td></tr>
  <tr><td style="padding:32px 40px 24px;">
    <p style="margin:0;font-size:1rem;color:rgba(246,247,251,0.85);line-height:1.7;">
      Bonjour {first_name},<br><br>
      C'est notre dernière relance — nous ne voulons pas être insistants.<br><br>
      Si votre projet est toujours d'actualité, nous serions ravis d'en discuter.
      Sinon, nous comprenons parfaitement et vous souhaitons bonne continuation.<br><br>
      Dans tous les cas, nos ressources gratuites restent accessibles :
    </p>
    <ul style="color:rgba(246,247,251,0.7);line-height:2;">
      <li><a href="{site_url}/simulateur/" style="color:#4D6FFF;">Diagnostics gratuits (29 simulateurs)</a></li>
      <li><a href="{site_url}/chroniques/" style="color:#4D6FFF;">Articles & réflexions</a></li>
    </ul>
  </td></tr>
  <tr><td style="padding:24px 40px;border-top:1px solid rgba(246,247,251,0.08);text-align:center;">
    <p style="margin:0;font-size:0.78rem;color:rgba(246,247,251,0.35);">
      Trait d'Union Studio · Cayenne, Guyane
    </p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

        async_send_generic_email(lead.email, subject, html)
