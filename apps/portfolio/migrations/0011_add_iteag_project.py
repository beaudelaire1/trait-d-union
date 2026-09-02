"""Ajoute l'étude de cas ITEAG à « Nos signatures ».

Plateforme académique et institutionnelle de l'Institut de Théologie
Évangélique des Antilles et de la Guyane : migration WordPress →
Django 5 / Wagtail 7, quatre portails, e-learning vidéo à accès contrôlé.

Idempotente : elle s'appuie sur le slug ``iteag``. Le retour arrière
supprime le projet et, en cascade, ses phases de stratégie.
"""

from django.db import migrations


SLUG = "iteag"
PROJECT_URL = "https://iteag-preprod.137.74.169.188.sslip.io/"

OBJECTIF = """\
<p>L'ITEAG forme à la théologie depuis la Guadeloupe, avec un rayonnement sur
la Martinique et la Guyane. Son site — un WordPress vitrine d'une douzaine de
pages — disait ce que l'institut proposait, mais ne portait rien de ce qu'il
fait : les <strong>2 635 notices</strong> de la bibliothèque restaient hors
ligne, les actualités se publiaient sous forme d'affiches, et les vidéos de
cours étaient distribuées <em>sur demande au secrétariat</em>, une par une.</p>
<p>Entre-temps, le modèle pédagogique s'était affirmé : quatre sessions
intensives par an sur six ans, un cours validé pour 2,5 crédits ECTS,
180 crédits au diplôme, une double filière — diplôme ITEAG ou bachelor délivré
avec la FLTE de Vaux-sur-Seine, dont 30 crédits sont obtenus hors les murs.
Aucun de ces mouvements n'était suivi ailleurs que dans des tableurs.</p>
<p><strong>Objectif :</strong> faire passer l'ITEAG d'un site vitrine à une
plateforme académique — candidature, admission, inscription, sessions, notes,
progression ECTS, bibliothèque, formation vidéo à distance — administrable par
un secrétariat non technique, et dont l'institut reste propriétaire.</p>"""

DEFI = """\
<p>Le piège d'un projet comme celui-ci est de plier l'institut au modèle d'un
LMS générique. La contrainte structurante était l'inverse : c'est
l'architecture qui devait épouser le modèle ITEAG — des sessions et non des
semestres, des crédits obtenus dans une institution partenaire, des étudiants
libres qui suivent les mêmes cours sans en demander la validation.</p>
<ul>
<li><strong>Quatre portails, un seul déploiement.</strong> Public, étudiant,
enseignant, administratif : quatre lectures d'un même référentiel, chacune
limitée à ce que son rôle justifie. Un monolithe modulaire, sans
microservices — le graphe de dépendances entre applications est déclaré et
vérifié à chaque exécution de la suite de tests.</li>
<li><strong>La vidéo de cours est la valeur commerciale de l'institut.</strong>
Aucune adresse de fichier ne figure dans le HTML servi ; le droit est
revérifié à <em>chaque</em> demande de lecture, jamais au seul chargement de
la page ; l'adresse délivrée expire en quelques minutes ; chaque octroi est
journalisé et le nombre de flux simultanés par compte est plafonné.</li>
<li><strong>Le débit, pas seulement le stockage.</strong> Un fichier servi à
débit constant depuis un espace privé ne s'adapte pas à la bande passante
réelle d'un étudiant en Guyane ou en Martinique — il attend, puis il
abandonne. La diffusion a été déléguée à un fournisseur à adresse signée et
débit adaptatif, sans lecteur tiers embarqué : les événements de lecture
restent les nôtres, donc la progression reste mesurable côté serveur.</li>
<li><strong>Le rôle n'est pas le droit.</strong> Être « étudiant » ne dit rien
du droit de suivre <em>ce</em> module. Le droit est une donnée que le
secrétariat octroie, suspend, prolonge ou révoque sans développeur, et toute
l'autorisation métier passe par une fonction unique — un test d'architecture
interdit de la contourner.</li>
<li><strong>Une politique de sécurité de contenu stricte</strong>
(<code>script-src 'self'</code>, sans <code>unsafe-inline</code> ni
<code>unsafe-eval</code>), donc pas de framework client : rendu serveur,
HTMX pour les échanges, composants natifs pour le reste.</li>
<li><strong>Reprendre l'existant sans rien perdre :</strong> les
2 635 notices, les pages éditoriales, les images hébergées à l'extérieur et
les redirections de toutes les anciennes adresses.</li>
</ul>"""

