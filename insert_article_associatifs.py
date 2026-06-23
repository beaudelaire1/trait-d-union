"""Insertion de la chronique « Trois outils qui se complètent » (outils associatifs).

À lancer depuis le Shell Render du service web (le host interne de la base y est
résolu et DATABASE_URL est déjà présent dans l'environnement) :

    python insert_article_associatifs.py

Ou depuis une machine ayant accès à la base externe :

    DATABASE_URL="postgresql://.../traitdunion" python insert_article_associatifs.py

Le script est idempotent : relancé, il met à jour l'article existant (même slug).

⚠️ Le corps est stocké en HTML : le template des Chroniques rend `article.body`
via le filtre `safe_html` (nh3) SANS conversion Markdown. Stocker du Markdown
afficherait les `##`/`**` en clair.
"""
import os

import django
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from datetime import datetime  # noqa: E402

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.chroniques.models import Article, Category  # noqa: E402

User = get_user_model()

TITLE = "Trois outils qui se complètent. Un plafond qu'ils partagent."
SUBTITLE = "Ce que la combinaison règle — et ce qu'elle suppose déjà résolu."
CATEGORY_NAME = "Organisations"
EXCERPT = (
    "Trois outils structurent aujourd'hui la gestion associative française : "
    "HelloAsso, AssoConnect, B-Association. Pris en chaîne, chacun répond à la "
    "limite du précédent. Ensemble, ils couvrent l'essentiel des besoins d'une "
    "association de taille courante. Trait d'Union Studio produit des plateformes "
    "numériques sur mesure — et n'a aucun intérêt à orienter une structure vers le "
    "sur-mesure si cette combinaison suffit. Cette analyse le démontre, puis "
    "cartographie le plafond structurel que même leur réunion ne franchit pas."
)
META_DESCRIPTION = (
    "HelloAsso, AssoConnect, B-Association : ce que leur combinaison règle pour une "
    "association — et le plafond qu'elle ne franchit pas."
)

