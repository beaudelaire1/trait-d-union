"""Script temporaire pour mettre à jour les templates email avec la signature."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.leads.email_models import EmailTemplate

# Signature commune avec coordonnées
SIGNATURE = '''
<hr style="border: none; border-top: 1px solid rgba(246, 247, 251, 0.1); margin: 30px 0;">
<p style="margin: 0;"><strong>L'équipe Trait d'Union Studio</strong></p>
<p style="margin: 5px 0; color: rgba(246, 247, 251, 0.7);"><em>Design & Développement Web Premium</em></p>
<p style="margin: 10px 0;">
    🌐 <a href="https://www.traitdunion.it" style="color: #0B2DFF;">www.traitdunion.it</a><br>
    📧 <a href="mailto:contact@traitdunion.it" style="color: #0B2DFF;">contact@traitdunion.it</a><br>
    📞 <a href="tel:+594694358041" style="color: #0B2DFF;">+594 694 35 80 41</a>
</p>
'''

count = 0
for template in EmailTemplate.objects.all():
    if 'www.traitdunion.it' not in template.body_html:
        body = template.body_html
        
        # Nettoyer les anciennes signatures (différentes variantes)
        old_signatures = [
            "<p><strong>L'équipe Trait d'Union Studio</strong></p>",
            "<p><strong>L'équipe Trait d'Union Studio</strong><br>",
            "<em>Design & Développement Web Premium</em></p>",
        ]
        for old_sig in old_signatures:
            body = body.replace(old_sig, '')
        
        # Ajouter la nouvelle signature
        template.body_html = body.strip() + SIGNATURE
        template.save()
        count += 1
        print(f'✓ Mis à jour: {template.name}')

print(f'\n🎉 Total: {count} templates mis à jour avec les coordonnées')