STRATEGIE = """\
<p>Une plateforme de cette ampleur ne se livre pas en une fois. Le projet a été
découpé en lots, chacun tenu de produire une valeur démontrable — une
fonctionnalité qu'on peut montrer, pas une couche technique invisible — et
aucun lot n'est déclaré terminé avec une dette reportée sur le suivant.</p>
<p>Le premier lot ne contenait aucune fonctionnalité : il remettait le socle en
état. Construire sur une intégration continue rouge revient à ne pas savoir ce
qui casse.</p>"""

RESULTAT = """\
<p>La plateforme est aujourd'hui déployée en préproduction, ouverte à la
validation du secrétariat ITEAG avant la bascule du domaine. Elle couvre la
chaîne complète : de la candidature déposée en ligne à l'attestation de module
téléchargée par l'étudiant.</p>
<ul>
<li><strong>Quatre portails livrés</strong> — public, étudiant, enseignant,
administratif — répartis sur 14 applications Django découplées.</li>
<li><strong>E-learning vidéo complet :</strong> modules structurés en chapitres
et leçons, lecteur sécurisé, reprise de lecture à la position quittée,
sous-titres et transcription, attestation PDF nominative à code de
vérification public.</li>
<li><strong>Plus de 2 400 tests verts, 92 % de couverture</strong>, et
<strong>100 % sur le contrôle d'accès</strong> — ses onze cas de refus sont
testés un par un. Lint et format à zéro, intégration continue verte sur
PostgreSQL.</li>
<li><strong>Les 2 635 notices de la bibliothèque sont en ligne</strong> et
cherchables en plein texte, filtrables par auteur, année et mot-clé.</li>
<li><strong>Un secrétariat autonome :</strong> l'éditorial se publie dans
Wagtail, les accès aux modules s'octroient, se suspendent et se révoquent
depuis l'administration — sans nous.</li>
<li><strong>Exploitation documentée :</strong> déploiement OVH Cloud sous
Coolify, sauvegardes éprouvées (RPO 24 h, RTO 4 h), supervision et alertes,
manuel de reprise et guides utilisateur par rôle.</li>
</ul>
<p>Les décisions d'architecture sont écrites, datées et motivées — y compris
celles que nous avons remplacées en cours de route. L'ITEAG reçoit un code
source documenté et auditable : la souveraineté n'était pas une clause de
style du cahier des charges, c'était l'un de ses six objectifs.</p>"""

TECHNOLOGIES = [
    "Django 5.2",
    "Wagtail 7",
    "Python 3.12",
    "PostgreSQL 16",
    "Redis",
    "Celery",
    "HTMX",
    "Alpine.js (build CSP)",
    "Tailwind CSS 4",
    "WeasyPrint",
    "Bunny Stream (HLS signé)",
    "Cloudflare R2 & Turnstile",
    "Sentry",
    "Docker / Coolify (OVH Cloud)",
]

