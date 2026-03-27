import os
import django
from django.utils.text import slugify

# Configure Django pour utiliser la configuration de production si on veut la DB distante
# L'utilisateur devra exécuter : DATABASE_URL="postgres://..." python insert_article.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.chroniques.models import Article, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def main():
    print("Insertion de l'article dans la base de données distante...")
    
    title = "Les KPIs qui comptent vraiment pour une TPE/PME"
    subtitle = "Décider sans service comptable — lire ses chiffres comme un pilote lit ses instruments"
    # Create a nice slug
    slug = slugify(title)
    
    # Text en Markdown
    body = """La culture des indicateurs de performance a longtemps été l'apanage des grandes organisations, dotées de contrôleurs de gestion, de directions financières et de tableaux de bord alimentés par des ERP à six chiffres. Les TPE et PME, soumises aux mêmes impératifs de décision mais privées de ces ressources, ont souvent développé un rapport ambigu aux chiffres : soit une *dépendance totale à l'expert-comptable* — qui rend ses conclusions trimestre après trimestre, quand les décisions auraient dû être prises il y a deux mois — soit une *intuition artisanale*, honnête mais aveugle, qui fait confondre le solde bancaire avec la santé de l'entreprise. 

Cet article propose une troisième voie : **un tableau de bord réduit, lisible sans formation comptable, construit sur une poignée d'indicateurs capables de déclencher une décision en moins de dix minutes.** Pas tous les KPIs. **Les bons.**

## I. Pourquoi la plupart des frameworks KPI ne sont pas faits pour vous

Il existe une industrie entière dédiée à la production de frameworks de pilotage. *Balanced Scorecard*, OKRs, tableaux de bord prospectifs, matrices de performance à trente indicateurs — ces outils ont été conçus dans des contextes où le problème n'était pas de manquer d'information, mais d'en avoir trop et de mal la prioriser. 

Une multinationale avec cent lignes de produits et vingt marchés géographiques a effectivement besoin d'arbitrer entre des dizaines de métriques concurrentes. Une TPE de huit personnes ou une PME de cinquante n'a pas ce problème. Son problème est inverse : **elle n'a ni le temps, ni les ressources, ni l'infrastructure de données pour alimenter un tableau de bord complexe** — et tenter de le faire génère plus de paralysie que de lucidité.

Le piège le plus courant est celui de la précision illusoire. Un dirigeant de PME qui passe deux heures par mois à construire un tableau de bord à vingt colonnes dans un fichier Excel obtient, au terme de cet exercice, un document qui lui donne l'impression de piloter — mais qui n'a, en pratique, déclenché *aucune* décision qu'il n'aurait pas prise autrement. La précision sans intelligibilité est une forme de confort intellectuel qui coûte cher. 

Ce qu'un dirigeant de TPE/PME a besoin, ce ne sont pas vingt indicateurs à surveiller. Ce sont cinq ou six indicateurs qui, réunis, lui permettent de répondre à une seule question : **est-ce que mon entreprise va dans la bonne direction, et si non, où dois-je intervenir en premier ?**

> *"Un bon tableau de bord pour une PME n'est pas celui qui contient le plus d'informations. C'est celui qui rend une décision évidente en moins de dix minutes."*

## II. Le premier cercle — les trois indicateurs de survie

Avant de parler de performance, il faut parler de survie. Ces trois indicateurs constituent le socle minimal en dessous duquel aucune autre métrique n'a de sens, parce qu'une entreprise qui ne les surveille pas risque de ne pas être là pour appliquer les leçons du trimestre suivant.

### 1. Le solde de trésorerie prévisionnel à 30 jours
Non pas le solde actuel — *n'importe qui peut regarder son compte en banque* — mais le solde **projeté** : ce que le compte affichera dans trente jours après avoir intégré les encaissements attendus et les décaissements certains. La différence entre ces deux notions est la différence entre savoir *où l'on est* et savoir *où l'on va*. 

Une entreprise dont le compte affiche 40 000 euros aujourd'hui mais dont la masse salariale tombe dans huit jours et dont le principal client n'a pas encore payé sa facture en retard de vingt-deux jours n'est pas en bonne santé — elle est en danger, et elle l'ignore. Ce calcul prend dix minutes sur un tableau simple. Ne pas le faire est l'une des erreurs les plus fréquentes et les plus coûteuses des dirigeants de TPE.

### 2. Le délai moyen de paiement client (DSO)
Ou *Days Sales Outstanding*. Il mesure le nombre de jours moyen qui s'écoule entre une vente et son encaissement effectif. Une entreprise dont le DSO dépasse ses propres délais de paiement fournisseurs finance le besoin en fonds de roulement de ses clients avec sa propre trésorerie — parfois sans s'en rendre compte. 

Chaque jour de DSO supplémentaire représente de la trésorerie immobilisée. Une PME qui réduit son DSO de quarante-cinq jours à trente jours sur un CA de 500 000 euros libère mécaniquement environ **20 000 euros de trésorerie**, sans vendre un seul euro de plus.

### 3. Le taux de marge brute
Pas le chiffre d'affaires — le chiffre d'affaires ne dit rien sur ce que l'on garde. La marge brute, c'est ce qui reste après avoir payé les coûts directement liés à la production ou à la vente : matières premières, sous-traitance, commissions directes. 

Si ce taux baisse d'un mois sur l'autre alors que le CA reste stable, c'est le signal que quelque chose a changé dans la structure des coûts directs — et que ce changement, s'il n'est pas corrigé, se répercutera sur le résultat net avec un décalage de quelques semaines.

## III. Le deuxième cercle — les indicateurs de momentum commercial

Une fois la survie assurée, les indicateurs de momentum commercial permettent de lire la dynamique de l'activité, indépendamment de ce que l'expert-comptable rendra dans deux mois. Ils répondent à une question simple : **est-ce que l'activité accélère, stagne ou ralentit — et pourquoi ?**

- **Le taux de conversion** : C'est le rapport entre le nombre de devis envoyés (ou de propositions commerciales formulées) et le nombre de missions (ou commandes) effectivement signées. C'est l'un des indicateurs les plus révélateurs et les moins suivis des PME de services. Un taux de conversion en baisse alors que le volume de propositions reste stable signifie l'une des choses suivantes : *le positionnement tarifaire est devenu inadapté au marché, la qualité des propositions s'est dégradée, la cible commerciale a dérivé vers des prospects moins qualifiés, ou un concurrent a modifié son offre.* Chacune de ces causes appelle une réponse différente — mais sans cet indicateur, on ne sait même pas qu'il y a un problème.
- **Le chiffre d'affaires récurrent vs ponctuel** : Une distinction que peu de PME formalisent, alors qu'elle est l'une des plus importantes pour comprendre la prévisibilité de l'activité. Le CA récurrent — abonnements, contrats cadres, maintenance, prestations régulières — est celui sur lequel on peut construire une projection fiable. Le CA ponctuel — projets one-shot, ventes à de nouveaux clients sans suite — est celui qui peut disparaître d'un mois sur l'autre sans préavis. Une entreprise dont 80% du CA est ponctuel est **structurellement plus exposée au risque** qu'une entreprise dont 50% est récurrent, même si leur chiffre d'affaires global est identique. 
- **Le taux de croissance nette de la base client** : Le nombre de nouveaux clients acquis par mois, rapporté au nombre de clients perdus ou inactifs sur la même période. Un dirigeant qui signe trois nouveaux clients par mois tout en perdant deux clients existants ne grandit pas à trois clients par mois — *il grandit à un*. Et si ces clients perdus étaient ceux qui avaient les paniers moyens les plus élevés, il est possible qu'il régresse en valeur tout en progressant en volume. Cette nuance est souvent au cœur d'une dégradation silencieuse de la rentabilité.

## IV. Le troisième cercle — l'indicateur de structure

Il existe un indicateur que les PME évitent souvent parce qu'il est inconfortable à regarder, mais qui est le plus révélateur de la solidité structurelle de l'entreprise : **le ratio charges fixes / marge brute**, ou taux de couverture des charges fixes.

Ce ratio répond à la question suivante : pour chaque euro de marge brute générée, quelle proportion est absorbée par les charges fixes avant même que l'on commence à parler de résultat ? 
- Une entreprise dont les charges fixes représentent 90% de la marge brute n'a quasiment aucune marge d'absorption face à un choc d'activité. Une baisse de 10% du CA peut suffire à faire basculer le résultat dans le rouge. 
- À l'inverse, une entreprise dont les charges fixes ne représentent que 50% de la marge brute dispose d'un coussin significatif : elle peut encaisser une variation d'activité, financer une action commerciale, ou supporter un retard de paiement sans compromettre immédiatement son équilibre.

> *"Le taux de couverture des charges fixes est le baromètre de la résilience. Il dit, en un seul chiffre, combien de tempête l'entreprise peut encaisser avant de prendre l'eau."*

Ce ratio se calcule en moins de trois minutes à partir de deux données que tout dirigeant de PME connaît approximativement : sa marge brute mensuelle et le total de ses charges fixes mensuelles. Il n'y a besoin ni de bilan, ni de liasse fiscale, ni d'expert-comptable. Il suffit d'une feuille et d'une soustraction.

## V. Comment lire ces indicateurs ensemble — la règle des signaux

Disposer de ces indicateurs est une chose. Savoir comment les lire conjointement pour déclencher une décision en est une autre. La règle la plus simple — et la plus efficace — est celle des signaux simultanés : 

🚨 **Un seul indicateur** en dehors de sa zone normale est un avertissement à surveiller. 
🚨🚨 **Deux indicateurs** simultanément dégradés constituent un signal d'alerte. 
🚨🚨🚨 **Trois indicateurs** dégradés simultanément sont une urgence qui justifie une réunion stratégique dans la semaine.

Concrètement : si la **trésorerie prévisionnelle à 30 jours devient négative** ET que le **DSO dépasse 45 jours** ET que le **taux de conversion est en baisse** depuis deux mois, il ne s'agit plus d'un aléa. Il s'agit d'un problème systémique qui touche simultanément la politique de recouvrement, l'efficacité commerciale et la gestion des flux — et qui requiert une intervention coordonnée. Ce diagnostic, un dirigeant qui suit ces six indicateurs peut le poser seul, en vingt minutes, le premier lundi de chaque mois.

La cadence est elle-même une décision. Certains indicateurs doivent être lus **chaque semaine** *(trésorerie prévisionnelle, DSO)*. D'autres se lisent **mensuellement** *(taux de conversion, répartition CA récurrent/ponctuel, couverture des charges fixes)*. La discipline de la lecture régulière, même sommaire, vaut infiniment mieux que l'analyse exhaustive trimestrielle qui arrive toujours trop tard pour agir.

## VI. Ce que ces indicateurs ne remplacent pas — et ce qu'ils remplacent réellement

Il serait malhonnête de conclure sans nommer ce que ces KPIs ne peuvent *pas* faire. Ils ne remplacent pas l'expertise d'un comptable pour l'optimisation fiscale, l'établissement des comptes annuels ou la vérification de la conformité sociale. Ils ne produisent pas de liasse fiscale. Ils ne vous diront pas si votre structure juridique est adaptée à votre niveau de développement. Pour tout cela, l'expert-comptable reste indispensable.

Ce que ces indicateurs remplacent, en revanche, c'est **l'attente**. 
- L'attente du bilan trimestriel pour savoir si l'on a gagné ou perdu de l'argent. 
- L'attente de la réunion mensuelle pour apprendre que la trésorerie est tendue. 
- L'attente d'un signal extérieur pour prendre une décision qui aurait dû être prise il y a six semaines. 

Dans une TPE ou une PME, six semaines de retard dans une décision commerciale ou financière ne sont pas un inconvénient — elles peuvent représenter un point de non-retour.

La lecture des chiffres n'est pas une compétence réservée aux financiers. **C'est une compétence de dirigeant.** Et comme toutes les compétences de dirigeant, elle s'acquiert par la pratique, non par la délégation. 

> *"Celui qui ne lit pas ses propres indicateurs ne pilote pas son entreprise — il espère qu'elle se pilote seule."*
"""
    
    # Try getting the author (usually the superuser or the first user)
    author = User.objects.filter(is_superuser=True).first()
    if not author:
        author = User.objects.first()

    # Create category if missing
    category, _ = Category.objects.get_or_create(
        name="Business & Management",
        defaults={"slug": "business-management"}
    )

    try:
        # Check if already exists
        article = Article.objects.get(slug=slug)
        article.title = title
        article.subtitle = subtitle
        article.body = body
        article.category = category
        article.is_published = True
        article.save()
        print(f"Article '{title}' mis à jour avec succès !")
    except Article.DoesNotExist:
        # Create new
        article = Article.objects.create(
            title=title,
            subtitle=subtitle,
            slug=slug,
            category=category,
            body=body,
            author=author,
            is_published=True,
            excerpt="Un tableau de bord réduit, lisible sans formation comptable, construit sur une poignée d'indicateurs capables de déclencher une décision en moins de dix minutes."
        )
        print(f"Article '{title}' créé avec succès !")

if __name__ == '__main__':
    main()