BODY = """<p>Le réflexe est compréhensible. Trait d'Union Studio produit des plateformes numériques sur mesure. La posture attendue serait de pointer les lacunes des outils existants pour justifier son propre modèle. Ce type de raisonnement existe dans le secteur. Il est courant. Et il est intellectuellement malhonnête.</p>

<p>Trois outils structurent aujourd'hui la gestion associative française — HelloAsso, AssoConnect, B-Association. Pris séparément, chacun couvre un périmètre précis. Pris ensemble, ils répondent à l'essentiel des besoins d'une association de taille courante. Cette analyse le démontre en suivant une logique de chaîne : la limite d'un outil devient le point de départ du suivant.</p>

<p>À la fin : ce que même leur réunion laisse ouvert. C'est là, et là seulement, que la question du sur-mesure devient une question honnête.</p>

<blockquote><em>« Pousser une petite association vers un outil sur mesure quand la combinaison de ces trois solutions suffit à ses besoins serait une faute de diagnostic. Trait d'Union Studio préfère le dire. »</em></blockquote>

<h2>I. HelloAsso : la collecte résolue, la gestion absente</h2>

<p>HelloAsso s'est imposé depuis 2009 comme l'outil de référence pour la collecte en ligne dans le monde associatif français. Plus de 450 000 associations utilisent la plateforme. Trois milliards d'euros ont été collectés depuis sa création et intégralement reversés aux structures, sans frais ni commission.</p>

<p>Le modèle économique mérite d'être compris avant tout autre jugement : HelloAsso se finance exclusivement par les contributions volontaires que les payeurs laissent à l'issue de chaque transaction. Le service est structurellement gratuit pour l'association. Pas freemium. Pas de version bridée. Gratuit.</p>

<p>Le périmètre fonctionnel est cohérent avec cette promesse — adhésions en ligne, billetterie, collectes de dons, crowdfunding, boutique, reçus fiscaux automatisés. Pour une association qui cherche à numériser ses flux financiers entrants sans budget, HelloAsso règle le problème en quelques heures.</p>

<p>La limite est symétrique à la force : HelloAsso ne gère pas. Il collecte. Aucun CRM natif, aucune comptabilité intégrée, aucun module de communication interne. Les membres s'inscrivent, paient, reçoivent leur reçu — et c'est là que l'outil s'arrête. Ce qui reste à gérer — suivi des adhérents dans la durée, pilotage des finances, structuration des sections — reste à la charge de l'association, sans outillage dédié.</p>

<blockquote><em>HelloAsso pose la question à laquelle il ne répond pas : une fois l'argent collecté, comment gère-t-on ?</em></blockquote>

<h2>II. AssoConnect : la gestion couverte — mais à quel coût réel ?</h2>

<p>AssoConnect a été conçu pour répondre précisément à cette question. Créé en 2014 à Paris, le logiciel revendique plus de 40 000 associations clientes et se positionne comme la solution tout-en-un du marché français. Le positionnement est justifié : le périmètre est nettement plus large que HelloAsso.</p>

<p>CRM adhérents avec historique des renouvellements et segmentation par champs personnalisés. Comptabilité automatisée avec bilan et compte de résultat. Paiements en ligne — carte bancaire, virement, prélèvement SEPA. Billetterie, emailing, création de site internet. Depuis 2025, un compte pro directement intégré : carte physique, RIB, IBAN, gestion des notes de frais des bénévoles. Chaque paiement reçu génère automatiquement une écriture comptable. La double saisie disparaît.</p>

<p>Pour une association culturelle ou sportive entre 100 et 500 adhérents, avec des cotisations annuelles, une assemblée générale et quelques événements par an, AssoConnect est un choix pertinent. Le fait de le dire n'est pas une concession — c'est un diagnostic.</p>

<p>Deux points exigent cependant d'être nommés sans atténuation.</p>

<p>Le premier concerne le <strong>coût réel</strong>. Le forfait gratuit se limite à la collecte de paiements. Les fonctionnalités de comptabilité démarrent à 23 € TTC par mois. Le forfait complet — membres, comptabilité, communication, site internet — se situe entre 39 € et 199 € par mois selon le volume de contacts, auxquels s'ajoutent des frais de transaction sur chaque paiement en ligne de 1,8 % + 0,25 €. Pour une association qui collecte 200 cotisations à 50 € par an, ces frais représentent entre 500 € et 1 250 € annuels en sus de l'abonnement. Le tarif affiché et le coût réel divergent de façon régulière.</p>

<p>Le second est <strong>structurel</strong>. AssoConnect couvre l'administratif associatif. Il ne communique pas avec les systèmes extérieurs : logiciels de paie, ERP sectoriels, outils de planification professionnels. Une association qui gère des équipes terrain, des qualifications à renouveler, des plannings d'astreinte ou des intervenants rémunérés sort du périmètre de ce que l'outil peut traiter.</p>

<blockquote><em>AssoConnect règle la gestion courante. Il ne règle pas les processus métier qui dépassent l'administratif standard.</em></blockquote>

<h2>III. B-Association : la profondeur comptable, sans la collecte</h2>

<p>B-Association est l'aîné des trois. Sorti en 2001, il accompagne plus de 44 000 associations depuis près de vingt-cinq ans — une durée que ni HelloAsso ni AssoConnect ne peuvent revendiquer. Cette ancienneté se traduit par une maturité fonctionnelle réelle sur les domaines qu'il couvre : gestion des adhérents avec champs personnalisés, cotisations par foyer, paiements échelonnés, suivi des certificats médicaux sur trois ans, comptabilité par exercice et catégorie, gestion du matériel et des prêts.</p>

<p>Le modèle tarifaire est structurellement différent des deux précédents. La version Web — accessible en ligne, multi-utilisateurs, mise à jour automatique, jusqu'à dix pôles de gestion distincts — est proposée à 95 € la première année, 79 € à partir de la deuxième. Pas d'abonnement mensuel. Pas de frais de transaction. Un règlement annuel fixe. Pour une association dont le bureau de trésorerie a des besoins comptables précis et un budget contraint, ce rapport est difficile à contester.</p>

<p>Trois limites méritent d'être nommées. B-Association ne propose pas de collecte de dons ni de billetterie en ligne — ce qui le rend structurellement dépendant d'un outil complémentaire pour l'ensemble de la partie financière entrante. L'interface, fonctionnelle, porte l'âge du logiciel et implique un temps de prise en main plus long que ses concurrents plus récents. Enfin, et c'est le point le plus sensible pour les associations sous convention publique : les données de la version cloud sont hébergées aux États-Unis. Toute structure recevant des subventions publiques ou traitant des données personnelles sensibles de ses membres doit traiter ce point avant toute décision — pas après.</p>

<blockquote><em>B-Association approfondit là où AssoConnect survole. Mais il ne collecte pas, et ses données partent outre-Atlantique.</em></blockquote>

<h2>IV. La combinaison : ce qu'elle règle</h2>

<p>La logique de chaîne produit deux configurations cohérentes pour la majorité des cas courants.</p>

<p>La première associe HelloAsso et AssoConnect. HelloAsso prend en charge l'intégralité des flux financiers entrants sans frais. AssoConnect gère le reste : membres, comptabilité, communication, présence en ligne. Le coût mensuel d'AssoConnect est compensé par la gratuité de HelloAsso sur la collecte. Les deux outils fonctionnent indépendamment, sans connecteur natif entre eux, ce qui implique une gestion manuelle du point de jonction — mais ce point de friction reste gérable pour la majorité des structures.</p>

<p>La seconde associe HelloAsso et B-Association. Elle s'adresse aux associations dont les besoins comptables sont fins et le budget annuel contraint. HelloAsso assure la collecte. B-Association prend en charge la comptabilité, les adhérents et la gestion du matériel pour moins de 80 € par an renouvelable. La couverture fonctionnelle est moins large que la première configuration, mais le coût total est nettement inférieur.</p>

<p>Pour une association de quartier, un club sportif, une structure culturelle ou une organisation humanitaire de taille standard, l'une ou l'autre de ces combinaisons couvre l'essentiel. Recommander autre chose sans que les besoins l'exigent clairement serait une faute de diagnostic — et, de la part d'un studio numérique, une posture commerciale que Trait d'Union Studio refuse d'assumer.</p>

<h2>V. Ce que les trois réunis ne règlent pas</h2>

<p>L'analyse serait incomplète sans cartographier ce que la combinaison optimale laisse ouvert.</p>

<p>La question de la <strong>souveraineté des données</strong> reste entière. HelloAsso et AssoConnect hébergent en France ; B-Association héberge aux États-Unis dans sa version cloud. Mais dans les trois cas, l'association ne choisit pas son hébergeur, ne contrôle pas ses sauvegardes et ne peut pas migrer ses données sans dépendre de l'éditeur. En cas de rachat, de fermeture ou de changement tarifaire unilatéral, elle n'a aucun levier. La dépendance est structurelle, pas accidentelle.</p>

<p>La <strong>personnalisation des processus</strong> reste hors de portée. Les trois outils suivent une logique standard : adhésions, cotisations, événements, comptabilité. Une association dont les processus s'écartent de ce schéma — gestion de ressources humaines bénévoles complexe, planification opérationnelle multi-sites, suivi de qualifications avec alertes d'expiration, intégration avec un logiciel de paie — se retrouve rapidement aux limites de ce que le paramétrage permet. Le SaaS généraliste est conçu pour le cas médian. Il ne se plie pas aux cas particuliers.</p>

<p>L'<strong>évolution de l'association</strong> est contrainte par la roadmap de l'éditeur. Une fonctionnalité absente aujourd'hui dépend d'une décision commerciale extérieure à l'association. AssoConnect ajuste ses tarifs en fonction du volume de contacts : une association en croissance voit sa facture augmenter sans avoir décidé d'évoluer. Et si deux outils sont combinés, leur cohérence lors des mises à jour n'est jamais garantie — chaque éditeur met à jour selon son propre calendrier.</p>

<p>L'<strong>automatisation</strong> proposée reste celle de l'éditeur, pas celle de l'association. Les tâches répétitives de base sont automatisées : envois de reçus, rappels de cotisation, écritures comptables. Construire des flux métier sur mesure — déclenchement d'actions conditionnelles complexes, intégration avec des API tierces, tableaux de bord consolidant des sources hétérogènes — reste hors du périmètre des trois solutions, quelle que soit leur combinaison.</p>

<p>L'<strong>intégration avec un environnement informatique existant</strong>, enfin, n'est assurée nativement par aucun des trois outils. Une association disposant d'un logiciel RH, d'un ERP de branche ou d'une base de données membres existante devra assumer elle-même le coût et la complexité de la connexion — si tant est que les API disponibles le permettent.</p>

<blockquote><em>Les trois outils résolvent la gestion associative standard. Ils ne résolvent pas les organisations associatives complexes.</em></blockquote>

<h2>VI. La frontière</h2>

<p>La question du sur-mesure devient légitime quand plusieurs de ces conditions se cumulent : des processus métier que le SaaS standard ne peut pas couvrir, une obligation de souveraineté des données que les conditions d'hébergement des éditeurs ne permettent pas de garantir, une intégration avec des systèmes existants que les API disponibles ne permettent pas de réaliser proprement, et une taille d'organisation qui rend l'investissement initial proportionné.</p>

<p>Ces conditions ne décrivent pas une association de quartier. Elles décrivent une organisation structurée, souvent en croissance, parfois multi-sites, dont la complexité opérationnelle a dépassé le périmètre du généraliste.</p>

<p>Dans ce périmètre précis — et dans ce périmètre seulement — un outil construit sur mesure devient la réponse juste. Pas avant.</p>

<p><em>Trait d'Union Studio — Studio numérique sur mesure, Cayenne, Guyane française.</em></p>"""


def main() -> None:
    slug = slugify(TITLE)
    print(f"Insertion / mise à jour de la chronique : {slug}")

    author = (
        User.objects.filter(is_superuser=True).first()
        or User.objects.first()
    )

    category, _ = Category.objects.get_or_create(
        name=CATEGORY_NAME,
        defaults={"slug": slugify(CATEGORY_NAME)},
    )

    # Juin 2026 — date de publication annoncée dans l'article
    publish_date = timezone.make_aware(datetime(2026, 6, 15, 9, 0))

    article, created = Article.objects.update_or_create(
        slug=slug,
        defaults={
            "title": TITLE,
            "subtitle": SUBTITLE,
            "category": category,
            "excerpt": EXCERPT,
            "meta_description": META_DESCRIPTION,
            "body": BODY,
            "author": author,
            "is_published": True,
            "publish_date": publish_date,
        },
    )

    verb = "créé" if created else "mis à jour"
    print(f"✅ Article {verb} : « {article.title} » (id={article.pk})")
    print(f"   URL : /chroniques/{article.slug}/")


if __name__ == "__main__":
    main()