PHASES = [
    (
        "Phase 1 · Cadrage",
        "Modèle pédagogique avant modèle de données",
        "search",
        "Trois semaines à documenter la réalité de l'institut — sessions "
        "intensives, crédits ECTS, partenariat FLTE, parcours libre — avant "
        "d'écrire une ligne. Le cahier des charges en est sorti exécutable : "
        "chaque fonctionnalité priorisée et assortie de son critère "
        "d'acceptation.",
        1,
    ),
    (
        "Phase 2 · Socle",
        "Remise à niveau et intégration continue verte",
        "test",
        "Lot bloquant, sans fonctionnalité : lint et format remis à zéro, "
        "chaîne d'assets de production rétablie, politique de sécurité de "
        "contenu appliquée, test d'architecture ajouté. Sortie de lot : image "
        "de production vérifiée et suite verte.",
        2,
    ),
    (
        "Phase 3 · Architecture",
        "Décisions écrites, contrôle d'accès unique",
        "architecture",
        "Séparation du rôle et du droit, point de contrôle unique pour "
        "l'autorisation métier, abstraction de la diffusion vidéo. Cette "
        "abstraction a payé : changer de fournisseur de diffusion en cours de "
        "projet n'a touché ni les vues ni les gabarits.",
        3,
    ),
    (
        "Phase 4 · Développement",
        "Les quatre portails, par lots démontrables",
        "code",
        "Domaine e-learning d'abord — il est le chemin critique dont trois "
        "lots dépendent — puis l'étudiant, l'enseignant, l'administration et "
        "enfin le portail public. Chaque lot clos par une démonstration, pas "
        "par un rapport d'avancement.",
        4,
    ),
    (
        "Phase 5 · Qualité",
        "Accessibilité, performance, revue de sécurité",
        "security",
        "Audit WCAG 2.2 AA jusqu'au lecteur vidéo, budget de performance tenu "
        "sur les pages clés, dépendances auditées, requêtes N+1 éliminées sur "
        "les listes principales. La couverture est portée au-delà de 90 %, et "
        "au maximum là où un défaut coûterait le plus.",
        5,
    ),
    (
        "Phase 6 · Exploitation",
        "Migration du contenu et mise en service",
        "deploy",
        "Import du catalogue, reprise des pages et des actualités, "
        "redirections de toutes les anciennes adresses, sauvegardes "
        "restaurées et chronométrées, supervision active. Un exploitant tiers "
        "peut reprendre la main : c'est le critère d'acceptation du manuel.",
        6,
    ),
]


def forwards(apps, schema_editor):
    """Écrit la fiche et ses phases, sans toucher aux images.

    Les champs d'image ne figurent pas dans ``defaults`` : une capture
    téléversée depuis l'admin survit donc à une réexécution.
    """
    Project = apps.get_model("portfolio", "Project")
    StrategyPhase = apps.get_model("portfolio", "StrategyPhase")

    project, _ = Project.objects.update_or_create(
        slug=SLUG,
        defaults={
            "title": "ITEAG",
            "project_type": "outils",
            "client_name": "Institut de Théologie Évangélique des Antilles et de la Guyane",
            "url": PROJECT_URL,
            "objective": OBJECTIF,
            "solution": DEFI,
            "strategy": STRATEGIE,
            "result": RESULTAT,
            "technologies": TECHNOLOGIES,
            "is_featured": True,
            "is_published": True,
        },
    )

    StrategyPhase.objects.filter(project_id=project.pk).delete()
    StrategyPhase.objects.bulk_create([
        StrategyPhase(
            project_id=project.pk,
            phase_label=label,
            title=title,
            icon=icon,
            description=description,
            order=order,
        )
        for label, title, icon, description, order in PHASES
    ])


def backwards(apps, schema_editor):
    """Retire la fiche — sauf si quelqu'un l'a reprise depuis.

    Annuler une migration doit rendre la base à son état d'avant, pas
    détruire ce qui est arrivé après. Tant que la fiche porte exactement le
    texte semé ici et aucune image, elle n'existe que par cette migration :
    on la supprime, ses phases avec elle. Dès qu'elle a été rédigée dans
    l'admin ou qu'une capture y a été téléversée — ou qu'un projet du même
    slug préexistait — le travail n'est pas le nôtre : on la laisse.
    """
    Project = apps.get_model("portfolio", "Project")

    project = Project.objects.filter(slug=SLUG).first()
    if project is None:
        return

    inchangee = (
        project.objective == OBJECTIF
        and project.solution == DEFI
        and project.strategy == STRATEGIE
        and project.result == RESULTAT
        and not project.image_ch02
        and not project.image_ch03
        and not project.image_ch04
        and not project.thumbnail
    )
    if inchangee:
        project.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0010_merge_20260902_netexpress_audit"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
