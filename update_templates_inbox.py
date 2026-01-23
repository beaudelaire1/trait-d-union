#!/usr/bin/env python
"""Mettre à jour les templates avec un format simple pour inbox."""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from apps.leads.email_models import EmailTemplate

# Signature simple (pas de HTML complexe)
SIGNATURE_SIMPLE = '''
--
<strong>Vilme BEAUDELAIRE</strong>
Trait d'Union Studio
📧 contact@traitdunion.it
📞 +594 694 35 80 41
🌐 www.traitdunion.it
'''

# Template Prospection initiale - format simple
PROSPECTION_SIMPLE = f'''<p>Bonjour,</p>

<p>Je vous contacte au nom de Trait d'Union Studio (TUS). Nous accompagnons des entreprises en Guyane et aux Antilles dans leur transformation digitale, avec une approche qui va au-delà d'une agence web classique : nous concevons des outils concrets qui améliorent l'organisation, le suivi client et la performance au quotidien.</p>

<p>Concrètement, nous pouvons vous aider sur :</p>

<p>• Sites web sur mesure (rapides, fiables, orientés résultats)<br>
• E-commerce : parcours d'achat optimisé, gestion produits/commandes, paiement, suivi<br>
• Applications web & outils internes (mini-ERP) : devis/facturation, CRM, suivi des prestations, tableaux de bord, espaces client/équipe, automatisations<br>
• Identité & design premium : une image cohérente et professionnelle qui vous différencie</p>

<p>Notre objectif n'est pas seulement "d'être présent en ligne", mais de mettre en place un écosystème digital utile, pensé pour vous faire gagner du temps et soutenir votre croissance.</p>

<p>Si vous le souhaitez, je peux vous proposer un court échange (10-15 min) pour comprendre vos besoins et vous dire, très simplement, ce qu'on pourrait améliorer ou automatiser chez vous.</p>

<p>Bien à vous,</p>
{SIGNATURE_SIMPLE}'''

# Mettre à jour le template
t = EmailTemplate.objects.get(name='Prospection initiale')
t.subject = "Question sur votre activité"  # Sujet neutre, pas marketing
t.body_html = PROSPECTION_SIMPLE
t.save()
print("✅ Template 'Prospection initiale' mis à jour (format inbox)")

# Créer un template encore plus simple
PROSPECTION_ULTRA_SIMPLE = f'''<p>Bonjour,</p>

<p>Je me permets de vous contacter car j'ai remarqué votre activité et je pense sincèrement pouvoir vous aider.</p>

<p>Chez Trait d'Union Studio, nous créons des sites web et des outils digitaux pour les entreprises de Guyane et des Antilles. Pas de formules toutes faites : on part de vos besoins réels.</p>

<p>Seriez-vous disponible pour un appel de 10 minutes cette semaine ? Je pourrais vous donner quelques pistes concrètes, sans engagement.</p>

<p>Bien cordialement,</p>
{SIGNATURE_SIMPLE}'''

# Créer ou mettre à jour
t2, created = EmailTemplate.objects.update_or_create(
    name='Prospection simple (inbox)',
    defaults={
        'category': 'prospection',
        'subject': 'Votre projet web',
        'body_html': PROSPECTION_ULTRA_SIMPLE,
        'is_active': True,
    }
)
print(f"{'✅ Créé' if created else '↻ Mis à jour'}: Template 'Prospection simple (inbox)'")

# Template de relance simple
RELANCE_SIMPLE = f'''<p>Bonjour,</p>

<p>Je vous avais contacté il y a quelques jours concernant vos projets web.</p>

<p>Je me permets de revenir vers vous car je pense vraiment pouvoir vous apporter quelque chose de concret. Avez-vous eu le temps d'y réfléchir ?</p>

<p>Je reste disponible si vous souhaitez en discuter.</p>

<p>Bonne journée,</p>
{SIGNATURE_SIMPLE}'''

t3, created = EmailTemplate.objects.update_or_create(
    name='Relance simple (inbox)',
    defaults={
        'category': 'relance',
        'subject': 'Suite à mon message',
        'body_html': RELANCE_SIMPLE,
        'is_active': True,
    }
)
print(f"{'✅ Créé' if created else '↻ Mis à jour'}: Template 'Relance simple (inbox)'")

print("\n📊 Total templates:", EmailTemplate.objects.count())
