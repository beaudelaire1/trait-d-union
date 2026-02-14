#!/usr/bin/env python
"""Script pour mettre à jour le template Prospection initiale."""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from apps.leads.email_models import EmailTemplate

SIGNATURE = '''
<hr style="border: none; border-top: 1px solid rgba(246, 247, 251, 0.1); margin: 30px 0;">
<p style="margin: 0;"><strong>L'équipe Trait d'Union Studio</strong></p>
<p style="margin: 5px 0; color: rgba(246, 247, 251, 0.7);"><em>Architecture Digitale</em></p>
<p style="margin: 10px 0;">
    🌐 <a href="https://www.traitdunion.it" style="color: #0B2DFF;">www.traitdunion.it</a><br>
    📧 <a href="mailto:contact@traitdunion.it" style="color: #0B2DFF;">contact@traitdunion.it</a><br>
    📞 <a href="tel:+594694358041" style="color: #0B2DFF;">+594 694 35 80 41</a>
</p>
'''

NEW_BODY = f'''
<p>Bonjour,</p>

<p>Je vous contacte au nom de <strong>Trait d'Union Studio (TUS)</strong>. Nous accompagnons des entreprises en <strong>Guyane et aux Antilles</strong> dans leur transformation digitale : nous concevons des <strong>outils concrets</strong> qui améliorent l'organisation, le suivi client et la performance au quotidien.</p>

<p>Concrètement, nous pouvons vous aider sur :</p>
<ul>
    <li><strong>Sites web sur mesure</strong> (rapides, fiables, orientés résultats)</li>
    <li><strong>E-commerce</strong> : parcours d'achat optimisé, gestion produits/commandes, paiement, suivi</li>
    <li><strong>Applications web & outils internes (mini-ERP)</strong> : devis/facturation, CRM, suivi des prestations, tableaux de bord, espaces client/équipe, automatisations</li>
</ul>

<p>Notre objectif n'est pas seulement "d'être présent en ligne", mais de mettre en place un <strong>écosystème digital utile</strong>, pensé pour vous faire gagner du temps et soutenir votre croissance.</p>

<p>Si vous le souhaitez, je peux vous proposer un <strong>court échange</strong> (10–15 min) pour comprendre vos besoins et vous dire, très simplement, ce qu'on pourrait améliorer ou automatiser chez vous.</p>

<p>Bien à vous,</p>
{SIGNATURE}
'''

t = EmailTemplate.objects.get(name='Prospection initiale')
t.subject = "Accompagnement digital sur-mesure – Trait d'Union Studio"
t.body_html = NEW_BODY
t.save()

print("✅ Template 'Prospection initiale' mis à jour sur PRODUCTION!")
print(f"   Nouveau sujet: {t.subject}")
