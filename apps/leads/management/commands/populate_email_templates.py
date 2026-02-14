"""Management command to populate default email templates."""
from django.core.management.base import BaseCommand
from apps.leads.email_models import EmailTemplate, EmailTemplateCategory


# Signature commune pour tous les emails
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


class Command(BaseCommand):
    help = 'Populate database with default email templates following TUS brand guidelines'

    def handle(self, *args, **options):
        templates = [
            # ==========================================
            # 🎯 PROSPECTION
            # ==========================================
            {
                'name': 'Prospection initiale',
                'category': EmailTemplateCategory.PROSPECTION,
                'subject': 'Accompagnement digital sur-mesure – Trait d\'Union Studio',
                'body_html': f'''
<p>Bonjour,</p>

<p>Je vous contacte au nom de <strong>Trait d'Union Studio (TUS)</strong>. Nous accompagnons des entreprises en <strong>Guyane et aux Antilles</strong> dans leur transformation digitale : nous concevons des <strong>outils concrets</strong> qui améliorent l'organisation, le suivi client et la performance au quotidien.</p>

<p>Concrètement, nous pouvons vous aider sur :</p>
<ul>
    <li><strong>Sites web sur mesure</strong> (rapides, fiables, orientés résultats)</li>
    <li><strong>E-commerce</strong> : parcours d'achat optimisé, gestion produits/commandes, paiement, suivi</li>
    <li><strong>Applications web & outils internes (mini-ERP)</strong> : devis/facturation, CRM, suivi des prestations, tableaux de bord, espaces client/équipe, automatisations</li>
    <li><strong>Identité & design premium</strong> : une image cohérente et professionnelle qui vous différencie</li>
</ul>

<p>Notre objectif n'est pas seulement "d'être présent en ligne", mais de mettre en place un <strong>écosystème digital utile</strong>, pensé pour vous faire gagner du temps et soutenir votre croissance.</p>

<p>Si vous le souhaitez, je peux vous proposer un <strong>court échange</strong> (10–15 min) pour comprendre vos besoins et vous dire, très simplement, ce qu'on pourrait améliorer ou automatiser chez vous.</p>

<p>Bien à vous,</p>
{SIGNATURE}
                '''
            },
            {
                'name': 'Prospection ciblée e-commerce',
                'category': EmailTemplateCategory.PROSPECTION,
                'subject': 'Votre boutique en ligne mérite mieux 🛒',
                'body_html': f'''
<p>Bonjour,</p>

<p>Je viens de découvrir votre activité et je pense sincèrement que vous passez à côté d'<strong>opportunités de vente en ligne</strong>.</p>

<p>🎯 <strong>Le constat :</strong></p>
<p>En 2026, <strong>78% des achats</strong> commencent par une recherche en ligne. Sans présence digitale optimisée, vous laissez vos concurrents capter vos clients potentiels.</p>

<p>💰 <strong>Ce qu'on peut faire ensemble :</strong></p>
<ul>
    <li>Créer une boutique en ligne <strong>qui vend vraiment</strong></li>
    <li>Optimiser votre référencement pour être visible sur Google</li>
    <li>Mettre en place un système de paiement sécurisé et simple</li>
    <li>Automatiser vos processus (stock, livraison, factures)</li>
</ul>

<p>📈 <strong>Résultat moyen de nos clients :</strong> +40% de chiffre d'affaires dans les 6 premiers mois.</p>

<p>Ça vous tente d'en discuter ?</p>
{SIGNATURE}
                '''
            },
            {
                'name': 'Prospection refonte de site',
                'category': EmailTemplateCategory.PROSPECTION,
                'subject': 'Votre site web a besoin d\'un coup de boost ? 🚀',
                'body_html': f'''
<p>Bonjour,</p>

<p>J'ai pris le temps de visiter votre site web et j'ai quelques observations qui pourraient vous intéresser.</p>

<p>⚠️ <strong>Ce que j'ai remarqué :</strong></p>
<ul>
    <li>Design qui date un peu (les visiteurs jugent en 3 secondes)</li>
    <li>Temps de chargement perfectible</li>
    <li>Expérience mobile à améliorer</li>
    <li>Potentiel SEO inexploité</li>
</ul>

<p>✅ <strong>Ce qu'une refonte vous apporterait :</strong></p>
<ul>
    <li>Image <strong>moderne et professionnelle</strong></li>
    <li>Site <strong>ultra-rapide</strong> (moins de 2 secondes de chargement)</li>
    <li>Parfaitement adapté aux mobiles</li>
    <li><strong>Meilleur référencement</strong> Google</li>
</ul>

<p>Je serais ravi de vous présenter quelques pistes d'amélioration lors d'un appel de 15 minutes. Qu'en dites-vous ?</p>
{SIGNATURE}
                '''
            },
            
            # ==========================================
            # 🔄 RELANCE
            # ==========================================
            {
                'name': 'Relance douce',
                'category': EmailTemplateCategory.RELANCE,
                'subject': 'Re: Votre projet digital 💭',
                'body_html': '''
<p>Bonjour,</p>

<p>Je me permets de revenir vers vous concernant notre dernier échange.</p>

<p>Je sais que vous êtes probablement très occupé(e), mais je voulais simplement m'assurer que vous aviez bien reçu mon message précédent.</p>

<p>🤔 <strong>Peut-être que :</strong></p>
<ul>
    <li>Le timing n'est pas le bon (pas de souci, dites-le moi)</li>
    <li>Vous avez des questions auxquelles je peux répondre</li>
    <li>Vous souhaitez explorer d'autres options</li>
</ul>

<p>Je reste à votre disposition, sans aucune pression.</p>

<p>Bonne journée,</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Relance proposition commerciale',
                'category': EmailTemplateCategory.RELANCE,
                'subject': '📋 Votre proposition commerciale - Des questions ?',
                'body_html': '''
<p>Bonjour,</p>

<p>Je reviens vers vous concernant la <strong>proposition commerciale</strong> que nous vous avons transmise le [DATE].</p>

<p>📌 <strong>Pour rappel, notre offre inclut :</strong></p>
<ul>
    <li>✓ [Prestation principale]</li>
    <li>✓ [Prestation 2]</li>
    <li>✓ [Prestation 3]</li>
    <li>✓ Support et accompagnement personnalisé</li>
</ul>

<p>💬 <strong>Avez-vous des questions ?</strong></p>
<p>Je serais ravi d'organiser un <strong>point téléphonique rapide</strong> pour clarifier certains points ou ajuster notre proposition à vos besoins.</p>

<p>⏰ <strong>Bon à savoir :</strong> Cette offre est valable jusqu'au [DATE LIMITE].</p>

<p>Dans l'attente de votre retour,</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Relance dernier rappel',
                'category': EmailTemplateCategory.RELANCE,
                'subject': '⏰ Dernière relance - Votre projet web',
                'body_html': '''
<p>Bonjour,</p>

<p>C'est mon dernier message concernant notre échange sur votre projet digital.</p>

<p>Je comprends parfaitement si :</p>
<ul>
    <li>🔴 Ce n'est plus d'actualité</li>
    <li>🟡 Vous préférez reporter à plus tard</li>
    <li>🟢 Vous êtes toujours intéressé(e) mais débordé(e)</li>
</ul>

<p>Un simple mot de votre part me permettrait de savoir où vous en êtes.</p>

<p>Quoi qu'il en soit, je vous souhaite une excellente continuation dans vos projets ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 💼 DEVIS
            # ==========================================
            {
                'name': 'Envoi de devis',
                'category': EmailTemplateCategory.DEVIS,
                'subject': '📋 Votre devis Trait d\'Union Studio - [Projet]',
                'body_html': '''
<p>Bonjour,</p>

<p>Suite à nos échanges, j'ai le plaisir de vous transmettre notre <strong>proposition commerciale détaillée</strong>.</p>

<p>📦 <strong>Récapitulatif de votre projet :</strong></p>
<ul>
    <li><strong>Type :</strong> [Site vitrine / E-commerce / Application web]</li>
    <li><strong>Objectif :</strong> [Objectif principal]</li>
    <li><strong>Délai :</strong> [X semaines/mois]</li>
</ul>

<p>💰 <strong>Investissement total :</strong> [MONTANT] € HT</p>

<p>📎 Vous trouverez ci-joint le devis détaillé avec le descriptif complet des prestations.</p>

<p>✨ <strong>Ce qui est inclus :</strong></p>
<ul>
    <li>✓ Design sur-mesure aux couleurs de votre marque</li>
    <li>✓ Développement responsive (mobile, tablette, desktop)</li>
    <li>✓ Optimisation SEO de base</li>
    <li>✓ Formation à l'utilisation</li>
    <li>✓ Support technique 30 jours</li>
</ul>

<p>Je reste disponible pour toute question ou ajustement.</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Devis accepté - Prochaines étapes',
                'category': EmailTemplateCategory.DEVIS,
                'subject': '🎉 Devis accepté - On démarre votre projet !',
                'body_html': '''
<p>Bonjour,</p>

<p>🎉 <strong>Excellente nouvelle !</strong> Nous avons bien reçu votre accord pour démarrer le projet.</p>

<p>📋 <strong>Prochaines étapes :</strong></p>
<ol>
    <li><strong>Aujourd'hui :</strong> Vous recevrez la facture d'acompte (30%)</li>
    <li><strong>Dès réception du paiement :</strong> Kick-off du projet</li>
    <li><strong>Semaine 1 :</strong> Réunion de cadrage + maquettes</li>
    <li><strong>Semaine 2-X :</strong> Développement avec points réguliers</li>
</ol>

<p>📅 <strong>Planning prévisionnel :</strong></p>
<ul>
    <li>Démarrage : [DATE]</li>
    <li>Première version : [DATE]</li>
    <li>Livraison finale : [DATE]</li>
</ul>

<p>Nous sommes impatients de commencer ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 🙏 REMERCIEMENT
            # ==========================================
            {
                'name': 'Remerciement après rendez-vous',
                'category': EmailTemplateCategory.REMERCIEMENT,
                'subject': '🙏 Merci pour votre temps !',
                'body_html': '''
<p>Bonjour,</p>

<p>Je tenais à vous remercier sincèrement pour le temps que vous nous avez accordé lors de notre échange.</p>

<p>📝 <strong>Ce que j'ai retenu de notre discussion :</strong></p>
<ul>
    <li><strong>Votre projet :</strong> [Description]</li>
    <li><strong>Vos objectifs :</strong> [Objectifs clés]</li>
    <li><strong>Vos défis :</strong> [Points de friction actuels]</li>
    <li><strong>Timeline souhaitée :</strong> [Délais]</li>
</ul>

<p>📎 Comme convenu, je vous prépare une proposition adaptée à vos besoins. Vous la recevrez d'ici [DÉLAI].</p>

<p>D'ici là, n'hésitez pas si vous avez des questions ou des précisions à apporter.</p>

<p>À très bientôt,</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Remerciement projet terminé',
                'category': EmailTemplateCategory.REMERCIEMENT,
                'subject': '🎉 Projet livré - Un immense merci !',
                'body_html': '''
<p>Bonjour,</p>

<p>🎉 <strong>Votre projet est maintenant en ligne !</strong></p>

<p>Nous tenions à vous remercier pour votre confiance tout au long de cette collaboration. Ce fut un réel plaisir de travailler avec vous.</p>

<p>🔗 <strong>Votre nouveau site :</strong> [URL DU SITE]</p>

<p>📚 <strong>Ressources utiles :</strong></p>
<ul>
    <li>Guide d'utilisation (en pièce jointe)</li>
    <li>Accès administration : [URL ADMIN]</li>
    <li>Support technique : support@traitdunion.it</li>
</ul>

<p>⭐ <strong>Un petit service ?</strong></p>
<p>Si vous êtes satisfait de notre travail, un avis Google ou une recommandation à votre réseau nous aiderait énormément ! <a href="[LIEN AVIS]">Laisser un avis</a></p>

<p>Nous restons à votre disposition pour toute question ou évolution future.</p>

<p>Encore merci et belle réussite avec votre nouveau site ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Remerciement avis client',
                'category': EmailTemplateCategory.REMERCIEMENT,
                'subject': '💜 Merci pour votre avis !',
                'body_html': '''
<p>Bonjour,</p>

<p>Nous venons de lire votre avis et nous sommes vraiment touchés ! 💜</p>

<p>Vos mots comptent énormément pour nous et nous motivent à toujours nous dépasser pour nos clients.</p>

<p>En guise de remerciement, nous vous offrons <strong>10% de réduction</strong> sur votre prochaine prestation (maintenance, évolution, nouveau projet).</p>

<p>🎁 <strong>Code promo :</strong> MERCI10</p>

<p>N'hésitez pas à nous recommander autour de vous, c'est le plus beau compliment que vous puissiez nous faire.</p>

<p>À très bientôt,</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 🎁 BONS PLANS
            # ==========================================
            {
                'name': 'Offre spéciale limitée',
                'category': EmailTemplateCategory.BONS_PLANS,
                'subject': '🔥 Offre flash : -20% sur votre site web !',
                'body_html': '''
<p>Bonjour,</p>

<p>🎉 <strong>Offre exceptionnelle réservée à nos contacts privilégiés !</strong></p>

<p>Pour célébrer [OCCASION], nous vous offrons <strong>20% de réduction</strong> sur tous nos services de création web.</p>

<p>🎯 <strong>Cette offre comprend :</strong></p>
<ul>
    <li>✓ Site vitrine professionnel</li>
    <li>✓ Boutique e-commerce</li>
    <li>✓ Application web sur-mesure</li>
    <li>✓ Refonte de site existant</li>
</ul>

<p>⏰ <strong>Attention :</strong> Offre valable uniquement jusqu'au <strong>[DATE LIMITE]</strong></p>

<p>💬 Pour en profiter, répondez simplement à cet email ou réservez un appel découverte.</p>

<p>Ne laissez pas passer cette opportunité ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Pack maintenance avantageux',
                'category': EmailTemplateCategory.BONS_PLANS,
                'subject': '🛡️ Protégez votre site avec notre pack maintenance',
                'body_html': '''
<p>Bonjour,</p>

<p>Votre site web est un <strong>investissement précieux</strong>. Il mérite d'être chouchouté !</p>

<p>🛡️ <strong>Notre Pack Maintenance :</strong></p>
<ul>
    <li>✓ Mises à jour de sécurité mensuelles</li>
    <li>✓ Sauvegardes automatiques quotidiennes</li>
    <li>✓ Monitoring actif</li>
    <li>✓ Support prioritaire</li>
    <li>✓ Petites modifications incluses (2h/mois)</li>
</ul>

<p>💰 <strong>Tarif :</strong> À partir de [XX]€/mois</p>

<p>🎁 <strong>Offre de lancement :</strong> Le premier mois offert !</p>

<p>Protégez votre investissement dès maintenant.</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Parrainage récompensé',
                'category': EmailTemplateCategory.BONS_PLANS,
                'subject': '🎁 Gagnez 100€ en nous recommandant !',
                'body_html': '''
<p>Bonjour,</p>

<p>Vous êtes satisfait de nos services ? <strong>Faites-en profiter votre réseau !</strong></p>

<p>🎁 <strong>Programme de parrainage :</strong></p>
<ul>
    <li><strong>Vous gagnez :</strong> 100€ de réduction sur votre prochaine facture</li>
    <li><strong>Votre filleul gagne :</strong> 10% de réduction sur son premier projet</li>
</ul>

<p>📋 <strong>Comment ça marche ?</strong></p>
<ol>
    <li>Parlez de nous à un ami, collègue ou partenaire</li>
    <li>Il nous contacte en mentionnant votre nom</li>
    <li>Dès que son projet démarre, vous recevez votre récompense !</li>
</ol>

<p>Pas de limite ! Plus vous parrainez, plus vous gagnez. 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # ✅ CONFIRMATION
            # ==========================================
            {
                'name': 'Confirmation de rendez-vous',
                'category': EmailTemplateCategory.CONFIRMATION,
                'subject': '📅 Rendez-vous confirmé - [DATE]',
                'body_html': '''
<p>Bonjour,</p>

<p>Je vous confirme notre <strong>rendez-vous</strong> :</p>

<p>📅 <strong>Date :</strong> [JOUR] [DATE]<br>
🕐 <strong>Heure :</strong> [HEURE]<br>
📍 <strong>Lieu :</strong> [ADRESSE / Visioconférence]<br>
⏱️ <strong>Durée prévue :</strong> [XX] minutes</p>

<p>📋 <strong>Ordre du jour :</strong></p>
<ul>
    <li>Présentation de vos besoins</li>
    <li>Échange sur votre projet</li>
    <li>Nos recommandations</li>
    <li>Questions / Réponses</li>
</ul>

<p>💻 <strong>Lien visio :</strong> <a href="[LIEN]">[LIEN]</a></p>

<p>Si vous devez modifier ce créneau, merci de me prévenir 24h à l'avance.</p>

<p>À [JOUR] ! 👋</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Confirmation de commande',
                'category': EmailTemplateCategory.CONFIRMATION,
                'subject': '✅ Commande confirmée - Projet [NOM]',
                'body_html': '''
<p>Bonjour,</p>

<p>🎉 <strong>Votre commande est confirmée !</strong></p>

<p>Nous avons bien reçu votre paiement et votre projet est officiellement lancé.</p>

<p>📦 <strong>Récapitulatif :</strong></p>
<ul>
    <li><strong>Projet :</strong> [NOM DU PROJET]</li>
    <li><strong>Référence :</strong> #[NUMÉRO]</li>
    <li><strong>Montant :</strong> [MONTANT] € HT</li>
    <li><strong>Date de démarrage :</strong> [DATE]</li>
</ul>

<p>📋 <strong>Prochaines étapes :</strong></p>
<ol>
    <li>Réunion de kick-off (vous recevrez une invitation)</li>
    <li>Validation du cahier des charges</li>
    <li>Démarrage du développement</li>
</ol>

<p>Votre chef de projet vous contactera sous 48h pour planifier la première réunion.</p>

<p>Merci pour votre confiance ! 🙏</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 📊 SUIVI DE PROJET
            # ==========================================
            {
                'name': 'Point d\'avancement hebdomadaire',
                'category': EmailTemplateCategory.SUIVI,
                'subject': '📊 Point projet - Semaine [X]',
                'body_html': '''
<p>Bonjour,</p>

<p>Voici le <strong>point d'avancement hebdomadaire</strong> de votre projet :</p>

<p>✅ <strong>Réalisé cette semaine :</strong></p>
<ul>
    <li>✓ [Tâche 1]</li>
    <li>✓ [Tâche 2]</li>
    <li>✓ [Tâche 3]</li>
</ul>

<p>🚧 <strong>En cours :</strong></p>
<ul>
    <li>⏳ [Tâche en cours 1]</li>
    <li>⏳ [Tâche en cours 2]</li>
</ul>

<p>📅 <strong>Prévu pour la semaine prochaine :</strong></p>
<ul>
    <li>→ [Prochaine tâche 1]</li>
    <li>→ [Prochaine tâche 2]</li>
</ul>

<p>📈 <strong>Avancement global :</strong> [XX]%</p>

<p>⚠️ <strong>Points d'attention :</strong></p>
<ul>
    <li>[Point à surveiller ou en attente de votre retour]</li>
</ul>

<p>N'hésitez pas si vous avez des questions !</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Demande de validation',
                'category': EmailTemplateCategory.SUIVI,
                'subject': '👀 Validation requise - [Élément à valider]',
                'body_html': '''
<p>Bonjour,</p>

<p>Nous avons terminé une étape importante de votre projet et avons besoin de votre <strong>validation</strong> pour continuer.</p>

<p>🎨 <strong>Élément à valider :</strong> [Maquettes / Développement / Contenu]</p>

<p>🔗 <strong>Lien de prévisualisation :</strong> <a href="[URL]">[URL]</a></p>

<p>📋 <strong>Merci de vérifier :</strong></p>
<ul>
    <li>☐ [Point de vérification 1]</li>
    <li>☐ [Point de vérification 2]</li>
    <li>☐ [Point de vérification 3]</li>
</ul>

<p>💬 <strong>Vos retours :</strong></p>
<p>Vous pouvez nous faire part de vos remarques directement par email ou via ce document partagé : [LIEN]</p>

<p>⏰ <strong>Date limite :</strong> [DATE] (pour respecter le planning)</p>

<p>Merci d'avance pour votre retour rapide !</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 👋 BIENVENUE
            # ==========================================
            {
                'name': 'Bienvenue nouveau client',
                'category': EmailTemplateCategory.BIENVENUE,
                'subject': '👋 Bienvenue chez Trait d\'Union Studio !',
                'body_html': '''
<p>Bonjour et bienvenue ! 🎉</p>

<p>Toute l'équipe de <strong>Trait d'Union Studio</strong> est ravie de vous compter parmi nos clients.</p>

<p>🚀 <strong>Voici ce qui vous attend :</strong></p>
<ul>
    <li>Un accompagnement <strong>personnalisé</strong> de A à Z</li>
    <li>Une communication <strong>transparente</strong> à chaque étape</li>
    <li>Un résultat <strong>qui dépasse vos attentes</strong></li>
</ul>

<p>📱 <strong>Vos contacts :</strong></p>
<ul>
    <li><strong>Chef de projet :</strong> [NOM] - [EMAIL]</li>
    <li><strong>Support technique :</strong> support@traitdunion.it</li>
    <li><strong>Urgences :</strong> [TÉLÉPHONE]</li>
</ul>

<p>📚 <strong>Ressources utiles :</strong></p>
<ul>
    <li><a href="[LIEN]">Notre processus de travail</a></li>
    <li><a href="[LIEN]">FAQ clients</a></li>
</ul>

<p>Nous sommes impatients de démarrer cette collaboration ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 🎂 ANNIVERSAIRE
            # ==========================================
            {
                'name': 'Anniversaire collaboration',
                'category': EmailTemplateCategory.ANNIVERSAIRE,
                'subject': '🎂 1 an déjà ! Merci pour votre fidélité',
                'body_html': '''
<p>Bonjour,</p>

<p>🎂 <strong>Joyeux anniversaire !</strong></p>

<p>Il y a exactement 1 an, nous avons eu le plaisir de commencer à travailler ensemble. Le temps passe vite quand on collabore avec des clients aussi géniaux que vous !</p>

<p>📊 <strong>Ce qu'on a accompli ensemble :</strong></p>
<ul>
    <li>[Réalisation 1]</li>
    <li>[Réalisation 2]</li>
    <li>[Statistique positive]</li>
</ul>

<p>🎁 <strong>Pour fêter ça, nous vous offrons :</strong></p>
<p><strong>15% de réduction</strong> sur votre prochaine prestation<br>
Code : <strong>ANNIV15</strong> (valable 30 jours)</p>

<p>Merci pour votre confiance et à très vite pour de nouvelles aventures digitales ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 📰 NEWSLETTER
            # ==========================================
            {
                'name': 'Newsletter mensuelle',
                'category': EmailTemplateCategory.NEWSLETTER,
                'subject': '📰 Les actus web du mois - [MOIS ANNÉE]',
                'body_html': '''
<p>Bonjour,</p>

<p>Voici votre <strong>dose mensuelle d'actualités web</strong> ! ☕</p>

<p>📌 <strong>L'actu à ne pas manquer :</strong></p>
<p>[Titre de l'actualité principale]</p>
<p>[Résumé en 2-3 phrases]</p>

<p>💡 <strong>Nos conseils du mois :</strong></p>
<ul>
    <li><strong>[Conseil 1] :</strong> [Explication courte]</li>
    <li><strong>[Conseil 2] :</strong> [Explication courte]</li>
</ul>

<p>🚀 <strong>Nos dernières réalisations :</strong></p>
<p>Découvrez le nouveau site de [CLIENT] : <a href="[URL]">[URL]</a></p>

<p>📅 <strong>Événement à venir :</strong></p>
<p>[Description événement]</p>

<p>Des questions ? Répondez simplement à cet email.</p>

<p>Bonne lecture ! 📖</p>
<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # ⭐ SATISFACTION
            # ==========================================
            {
                'name': 'Demande d\'avis client',
                'category': EmailTemplateCategory.SATISFACTION,
                'subject': '⭐ Votre avis compte pour nous !',
                'body_html': '''
<p>Bonjour,</p>

<p>Votre projet est maintenant terminé et nous espérons que vous en êtes pleinement satisfait ! 🎉</p>

<p>⭐ <strong>Pourriez-vous nous accorder 2 minutes ?</strong></p>
<p>Votre avis nous aide énormément à nous améliorer et à rassurer de futurs clients.</p>

<p>👉 <strong>Laisser un avis Google :</strong> <a href="[LIEN GOOGLE]">[LIEN]</a></p>

<p>📝 <strong>Quelques idées pour votre avis :</strong></p>
<ul>
    <li>La qualité de notre communication</li>
    <li>Le respect des délais</li>
    <li>La qualité du résultat final</li>
    <li>Votre niveau de satisfaction global</li>
</ul>

<p>Un immense merci d'avance ! 🙏</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            {
                'name': 'Enquête de satisfaction',
                'category': EmailTemplateCategory.SATISFACTION,
                'subject': '📋 Enquête satisfaction - 1 minute chrono',
                'body_html': '''
<p>Bonjour,</p>

<p>Dans un souci d'<strong>amélioration continue</strong>, nous aimerions recueillir votre feedback sur notre collaboration.</p>

<p>📊 <strong>3 questions rapides :</strong></p>
<ol>
    <li><strong>Communication :</strong> Comment évaluez-vous nos échanges ? (1-5)</li>
    <li><strong>Qualité :</strong> Le résultat correspond-il à vos attentes ? (1-5)</li>
    <li><strong>Recommandation :</strong> Nous recommanderiez-vous ? (Oui/Non)</li>
</ol>

<p>👉 <strong>Répondre au questionnaire :</strong> <a href="[LIEN]">[LIEN]</a></p>

<p>💬 <strong>Un commentaire à ajouter ?</strong><br>
Répondez simplement à cet email, nous lisons tout !</p>

<p>Merci pour votre précieux retour ! 🙏</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
            
            # ==========================================
            # 🤝 PARRAINAGE
            # ==========================================
            {
                'name': 'Invitation parrainage',
                'category': EmailTemplateCategory.PARRAINAGE,
                'subject': '🤝 Recommandez-nous et gagnez !',
                'body_html': '''
<p>Bonjour,</p>

<p>Vous êtes content de notre travail ? <strong>Partagez la bonne nouvelle !</strong> 🎉</p>

<p>🎁 <strong>Notre programme de parrainage :</strong></p>
<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
    <tr>
        <td style="padding: 15px; background: rgba(11, 45, 255, 0.1); border-radius: 8px;">
            <strong>Pour vous :</strong><br>
            100€ de réduction sur votre prochaine facture
        </td>
    </tr>
    <tr>
        <td style="padding: 15px; background: rgba(34, 197, 94, 0.1); border-radius: 8px; margin-top: 10px;">
            <strong>Pour votre filleul :</strong><br>
            10% de réduction sur son premier projet
        </td>
    </tr>
</table>

<p>📋 <strong>C'est simple :</strong></p>
<ol>
    <li>Parlez de nous à votre réseau</li>
    <li>Votre contact nous appelle en vous mentionnant</li>
    <li>Dès qu'il signe, vous recevez votre récompense !</li>
</ol>

<p>🔗 <strong>Votre lien de parrainage :</strong> <a href="[LIEN]">[LIEN]</a></p>

<p>Pas de limite de parrainages ! 🚀</p>

<p><strong>L'équipe Trait d'Union Studio</strong></p>
                '''
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = EmailTemplate.objects.update_or_create(
                name=template_data['name'],
                category=template_data['category'],
                defaults={
                    'subject': template_data['subject'],
                    'body_html': template_data['body_html'].strip(),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Créé: {template.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Mis à jour: {template.name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Terminé ! {created_count} créés, {updated_count} mis à jour'))
        self.stdout.write(self.style.SUCCESS(f'📊 Total templates: {EmailTemplate.objects.filter(is_active=True).count()}'))
