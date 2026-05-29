"""Catalogue de questions du diagnostic terrain — Trait d'Union Studio.

Ce module est la **source unique de vérité** des questions posées pendant un
diagnostic terrain (entretien client). Les questions sont :

- Pré-établies et structurées en *domaines* (santé financière, commercial,
  organisation, stratégie, risques).
- Orientées par le **profil d'entreprise** choisi en amont
  (``solo`` / ``pme`` / ``strategique``) — chaque question déclare les profils
  auxquels elle s'applique.
- Typées (``currency``, ``percent``, ``number``, ``scale``, ``choice``,
  ``boolean``) pour piloter le rendu du formulaire et la validation.

Le moteur de scoring (:mod:`apps.diagnostic.field_scoring`) consomme les
réponses collectées ici pour produire un score objectif /100, des signaux
d'alerte et un plan d'action priorisé.

Aucune logique de calcul ne vit dans ce fichier : il ne décrit que la
*structure* du questionnaire.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Profils d'entreprise ─────────────────────────────────────────────
# Le profil choisi en amont oriente l'ensemble du questionnaire. Il décrit
# la SITUATION / MATURITÉ de l'entreprise, indépendamment de son secteur.
PROFILES: dict[str, dict[str, str]] = {
    "solo": {
        "label": "Indépendant / Freelance",
        "tagline": "Entrepreneur seul, aucun salarié",
        "icon": "👤",
        "description": (
            "Diagnostic centré sur la capacité facturable, la rentabilité "
            "personnelle, la dépendance commerciale et la friction "
            "opérationnelle du solo. On vérifie surtout que le temps se "
            "transforme bien en chiffre d'affaires."
        ),
    },
    "tpe": {
        "label": "TPE · 1 à 9 salariés",
        "tagline": "Petite équipe, dirigeant très opérationnel",
        "icon": "🏪",
        "description": (
            "Diagnostic centré sur la rentabilité réelle, la première "
            "délégation, la trésorerie et la dépendance au dirigeant. "
            "L'enjeu : sortir du tout-sur-le-patron sans casser la marge."
        ),
    },
    "pme": {
        "label": "PME · 10 à 50 personnes",
        "tagline": "Structure établie, enjeux d'organisation",
        "icon": "🏢",
        "description": (
            "Diagnostic centré sur le pilotage de la marge, la délégation, "
            "le mix de prestations, la trésorerie et la dépendance client. "
            "L'enjeu : piloter par les chiffres plutôt qu'au ressenti."
        ),
    },
    "croissance": {
        "label": "Forte croissance / Scale-up",
        "tagline": "Activité qui accélère vite",
        "icon": "🚀",
        "description": (
            "Diagnostic centré sur la soutenabilité de la croissance : "
            "trésorerie qui suit le rythme, acquisition rentable, "
            "organisation qui tient la charge et risques de surchauffe."
        ),
    },
    "reprise": {
        "label": "Création / reprise récente",
        "tagline": "Moins de 3 ans d'activité",
        "icon": "🌱",
        "description": (
            "Diagnostic centré sur l'atteinte du point mort, la maîtrise des "
            "premières charges, la constitution d'un portefeuille client et "
            "la trésorerie de démarrage — les fondations à sécuriser."
        ),
    },
    "strategique": {
        "label": "Réflexion stratégique",
        "tagline": "Pivot, croissance externe ou cession en vue",
        "icon": "♟️",
        "description": (
            "Diagnostic centré sur le positionnement, la taille de marché, "
            "la valeur de l'entreprise et la résilience face aux risques. "
            "L'enjeu : préparer une décision structurante."
        ),
    },
}

# ── Secteurs d'activité (contextualisation + questions ciblées) ──────
SECTORS: list[tuple[str, str]] = [
    ("commerce", "Commerce de détail / Négoce"),
    ("ecommerce", "E-commerce / Vente en ligne"),
    ("restauration", "Restauration / Café / Traiteur"),
    ("hotellerie", "Hôtellerie / Hébergement"),
    ("tourisme", "Tourisme / Loisirs / Activités"),
    ("services_pro", "Services aux entreprises (B2B)"),
    ("services_part", "Services aux particuliers (B2C)"),
    ("conseil", "Conseil / Profession libérale"),
    ("sante", "Santé / Bien-être / Paramédical"),
    ("beaute", "Beauté / Coiffure / Esthétique"),
    ("artisanat", "Artisanat / Métiers d'art"),
    ("btp", "BTP / Construction / Rénovation"),
    ("industrie", "Industrie / Production"),
    ("transport", "Transport / Logistique"),
    ("immobilier", "Immobilier / Gestion locative"),
    ("formation", "Formation / Éducation"),
    ("evenementiel", "Événementiel / Communication"),
    ("agro", "Agriculture / Pêche / Agroalimentaire"),
    ("numerique", "Numérique / Tech / Studio"),
    ("association", "Association / ESS"),
    ("autre", "Autre activité"),
]


# ── Domaines de scoring ──────────────────────────────────────────────
# Chaque domaine porte un poids dans le score global /100. La somme des
# poids vaut 1.0. Les poids sont ajustés par profil dans field_scoring.
@dataclass(frozen=True)
class Domain:
    key: str
    label: str
    icon: str
    description: str


DOMAINS: dict[str, Domain] = {
    "finance": Domain(
        "finance", "Santé financière", "💶",
        "Trésorerie, marge, couverture des charges, délais de paiement.",
    ),
    "commercial": Domain(
        "commercial", "Commercial & acquisition", "🎯",
        "Conversion, coût d'acquisition, dépendance client, récurrence.",
    ),
    "organisation": Domain(
        "organisation", "Organisation & capacité", "⚙️",
        "Capacité facturable, friction, délégation, outils.",
    ),
    "strategie": Domain(
        "strategie", "Stratégie & positionnement", "🧭",
        "Pricing, mix d'offres, saisonnalité, vision.",
    ),
    "risques": Domain(
        "risques", "Risques & résilience", "🛡️",
        "Dépendance fournisseur, client clé, exposition territoriale.",
    ),
    # Bloc métier : questions 100 % spécifiques au secteur choisi. Non noté
    # dans le score /100 (sert l'analyse qualitative et le rapport). Le titre
    # et l'icône de ce bloc sont remplacés dynamiquement par ceux du secteur
    # (cf. SECTOR_BLOCKS) dans sections_for_profile().
    "metier": Domain(
        "metier", "Spécificités métier", "🔧",
        "Indicateurs propres au métier de l'entreprise.",
    ),
}


# ── Titre du bloc métier selon le secteur ────────────────────────────
# Permet d'afficher un bloc visiblement différent d'un secteur à l'autre
# (« Spécificités restauration », « Spécificités BTP », etc.) plutôt qu'un
# intitulé générique identique pour tous.
SECTOR_BLOCKS: dict[str, tuple[str, str]] = {
    "commerce": ("🛍️", "Spécificités commerce de détail"),
    "ecommerce": ("🛒", "Spécificités e-commerce"),
    "restauration": ("🍽️", "Spécificités restauration"),
    "hotellerie": ("🏨", "Spécificités hôtellerie"),
    "tourisme": ("🏝️", "Spécificités tourisme & loisirs"),
    "services_pro": ("🤝", "Spécificités services B2B"),
    "services_part": ("🧰", "Spécificités services aux particuliers"),
    "conseil": ("⚖️", "Spécificités conseil & libéral"),
    "sante": ("🩺", "Spécificités santé & bien-être"),
    "beaute": ("💇", "Spécificités beauté & esthétique"),
    "artisanat": ("🛠️", "Spécificités artisanat"),
    "btp": ("🏗️", "Spécificités BTP & construction"),
    "industrie": ("🏭", "Spécificités industrie"),
    "transport": ("🚚", "Spécificités transport & logistique"),
    "immobilier": ("🏠", "Spécificités immobilier"),
    "formation": ("🎓", "Spécificités formation"),
    "evenementiel": ("🎪", "Spécificités événementiel"),
    "agro": ("🌾", "Spécificités agriculture & agro"),
    "numerique": ("💻", "Spécificités numérique & tech"),
    "association": ("🤲", "Spécificités association & ESS"),
    "autre": ("🧩", "Spécificités de votre activité"),
}


# ── Définition d'une question ────────────────────────────────────────
@dataclass(frozen=True)
class Question:
    """Une question pré-établie du diagnostic terrain.

    Attributes:
        id: Identifiant unique stable (clé dans le dict des réponses).
        label: Question formulée intégralement, lisible telle quelle à voix
            haute par n'importe quel chargé de diagnostic TUS.
        domain: Clé du domaine de scoring (cf. DOMAINS).
        type: Type de saisie (currency, percent, number, scale, choice, boolean).
        profiles: Profils auxquels la question s'applique.
        sectors: Secteurs auxquels la question s'applique. Vide = tous les
            secteurs (question universelle). Renseigné = question ciblée.
        exclude_sectors: Secteurs auxquels la question ne doit JAMAIS être
            posée, même si elle est universelle. Sert à retirer une question
            qui n'a pas de sens pour un type d'activité (ex. ne pas
            interroger une entreprise de services à la personne sur ses
            approvisionnements ou ses fournisseurs).
        help: Aide contextuelle (pourquoi on pose la question, comment situer
            la réponse).
        short: Libellé court utilisé dans les rapports/synthèses.
        unit: Unité affichée (€, %, j, h…).
        required: Question obligatoire pour valider le formulaire.
        choices: Options pour le type ``choice`` (value, label).
        placeholder: Exemple de réponse.
        min / max: Bornes de validation (numériques).
        scale_labels: Étiquettes des extrémités pour le type ``scale``.
    """

    id: str
    label: str
    domain: str
    type: str
    profiles: tuple[str, ...]
    sectors: tuple[str, ...] = ()
    exclude_sectors: tuple[str, ...] = ()
    help: str = ""
    short: str = ""
    unit: str = ""
    required: bool = False
    choices: tuple[tuple[str, str], ...] = ()
    placeholder: str = ""
    min: float | None = None
    max: float | None = None
    scale_labels: tuple[str, str] = ("Faible", "Élevé")


ALL_PROFILES = ("solo", "tpe", "pme", "croissance", "reprise", "strategique")
ALL_SECTORS = tuple(value for value, _label in SECTORS)

# Groupes de profils — servent à conditionner certaines questions métier
# selon le TYPE d'entreprise (variantes par profil), pour qu'un indépendant
# et une PME du même secteur ne voient pas exactement le même questionnaire.
P_ETABLI = ("tpe", "pme", "croissance", "strategique")   # structures avec équipe
P_STRUCT = ("pme", "croissance", "strategique")           # structures matures
P_PETIT = ("solo", "tpe", "reprise")                      # petites structures / jeunes

# ── Cohérence métier : périmètres d'exclusion par modèle économique ──
# Certaines questions universelles supposent un modèle d'activité précis. On
# les retire des secteurs où elles n'ont pas de sens (cf. exclude_sectors),
# afin que le diagnostic reste crédible quel que soit le métier.

# Prestation immatérielle : ni négoce de marchandises ni production physique.
# → pas d'enjeu d'approvisionnement, de fournisseur ni d'import structurant.
SERVICES_IMMATERIELS = (
    "services_part", "services_pro", "conseil", "numerique", "formation",
    "immobilier",
)

# Vente directe / transactionnelle : on vend au comptoir, en ligne ou à la
# carte. → la notion de devis / proposition commerciale n'a pas de sens.
SECTEURS_SANS_DEVIS = (
    "commerce", "ecommerce", "restauration", "beaute", "sante",
)

# Clientèle atomisée (B2C de masse). → parler d'un « plus gros client » ou
# d'une dépendance à un client unique n'a pas de sens.
SECTEURS_CLIENTELE_DIFFUSE = (
    "commerce", "ecommerce", "restauration", "beaute", "sante",
    "hotellerie", "tourisme",
)

# Modèle « prix-produit / forfait / commission » : on ne facture pas le temps
# passé. → le taux d'heures facturables et le taux horaire n'ont pas de sens.
SECTEURS_PRIX_PRODUIT = (
    "commerce", "ecommerce", "restauration", "hotellerie", "tourisme",
    "beaute", "sante", "immobilier", "transport", "agro", "association",
    "industrie",
)


# ── Catalogue complet des questions ──────────────────────────────────
# Organisé par domaine pour la lisibilité ; le formulaire les regroupe
# dynamiquement par section.
QUESTIONS: tuple[Question, ...] = (
    # ───────────────────────── SANTÉ FINANCIÈRE ─────────────────────
    Question(
        "ca_mensuel",
        "En moyenne, combien l'entreprise encaisse-t-elle de chiffre "
        "d'affaires chaque mois ?",
        "finance", "currency", ALL_PROFILES, unit="€", required=True,
        short="CA mensuel moyen", placeholder="12000",
        help="Prenez la moyenne du CA réellement encaissé sur les 6 derniers "
             "mois. En cas de doute, additionnez le CA de l'année et divisez "
             "par 12.",
    ),
    Question(
        "charges_fixes",
        "Chaque mois, quel montant de charges tombe quoi qu'il arrive, "
        "même sans activité ?",
        "finance", "currency", ALL_PROFILES, unit="€", required=True,
        short="Charges fixes mensuelles", placeholder="6500",
        help="Loyer, salaires et cotisations, abonnements, assurances, "
             "remboursements d'emprunt — tout ce qui se paie chaque mois "
             "indépendamment des ventes.",
    ),
    Question(
        "charges_variables_pct",
        "Sur 100 € de vente, combien partent directement en coûts liés à "
        "cette vente ?",
        "finance", "percent", ALL_PROFILES, unit="%", required=True,
        short="Charges variables (% du CA)", placeholder="25", min=0, max=100,
        help="Coûts proportionnels au chiffre d'affaires : matières premières, "
             "marchandises, sous-traitance, commissions. Exemple : 25 € sur "
             "100 € de vente → saisir 25.",
    ),
    Question(
        "tresorerie_actuelle",
        "Quel montant l'entreprise a-t-elle réellement disponible sur ses "
        "comptes aujourd'hui ?",
        "finance", "currency", ALL_PROFILES, unit="€",
        short="Trésorerie disponible", placeholder="8000",
        help="Solde réellement mobilisable sur l'ensemble des comptes, hors "
             "découvert autorisé non utilisé.",
    ),
    Question(
        "encaissements_30j",
        "Dans les 30 prochains jours, quelles rentrées d'argent sont quasi "
        "certaines ?",
        "finance", "currency", ALL_PROFILES, unit="€",
        short="Encaissements à 30 j", placeholder="14000",
        help="Factures déjà émises dont le règlement est attendu ce mois-ci, "
             "plus les ventes très probables.",
    ),
    Question(
        "decaissements_30j",
        "Dans les 30 prochains jours, quelles sorties d'argent sont "
        "incontournables ?",
        "finance", "currency", ALL_PROFILES, unit="€",
        short="Décaissements à 30 j", placeholder="11000",
        help="Sorties engagées et inévitables du mois à venir : salaires, "
             "loyer, fournisseurs, échéances, impôts et cotisations.",
    ),
    Question(
        "creances_clients",
        "À ce jour, quel montant total de factures avez-vous émises mais pas "
        "encore été payé ?",
        "finance", "currency", ("tpe", "pme", "croissance", "strategique"),
        unit="€", short="Encours clients", placeholder="18000",
        help="Total des factures envoyées et non encore réglées. Sert à "
             "mesurer le délai moyen de paiement (DSO).",
    ),
    Question(
        "delai_paiement",
        "En réalité, combien de jours s'écoulent en moyenne entre votre "
        "facture et son paiement ?",
        "finance", "number", ALL_PROFILES, unit="jours",
        short="Délai de paiement client", placeholder="38", min=0, max=180,
        help="Comptez le délai réellement constaté, pas celui inscrit sur la "
             "facture. Au-delà de 45 jours, la trésorerie souffre.",
    ),

    # ───────────────────────── COMMERCIAL ───────────────────────────
    Question(
        "devis_envoyes",
        "Combien de devis ou propositions commerciales envoyez-vous en "
        "moyenne par mois ?",
        "commercial", "number", ALL_PROFILES,
        exclude_sectors=SECTEURS_SANS_DEVIS, unit="/mois",
        short="Devis envoyés / mois", placeholder="8", min=0,
        help="Volume de propositions en haut de l'entonnoir commercial : "
             "comptez les devis ou propositions écrites adressés à des "
             "prospects sérieux.",
    ),
    Question(
        "devis_signes",
        "Sur ces devis ou propositions, combien sont signés en moyenne "
        "chaque mois ?",
        "commercial", "number", ALL_PROFILES,
        exclude_sectors=SECTEURS_SANS_DEVIS, unit="/mois",
        short="Devis signés / mois", placeholder="3", min=0,
        help="Sert à calculer votre taux de transformation commercial "
             "(signés ÷ envoyés).",
    ),
    Question(
        "nb_clients_actifs",
        "Combien de clients différents avez-vous servis sur les "
        "12 derniers mois ?",
        "commercial", "number", ALL_PROFILES, unit="clients",
        short="Clients actifs", placeholder="18", min=0,
        help="Clients ayant généré du chiffre d'affaires sur l'année écoulée. "
             "En vente au comptoir, donnez une estimation raisonnable.",
    ),
    Question(
        "part_plus_gros_client",
        "Si vous regardez votre plus gros client, quelle part de votre CA "
        "total représente-t-il ?",
        "commercial", "percent", ALL_PROFILES,
        exclude_sectors=SECTEURS_CLIENTELE_DIFFUSE, unit="%",
        short="Poids du 1er client", placeholder="40", min=0, max=100,
        help="Mesure la dépendance commerciale. Au-delà de 30 %, perdre ce "
             "client deviendrait dangereux.",
    ),
    Question(
        "budget_marketing",
        "Combien dépensez-vous chaque mois pour attirer de nouveaux clients ?",
        "commercial", "currency", ALL_PROFILES, unit="€",
        short="Budget acquisition / mois", placeholder="400",
        help="Publicité, réseaux sociaux, création de contenu, événements, "
             "prospection externalisée, référencement.",
    ),
    Question(
        "nouveaux_clients",
        "Combien de nouveaux clients gagnez-vous en moyenne chaque mois ?",
        "commercial", "number", ALL_PROFILES, unit="/mois",
        short="Nouveaux clients / mois", placeholder="2", min=0,
        help="Croisé avec le budget d'acquisition, cela donne le coût "
             "d'acquisition d'un client (CAC).",
    ),
    Question(
        "ca_recurrent_pct",
        "Quelle part de votre chiffre d'affaires est récurrente, prévue "
        "d'avance (contrats, abonnements) ?",
        "commercial", "percent", ALL_PROFILES, unit="%",
        short="Part de CA récurrent", placeholder="30", min=0, max=100,
        help="CA prévisible chaque mois (abonnements, contrats, maintenance) "
             "par opposition au ponctuel. La récurrence stabilise le modèle.",
    ),
    # Questions ciblées — commerce, restauration, e-commerce, services B2C…
    Question(
        "panier_moyen",
        "Combien un client dépense-t-il en moyenne à chaque achat ou "
        "passage ?",
        "commercial", "currency",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("commerce", "ecommerce", "restauration", "hotellerie",
                 "beaute", "tourisme", "sante"),
        unit="€", short="Panier moyen", placeholder="45",
        help="Le panier moyen (ou ticket moyen) : montant moyen d'une "
             "transaction. Un levier souvent plus rapide à activer que le "
             "volume de clients.",
    ),
    Question(
        "frequence_achat",
        "Un client type revient-il acheter souvent, ou est-ce surtout des "
        "achats ponctuels ?",
        "commercial", "scale",
        ("solo", "tpe", "pme", "croissance", "reprise", "strategique"),
        sectors=("commerce", "ecommerce", "restauration", "hotellerie",
                 "beaute", "tourisme", "services_part"),
        short="Fidélité / fréquence d'achat",
        scale_labels=("Achat unique", "Revient très souvent"),
        help="La fréquence de ré-achat conditionne la valeur d'un client dans "
             "le temps et la dépendance à l'acquisition permanente.",
    ),

    # ───────────────────────── ORGANISATION ─────────────────────────
    Question(
        "heures_travaillees",
        "Une semaine type, combien d'heures consacrez-vous réellement à "
        "l'entreprise ?",
        "organisation", "number", ("solo", "tpe", "pme", "reprise"),
        unit="h/sem", short="Heures travaillées / sem", placeholder="55",
        min=0, max=120,
        help="Charge de travail réelle, tout compris : production, gestion, "
             "déplacements, administratif.",
    ),
    Question(
        "heures_facturees",
        "Sur ces heures, combien sont réellement facturées à un client "
        "chaque semaine ?",
        "organisation", "number", ("solo", "tpe", "pme", "reprise"),
        exclude_sectors=SECTEURS_PRIX_PRODUIT,
        unit="h/sem", short="Heures facturées / sem", placeholder="25",
        min=0, max=120,
        help="Seulement les heures qui génèrent du chiffre d'affaires. "
             "L'écart avec les heures travaillées révèle le temps non "
             "valorisé.",
    ),
    Question(
        "taux_horaire",
        "En moyenne, à combien facturez-vous une heure de travail ?",
        "organisation", "currency", ("solo", "tpe", "pme", "reprise"),
        exclude_sectors=SECTEURS_PRIX_PRODUIT,
        unit="€/h", short="Taux horaire moyen", placeholder="60",
        help="Tarif horaire moyen réellement facturé. Sert à estimer votre "
             "capacité maximale de chiffre d'affaires.",
    ),
    Question(
        "tjm",
        "Quel est votre taux journalier moyen facturé (TJM) ?",
        "organisation", "currency",
        ("solo", "tpe", "pme", "croissance"),
        sectors=("conseil", "services_pro", "numerique", "formation"),
        unit="€/jour", short="TJM", placeholder="450",
        help="Tarif moyen d'une journée de prestation. Repère clé pour les "
             "métiers de conseil et de services intellectuels.",
    ),
    Question(
        "taux_occupation",
        "Quel est votre taux de remplissage ou d'occupation moyen ?",
        "organisation", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("restauration", "hotellerie", "sante", "beaute", "tourisme"),
        unit="%", short="Taux d'occupation", placeholder="65", min=0, max=100,
        help="Part des places, couverts, chambres ou créneaux réellement "
             "occupés par rapport à votre capacité totale.",
    ),
    Question(
        "nb_outils_saas",
        "Combien de logiciels ou d'outils différents utilisez-vous pour "
        "faire tourner l'entreprise ?",
        "organisation", "number", ALL_PROFILES, unit="outils",
        short="Nombre d'outils", placeholder="12", min=0,
        help="Comptez tableurs, logiciels de caisse, compta, devis, agenda, "
             "messagerie pro… Trop d'outils non reliés = temps perdu et "
             "données dispersées.",
    ),
    Question(
        "friction_niveau",
        "Au quotidien, diriez-vous que tout est fluide, ou qu'on perd du "
        "temps en tâches manuelles et re-saisies ?",
        "organisation", "scale", ALL_PROFILES,
        short="Niveau de friction",
        scale_labels=("Tout est fluide", "Chaos permanent"),
        help="Perception du temps perdu en re-saisies, oublis, allers-retours "
             "et tâches répétitives évitables. 1 = rodé, 5 = on éteint des "
             "incendies en continu.",
    ),
    Question(
        "effectif",
        "Combien de personnes travaillent dans l'entreprise, vous compris ?",
        "organisation", "number", ("tpe", "pme", "croissance", "strategique"),
        unit="personnes", short="Effectif total", placeholder="3", min=1,
        help="Équivalents temps plein, dirigeant inclus. Sert à évaluer la "
             "productivité par personne et le seuil de délégation.",
    ),
    Question(
        "delegation_niveau",
        "Pouvez-vous déléguer des tâches importantes sans que la qualité "
        "baisse ou que tout vous retombe dessus ?",
        "organisation", "scale", ("tpe", "pme", "croissance", "strategique"),
        short="Capacité de délégation",
        scale_labels=("Tout repose sur moi", "Délégation maîtrisée"),
        help="Mesure à quel point l'activité dépend encore personnellement du "
             "dirigeant.",
    ),

    # ───────────────────────── STRATÉGIE ────────────────────────────
    Question(
        "nb_offres",
        "Combien de prestations ou de produits différents proposez-vous ?",
        "strategie", "number", ALL_PROFILES, unit="offres",
        short="Nombre d'offres", placeholder="6", min=1,
        help="Une offre trop large disperse l'énergie ; trop étroite "
             "concentre le risque sur peu de sources de revenus.",
    ),
    Question(
        "saisonnalite",
        "Votre activité est-elle régulière toute l'année, ou marquée par de "
        "forts pics et creux ?",
        "strategie", "scale", ALL_PROFILES,
        short="Saisonnalité",
        scale_labels=("Très régulière", "Très saisonnière"),
        help="Amplitude des hauts et des bas dans l'année. Une forte "
             "saisonnalité exige d'anticiper la trésorerie des creux.",
    ),
    Question(
        "pricing_maitrise",
        "Êtes-vous à l'aise pour fixer et défendre vos prix, ou avez-vous le "
        "sentiment de les subir ?",
        "strategie", "scale", ALL_PROFILES,
        short="Maîtrise des prix",
        scale_labels=("Je subis mes prix", "Je pilote mes prix"),
        help="Capacité à fixer ses tarifs sereinement et à les défendre sans "
             "se justifier ni céder systématiquement des remises.",
    ),
    Question(
        "derniere_hausse_prix",
        "À quand remonte votre dernière augmentation de prix ?",
        "strategie", "choice", ALL_PROFILES,
        short="Dernière hausse de prix",
        choices=(
            ("recent", "Il y a moins d'un an"),
            ("moyen", "Il y a 1 à 2 ans"),
            ("ancien", "Il y a plus de 2 ans"),
            ("jamais", "Je n'ai jamais augmenté mes prix"),
        ),
        help="Sans hausse régulière, l'inflation grignote la marge année "
             "après année.",
    ),
    Question(
        "vision_3ans",
        "Avez-vous une vision claire de ce que sera l'entreprise dans 3 ans ?",
        "strategie", "scale", ("croissance", "strategique"),
        short="Clarté de la vision 3 ans",
        scale_labels=("Je navigue à vue", "Cap très clair"),
        help="Existence d'un cap stratégique formalisé, chiffré et partagé "
             "avec l'équipe.",
    ),
    Question(
        "taille_marche",
        "Selon vous, le marché local accessible est-il assez grand pour "
        "continuer à croître ?",
        "strategie", "choice", ("croissance", "strategique"),
        short="Potentiel du marché local",
        choices=(
            ("large", "Largement suffisant pour croître"),
            ("limite", "Suffisant mais qui commence à plafonner"),
            ("etroit", "Trop étroit, déjà saturé"),
            ("inconnu", "Je ne sais pas vraiment le mesurer"),
        ),
        help="Évalue le potentiel de croissance sur le territoire avant "
             "d'envisager export, diversification ou nouveau marché.",
    ),

    # ───────────────────────── RISQUES & RÉSILIENCE ─────────────────
    Question(
        "part_plus_gros_fournisseur",
        "Votre principal fournisseur représente quelle part de vos achats ?",
        "risques", "percent", ALL_PROFILES,
        exclude_sectors=SERVICES_IMMATERIELS, unit="%",
        short="Poids du 1er fournisseur", placeholder="35", min=0, max=100,
        help="Mesure la dépendance d'approvisionnement. Critique en contexte "
             "insulaire : délai, rupture, hausse de prix subie.",
    ),
    Question(
        "exposition_import",
        "Vos approvisionnements dépendent-ils beaucoup des importations et "
        "des délais maritimes ?",
        "risques", "scale", ALL_PROFILES,
        exclude_sectors=SERVICES_IMMATERIELS,
        short="Exposition aux importations",
        scale_labels=("Appro locale fiable", "Tout importé / fragile"),
        help="Exposition aux ruptures logistiques et aux délais "
             "d'acheminement — enjeu majeur en Antilles-Guyane.",
    ),
    Question(
        "homme_cle",
        "Si vous (ou une personne clé) deviez vous arrêter du jour au "
        "lendemain, l'activité tiendrait-elle ?",
        "risques", "scale", ALL_PROFILES,
        short="Dépendance à une personne clé",
        scale_labels=("Aucune dépendance", "Une personne irremplaçable"),
        help="Risque de continuité quand un savoir-faire ou des relations "
             "clés reposent sur une seule tête.",
    ),
    Question(
        "carnet_commandes",
        "Combien de mois d'activité votre carnet de commandes couvre-t-il "
        "déjà ?",
        "risques", "number",
        ("solo", "tpe", "pme", "croissance", "reprise", "strategique"),
        sectors=("btp", "artisanat", "industrie", "evenementiel",
                 "services_pro"),
        unit="mois", short="Visibilité carnet de commandes",
        placeholder="3", min=0, max=48,
        help="Visibilité réelle sur le travail déjà signé devant vous. "
             "Un carnet court fragilise la planification et la trésorerie.",
    ),
    Question(
        "part_ca_public",
        "Quelle part de votre chiffre d'affaires provient de la commande "
        "publique (collectivités, État) ?",
        "risques", "percent", ("tpe", "pme", "croissance", "strategique"),
        unit="%", short="Part commande publique", placeholder="20",
        min=0, max=100,
        help="Le secteur public paie souvent plus tard : un poids élevé pèse "
             "directement sur la trésorerie (DSO).",
    ),
    Question(
        "tresorerie_secours",
        "Sans aucune nouvelle rentrée d'argent, combien de mois l'entreprise "
        "tiendrait-elle avec ses réserves ?",
        "risques", "number", ALL_PROFILES, unit="mois",
        short="Matelas de sécurité", placeholder="2", min=0, max=36,
        help="Nombre de mois de charges couverts par l'épargne disponible. "
             "C'est l'amortisseur en cas de coup dur.",
    ),

    # ═════════════════════════════════════════════════════════════════
    #  QUESTIONS SECTORIELLES COMPLÉMENTAIRES
    #  Activées uniquement quand le secteur correspondant est choisi,
    #  pour que le questionnaire colle au métier réel de l'entreprise.
    # ═════════════════════════════════════════════════════════════════

    # ── FINANCE ──────────────────────────────────────────────────────
    Question(
        "ratio_cout_matiere",
        "Quel pourcentage de votre chiffre d'affaires part dans l'achat des "
        "matières premières (denrées, ingrédients) ?",
        "finance", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("restauration", "hotellerie", "agro"),
        unit="%", short="Coût matière (food cost)", placeholder="30",
        min=0, max=100,
        help="Le « food cost » : poids des denrées dans le prix de vente. "
             "Au-delà de 35 %, la marge fond rapidement en restauration.",
    ),
    Question(
        "marge_revente_pct",
        "Sur un produit vendu, quel pourcentage vous reste-t-il après avoir "
        "payé son achat ou sa fabrication ?",
        "finance", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("commerce", "ecommerce", "artisanat"),
        unit="%", short="Taux de marge sur revente", placeholder="40",
        min=0, max=100,
        help="Marge commerciale moyenne : (prix de vente − coût d'achat) / "
             "prix de vente. Cœur de la rentabilité d'un négoce.",
    ),

    # ── COMMERCIAL ───────────────────────────────────────────────────
    Question(
        "taux_conversion_web",
        "Sur 100 visiteurs de votre site, combien finissent par acheter ou "
        "demander un devis ?",
        "commercial", "number",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("ecommerce", "numerique"),
        unit="sur 100", short="Taux de conversion web", placeholder="2",
        min=0, max=100,
        help="Taux de conversion du site. En e-commerce, 1 à 3 % est courant ; "
             "en dessous de 1 %, le tunnel de vente fuit.",
    ),
    Question(
        "taux_retour_produits",
        "Quelle part des produits vendus vous revient en retour, échange ou "
        "réclamation ?",
        "commercial", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("ecommerce", "commerce"),
        unit="%", short="Taux de retours / SAV", placeholder="8",
        min=0, max=100,
        help="Un taux de retour élevé ronge la marge (logistique, remise en "
             "stock) et signale souvent un problème d'offre ou de description.",
    ),
    Question(
        "reservation_directe_pct",
        "Quelle part de vos réservations arrive en direct, sans passer par une "
        "plateforme qui prend une commission ?",
        "commercial", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("hotellerie", "tourisme", "restauration"),
        unit="%", short="Part de réservations directes", placeholder="40",
        min=0, max=100,
        help="Les plateformes (OTA, agrégateurs) prélèvent 10 à 25 %. Plus la "
             "réservation directe est forte, plus la marge est préservée.",
    ),

    # ── ORGANISATION ─────────────────────────────────────────────────
    Question(
        "taux_staffing",
        "En moyenne, quel pourcentage du temps de vos équipes est vendu à un "
        "client (par opposition à l'inter-contrat) ?",
        "organisation", "percent",
        ("tpe", "pme", "croissance", "reprise"),
        sectors=("conseil", "services_pro", "numerique"),
        unit="%", short="Taux de staffing", placeholder="75",
        min=0, max=100,
        help="Taux d'occupation facturable des consultants. En dessous de "
             "70 %, la masse salariale n'est pas couverte par la production.",
    ),
    Question(
        "taux_sous_traitance",
        "Quelle part de vos chantiers ou commandes confiez-vous à des "
        "sous-traitants ?",
        "organisation", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("btp", "artisanat", "industrie", "evenementiel"),
        unit="%", short="Part de sous-traitance", placeholder="25",
        min=0, max=100,
        help="La sous-traitance apporte de la souplesse mais dilue la marge "
             "et la maîtrise qualité si elle devient majoritaire.",
    ),
    Question(
        "rotation_stock",
        "Combien de jours, en moyenne, un produit reste-t-il en stock avant "
        "d'être vendu ?",
        "organisation", "number",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("commerce", "ecommerce", "agro", "industrie"),
        unit="jours", short="Rotation des stocks", placeholder="45",
        min=0, max=365,
        help="Délai d'écoulement du stock. Plus il est long, plus de "
             "trésorerie dort en rayon et plus le risque d'invendus grandit.",
    ),

    # ── RISQUES ──────────────────────────────────────────────────────
    Question(
        "saisonnalite_dependance",
        "Votre activité dépend-elle fortement d'une saison ou d'une période "
        "de l'année ?",
        "risques", "scale", ALL_PROFILES,
        sectors=("tourisme", "evenementiel", "restauration", "agro",
                 "hotellerie"),
        short="Dépendance à la saison",
        scale_labels=("Activité régulière", "Tout se joue sur une saison"),
        help="Une forte saisonnalité concentre le chiffre d'affaires sur "
             "quelques mois et tend la trésorerie le reste de l'année.",
    ),
    Question(
        "no_show_pct",
        "Quelle part de vos rendez-vous ou réservations se transforme en "
        "absence non prévenue (no-show) ?",
        "risques", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("restauration", "hotellerie", "sante", "beaute"),
        unit="%", short="Taux de no-show", placeholder="10",
        min=0, max=100,
        help="Chaque créneau perdu est un revenu non rattrapable. Un no-show "
             "élevé justifie acompte, rappels automatiques ou surbooking.",
    ),
    Question(
        "taux_remplissage_tournees",
        "En moyenne, à quel point vos véhicules ou tournées sont-ils remplis "
        "par rapport à leur capacité ?",
        "risques", "percent",
        ("solo", "tpe", "pme", "croissance", "reprise"),
        sectors=("transport",),
        unit="%", short="Remplissage des tournées", placeholder="70",
        min=0, max=100,
        help="Rouler à vide ou à moitié plein détruit la marge : carburant et "
             "temps chauffeur sont engagés quel que soit le taux de charge.",
    ),

    # ── STRATÉGIE ────────────────────────────────────────────────────
    Question(
        "part_subventions",
        "Quelle part de vos ressources provient de subventions, aides ou "
        "financements publics ?",
        "strategie", "percent", ALL_PROFILES,
        sectors=("association", "agro", "formation"),
        unit="%", short="Part de subventions", placeholder="40",
        min=0, max=100,
        help="Une dépendance forte aux aides fragilise le modèle si elles "
             "diminuent : à équilibrer avec des ressources propres.",
    ),
    Question(
        "lots_geres",
        "Combien de biens ou de lots gérez-vous actuellement ?",
        "strategie", "number",
        ("solo", "tpe", "pme", "croissance", "reprise", "strategique"),
        sectors=("immobilier",),
        unit="lots", short="Portefeuille géré", placeholder="120", min=0,
        help="Volume de biens sous gestion : base des revenus récurrents et "
             "indicateur de l'effet d'échelle de l'activité.",
    ),

    # ═════════════════════════════════════════════════════════════════
    #  BLOC MÉTIER — questions 100 % spécifiques au secteur (domain="metier")
    #  Affichées dans un bloc titré au nom du secteur (cf. SECTOR_BLOCKS).
    #  Certaines sont conditionnées au profil (variantes par type d'entreprise).
    #  Ces réponses nourrissent l'analyse qualitative et le rapport, sans
    #  entrer dans le score /100.
    # ═════════════════════════════════════════════════════════════════

    # ── COMMERCE DE DÉTAIL / NÉGOCE ──────────────────────────────────
    Question(
        "com_surface_vente",
        "Quelle est la surface de vente de votre point de vente principal ?",
        "metier", "number", ALL_PROFILES, sectors=("commerce",),
        unit="m²", short="Surface de vente", placeholder="80", min=0,
        help="Sert à mesurer le chiffre d'affaires au m² — indicateur clé de "
             "performance d'un commerce physique.",
    ),
    Question(
        "com_passage_jour",
        "Combien de personnes franchissent votre porte un jour de semaine "
        "type ?",
        "metier", "number", ALL_PROFILES, sectors=("commerce",),
        unit="visiteurs/j", short="Trafic en magasin", placeholder="120", min=0,
        help="Le flux entrant : base du calcul du taux de transformation et de "
             "l'efficacité de votre vitrine / emplacement.",
    ),
    Question(
        "com_taux_transformation",
        "Sur 100 personnes qui entrent, combien repartent avec un achat ?",
        "metier", "number", ALL_PROFILES, sectors=("commerce",),
        unit="sur 100", short="Taux de transformation", placeholder="25",
        min=0, max=100,
        help="Taux de transformation en magasin. Un trafic élevé qui ne "
             "convertit pas signale un problème d'offre, de prix ou d'accueil.",
    ),
    Question(
        "com_part_ligne",
        "Quelle part de vos ventes se fait en ligne (e-shop, click & "
        "collect) ?",
        "metier", "percent", ALL_PROFILES, sectors=("commerce",),
        unit="%", short="Part des ventes en ligne", placeholder="15",
        min=0, max=100,
        help="Mesure votre dépendance au point de vente physique et votre "
             "capacité à capter la demande omnicanale.",
    ),
    Question(
        "com_invendus_pct",
        "Quelle part de vos achats finit en démarque (invendus, soldes "
        "profonds, casse) ?",
        "metier", "percent", P_ETABLI, sectors=("commerce",),
        unit="%", short="Taux de démarque", placeholder="8", min=0, max=100,
        help="La démarque détruit directement la marge. Au-delà de 10 %, la "
             "politique d'achat et la gestion des stocks sont à revoir.",
    ),
    Question(
        "com_nb_points_vente",
        "Combien de points de vente exploitez-vous ?",
        "metier", "number", P_STRUCT, sectors=("commerce",),
        unit="boutiques", short="Nombre de points de vente", placeholder="3",
        min=0,
        help="Le pilotage multi-sites change la donne : homogénéité de l'offre, "
             "logistique et reporting par magasin deviennent critiques.",
    ),
    Question(
        "com_fidelite",
        "Disposez-vous d'un programme de fidélité réellement actif ?",
        "metier", "scale", ALL_PROFILES, sectors=("commerce",),
        short="Fidélisation client",
        scale_labels=("Aucun / inactif", "Actif et exploité"),
        help="Faire revenir un client coûte bien moins cher que d'en conquérir "
             "un nouveau : un levier de marge souvent sous-exploité.",
    ),

    # ── E-COMMERCE / VENTE EN LIGNE ──────────────────────────────────
    Question(
        "eco_panier_abandon",
        "Sur 100 paniers créés sur votre site, combien sont abandonnés avant "
        "le paiement ?",
        "metier", "number", ALL_PROFILES, sectors=("ecommerce",),
        unit="sur 100", short="Taux d'abandon panier", placeholder="70",
        min=0, max=100,
        help="L'abandon de panier (souvent 60-80 %) est la première fuite de "
             "CA : frais de port, friction au paiement ou manque de réassurance.",
    ),
    Question(
        "eco_cout_acquisition",
        "Combien vous coûte en moyenne l'acquisition d'un nouveau client "
        "(publicité + marketing) ?",
        "metier", "currency", ALL_PROFILES, sectors=("ecommerce",),
        unit="€", short="Coût d'acquisition (CAC)", placeholder="18", min=0,
        help="À comparer au panier moyen et à la valeur vie client. Un CAC "
             "supérieur à la première marge n'est tenable qu'avec du réachat.",
    ),
    Question(
        "eco_part_marketplace",
        "Quelle part de vos ventes passe par une marketplace (Amazon, "
        "Cdiscount…) qui prélève une commission ?",
        "metier", "percent", ALL_PROFILES, sectors=("ecommerce",),
        unit="%", short="Part marketplaces", placeholder="35", min=0, max=100,
        help="Les marketplaces apportent du volume mais prélèvent 10-20 % et "
             "vous coupent de la relation client : un risque de dépendance.",
    ),
    Question(
        "eco_recurrence_achat",
        "Vos clients reviennent-ils acheter, ou achètent-ils une seule fois ?",
        "metier", "scale", ALL_PROFILES, sectors=("ecommerce",),
        short="Réachat client",
        scale_labels=("Achat unique", "Réachat fréquent"),
        help="Un modèle qui repose uniquement sur l'acquisition est fragile. "
             "Le réachat est ce qui rend la croissance rentable.",
    ),
    Question(
        "eco_delai_prepa",
        "Combien d'heures s'écoulent en moyenne entre la commande et son "
        "expédition ?",
        "metier", "number", ALL_PROFILES, sectors=("ecommerce",),
        unit="heures", short="Délai de préparation", placeholder="24", min=0,
        help="La rapidité d'expédition pèse sur la satisfaction et les avis. "
             "Au-delà de 48 h, le taux de litige et d'annulation grimpe.",
    ),
    Question(
        "eco_taux_repeat",
        "Quelle part de votre CA provient de clients déjà existants ?",
        "metier", "percent", P_STRUCT, sectors=("ecommerce",),
        unit="%", short="CA clients récurrents", placeholder="40",
        min=0, max=100,
        help="Indicateur de maturité : une boutique mature vit de sa base "
             "client, pas seulement de l'acquisition payante.",
    ),

    # ── RESTAURATION / CAFÉ / TRAITEUR ───────────────────────────────
    Question(
        "rest_couverts_jour",
        "Combien de couverts servez-vous un jour d'affluence normale ?",
        "metier", "number", ALL_PROFILES, sectors=("restauration",),
        unit="couverts", short="Couverts / jour", placeholder="80", min=0,
        help="Le volume de couverts, croisé au ticket moyen, donne le CA "
             "potentiel réel de votre établissement.",
    ),
    Question(
        "rest_rotation_table",
        "Combien de fois une table est-elle réoccupée sur un même service ?",
        "metier", "number", ALL_PROFILES, sectors=("restauration",),
        unit="rotations", short="Rotation des tables", placeholder="2", min=0,
        help="La rotation conditionne le CA à capacité égale. Une rotation "
             "faible peut venir d'un service lent ou d'une carte trop large.",
    ),
    Question(
        "rest_part_boisson",
        "Quelle part du ticket provient des boissons (souvent la vraie "
        "marge) ?",
        "metier", "percent", ALL_PROFILES, sectors=("restauration",),
        unit="%", short="Part boissons", placeholder="30", min=0, max=100,
        help="Les boissons portent une marge bien supérieure aux plats. Un "
             "ratio faible laisse de la rentabilité sur la table.",
    ),
    Question(
        "rest_pertes_matiere",
        "Quelle part des denrées part en pertes (périmé, erreurs, "
        "gaspillage) ?",
        "metier", "percent", P_ETABLI, sectors=("restauration",),
        unit="%", short="Pertes matière", placeholder="6", min=0, max=100,
        help="Le gaspillage s'ajoute au food cost. Au-delà de 5 %, la gestion "
             "des achats et des portions est à reprendre.",
    ),
    Question(
        "rest_avis_note",
        "Quelle est votre note moyenne sur les plateformes d'avis (Google, "
        "TripAdvisor) ?",
        "metier", "scale", ALL_PROFILES, sectors=("restauration",),
        short="Note d'e-réputation",
        scale_labels=("Mauvaise / absente", "Excellente"),
        help="En restauration, la note en ligne fait remplir (ou vider) la "
             "salle. C'est un actif commercial à part entière.",
    ),
    Question(
        "rest_part_livraison",
        "Quelle part de votre CA passe par la livraison (Uber Eats, "
        "Deliveroo…) ?",
        "metier", "percent", ALL_PROFILES, sectors=("restauration",),
        unit="%", short="Part livraison", placeholder="20", min=0, max=100,
        help="Les plateformes de livraison prélèvent jusqu'à 30 % : un volume "
             "fort peut gonfler le CA tout en écrasant la marge.",
    ),
    Question(
        "rest_personnel_pct",
        "Quelle part du CA part en masse salariale (cuisine + salle) ?",
        "metier", "percent", P_STRUCT, sectors=("restauration",),
        unit="%", short="Coût personnel", placeholder="35", min=0, max=100,
        help="Avec le food cost, c'est l'autre grand poste. La somme des deux "
             "(prime cost) doit rester sous ~65 % pour dégager une marge.",
    ),

    # ── HÔTELLERIE / HÉBERGEMENT ─────────────────────────────────────
    Question(
        "hot_adr",
        "Quel est votre prix moyen par nuitée réellement vendue (ADR) ?",
        "metier", "currency", ALL_PROFILES, sectors=("hotellerie",),
        unit="€", short="Prix moyen / nuitée (ADR)", placeholder="95", min=0,
        help="L'Average Daily Rate : prix moyen encaissé par chambre vendue. "
             "Croisé au taux d'occupation, il donne le RevPAR.",
    ),
    Question(
        "hot_revpar",
        "Quel est votre revenu moyen par chambre disponible (RevPAR) ?",
        "metier", "currency", P_ETABLI, sectors=("hotellerie",),
        unit="€", short="RevPAR", placeholder="68", min=0,
        help="Le RevPAR (prix moyen × taux d'occupation) est l'indicateur roi "
             "de l'hôtellerie : il mesure la performance réelle du parc.",
    ),
    Question(
        "hot_duree_sejour",
        "Quelle est la durée moyenne d'un séjour chez vous (en nuitées) ?",
        "metier", "number", ALL_PROFILES, sectors=("hotellerie",),
        unit="nuitées", short="Durée moyenne de séjour", placeholder="2", min=0,
        help="Des séjours longs réduisent les coûts de rotation (ménage, "
             "check-in) et stabilisent le taux d'occupation.",
    ),
    Question(
        "hot_part_extra",
        "Quelle part du CA provient des extras (restauration, spa, "
        "services) ?",
        "metier", "percent", ALL_PROFILES, sectors=("hotellerie",),
        unit="%", short="Part des extras", placeholder="25", min=0, max=100,
        help="Les revenus annexes améliorent fortement la rentabilité par "
             "client sans dépendre du taux d'occupation.",
    ),
    Question(
        "hot_repeat_client",
        "Quelle part de vos clients sont des habitués qui reviennent ?",
        "metier", "percent", P_ETABLI, sectors=("hotellerie",),
        unit="%", short="Clients fidèles", placeholder="20", min=0, max=100,
        help="Un client fidèle réserve souvent en direct et coûte moins cher "
             "en commission : un levier de marge directe.",
    ),
    Question(
        "hot_avis_note",
        "Quelle est votre note moyenne sur les plateformes (Booking, "
        "Google) ?",
        "metier", "scale", ALL_PROFILES, sectors=("hotellerie",),
        short="Note d'e-réputation",
        scale_labels=("Mauvaise / absente", "Excellente"),
        help="La note conditionne votre classement sur les plateformes et donc "
             "votre visibilité et votre taux d'occupation.",
    ),

    # ── TOURISME / LOISIRS / ACTIVITÉS ───────────────────────────────
    Question(
        "tou_capacite_jour",
        "Combien de personnes pouvez-vous accueillir au maximum par jour ?",
        "metier", "number", ALL_PROFILES, sectors=("tourisme",),
        unit="pers./j", short="Capacité d'accueil", placeholder="60", min=0,
        help="Votre plafond physique de production : il borne le CA atteignable "
             "et oriente la stratégie de remplissage et de tarif.",
    ),
    Question(
        "tou_remplissage",
        "En haute saison, à quel taux remplissez-vous cette capacité ?",
        "metier", "percent", ALL_PROFILES, sectors=("tourisme",),
        unit="%", short="Taux de remplissage", placeholder="75", min=0, max=100,
        help="Un faible remplissage même en pointe interroge la demande, la "
             "visibilité ou la politique tarifaire.",
    ),
    Question(
        "tou_meteo_dependance",
        "Votre activité dépend-elle de la météo ?",
        "metier", "scale", ALL_PROFILES, sectors=("tourisme",),
        short="Dépendance météo",
        scale_labels=("Indifférente", "Très sensible"),
        help="Une forte dépendance météo augmente la volatilité du CA : à "
             "compenser par des offres « tout temps » ou des reports.",
    ),
    Question(
        "tou_panier_extra",
        "Quelle part du CA vient des ventes additionnelles (options, "
        "boutique, restauration) ?",
        "metier", "percent", ALL_PROFILES, sectors=("tourisme",),
        unit="%", short="Ventes additionnelles", placeholder="20",
        min=0, max=100,
        help="Augmenter le panier par client est souvent plus rentable que "
             "d'augmenter la fréquentation, déjà plafonnée par la capacité.",
    ),
    Question(
        "tou_anticipation_resa",
        "Combien de jours à l'avance vos clients réservent-ils en moyenne ?",
        "metier", "number", ALL_PROFILES, sectors=("tourisme",),
        unit="jours", short="Anticipation des réservations", placeholder="14",
        min=0,
        help="Une bonne visibilité permet d'optimiser les prix (yield) et "
             "d'ajuster les ressources. Le « last minute » la complique.",
    ),
    Question(
        "tou_part_groupes",
        "Quelle part de votre CA provient des groupes / B2B (CE, agences, "
        "scolaires) ?",
        "metier", "percent", P_ETABLI, sectors=("tourisme",),
        unit="%", short="Part groupes / B2B", placeholder="30", min=0, max=100,
        help="Les groupes sécurisent le remplissage mais négocient les prix : "
             "un équilibre à trouver avec la clientèle individuelle.",
    ),

    # ── SERVICES AUX ENTREPRISES (B2B) ───────────────────────────────
    Question(
        "spro_duree_mission",
        "Quelle est la durée moyenne d'une mission ou d'un contrat (en "
        "mois) ?",
        "metier", "number", ALL_PROFILES, sectors=("services_pro",),
        unit="mois", short="Durée moyenne de mission", placeholder="6", min=0,
        help="Des missions longues stabilisent le CA et réduisent l'effort "
             "commercial ; des missions courtes exigent un pipeline nourri.",
    ),
    Question(
        "spro_taux_upsell",
        "Quelle part de votre CA provient de ventes additionnelles chez des "
        "clients existants ?",
        "metier", "percent", ALL_PROFILES, sectors=("services_pro",),
        unit="%", short="Upsell clients existants", placeholder="30",
        min=0, max=100,
        help="Développer un client acquis coûte bien moins cher qu'en "
             "conquérir un nouveau : un moteur de croissance rentable.",
    ),
    Question(
        "spro_cycle_vente",
        "Combien de jours s'écoulent entre le premier contact et la "
        "signature ?",
        "metier", "number", ALL_PROFILES, sectors=("services_pro",),
        unit="jours", short="Cycle de vente", placeholder="45", min=0,
        help="Un cycle long mobilise de la trésorerie commerciale et exige "
             "d'anticiper la prospection plusieurs mois à l'avance.",
    ),
    Question(
        "spro_nps",
        "Vos clients vous recommanderaient-ils spontanément ?",
        "metier", "scale", ALL_PROFILES, sectors=("services_pro",),
        short="Recommandation client",
        scale_labels=("Peu probable", "Très probable"),
        help="En B2B, la recommandation est le premier canal d'acquisition. "
             "Une faible propension à recommander annonce du churn.",
    ),
    Question(
        "spro_pipe_couverture",
        "Combien de mois de CA votre pipeline d'opportunités qualifiées "
        "couvre-t-il ?",
        "metier", "number", P_ETABLI, sectors=("services_pro",),
        unit="mois", short="Couverture du pipeline", placeholder="3", min=0,
        help="La visibilité commerciale : un pipeline court annonce un trou "
             "d'activité quelques mois plus tard.",
    ),
    Question(
        "spro_concentration_secteur",
        "Vos clients sont-ils concentrés sur un même secteur d'activité ?",
        "metier", "scale", P_STRUCT, sectors=("services_pro",),
        short="Concentration sectorielle",
        scale_labels=("Très diversifié", "Un seul secteur"),
        help="Une dépendance à un secteur unique expose à ses retournements "
             "(conjoncture, réglementation) : à surveiller comme un risque.",
    ),

    # ── SERVICES AUX PARTICULIERS (B2C) ──────────────────────────────
    Question(
        "spart_zone_chalandise",
        "Dans quel rayon (en km) se trouve l'essentiel de vos clients ?",
        "metier", "number", ALL_PROFILES, sectors=("services_part",),
        unit="km", short="Zone de chalandise", placeholder="20", min=0,
        help="Définit votre marché adressable réel et le temps de trajet "
             "non facturable entre interventions.",
    ),
    Question(
        "spart_recommandation_pct",
        "Quelle part de vos nouveaux clients vient du bouche-à-oreille ?",
        "metier", "percent", ALL_PROFILES, sectors=("services_part",),
        unit="%", short="Part bouche-à-oreille", placeholder="50",
        min=0, max=100,
        help="Le bouche-à-oreille est gratuit mais peu maîtrisable. Trop en "
             "dépendre fragilise la croissance et la prévisibilité.",
    ),
    Question(
        "spart_taux_reabonnement",
        "Quelle part de vos clients refait appel à vous dans l'année ?",
        "metier", "percent", ALL_PROFILES, sectors=("services_part",),
        unit="%", short="Taux de réachat", placeholder="40", min=0, max=100,
        help="La récurrence transforme un client en revenu prévisible. C'est "
             "le cœur de la rentabilité d'un service de proximité.",
    ),
    Question(
        "spart_avis_note",
        "Quelle est votre note moyenne sur les plateformes en ligne ?",
        "metier", "scale", ALL_PROFILES, sectors=("services_part",),
        short="Note d'e-réputation",
        scale_labels=("Mauvaise / absente", "Excellente"),
        help="Pour un service local, les avis Google sont devenus le premier "
             "réflexe des clients avant de choisir.",
    ),
    Question(
        "spart_capacite_rdv",
        "Combien d'interventions ou de rendez-vous pouvez-vous honorer par "
        "semaine ?",
        "metier", "number", ALL_PROFILES, sectors=("services_part",),
        unit="/semaine", short="Capacité hebdomadaire", placeholder="25", min=0,
        help="Votre plafond de production. S'il est saturé, la croissance "
             "passe par l'embauche, la hausse des prix ou l'optimisation.",
    ),
    Question(
        "spart_part_urgence",
        "Quelle part de votre activité relève de l'urgence / du dépannage ?",
        "metier", "percent", P_PETIT, sectors=("services_part",),
        unit="%", short="Part urgence / dépannage", placeholder="30",
        min=0, max=100,
        help="L'urgence se facture plus cher mais désorganise le planning. Un "
             "fort taux rend l'activité difficile à lisser et à déléguer.",
    ),

    # ── CONSEIL / PROFESSION LIBÉRALE ────────────────────────────────
    Question(
        "cons_jours_factures_an",
        "Combien de jours réellement facturables visez-vous sur l'année ?",
        "metier", "number", ALL_PROFILES, sectors=("conseil",),
        unit="jours/an", short="Jours facturables / an", placeholder="180",
        min=0, max=366,
        help="Le vrai plafond de revenu d'un libéral. Entre congés, admin et "
             "prospection, 180-200 jours est souvent un maximum réaliste.",
    ),
    Question(
        "cons_taux_realisation",
        "Sur le temps réellement passé pour vos clients, quelle part "
        "facturez-vous ?",
        "metier", "percent", ALL_PROFILES, sectors=("conseil",),
        unit="%", short="Taux de réalisation", placeholder="80",
        min=0, max=100,
        help="Le temps « offert » (dépassements, reprises) ronge le taux "
             "journalier réel bien en dessous du TJM affiché.",
    ),
    Question(
        "cons_part_forfait",
        "Quelle part de vos missions est au forfait (vs facturée à la "
        "journée) ?",
        "metier", "percent", ALL_PROFILES, sectors=("conseil",),
        unit="%", short="Part au forfait", placeholder="40", min=0, max=100,
        help="Le forfait peut booster la marge si bien cadré, ou la détruire "
             "en cas de dérive de charge mal maîtrisée.",
    ),
    Question(
        "cons_prescription_pct",
        "Quelle part de vos clients vient de prescripteurs / apporteurs "
        "d'affaires ?",
        "metier", "percent", ALL_PROFILES, sectors=("conseil",),
        unit="%", short="Part prescription", placeholder="50", min=0, max=100,
        help="La prescription est un canal puissant mais subi. La rendre "
             "active (réseau structuré) sécurise le flux d'affaires.",
    ),
    Question(
        "cons_specialisation",
        "Êtes-vous positionné sur une niche d'expertise ou plutôt "
        "généraliste ?",
        "metier", "scale", ALL_PROFILES, sectors=("conseil",),
        short="Spécialisation",
        scale_labels=("Généraliste", "Niche d'expert"),
        help="La spécialisation justifie un tarif premium et réduit la "
             "concurrence : un positionnement clair vaut de la marge.",
    ),
    Question(
        "cons_temps_admin",
        "Quelle part de votre temps part en administratif non facturable ?",
        "metier", "percent", P_PETIT, sectors=("conseil",),
        unit="%", short="Temps administratif", placeholder="20",
        min=0, max=100,
        help="Chaque heure d'admin est une heure non vendue. Au-delà de 25 %, "
             "déléguer ou outiller devient rentable.",
    ),

    # ── SANTÉ / BIEN-ÊTRE / PARAMÉDICAL ──────────────────────────────
    Question(
        "sante_patients_jour",
        "Combien de patients ou de clients voyez-vous un jour type ?",
        "metier", "number", ALL_PROFILES, sectors=("sante",),
        unit="/jour", short="Patients / jour", placeholder="18", min=0,
        help="Le volume quotidien, croisé au tarif moyen, donne le CA réel et "
             "révèle la charge de travail soutenable.",
    ),
    Question(
        "sante_part_conventionne",
        "Quelle part de votre activité est conventionnée / remboursée (vs "
        "honoraires libres) ?",
        "metier", "percent", ALL_PROFILES, sectors=("sante",),
        unit="%", short="Part conventionnée", placeholder="70", min=0, max=100,
        help="Le conventionné sécurise le volume mais plafonne les tarifs. La "
             "part libre est souvent le vrai levier de revenu.",
    ),
    Question(
        "sante_delai_rdv",
        "Quel est le délai moyen pour obtenir un rendez-vous (en jours) ?",
        "metier", "number", ALL_PROFILES, sectors=("sante",),
        unit="jours", short="Délai de RDV", placeholder="7", min=0,
        help="Un délai long signale une demande forte (opportunité de tarif "
             "ou d'embauche) mais aussi un risque de fuite de patientèle.",
    ),
    Question(
        "sante_fidelisation",
        "Quelle part de votre patientèle est suivie de façon régulière ?",
        "metier", "percent", ALL_PROFILES, sectors=("sante",),
        unit="%", short="Patientèle suivie", placeholder="60", min=0, max=100,
        help="Un suivi régulier stabilise l'activité et la trésorerie, et "
             "réduit la dépendance à l'acquisition de nouveaux patients.",
    ),
    Question(
        "sante_part_actes_techniques",
        "Quelle part de votre CA provient d'actes techniques à forte "
        "valeur ?",
        "metier", "percent", P_ETABLI, sectors=("sante",),
        unit="%", short="Actes à forte valeur", placeholder="35",
        min=0, max=100,
        help="Le mix d'actes pilote la rentabilité : trop d'actes peu "
             "valorisés sature l'agenda sans dégager de marge.",
    ),
    Question(
        "sante_equipe_soignante",
        "Combien de praticiens exercent au sein de la structure ?",
        "metier", "number", P_STRUCT, sectors=("sante",),
        unit="praticiens", short="Praticiens", placeholder="4", min=0,
        help="La structuration en équipe change le pilotage : planning "
             "partagé, mutualisation des coûts et continuité de service.",
    ),

    # ── BEAUTÉ / COIFFURE / ESTHÉTIQUE ───────────────────────────────
    Question(
        "beau_part_revente_produits",
        "Quelle part de votre CA vient de la revente de produits (vs "
        "prestations) ?",
        "metier", "percent", ALL_PROFILES, sectors=("beaute",),
        unit="%", short="Part revente produits", placeholder="15",
        min=0, max=100,
        help="La revente porte une marge élevée et ne consomme pas de temps "
             "de fauteuil : un levier de rentabilité souvent négligé.",
    ),
    Question(
        "beau_taux_remplissage_agenda",
        "À quel taux votre agenda est-il rempli une semaine type ?",
        "metier", "percent", ALL_PROFILES, sectors=("beaute",),
        unit="%", short="Remplissage de l'agenda", placeholder="70",
        min=0, max=100,
        help="Le fauteuil vide est du revenu perdu pour toujours. Optimiser "
             "le remplissage prime sur la hausse des prix.",
    ),
    Question(
        "beau_clients_reguliers",
        "Quelle part de vos clients revient régulièrement (habitués, "
        "abonnés) ?",
        "metier", "percent", ALL_PROFILES, sectors=("beaute",),
        unit="%", short="Clients réguliers", placeholder="55", min=0, max=100,
        help="La fidélité fait la stabilité du CA dans un métier de "
             "récurrence : un client fidèle vaut bien plus qu'une promo.",
    ),
    Question(
        "beau_prestation_phare",
        "Une seule prestation concentre-t-elle l'essentiel de votre CA ?",
        "metier", "scale", ALL_PROFILES, sectors=("beaute",),
        short="Concentration de l'offre",
        scale_labels=("Offre équilibrée", "Tout sur une prestation"),
        help="Dépendre d'une seule prestation expose aux modes et à la "
             "concurrence : diversifier sécurise le revenu.",
    ),
    Question(
        "beau_reservation_en_ligne",
        "Vos clients peuvent-ils réserver en ligne facilement ?",
        "metier", "scale", ALL_PROFILES, sectors=("beaute",),
        short="Réservation en ligne",
        scale_labels=("Non / téléphone seul", "Oui, fluide 24/7"),
        help="La réservation en ligne réduit les no-shows, remplit les "
             "créneaux creux et libère du temps au comptoir.",
    ),
    Question(
        "beau_nb_postes",
        "Combien de postes de travail / praticiens actifs avez-vous ?",
        "metier", "number", P_ETABLI, sectors=("beaute",),
        unit="postes", short="Postes actifs", placeholder="3", min=0,
        help="La capacité de production de l'institut/salon. Un poste non "
             "pourvu ou inoccupé pèse directement sur la rentabilité du loyer.",
    ),

    # ── ARTISANAT / MÉTIERS D'ART ────────────────────────────────────
    Question(
        "art_part_sur_mesure",
        "Quelle part de votre activité est du sur-mesure (vs série / "
        "standard) ?",
        "metier", "percent", ALL_PROFILES, sectors=("artisanat",),
        unit="%", short="Part sur-mesure", placeholder="60", min=0, max=100,
        help="Le sur-mesure valorise le savoir-faire mais se planifie mal et "
             "s'industrialise peu : un arbitrage marge / volume.",
    ),
    Question(
        "art_delai_realisation",
        "Quel est le délai moyen de réalisation d'une commande (en jours) ?",
        "metier", "number", ALL_PROFILES, sectors=("artisanat",),
        unit="jours", short="Délai de réalisation", placeholder="21", min=0,
        help="Le délai conditionne le carnet et la trésorerie : trop long, il "
             "fait fuir les clients ; mal estimé, il détruit la marge.",
    ),
    Question(
        "art_valorisation_savoir",
        "Vendez-vous votre savoir-faire à son juste prix, ou subissez-vous "
        "les prix du marché ?",
        "metier", "scale", ALL_PROFILES, sectors=("artisanat",),
        short="Valorisation du savoir-faire",
        scale_labels=("Prix subis", "Prix maîtrisés"),
        help="Le piège classique de l'artisan : un travail d'excellence "
             "facturé au prix d'un produit standard.",
    ),
    Question(
        "art_canal_vente",
        "Quel est votre principal canal de vente ?",
        "metier", "choice", ALL_PROFILES, sectors=("artisanat",),
        short="Canal de vente principal",
        choices=(
            ("atelier", "Atelier / boutique"),
            ("marches", "Marchés / salons"),
            ("ligne", "Vente en ligne"),
            ("revendeurs", "Revendeurs / dépôts-ventes"),
        ),
        help="Chaque canal a son économie : la vente directe préserve la marge, "
             "les revendeurs apportent du volume mais la divisent.",
    ),
    Question(
        "art_transmission",
        "Le savoir-faire repose-t-il sur une seule personne ?",
        "metier", "scale", P_STRUCT, sectors=("artisanat",),
        short="Dépendance au savoir-faire",
        scale_labels=("Équipe formée", "Une seule personne"),
        help="Un savoir-faire concentré sur une personne est un risque majeur "
             "de continuité et un frein à la valorisation de l'entreprise.",
    ),

    # ── BTP / CONSTRUCTION / RÉNOVATION ──────────────────────────────
    Question(
        "btp_taux_marge_chantier",
        "Sur un chantier type, quelle marge nette vous reste-t-il une fois "
        "tout payé ?",
        "metier", "percent", ALL_PROFILES, sectors=("btp",),
        unit="%", short="Marge nette par chantier", placeholder="12",
        min=0, max=100,
        help="La marge réelle après main-d'œuvre, matériaux et aléas. Des "
             "devis « au feeling » cachent souvent des chantiers à perte.",
    ),
    Question(
        "btp_depassement_budget",
        "Quelle part de vos chantiers dépasse le budget initial prévu ?",
        "metier", "percent", ALL_PROFILES, sectors=("btp",),
        unit="%", short="Chantiers en dépassement", placeholder="30",
        min=0, max=100,
        help="Le dépassement mange la marge prévue. Un taux élevé révèle un "
             "chiffrage ou un suivi de chantier à fiabiliser.",
    ),
    Question(
        "btp_delai_reglement_situations",
        "Combien de jours en moyenne pour être payé sur une situation de "
        "travaux ?",
        "metier", "number", ALL_PROFILES, sectors=("btp",),
        unit="jours", short="Délai de paiement situations", placeholder="60",
        min=0,
        help="Le BTP avance la trésorerie sur des mois. Des délais longs "
             "imposent un fonds de roulement solide pour éviter l'asphyxie.",
    ),
    Question(
        "btp_taux_intemperies",
        "Votre planning est-il souvent perturbé par les intempéries / "
        "aléas ?",
        "metier", "scale", ALL_PROFILES, sectors=("btp",),
        short="Exposition aux aléas",
        scale_labels=("Rarement", "Très souvent"),
        help="Les arrêts non planifiés décalent les chantiers et figent des "
             "coûts fixes (équipes, matériel) sans production.",
    ),
    Question(
        "btp_part_renovation",
        "Quelle part de votre activité est de la rénovation (vs "
        "construction neuve) ?",
        "metier", "percent", ALL_PROFILES, sectors=("btp",),
        unit="%", short="Part rénovation", placeholder="60", min=0, max=100,
        help="Rénovation et neuf n'ont ni la même saisonnalité, ni les mêmes "
             "marges, ni les mêmes aléas : à équilibrer selon la conjoncture.",
    ),
    Question(
        "btp_retenue_garantie",
        "Quel montant total est immobilisé en retenues de garantie chez vos "
        "clients ?",
        "metier", "currency", P_ETABLI, sectors=("btp",),
        unit="€", short="Retenues de garantie", placeholder="15000", min=0,
        help="5 % du marché bloqués jusqu'à un an : une trésorerie invisible "
             "mais bien réelle qu'il faut suivre et réclamer.",
    ),

    # ── INDUSTRIE / PRODUCTION ───────────────────────────────────────
    Question(
        "ind_taux_utilisation_machines",
        "À quel taux vos équipements de production tournent-ils par rapport "
        "à leur capacité ?",
        "metier", "percent", ALL_PROFILES, sectors=("industrie",),
        unit="%", short="Taux d'utilisation machines", placeholder="70",
        min=0, max=100,
        help="Un outil sous-utilisé immobilise du capital ; saturé, il bride "
             "la croissance. Le taux d'utilisation pilote l'investissement.",
    ),
    Question(
        "ind_taux_rebut",
        "Quelle part de votre production part en rebut / non-conformité ?",
        "metier", "percent", ALL_PROFILES, sectors=("industrie",),
        unit="%", short="Taux de rebut", placeholder="4", min=0, max=100,
        help="Chaque rebut est de la matière et du temps machine perdus. La "
             "non-qualité est un coût caché majeur en production.",
    ),
    Question(
        "ind_delai_production",
        "Quel est le délai moyen de production d'une commande (en jours) ?",
        "metier", "number", ALL_PROFILES, sectors=("industrie",),
        unit="jours", short="Délai de production", placeholder="15", min=0,
        help="Le délai conditionne la compétitivité et le besoin en fonds de "
             "roulement (encours de production à financer).",
    ),
    Question(
        "ind_dependance_matiere",
        "Êtes-vous exposé à la volatilité du prix des matières premières ?",
        "metier", "scale", ALL_PROFILES, sectors=("industrie",),
        short="Exposition matières premières",
        scale_labels=("Faible", "Très forte"),
        help="Sans clause de révision de prix, une flambée des matières peut "
             "transformer un carnet plein en chantiers à perte.",
    ),
    Question(
        "ind_part_export",
        "Quelle part de votre CA est réalisée à l'export ?",
        "metier", "percent", P_ETABLI, sectors=("industrie",),
        unit="%", short="Part export", placeholder="20", min=0, max=100,
        help="L'export diversifie les débouchés mais ajoute des risques "
             "(change, logistique, délais de paiement plus longs).",
    ),
    Question(
        "ind_automatisation",
        "Votre outil de production est-il automatisé / numérisé ?",
        "metier", "scale", P_STRUCT, sectors=("industrie",),
        short="Niveau d'automatisation",
        scale_labels=("Manuel", "Largement automatisé"),
        help="L'automatisation améliore la marge et la régularité, mais "
             "alourdit les charges fixes : à calibrer sur le volume réel.",
    ),

    # ── TRANSPORT / LOGISTIQUE ───────────────────────────────────────
    Question(
        "tra_cout_km",
        "Quel est votre coût de revient moyen au kilomètre ?",
        "metier", "currency", ALL_PROFILES, sectors=("transport",),
        unit="€/km", short="Coût au kilomètre", placeholder="1.2", min=0,
        help="La base de toute tarification rentable. Beaucoup de "
             "transporteurs facturent sans connaître leur vrai coût au km.",
    ),
    Question(
        "tra_part_retour_vide",
        "Quelle part de vos trajets se fait à vide (retours sans "
        "chargement) ?",
        "metier", "percent", ALL_PROFILES, sectors=("transport",),
        unit="%", short="Trajets à vide", placeholder="25", min=0, max=100,
        help="Un kilomètre à vide coûte presque autant qu'un kilomètre chargé. "
             "Réduire le vide est le premier levier de marge.",
    ),
    Question(
        "tra_dependance_carburant",
        "Votre rentabilité est-elle sensible au prix du carburant ?",
        "metier", "scale", ALL_PROFILES, sectors=("transport",),
        short="Exposition carburant",
        scale_labels=("Indexée / faible", "Très exposée"),
        help="Sans clause de répercussion gazole, chaque hausse du carburant "
             "se paie directement sur la marge.",
    ),
    Question(
        "tra_taux_ponctualite",
        "Quelle part de vos livraisons est faite dans les délais promis ?",
        "metier", "percent", ALL_PROFILES, sectors=("transport",),
        unit="%", short="Taux de ponctualité", placeholder="95",
        min=0, max=100,
        help="La fiabilité est le critère n°1 des donneurs d'ordre. Un taux "
             "qui baisse annonce des pénalités et des pertes de contrats.",
    ),
    Question(
        "tra_part_sous_traitance_trafic",
        "Quelle part de vos volumes confiez-vous à des affrétés / "
        "sous-traitants ?",
        "metier", "percent", P_ETABLI, sectors=("transport",),
        unit="%", short="Part affrétée", placeholder="30", min=0, max=100,
        help="L'affrètement absorbe les pics sans investir, mais dilue la "
             "marge et la maîtrise de la qualité de service.",
    ),
    Question(
        "tra_nb_vehicules",
        "Combien de véhicules composent votre flotte ?",
        "metier", "number", P_STRUCT, sectors=("transport",),
        unit="véhicules", short="Taille de flotte", placeholder="8", min=0,
        help="La flotte fixe une grande part des charges (financement, "
             "entretien, assurance) à couvrir quel que soit le remplissage.",
    ),

    # ── IMMOBILIER / GESTION LOCATIVE ────────────────────────────────
    Question(
        "immo_taux_occupation_parc",
        "Quel est le taux d'occupation de votre parc géré ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Occupation du parc", placeholder="95", min=0, max=100,
        help="La vacance locative est une perte sèche de revenus de gestion. "
             "Un taux qui baisse signale un problème de produit ou de marché.",
    ),
    Question(
        "immo_taux_impayes",
        "Quelle part des loyers que vous gérez est en impayé ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Taux d'impayés", placeholder="3", min=0, max=100,
        help="Les impayés engagent votre responsabilité de gestionnaire et "
             "pèsent sur la satisfaction des propriétaires bailleurs.",
    ),
    Question(
        "immo_honoraires_gestion",
        "Quel est votre taux d'honoraires de gestion moyen ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Honoraires de gestion", placeholder="7", min=0, max=100,
        help="Le socle de revenu récurrent de l'agence. Sous pression "
             "concurrentielle, chaque point d'honoraire compte.",
    ),
    Question(
        "immo_part_transaction",
        "Quelle part de votre CA vient de la transaction (vs gestion "
        "récurrente) ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Part transaction", placeholder="50", min=0, max=100,
        help="La transaction rapporte gros mais est volatile ; la gestion est "
             "régulière mais lente à construire. L'équilibre fait la solidité.",
    ),
    Question(
        "immo_mandats_exclusifs",
        "Quelle part de vos mandats sont des mandats exclusifs ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Mandats exclusifs", placeholder="40", min=0, max=100,
        help="L'exclusivité sécurise la commission et accélère la vente. Un "
             "faible taux disperse l'effort sur des biens partagés.",
    ),
    Question(
        "immo_rotation_locataires",
        "Quel est le taux de rotation annuel de vos locataires ?",
        "metier", "percent", P_ETABLI, sectors=("immobilier",),
        unit="%", short="Rotation des locataires", placeholder="15",
        min=0, max=100,
        help="Chaque rotation génère des frais (remise en état, recherche) et "
             "un risque de vacance : la stabilité locative protège la marge.",
    ),

    # ── FORMATION / ÉDUCATION ────────────────────────────────────────
    Question(
        "for_taux_remplissage_sessions",
        "À quel taux remplissez-vous vos sessions de formation ?",
        "metier", "percent", ALL_PROFILES, sectors=("formation",),
        unit="%", short="Remplissage des sessions", placeholder="75",
        min=0, max=100,
        help="Une session se tient avec des coûts quasi fixes : le "
             "remplissage fait toute la différence entre marge et perte.",
    ),
    Question(
        "for_part_finance_public",
        "Quelle part de votre CA est financée par fonds publics / OPCO / "
        "CPF ?",
        "metier", "percent", ALL_PROFILES, sectors=("formation",),
        unit="%", short="Part financement public", placeholder="60",
        min=0, max=100,
        help="Les financements publics structurent le marché mais exposent "
             "aux réformes (CPF, OPCO) : une dépendance à surveiller.",
    ),
    Question(
        "for_qualiopi",
        "Êtes-vous certifié Qualiopi / référencé pour le financement ?",
        "metier", "scale", ALL_PROFILES, sectors=("formation",),
        short="Certification Qualiopi",
        scale_labels=("Non", "Oui, certifié"),
        help="Qualiopi conditionne l'accès aux fonds publics : sans elle, une "
             "large part du marché finançable est fermée.",
    ),
    Question(
        "for_part_distanciel",
        "Quelle part de votre activité est en distanciel / e-learning ?",
        "metier", "percent", ALL_PROFILES, sectors=("formation",),
        unit="%", short="Part distanciel", placeholder="40", min=0, max=100,
        help="Le distanciel démultiplie la capacité sans coût de salle, mais "
             "demande d'autres compétences (production, animation à distance).",
    ),
    Question(
        "for_satisfaction_stagiaires",
        "Quel est le niveau de satisfaction moyen de vos stagiaires ?",
        "metier", "scale", ALL_PROFILES, sectors=("formation",),
        short="Satisfaction stagiaires",
        scale_labels=("Faible", "Excellente"),
        help="La satisfaction nourrit le bouche-à-oreille B2B et conditionne "
             "le maintien de la certification qualité.",
    ),
    Question(
        "for_recurrence_entreprises",
        "Quelle part de votre CA vient d'entreprises clientes récurrentes ?",
        "metier", "percent", P_ETABLI, sectors=("formation",),
        unit="%", short="Clients entreprises récurrents", placeholder="40",
        min=0, max=100,
        help="Les comptes entreprises récurrents stabilisent le CA et coûtent "
             "moins cher à vendre que l'inscription individuelle.",
    ),

    # ── ÉVÉNEMENTIEL / COMMUNICATION ─────────────────────────────────
    Question(
        "eve_nb_evenements_an",
        "Combien d'événements ou de projets livrez-vous par an ?",
        "metier", "number", ALL_PROFILES, sectors=("evenementiel",),
        unit="/an", short="Événements par an", placeholder="30", min=0,
        help="Le volume, croisé au budget moyen, donne le CA. Peu "
             "d'événements à fort budget = forte dépendance à chaque projet.",
    ),
    Question(
        "eve_panier_moyen_event",
        "Quel est le budget moyen d'un événement / projet client ?",
        "metier", "currency", ALL_PROFILES, sectors=("evenementiel",),
        unit="€", short="Budget moyen / projet", placeholder="8000", min=0,
        help="Le panier moyen oriente toute la stratégie : beaucoup de petits "
             "projets ou peu de gros n'exigent pas la même organisation.",
    ),
    Question(
        "eve_taux_marge_event",
        "Quelle marge nette vous reste-t-il sur un événement type ?",
        "metier", "percent", ALL_PROFILES, sectors=("evenementiel",),
        unit="%", short="Marge nette par projet", placeholder="20",
        min=0, max=100,
        help="Entre prestataires, location et imprévus, la marge fond vite. "
             "Un chiffrage rigoureux est vital dans ce métier de projet.",
    ),
    Question(
        "eve_acompte_signature",
        "Quelle part du prix exigez-vous en acompte à la signature ?",
        "metier", "percent", ALL_PROFILES, sectors=("evenementiel",),
        unit="%", short="Acompte à la signature", placeholder="40",
        min=0, max=100,
        help="L'acompte finance les engagements pris auprès des prestataires "
             "et protège des annulations : un amortisseur de trésorerie clé.",
    ),
    Question(
        "eve_part_recurrent_clients",
        "Quelle part de vos clients refait appel à vous l'année suivante ?",
        "metier", "percent", P_ETABLI, sectors=("evenementiel",),
        unit="%", short="Clients récurrents", placeholder="35", min=0, max=100,
        help="Les clients récurrents (événements annuels) réduisent l'effort "
             "commercial et donnent de la visibilité dans un métier en dents "
             "de scie.",
    ),

    # ── AGRICULTURE / PÊCHE / AGROALIMENTAIRE ────────────────────────
    Question(
        "agro_part_vente_directe",
        "Quelle part de votre production vendez-vous en direct (vs "
        "grossistes / coopérative) ?",
        "metier", "percent", ALL_PROFILES, sectors=("agro",),
        unit="%", short="Part vente directe", placeholder="40", min=0, max=100,
        help="La vente directe capte une marge bien supérieure, mais demande "
             "du temps commercial et logistique que la coop prend en charge.",
    ),
    Question(
        "agro_dependance_meteo",
        "Votre production dépend-elle fortement de la météo / du climat ?",
        "metier", "scale", ALL_PROFILES, sectors=("agro",),
        short="Dépendance climatique",
        scale_labels=("Faible", "Très forte"),
        help="L'aléa climatique fait varier les volumes d'une année à l'autre. "
             "L'assurance récolte et la diversification l'amortissent.",
    ),
    Question(
        "agro_part_transformation",
        "Quelle part de votre CA vient de produits transformés (à plus forte "
        "valeur) ?",
        "metier", "percent", ALL_PROFILES, sectors=("agro",),
        unit="%", short="Part produits transformés", placeholder="25",
        min=0, max=100,
        help="Transformer (conserves, jus, fromages) capte de la valeur "
             "ajoutée et lisse la saisonnalité de la vente du brut.",
    ),
    Question(
        "agro_label_qualite",
        "Bénéficiez-vous d'un label ou signe de qualité (bio, AOP, Label "
        "Rouge…) ?",
        "metier", "scale", ALL_PROFILES, sectors=("agro",),
        short="Label de qualité",
        scale_labels=("Aucun", "Label valorisé"),
        help="Un label justifie un prix premium et différencie sur un marché "
             "où le produit brut est souvent une commodité.",
    ),
    Question(
        "agro_dependance_distributeur",
        "Quelle part de vos volumes part chez un seul distributeur / "
        "acheteur ?",
        "metier", "percent", P_STRUCT, sectors=("agro",),
        unit="%", short="Dépendance distributeur", placeholder="50",
        min=0, max=100,
        help="Dépendre d'un acheteur dominant (GMS) expose à une pression "
             "permanente sur les prix et à un risque de déréférencement.",
    ),

    # ── NUMÉRIQUE / TECH / STUDIO ────────────────────────────────────
    Question(
        "num_part_recurrent_saas",
        "Quelle part de votre CA est récurrente (abonnements, SaaS, "
        "maintenance) ?",
        "metier", "percent", ALL_PROFILES, sectors=("numerique",),
        unit="%", short="CA récurrent", placeholder="40", min=0, max=100,
        help="Le récurrent est ce qui valorise une entreprise tech : "
             "prévisible, il vaut bien plus qu'un CA de prestation au coup par "
             "coup.",
    ),
    Question(
        "num_part_regie",
        "Quelle part de votre CA est en régie / facturée au temps passé ?",
        "metier", "percent", ALL_PROFILES, sectors=("numerique",),
        unit="%", short="Part en régie", placeholder="30", min=0, max=100,
        help="La régie sécurise la marge mais plafonne la valeur (vente de "
             "temps) ; le produit/forfait scale mais porte le risque.",
    ),
    Question(
        "num_cout_acquisition",
        "Combien coûte l'acquisition d'un nouveau client / utilisateur "
        "payant ?",
        "metier", "currency", ALL_PROFILES, sectors=("numerique",),
        unit="€", short="Coût d'acquisition", placeholder="120", min=0,
        help="À rapprocher de la valeur vie client (LTV). Un ratio LTV/CAC "
             "inférieur à 3 fragilise un modèle d'abonnement.",
    ),
    Question(
        "num_dependance_plateforme",
        "Dépendez-vous d'une plateforme tierce (store, API, place de "
        "marché) pour distribuer ?",
        "metier", "scale", ALL_PROFILES, sectors=("numerique",),
        short="Dépendance plateforme",
        scale_labels=("Indépendant", "Très dépendant"),
        help="Un changement de règles ou de commission d'une plateforme peut "
             "balayer la rentabilité du jour au lendemain.",
    ),
    Question(
        "num_churn",
        "Quelle part de vos clients abonnés résilie chaque année ?",
        "metier", "percent", P_ETABLI, sectors=("numerique",),
        unit="%", short="Taux de churn", placeholder="10", min=0, max=100,
        help="Le churn est le poison du SaaS : au-delà d'un certain seuil, "
             "vous remplissez un seau percé quoi que vous acquériez.",
    ),
    Question(
        "num_dette_technique",
        "Votre produit / base de code accumule-t-il de la dette technique ?",
        "metier", "scale", P_STRUCT, sectors=("numerique",),
        short="Dette technique",
        scale_labels=("Maîtrisée", "Préoccupante"),
        help="La dette technique ralentit les évolutions et fait grimper les "
             "coûts de maintenance : un risque souvent invisible au bilan.",
    ),

    # ── ASSOCIATION / ESS ────────────────────────────────────────────
    Question(
        "asso_part_cotisations",
        "Quelle part de vos ressources vient des cotisations / dons (vs "
        "subventions) ?",
        "metier", "percent", ALL_PROFILES, sectors=("association",),
        unit="%", short="Part cotisations / dons", placeholder="30",
        min=0, max=100,
        help="Les ressources propres (cotisations, dons) donnent de "
             "l'autonomie face au désengagement possible des financeurs.",
    ),
    Question(
        "asso_nb_adherents",
        "Combien d'adhérents ou de bénéficiaires comptez-vous ?",
        "metier", "number", ALL_PROFILES, sectors=("association",),
        unit="personnes", short="Adhérents / bénéficiaires", placeholder="250",
        min=0,
        help="La base de membres mesure l'utilité sociale et le poids dans "
             "les négociations de financement.",
    ),
    Question(
        "asso_dependance_benevoles",
        "L'activité dépend-elle fortement du bénévolat ?",
        "metier", "scale", ALL_PROFILES, sectors=("association",),
        short="Dépendance au bénévolat",
        scale_labels=("Faible", "Structurelle"),
        help="Le bénévolat est une force mais un risque de continuité : son "
             "essoufflement peut paralyser l'activité du jour au lendemain.",
    ),
    Question(
        "asso_part_autofinancement",
        "Quelle part de votre budget est autofinancée (activités propres, "
        "prestations) ?",
        "metier", "percent", ALL_PROFILES, sectors=("association",),
        unit="%", short="Taux d'autofinancement", placeholder="35",
        min=0, max=100,
        help="L'autofinancement est le gage de pérennité d'une structure de "
             "l'ESS : il réduit la vulnérabilité aux décisions publiques.",
    ),
    Question(
        "asso_renouvellement_subventions",
        "Vos financements publics sont-ils sécurisés sur plusieurs années ?",
        "metier", "scale", P_ETABLI, sectors=("association",),
        short="Sécurité des financements",
        scale_labels=("Annuels / incertains", "Pluriannuels"),
        help="Des conventions pluriannuelles donnent de la visibilité ; des "
             "subventions reconduites au coup par coup fragilisent le projet.",
    ),
    Question(
        "asso_masse_salariale_pct",
        "Quelle part de votre budget part en masse salariale ?",
        "metier", "percent", P_STRUCT, sectors=("association",),
        unit="%", short="Poids de la masse salariale", placeholder="60",
        min=0, max=100,
        help="Une masse salariale élevée rend la structure rigide : en cas de "
             "baisse de subvention, l'ajustement est lent et douloureux.",
    ),

    # ── AUTRE ACTIVITÉ ───────────────────────────────────────────────
    Question(
        "autre_modele_revenu",
        "Comment générez-vous principalement votre revenu ?",
        "metier", "choice", ALL_PROFILES, sectors=("autre",),
        short="Modèle de revenu",
        choices=(
            ("produits", "Vente de produits"),
            ("service", "Prestation de service"),
            ("abonnement", "Abonnement / récurrent"),
            ("commission", "Commission / intermédiation"),
            ("mixte", "Modèle mixte"),
        ),
        help="Le modèle de revenu détermine les leviers de marge et de "
             "croissance les plus pertinents pour votre activité.",
    ),
    Question(
        "autre_concentration_offre",
        "Une seule offre concentre-t-elle l'essentiel de votre CA ?",
        "metier", "scale", ALL_PROFILES, sectors=("autre",),
        short="Concentration de l'offre",
        scale_labels=("Offre diversifiée", "Tout sur une offre"),
        help="La mono-offre simplifie la gestion mais expose à tout "
             "retournement de marché ou d'usage.",
    ),
    Question(
        "autre_canal_principal",
        "Quel est votre principal canal d'acquisition de clients ?",
        "metier", "choice", ALL_PROFILES, sectors=("autre",),
        short="Canal d'acquisition principal",
        choices=(
            ("bao", "Bouche-à-oreille"),
            ("ligne", "En ligne (site, réseaux, pub)"),
            ("prospection", "Prospection directe"),
            ("prescripteurs", "Prescripteurs / partenaires"),
            ("physique", "Point de vente physique"),
        ),
        help="Connaître son canal dominant — et sa fragilité — est la base "
             "d'une stratégie d'acquisition maîtrisée.",
    ),
    Question(
        "autre_differenciation",
        "Vous différenciez-vous clairement de vos concurrents ?",
        "metier", "scale", ALL_PROFILES, sectors=("autre",),
        short="Différenciation",
        scale_labels=("Peu différencié", "Très différencié"),
        help="Sans différenciation claire, la concurrence se joue sur le prix "
             "— le terrain le plus destructeur de marge.",
    ),
    Question(
        "autre_part_nouveaux_clients",
        "Quelle part de votre CA vient de nouveaux clients chaque année ?",
        "metier", "percent", P_ETABLI, sectors=("autre",),
        unit="%", short="Part nouveaux clients", placeholder="30",
        min=0, max=100,
        help="L'équilibre entre conquête et fidélisation : trop de "
             "renouvellement signale un problème de rétention coûteux.",
    ),

    # ═════════════════════════════════════════════════════════════════
    #  RÉALITÉS TERRITORIALES — ANTILLES-GUYANE / OUTRE-MER
    #  Une question par secteur, ancrée dans le marché réel de TUS :
    #  fret & dépendance aux importations, octroi de mer, insularité,
    #  saison cyclonique, étroitesse du marché local, dispositifs DOM.
    #  (Bloc métier, hors score /100.)
    # ═════════════════════════════════════════════════════════════════
    Question(
        "com_dom_import",
        "Quelle part de vos marchandises est importée (hexagone, étranger) "
        "et soumise au fret et à l'octroi de mer ?",
        "metier", "percent", ALL_PROFILES, sectors=("commerce",),
        unit="%", short="Marchandises importées", placeholder="70",
        min=0, max=100,
        help="Outre-mer, les délais de fret imposent des stocks tampons et "
             "l'octroi de mer alourdit le prix de revient : un double impact "
             "sur la trésorerie et la marge.",
    ),
    Question(
        "eco_dom_logistique",
        "L'éloignement pénalise-t-il vos livraisons (surcoût de fret, délais, "
        "retours) ?",
        "metier", "scale", ALL_PROFILES, sectors=("ecommerce",),
        short="Contrainte logistique territoriale",
        scale_labels=("Peu pénalisant", "Très pénalisant"),
        help="Vendre depuis ou vers l'outre-mer renchérit le port et allonge "
             "les délais : un frein à la conversion et au réachat à anticiper.",
    ),
    Question(
        "rest_dom_appro",
        "Quelle part de vos denrées dépend d'imports soumis aux aléas de fret "
        "(ruptures, délais) ?",
        "metier", "percent", ALL_PROFILES, sectors=("restauration",),
        unit="%", short="Approvisionnement importé", placeholder="50",
        min=0, max=100,
        help="Une carte qui repose sur des produits importés s'expose aux "
             "ruptures et à la volatilité des prix. Le local sécurise l'appro "
             "et l'argument commercial.",
    ),
    Question(
        "hot_dom_clientele",
        "Quelle part de votre clientèle vient de l'hexagone / l'international "
        "(vs clientèle locale) ?",
        "metier", "percent", ALL_PROFILES, sectors=("hotellerie",),
        unit="%", short="Clientèle hors territoire", placeholder="60",
        min=0, max=100,
        help="Une forte dépendance à la clientèle extérieure lie votre "
             "remplissage à la desserte aérienne et à la saison touristique : "
             "un risque à amortir par la clientèle locale et affaires.",
    ),
    Question(
        "tou_dom_desserte",
        "Votre fréquentation dépend-elle de la desserte aérienne ou des "
        "escales de croisière ?",
        "metier", "scale", ALL_PROFILES, sectors=("tourisme",),
        short="Dépendance à la desserte",
        scale_labels=("Indépendante", "Très dépendante"),
        help="Une grève, une réduction de lignes ou une annulation d'escale "
             "peut effondrer la fréquentation : un risque structurel en "
             "territoire insulaire.",
    ),
    Question(
        "spro_dom_marche",
        "Votre marché est-il limité à votre territoire (département / île) ?",
        "metier", "scale", ALL_PROFILES, sectors=("services_pro",),
        short="Étroitesse du marché local",
        scale_labels=("Marché élargi", "Marché très local"),
        help="Un marché étroit plafonne la croissance et accentue la "
             "dépendance à quelques donneurs d'ordre : le développement hors "
             "territoire devient un relais clé.",
    ),
    Question(
        "spart_dom_pouvoir_achat",
        "Vos tarifs sont-ils contraints par le pouvoir d'achat local ?",
        "metier", "scale", ALL_PROFILES, sectors=("services_part",),
        short="Contrainte de pouvoir d'achat",
        scale_labels=("Peu contraints", "Très contraints"),
        help="La vie chère pèse sur la solvabilité des ménages : un "
             "positionnement prix mal calibré fait fuir une clientèle déjà "
             "sous tension.",
    ),
    Question(
        "cons_dom_concentration",
        "Votre clientèle est-elle concentrée sur le territoire local ?",
        "metier", "scale", ALL_PROFILES, sectors=("conseil",),
        short="Concentration territoriale",
        scale_labels=("Diversifiée", "Très locale"),
        help="Sur un marché restreint, la réputation circule vite mais le "
             "vivier de clients est limité : la prestation à distance ouvre un "
             "relais de croissance.",
    ),
    Question(
        "sante_dom_appro",
        "Subissez-vous des difficultés d'approvisionnement en consommables / "
        "équipements importés ?",
        "metier", "scale", ALL_PROFILES, sectors=("sante",),
        short="Approvisionnement médical",
        scale_labels=("Rarement", "Fréquemment"),
        help="L'éloignement allonge les délais de réassort et de maintenance "
             "du matériel : un stock de sécurité et des fournisseurs de "
             "secours évitent l'arrêt d'activité.",
    ),
    Question(
        "beau_dom_produits",
        "Vos produits de revente subissent-ils ruptures de gamme ou délais "
        "liés à l'import ?",
        "metier", "scale", ALL_PROFILES, sectors=("beaute",),
        short="Disponibilité des produits",
        scale_labels=("Rarement", "Fréquemment"),
        help="Une rupture sur un produit phare, c'est de la marge de revente "
             "perdue et un client déçu : anticiper les commandes est vital "
             "outre-mer.",
    ),
    Question(
        "art_dom_matiere",
        "Vos matières premières dépendent-elles d'imports soumis au fret et à "
        "l'octroi de mer ?",
        "metier", "scale", ALL_PROFILES, sectors=("artisanat",),
        short="Dépendance matières importées",
        scale_labels=("Faible", "Forte"),
        help="Le coût et le délai d'acheminement des matières pèsent sur le "
             "prix et la planification : les sourcer localement, quand c'est "
             "possible, est un avantage.",
    ),
    Question(
        "btp_dom_materiaux",
        "Quelle part de vos matériaux est importée et soumise aux délais de "
        "fret / à l'octroi de mer ?",
        "metier", "percent", ALL_PROFILES, sectors=("btp",),
        unit="%", short="Matériaux importés", placeholder="60",
        min=0, max=100,
        help="L'import des matériaux allonge les délais de chantier et "
             "renchérit les devis. Sans clause de révision, une flambée se "
             "paie sur la marge.",
    ),
    Question(
        "ind_dom_intrants",
        "Quelle part de vos intrants est importée et soumise à l'octroi de "
        "mer / au fret ?",
        "metier", "percent", ALL_PROFILES, sectors=("industrie",),
        unit="%", short="Intrants importés", placeholder="55",
        min=0, max=100,
        help="La dépendance aux intrants importés expose aux ruptures et à "
             "l'octroi de mer ; produire pour le marché inter-îles peut "
             "diversifier les débouchés.",
    ),
    Question(
        "tra_dom_inter_iles",
        "Votre activité dépend-elle du transport inter-îles ou de "
        "l'acheminement portuaire / aéroportuaire ?",
        "metier", "scale", ALL_PROFILES, sectors=("transport",),
        short="Dépendance portuaire / inter-îles",
        scale_labels=("Faible", "Forte"),
        help="Les ruptures de charge (port, aéroport, liaisons maritimes) "
             "ajoutent des délais et des coûts incompressibles propres à "
             "l'insularité.",
    ),
    Question(
        "immo_dom_defisc",
        "Quelle part de votre activité repose sur la défiscalisation outre-mer "
        "(Girardin, Pinel DOM) ?",
        "metier", "percent", ALL_PROFILES, sectors=("immobilier",),
        unit="%", short="Part défiscalisation DOM", placeholder="30",
        min=0, max=100,
        help="Les dispositifs de défiscalisation portent une part du marché "
             "ultramarin : une dépendance forte expose aux changements de "
             "réglementation fiscale.",
    ),
    Question(
        "for_dom_financement",
        "Vos financements dépendent-ils de dispositifs régionaux / européens "
        "(FSE, Région) spécifiques ?",
        "metier", "scale", ALL_PROFILES, sectors=("formation",),
        short="Dépendance aux dispositifs",
        scale_labels=("Faible", "Structurelle"),
        help="Les fonds régionaux et européens irriguent la formation "
             "outre-mer : leur calendrier et leurs critères conditionnent "
             "directement votre activité.",
    ),
    Question(
        "eve_dom_prestataires",
        "La disponibilité limitée de prestataires / matériel en local "
        "bride-t-elle vos projets ?",
        "metier", "scale", ALL_PROFILES, sectors=("evenementiel",),
        short="Ressources locales limitées",
        scale_labels=("Peu", "Fortement"),
        help="Un vivier restreint de prestataires et de matériel oblige à "
             "anticiper ou à faire venir des moyens, avec un surcoût logistique "
             "à intégrer au devis.",
    ),
    Question(
        "agro_dom_aides",
        "Quelle part de vos ressources dépend des aides agricoles spécifiques "
        "outre-mer (POSEI, FEADER) ?",
        "metier", "percent", ALL_PROFILES, sectors=("agro",),
        unit="%", short="Aides agricoles DOM", placeholder="35",
        min=0, max=100,
        help="Les aides spécifiques soutiennent la filière ultramarine mais "
             "fragilisent le modèle si elles évoluent : à équilibrer avec des "
             "ressources propres.",
    ),
    Question(
        "num_dom_export",
        "Quelle part de votre CA est réalisée hors de votre territoire "
        "(hexagone, international) ?",
        "metier", "percent", ALL_PROFILES, sectors=("numerique",),
        unit="%", short="CA hors territoire", placeholder="40",
        min=0, max=100,
        help="Le numérique permet de dépasser l'étroitesse du marché local : "
             "vendre hors territoire est souvent la clé d'une croissance "
             "soutenue.",
    ),
    Question(
        "asso_dom_dispositifs",
        "Vos financements dépendent-ils de dispositifs spécifiques (politique "
        "de la ville, FSE, contrats aidés) ?",
        "metier", "scale", ALL_PROFILES, sectors=("association",),
        short="Dépendance aux dispositifs publics",
        scale_labels=("Faible", "Structurelle"),
        help="Les dispositifs publics et les contrats aidés portent beaucoup "
             "de structures ultramarines : leur révision peut déséquilibrer "
             "brutalement le budget.",
    ),
    Question(
        "autre_dom_contraintes",
        "Votre activité est-elle exposée aux contraintes du territoire "
        "(fret / import, octroi de mer, saison cyclonique) ?",
        "metier", "scale", ALL_PROFILES, sectors=("autre",),
        short="Exposition territoriale",
        scale_labels=("Faible", "Forte"),
        help="Identifier l'exposition aux réalités ultramarines (logistique, "
             "fiscalité locale, climat) est le point de départ d'une stratégie "
             "de résilience adaptée.",
    ),
)


# ── Accès filtré par profil + secteur ────────────────────────────────
def _matches(q: Question, profile: str, sector: str | None) -> bool:
    """Vrai si la question s'applique au profil ET au secteur donnés.

    Une question sans ``sectors`` est universelle. Une question ciblée n'est
    retenue que si le secteur courant figure dans sa liste. Quand aucun
    secteur n'est renseigné, on n'affiche que les questions universelles.

    Une question explicitement exclue d'un secteur (``exclude_sectors``) n'y
    est jamais posée, même si elle est universelle : cela évite d'interroger
    un métier sur des notions qui n'ont pas de sens pour lui (par ex. les
    approvisionnements d'une entreprise de services à la personne).
    """
    if profile not in q.profiles:
        return False
    if sector and sector in q.exclude_sectors:
        return False
    if not q.sectors:
        return True
    return bool(sector) and sector in q.sectors


def questions_for_profile(profile: str, sector: str | None = None) -> list[Question]:
    """Retourne les questions applicables à un profil (et secteur), dans
    l'ordre du catalogue (donc regroupables par domaine)."""
    if profile not in PROFILES:
        profile = "pme"
    return [q for q in QUESTIONS if _matches(q, profile, sector)]


def sections_for_profile(profile: str, sector: str | None = None) -> list[dict[str, Any]]:
    """Regroupe les questions d'un profil/secteur par domaine, dans l'ordre
    des DOMAINS. Prêt à itérer dans le template du formulaire.

    Le bloc métier (``metier``) prend le titre et l'icône du secteur choisi
    (cf. SECTOR_BLOCKS) afin que la structure du questionnaire varie
    visiblement d'un secteur à l'autre.
    """
    qs = questions_for_profile(profile, sector)
    sections: list[dict[str, Any]] = []
    for key, domain in DOMAINS.items():
        domain_questions = [q for q in qs if q.domain == key]
        if not domain_questions:
            continue
        if key == "metier" and sector in SECTOR_BLOCKS:
            icon, label = SECTOR_BLOCKS[sector]
            domain = Domain(
                "metier", label, icon,
                "Indicateurs propres au métier et au secteur de l'entreprise.",
            )
        sections.append({
            "domain": domain,
            "questions": domain_questions,
        })
    return sections


def question_by_id(qid: str) -> Question | None:
    for q in QUESTIONS:
        if q.id == qid:
            return q
    return None
