"""Contenu stratégique par outil pour le rapport PDF.

Chaque entrée fournit (a) ce que l'outil mesure, (b) 3 questions
stratégiques à se poser après le diagnostic, (c) 5 prochaines étapes
concrètes, (d) un cadre d'analyse. Utilisé par le PDF pour livrer
un rapport substantiel même si le simulateur n'expose pas de snapshot.
"""
from __future__ import annotations


_DEFAULT = {
    'category': 'Diagnostic stratégique',
    'measures': (
        "Cet outil éclaire une zone précise de votre modèle économique. "
        "Les chiffres que vous avez saisis ne sont pas un verdict, "
        "mais une carte : ils révèlent où se trouve le levier qui fera "
        "bouger les lignes le plus vite."
    ),
    'questions': [
        "Quelle est la variable que je pourrais faire bouger de 10% "
        "sans bouleverser mon organisation ?",
        "Sur quel poste mes hypothèses sont-elles les moins certaines — "
        "et où ai-je le plus à perdre si je me trompe ?",
        "Qu'est-ce qui, dans mon quotidien, m'empêche d'activer ce levier "
        "dès aujourd'hui ?",
    ],
    'next_steps': [
        "Notez les 2 chiffres qui vous ont le plus surpris dans la simulation.",
        "Identifiez la personne de votre équipe (ou votre réseau) qui peut "
        "vous aider à affiner l'hypothèse la plus fragile.",
        "Testez un scénario à 30 jours : quelle action, avec quel résultat mesurable ?",
        "Fixez-vous une date pour relire ce rapport — l'écart entre les "
        "hypothèses et le réel est souvent la meilleure école.",
        "Si le diagnostic révèle un angle mort, provoquez une conversation "
        "structurée (coach, mentor, pair, expert) avant de décider.",
    ],
    'framework': (
        "Un bon diagnostic n'est pas celui qui donne toutes les réponses, "
        "mais celui qui pose les bonnes questions au bon moment. "
        "Le vôtre vient de démarrer."
    ),
}


TOOL_CONTENT = {
    # ── 10 outils existants ──────────────────────────────────
    'point-mort': {
        'category': 'Rentabilité',
        'measures': (
            "Le seuil de rentabilité est le point où vos revenus couvrent "
            "vos charges fixes. En dessous, chaque jour travaillé coûte. "
            "Au-dessus, chaque vente contribue à votre marge et à votre "
            "capacité à investir."
        ),
        'questions': [
            "Combien de jours par mois faut-il travailler pour atteindre ce seuil ?",
            "Quelle charge fixe pourrait passer en variable pour réduire ma zone rouge ?",
            "Ma marge unitaire me laisse-t-elle de la respiration, ou je survis ?",
        ],
        'next_steps': [
            "Listez chaque charge fixe mensuelle — même les petites.",
            "Identifiez 1 charge que vous pourriez renégocier ou remplacer.",
            "Calculez combien de ventes il faut pour absorber chaque charge.",
            "Fixez un objectif mensuel visible (tableau, agenda, équipe).",
            "Revoyez ce seuil chaque trimestre : il bouge avec votre structure.",
        ],
        'framework': "Point mort = charges fixes / taux de marge. Votre seuil est un rendez-vous, pas une finalité.",
    },
    'cac': {
        'category': 'Acquisition',
        'measures': (
            "Le coût d'acquisition client (CAC) mesure combien vous investissez "
            "pour gagner un nouveau client. Couplé à la valeur vie client (LTV), "
            "il détermine la santé durable de votre modèle."
        ),
        'questions': [
            "Combien de temps mettent mes clients à me rembourser leur propre acquisition ?",
            "Mon canal principal est-il scalable, ou dépend-il d'un goulot (moi, un employé, un algorithme) ?",
            "Si je double mon budget d'acquisition demain, qu'est-ce qui casse en premier ?",
        ],
        'next_steps': [
            "Calculez votre LTV moyenne sur 12 mois (panier × fréquence × durée).",
            "Mesurez votre ratio LTV/CAC — objectif sain : ≥ 3.",
            "Identifiez le canal au CAC le plus bas ET le plus stable.",
            "Documentez le parcours type depuis le premier contact jusqu'à la facturation.",
            "Testez une action de réduction du CAC (référencement organique, bouche-à-oreille structuré, contenu).",
        ],
        'framework': "Un CAC n'est pas un coût, c'est un investissement. Juge-le sur sa durée d'amortissement.",
    },
    'friction': {
        'category': 'Opérations',
        'measures': (
            "La friction opérationnelle est le temps, l'énergie et l'argent "
            "perdus dans les étapes invisibles : relances, ressaisies, doubles "
            "validations, outils mal connectés. Elle ne tue jamais d'un seul coup, "
            "elle ronge."
        ),
        'questions': [
            "Quelle tâche répétitive m'agace le plus chaque semaine — et pourquoi existe-t-elle encore ?",
            "Quel outil que j'utilise me fait perdre plus de temps qu'il n'en fait gagner ?",
            "Si un nouveau collaborateur arrivait demain, combien d'heures faudrait-il pour le former à cette friction ?",
        ],
        'next_steps': [
            "Listez les 5 tâches qui reviennent chaque semaine — notez leur durée.",
            "Pour chacune, demandez-vous : automatiser / déléguer / supprimer ?",
            "Identifiez le 'talon d'Achille' de votre workflow (le point où tout bloque si X est absent).",
            "Documentez 1 processus par écrit cette semaine — même imparfait.",
            "Mesurez le gain après 30 jours : heures, erreurs, stress.",
        ],
        'framework': "La friction invisible coûte toujours plus que l'outil pour la supprimer.",
    },
    'fragmentation': {
        'category': 'Concentration',
        'measures': (
            "L'indice de fragmentation révèle la dépendance de votre chiffre "
            "d'affaires à un petit nombre de clients. Un indice trop concentré "
            "est une fragilité ; un indice trop dispersé peut signaler un manque "
            "d'ancrage stratégique."
        ),
        'questions': [
            "Que se passe-t-il si mon plus gros client disparaît demain ?",
            "Est-ce que je veux diversifier ou approfondir la relation avec mes meilleurs clients ?",
            "Mes 20% de clients représentent-ils 80% de ma charge mentale — ou de ma marge ?",
        ],
        'next_steps': [
            "Classez vos clients par CA, puis par marge. Comparez les deux tops 5.",
            "Identifiez les clients 'énergivores mais peu rentables' : que faire ?",
            "Construisez une stratégie de référencement auprès de vos meilleurs clients.",
            "Fixez-vous une règle : aucun client > X % du CA d'ici 12 mois.",
            "Testez 1 segment nouveau — un prospect idéal, pas un prospect facile.",
        ],
        'framework': "Concentration = levier OU risque. Le distinguer, c'est la moitié du travail.",
    },
    'acse': {
        'category': 'Flux commercial',
        'measures': (
            "Le flux A.C.S.E (Attirer · Convertir · Servir · Étendre) est le "
            "pipeline vivant de toute activité de service. Le maillon le plus "
            "faible détermine le rythme global : inutile de sur-investir "
            "à un endroit si un autre étouffe le flux."
        ),
        'questions': [
            "Quel est mon maillon le plus faible aujourd'hui — et depuis combien de temps ?",
            "Est-ce que j'essaie de réparer l'aval alors que c'est l'amont qui coince ?",
            "Qu'est-ce qui m'empêche, concrètement, de travailler sur ce maillon cette semaine ?",
        ],
        'next_steps': [
            "Mesurez chaque maillon avec une métrique unique (leads/mois, taux de closing, NPS, panier moyen).",
            "Passez 1 heure cette semaine sur le maillon faible — pas plus, mais focus.",
            "Interrogez 3 clients existants sur leur expérience à chaque étape.",
            "Testez 1 hypothèse concrète (nouvelle offre, nouveau canal, nouveau rituel).",
            "Rendez-vous dans 30 jours pour refaire ce diagnostic et comparer.",
        ],
        'framework': "Le flux avance à la vitesse du maillon le plus faible. Tout le reste est du bruit.",
    },
    'plafond': {
        'category': 'Scalabilité',
        'measures': (
            "Le plafond de croissance est la limite au-delà de laquelle votre "
            "modèle actuel ne peut plus absorber de charge sans se transformer : "
            "passer de solo à équipe, de mission à produit, de service à système."
        ),
        'questions': [
            "Qu'est-ce qui, dans mon modèle actuel, est impossible à scaler ?",
            "Suis-je prêt·e à lâcher ma délivrance pour un rôle de pilotage ?",
            "Quel est le premier recrutement / outil / système qui débloque le palier suivant ?",
        ],
        'next_steps': [
            "Identifiez ce que vous êtes le ou la seul·e à pouvoir faire.",
            "Chronométrez une semaine-type : où passe votre temps ?",
            "Listez 3 tâches que vous pourriez déléguer / outiller cette année.",
            "Préparez un organigramme 'idéal' à 24 mois — même sur un post-it.",
            "Testez 1 délégation cette semaine — même petite, pour expérimenter.",
        ],
        'framework': "Le plafond, c'est souvent votre propre rôle. Le briser, c'est accepter d'en changer.",
    },
    'elasticite': {
        'category': 'Pricing',
        'measures': (
            "L'élasticité-prix mesure la sensibilité de votre demande aux "
            "variations de prix. Un marché rigide autorise des hausses ; "
            "un marché élastique impose de la valeur et de la différenciation."
        ),
        'questions': [
            "Depuis quand mes prix n'ont-ils pas bougé — et pourquoi ?",
            "Qu'est-ce que mes clients achètent vraiment : mon service, ou ma relation ?",
            "Suis-je prêt·e à perdre 10% de clients pour gagner 20% de marge ?",
        ],
        'next_steps': [
            "Testez une hausse de 5-10% sur les nouveaux clients uniquement.",
            "Observez le taux de conversion avant/après — 30 jours suffisent souvent.",
            "Articulez clairement ce qui justifie votre prix (résultat, rareté, expertise).",
            "Identifiez 3 concurrents indirects et leur positionnement prix.",
            "Préparez un plan de revalorisation annuelle (indexation, palier, prime).",
        ],
        'framework': "Ne baissez jamais un prix sans changer la promesse. Sinon, vous dévaluez le reste.",
    },
    'vallee-mort': {
        'category': 'Trésorerie',
        'measures': (
            "La 'vallée de la mort' est la période où vos charges ont augmenté "
            "mais les recettes ne suivent pas encore : recrutement, nouveau marché, "
            "investissement. C'est là que la trésorerie décide du destin."
        ),
        'questions': [
            "Combien de mois de trésorerie me restent-ils en mode dégradé (sans nouveau client) ?",
            "Mon BFR (besoin en fonds de roulement) est-il stable ou en dérive ?",
            "Qui préviens-je si la trajectoire devient critique — banquier, associé, famille ?",
        ],
        'next_steps': [
            "Construisez une trésorerie glissante à 13 semaines.",
            "Identifiez les 3 plus grosses sorties non essentielles.",
            "Négociez des délais fournisseurs si nécessaire — avant d'en avoir besoin.",
            "Renforcez vos acomptes : 30% à la commande, 30% à mi-parcours, 40% à la livraison.",
            "Préparez un 'plan B' écrit en une page : que faire si le pire arrive ?",
        ],
        'framework': "La trésorerie tue avant la rentabilité. Surveillez les flux, pas seulement les soldes.",
    },
    'retention': {
        'category': 'Fidélisation',
        'measures': (
            "La rétention mesure votre capacité à garder les clients que vous "
            "avez coûté si cher à acquérir. Un point de rétention vaut souvent "
            "10 points d'acquisition en marge nette."
        ),
        'questions': [
            "À quel moment mes clients me quittent-ils — et que se passe-t-il juste avant ?",
            "Quel geste simple doublerait ma rétention sans coûter plus cher ?",
            "Ai-je un rituel de suivi structuré, ou je laisse la relation au hasard ?",
        ],
        'next_steps': [
            "Interrogez 5 clients perdus : qu'est-ce qui les a fait partir ?",
            "Identifiez 'le moment de vérité' dans votre parcours — et renforcez-le.",
            "Mettez en place un contact structuré à J+30, J+90, J+180 après signature.",
            "Proposez 1 nouvelle valeur aux clients existants avant les nouveaux.",
            "Mesurez le NPS chaque trimestre — et agissez sur les réponses.",
        ],
        'framework': "Acquérir coûte, retenir multiplie. Les deux ne s'opposent pas, ils se renforcent.",
    },
    # ── 20 autres outils (contenu générique enrichi) ─────────
    'mix-produits': {'category': 'Portefeuille', 'measures': "Le mix produits révèle quels produits portent vraiment votre marge, lesquels épuisent votre énergie, et lesquels ont un potentiel sous-exploité.", 'questions': ["Quels produits me rapportent le plus en marge (pas en CA) ?", "Quel produit est 'un boulet émotionnel' — coûteux à délivrer, peu aimé, mais trop lié à mon identité ?", "Quel produit mériterait 10x plus d'attention commerciale ?"], 'next_steps': ["Classez chaque produit par marge absolue et par marge %.", "Identifiez le produit à retirer (ou à repositionner).", "Définissez un produit 'tête de gondole' qui raconte votre expertise.", "Testez un bundle ou une offre mensuelle pour stabiliser la récurrence.", "Révisez votre mix tous les 6 mois."], 'framework': "Le bon mix n'est pas le plus large, c'est le plus cohérent avec votre promesse."},
    'atterrissage': {'category': 'Onboarding', 'measures': "L'atterrissage client est le moment entre la signature et la première valeur perçue. C'est là que se joue la rétention à 12 mois, souvent sans qu'on le sache.", 'questions': ["Combien de temps met un nouveau client à ressentir sa première victoire ?", "Qu'est-ce que je fais le jour 1, semaine 1, mois 1 — et est-ce intentionnel ou improvisé ?", "Mon onboarding est-il un événement humain ou un tunnel automatisé ?"], 'next_steps': ["Cartographiez les 90 premiers jours d'un client type.", "Identifiez 3 moments clés à ritualiser (call J+7, livrable J+30, bilan J+90).", "Créez 1 document d'accueil qui donne de la clarté dès la signature.", "Mesurez la 'time to first value' — objectif : la réduire de 20%.", "Interrogez vos 3 derniers clients : qu'est-ce qui a manqué ?"], 'framework': "Un bon atterrissage vaut 3 relances. Investissez-y disproportionnellement."},
    'tresorerie': {'category': 'Trésorerie', 'measures': "La trésorerie est l'oxygène de votre entreprise. Elle dit la vérité, même quand les tableaux de rentabilité mentent.", 'questions': ["Combien de mois puis-je tenir sans revenus nouveaux ?", "Où se cachent mes BFR — stocks, clients en retard, avances fournisseurs ?", "Suis-je prêt·e pour un 'stress test' de 3 mois sans nouveau contrat ?"], 'next_steps': ["Construisez une trésorerie 13 semaines.", "Réduisez votre délai de paiement client moyen.", "Négociez des délais fournisseurs avant d'en avoir besoin.", "Séparez trésorerie opérationnelle et trésorerie stratégique (2 comptes).", "Alimentez un fond de réserve chaque mois, même petit."], 'framework': "La trésorerie n'est pas une conséquence, c'est une discipline."},
    'jumeaux-clients': {'category': 'Segmentation', 'measures': "Les 'jumeaux clients' sont les archétypes qui reviennent chez vous. Les identifier permet de dupliquer les meilleurs et d'éviter les pièges récurrents.", 'questions': ["Qui sont mes 3 meilleurs clients jamais — et qu'ont-ils en commun ?", "Quel profil m'épuise systématiquement — et pourquoi je continue à les accepter ?", "Si je devais cloner 10 clients, lesquels choisirais-je ?"], 'next_steps': ["Listez vos 10 derniers clients. Notez leur NPS, leur marge, leur charge émotionnelle.", "Identifiez 2 archétypes : 'idéal' et 'à éviter'.", "Rédigez un 'persona' détaillé de votre client idéal.", "Ajustez votre prospection pour attirer ce profil en priorité.", "Élégamment, refusez les profils 'à éviter' — et notez l'impact."], 'framework': "Vos meilleurs clients sont vos meilleurs commerciaux. Investissez dans leur duplication."},
    'correlation': {'category': 'Analyse', 'measures': "Les corrélations cachées (actions → résultats) sont souvent invisibles à l'œil nu. Les détecter, c'est arrêter de travailler dans le brouillard.", 'questions': ["Quelle action que je fais chaque mois donne-t-elle vraiment un résultat mesurable ?", "Quelle habitude 'héritée' n'a jamais été challengée ?", "Quel chiffre devrais-je suivre cette année que je ne suis pas aujourd'hui ?"], 'next_steps': ["Listez 5 actions récurrentes. Cherchez la corrélation avec votre CA.", "Abandonnez une action dont le retour n'est pas démontré.", "Mettez en place un suivi simple (tableau, app) sur 1 métrique clé.", "Revisitez vos décisions prises 'par instinct' il y a 12 mois.", "Construisez un dashboard mensuel de 5 chiffres max."], 'framework': "Ce qui est mesuré est amélioré. Ce qui n'est pas mesuré est souvent entretenu par habitude."},
    'delegation': {'category': 'Organisation', 'measures': "La capacité de délégation détermine si votre entreprise peut dépasser vos limites personnelles. Déléguer n'est pas se défausser : c'est construire un système.", 'questions': ["Quelles sont les 3 tâches que je fais et que quelqu'un d'autre pourrait mieux faire ?", "Qu'est-ce que je refuse de déléguer — et pourquoi (peur, perfectionnisme, fierté) ?", "Quel est le ROI d'une heure de mon temps sur ma tâche la plus stratégique ?"], 'next_steps': ["Listez vos tâches hebdo, notez celles à faible valeur ajoutée.", "Identifiez 1 tâche à déléguer ce trimestre — même imparfaitement.", "Documentez le processus avant de déléguer (vidéo Loom, checklist).", "Acceptez une baisse temporaire de qualité : c'est le prix de l'autonomie.", "Célébrez le premier succès d'autonomie — créez la culture."], 'framework': "Ne déléguez pas pour libérer du temps : déléguez pour acheter de la clarté stratégique."},
    'prix-psychologique': {'category': 'Pricing', 'measures': "Le prix psychologique est la zone où le marché se dit 'pas trop cher' et 'pas suspect'. Le trouver, c'est maximiser la conversion sans éroder la valeur.", 'questions': ["Quelle est la fourchette de prix où mes clients disent 'oui' sans réfléchir ?", "Quel prix dissuade des clients que je ne veux pas ?", "Est-ce que mon prix reflète la transformation que j'apporte, ou le temps que j'y passe ?"], 'next_steps': ["Testez 3 niveaux de prix sur 3 prospects sans engagement.", "Observez les objections : sont-elles sur le prix ou sur la valeur ?", "Construisez un argumentaire basé sur la transformation, pas sur la tâche.", "Proposez systématiquement 3 formules (eco, standard, premium).", "Révisez vos prix à chaque changement significatif de votre expertise."], 'framework': "Le bon prix n'est pas un compromis, c'est un alignement entre votre valeur et le langage du marché."},
    'dependance': {'category': 'Risque', 'measures': "La dépendance — à un client, un fournisseur, une plateforme, une personne — est le talon d'Achille de tout modèle. La cartographier, c'est la dompter.", 'questions': ["À qui ou à quoi mon activité ne peut-elle PAS survivre ?", "Quelle est la durée de vie de cette dépendance — 6 mois, 5 ans, indéfini ?", "Quelle serait la première étape pour la réduire sans la briser ?"], 'next_steps': ["Listez vos 5 dépendances majeures (client, fournisseur, algo, personne, outil).", "Notez leur criticité (1-10).", "Choisissez LA dépendance la plus risquée, et concevez un plan de réduction sur 18 mois.", "Identifiez un 'plan B' pour chaque dépendance critique.", "Revoyez cette carte chaque année."], 'framework': "La dépendance n'est pas le problème ; l'ignorance de celle-ci l'est."},
    'capacite': {'category': 'Opérations', 'measures': "La capacité de production — en heures, en têtes, en output — définit votre plafond physique. Au-delà, il faut industrialiser ou refuser.", 'questions': ["Quelle est ma capacité réelle (pas théorique) — en tenant compte des imprévus ?", "Quel goulot d'étranglement me coûte le plus aujourd'hui ?", "Suis-je prêt·e à refuser du travail pour ne pas casser mon système ?"], 'next_steps': ["Mesurez votre charge réelle sur 1 mois type (heures productives vs. administratif).", "Identifiez le goulot (vous-même, un outil, un fournisseur).", "Définissez un seuil d'alerte : au-delà de X charge, vous arrêtez de vendre.", "Créez une liste d'attente plutôt que de dégrader la qualité.", "Automatisez 1 tâche manuelle qui limite votre capacité."], 'framework': "La capacité n'est pas à maximiser : elle est à piloter. Trop tendue, elle casse."},
    'saisonnalite': {'category': 'Rythme', 'measures': "La saisonnalité révèle les hauts et les bas prévisibles. La subir, c'est fragile. La pilote, c'est stratégique.", 'questions': ["Quels sont mes 3 meilleurs et mes 3 pires mois — chaque année ?", "Comment j'utilise les périodes creuses : je les subis ou je les construis ?", "Puis-je lisser mes revenus via récurrence, pré-vente, abonnement ?"], 'next_steps': ["Cartographiez votre CA mensuel sur 24 mois.", "Identifiez les patterns (vacances, rentrée, fin d'année).", "Construisez une offre contra-cyclique (quand les autres dorment).", "Mettez en place un produit récurrent (abonnement, retainer).", "Budgétez l'année avec un lissage explicite — pas mois par mois."], 'framework': "La saisonnalité n'est pas une injustice, c'est une information. Utilisez-la."},
    'cout-promotion': {'category': 'Marketing', 'measures': "Le coût d'une promotion commerciale va bien au-delà du pourcentage affiché : ancrage bas-prix, cannibalisation, effet-référence, marge érodée.", 'questions': ["Quel a été le véritable ROI de ma dernière promo — au-delà du CA sur la période ?", "Mes clients attendent-ils désormais les soldes — et sabotent-ils le plein tarif ?", "Quelle alternative à la promo pour stimuler l'achat (bonus, urgence, exclusivité) ?"], 'next_steps': ["Analysez les 3 dernières promos : CA, marge, nouveaux clients, retours.", "Limitez la fréquence : 2 promos max par an.", "Privilégiez les bonus (gratuité additionnelle) aux remises.", "Créez de la rareté naturelle (capacité limitée, fenêtre courte).", "Documentez l'impact sur la perception de vos prix hors-promo."], 'framework': "Une promo est un outil puissant ET dangereux. Utilisée mal, elle forme un marché que vous ne voulez pas."},
    'valeur-sortie': {'category': 'Patrimoine', 'measures': "La valeur de sortie est le prix auquel votre entreprise se vendrait demain. Même si vous n'envisagez pas de vendre, c'est une boussole de création de valeur.", 'questions': ["Combien vaudrait mon entreprise si je partais demain en 6 mois ?", "Qu'est-ce qui est attaché à MA personne vs à l'entreprise elle-même ?", "Qu'est-ce qu'un repreneur trouverait 'prêt à l'emploi' — ou au contraire fragile ?"], 'next_steps': ["Documentez vos processus critiques (au moins les 5 plus importants).", "Créez un tableau de bord lisible par un tiers.", "Construisez des relations clients portées par l'entreprise, pas par vous.", "Réduisez votre 'key person risk' en formant un n°2.", "Faites évaluer votre boîte tous les 3 ans — même sans projet de vente."], 'framework': "Bâtir une entreprise vendable = bâtir une entreprise qui ne dépend plus de vous."},
    'effort-impact': {'category': 'Priorisation', 'measures': "La matrice effort/impact classe vos initiatives selon leur ratio énergie déployée / résultat espéré. Elle départage l'agitation de l'action.", 'questions': ["Quelles sont les 3 initiatives 'faciles et à fort impact' que je remets depuis 6 mois ?", "Quel projet 'long et incertain' dévore mon attention sans retour visible ?", "Que choisirais-je si je devais n'en garder que 3 cette année ?"], 'next_steps': ["Listez 10 initiatives en cours ou en attente.", "Placez-les dans une matrice 2x2 (effort × impact).", "Lancez immédiatement les 'quick wins' — cette semaine.", "Abandonnez officiellement 2 projets 'zombies'.", "Fixez 3 priorités trimestrielles visibles par toute l'équipe."], 'framework': "L'action a un coût d'opportunité : chaque oui est un non silencieux à autre chose."},
    'cout-inaction': {'category': 'Décision', 'measures': "Le coût de l'inaction est ce que vous perdez en ne décidant pas — opportunités, énergie, position de marché. Souvent supérieur au coût d'une décision imparfaite.", 'questions': ["Quelle décision je reporte depuis plus de 3 mois — et pourquoi ?", "Qu'est-ce que cette inaction me coûte chaque mois, en euros ou en énergie ?", "Si je décidais demain (même imparfaitement), quelle serait la pire issue réelle ?"], 'next_steps': ["Listez 3 décisions en suspens.", "Mettez une date butoir sur chacune.", "Identifiez ce qui bloque : information, peur, ego ?", "Prenez la plus petite décision concrète cette semaine.", "Documentez le résultat : le monde ne s'écroule presque jamais."], 'framework': "L'inaction n'est pas une position neutre : c'est une décision de subir le cours des choses."},
    'scenario-pivot': {'category': 'Stratégie', 'measures': "Un scénario pivot simule un changement majeur de modèle : nouvelle offre, nouveau segment, nouveau pricing. Le tester sur papier évite de le subir dans la réalité.", 'questions': ["Quel changement majeur ai-je envisagé sans jamais le chiffrer ?", "Quelle est la peur qui m'empêche de tester ce scénario, même petit ?", "Si je pivotais sans filet, de quoi aurais-je vraiment besoin ?"], 'next_steps': ["Écrivez votre scénario en 1 page : offre, prix, cible, rupture.", "Chiffrez-le sur 12 mois (optimiste, médian, pessimiste).", "Testez une mini-version avec 3 clients — sans engagement.", "Fixez des 'portes de sortie' (indicateurs qui disent stop).", "Revoyez votre scénario après 30 jours de test réel."], 'framework': "Pivoter n'est pas échouer : c'est apprendre plus vite que son marché."},
    'roi-marketing': {'category': 'Marketing', 'measures': "Le ROI marketing mesure ce que chaque euro investi en acquisition rapporte en chiffre d'affaires. Sans cette mesure, tout effort est un pari.", 'questions': ["Quel canal me rapporte vraiment — et lequel je continue par habitude ?", "Sur combien de mois je mesure le ROI — trop court, je pénalise les bons canaux ?", "Quelle partie de mon marketing n'est pas mesurable mais m'aide quand même ?"], 'next_steps': ["Listez vos canaux et leur coût mensuel.", "Attribuez chaque client à son canal d'origine.", "Calculez le ROI canal par canal sur 12 mois.", "Doublez l'investissement sur le meilleur canal.", "Supprimez le canal le plus coûteux à ROI flou."], 'framework': "Un canal sans mesure est un canal sans retour. Le brouillard coûte plus que l'investissement."},
    'pricing-paliers': {'category': 'Pricing', 'measures': "Les paliers tarifaires (small/medium/large) captent plus de clients en respectant leur capacité à payer. Bien conçus, ils augmentent la marge moyenne sans perdre personne.", 'questions': ["Mes prospects 'trop petits' me font-ils perdre du temps — ou j'aurais pu en capter plus avec un palier adapté ?", "Ai-je une offre premium qui justifie le standard ?", "Mes paliers reflètent-ils la transformation, ou juste le temps passé ?"], 'next_steps': ["Construisez 3 paliers : essentiel, complet, premium.", "Le premium doit être assumé : 2-3x le standard, pas juste +30%.", "Assurez-vous que chaque palier a une promesse distincte.", "Testez une nouvelle grille auprès de 5 prospects.", "Affinez après 90 jours selon le mix réel."], 'framework': "Trois paliers bien conçus captent plus que dix variantes floues. La clarté est un avantage compétitif."},
    'taille-marche': {'category': 'Marché', 'measures': "La taille du marché (TAM/SAM/SOM) définit votre plafond de croissance potentiel. Trop petit, vous plafonnez. Trop large, vous vous dispersez.", 'questions': ["Mon marché accessible est-il de 10, 1 000 ou 100 000 clients potentiels ?", "Suis-je sur un marché en croissance, stable ou en déclin ?", "Y a-t-il un 'sous-marché' niche qui me donnerait une position dominante ?"], 'next_steps': ["Estimez votre TAM (marché total) et SOM (marché atteignable).", "Interviewez 5 prospects hors de votre base actuelle.", "Identifiez 1 niche où vous pourriez devenir 'la référence'.", "Chiffrez le coût d'entrer dans une niche vs rester généraliste.", "Révisez votre positionnement chaque année."], 'framework': "Mieux vaut une niche dominée qu'un grand marché diffus. Profondeur > superficie."},
    'vulnerabilite-fournisseur': {'category': 'Risque', 'measures': "La vulnérabilité fournisseur mesure votre exposition à un prestataire, un logiciel, un service critique. Elle se révèle souvent après la panne.", 'questions': ["Lequel de mes fournisseurs me paralyserait s'il disparaissait demain ?", "Ai-je un plan B pour chaque brique critique — ou 'on verra le moment venu' ?", "Quel contrat renégocier, quelle alternative prospecter ?"], 'next_steps': ["Listez vos fournisseurs critiques avec niveau de dépendance.", "Identifiez 2-3 alternatives pour chaque brique majeure.", "Négociez des clauses de portabilité (données, code source).", "Testez un changement mineur pour vérifier la faisabilité.", "Documentez vos données et configurations dans un coffre-fort."], 'framework': "La résilience fournisseur se teste avant, pas pendant la crise."},
    'cout-non-qualite': {'category': 'Qualité', 'measures': "Le coût de la non-qualité — retours, SAV, mécontentements, bouche-à-oreille négatif — est souvent caché mais rarement négligeable. L'identifier, c'est le réduire.", 'questions': ["Combien de temps je passe à 'réparer' par mois — SAV, corrections, rattrapages ?", "Quelle erreur se répète — et pourquoi je n'ai pas encore outillé la prévention ?", "Combien perd-on en réputation pour chaque client mécontent ?"], 'next_steps': ["Mesurez le % de temps 'réparation' sur votre charge totale.", "Identifiez les 3 erreurs les plus fréquentes.", "Créez une check-list qualité avant livraison.", "Mettez en place un suivi post-livraison à J+14.", "Apprenez de chaque cas : post-mortem bref, écrit, partagé."], 'framework': "La non-qualité est un impôt invisible. Payer une fois la prévention coûte moins que payer 10 fois la réparation."},
}


def get_content_for(tool_slug: str) -> dict:
    """Retourne le contenu stratégique pour un outil, ou un défaut générique."""
    if not tool_slug:
        return _DEFAULT
    return TOOL_CONTENT.get(tool_slug, _DEFAULT)


# ──────────────────────────────────────────────────────────────────
# Interprétation conditionnelle : produire un diagnostic et des recos
# basés sur les VRAIES valeurs saisies / calculées par l'utilisateur.
# ──────────────────────────────────────────────────────────────────
import re as _re


def _to_number(raw: str) -> float | None:
    """Parse '2 000,50 €' ou '3.5%' → 2000.50 / 3.5 (None si illisible)."""
    if not raw:
        return None
    s = str(raw).strip()
    s = s.replace('\xa0', ' ').replace(' ', '')
    s = s.replace('€', '').replace('%', '').replace('x', '').strip()
    # Virgule décimale fr → point
    if ',' in s and '.' not in s:
        s = s.replace(',', '.')
    elif ',' in s and '.' in s:
        s = s.replace(',', '')
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _find(pairs: list[dict], *keywords: str) -> tuple[str, float | None]:
    """Cherche la première paire {label, value} dont le label contient un
    des keywords (case-insensitive). Retourne (label, parsed_number)."""
    for p in pairs or []:
        label = (p.get('label') or '').lower()
        if any(k.lower() in label for k in keywords):
            return p.get('label', ''), _to_number(p.get('value', ''))
    return '', None


def _fmt_money(v: float | int) -> str:
    try:
        return f"{int(round(v)):,} €".replace(',', ' ')
    except (ValueError, TypeError):
        return f"{v} €"


def _interpret_cac(inputs: list, results: list) -> dict:
    _, budget = _find(inputs, 'budget')
    _, ltv = _find(inputs, 'ltv', 'valeur vie')
    _, cac = _find(results, 'cac', "coût par client", 'cout par client')
    _, clients = _find(results, 'clients / mois', 'clients/mois', 'clients par mois')
    recos: list[str] = []
    headline = ''
    verdict = ''
    if cac and ltv:
        ratio = ltv / cac if cac > 0 else 0
        if ratio < 1 and cac > 0:
            verdict = (
                f"Chaque client vous coûte {_fmt_money(cac)} pour vous rapporter "
                f"{_fmt_money(ltv)} — soit un déficit de {_fmt_money(cac - ltv)}."
            )
            headline = (
                "Votre acquisition est déficitaire. Tant que ce ratio n'est pas "
                "inversé, chaque euro marketing creuse votre trésorerie."
            )
            recos = [
                "Stop à l'investissement marketing sur les canaux dont le CAC est > LTV — vérifiez d'abord par canal, pas en moyenne.",
                f"Objectif 30 jours : ramener le CAC sous {_fmt_money(ltv / 3)} (ratio LTV/CAC ≥ 3).",
                "Activez 1 levier de rétention (upsell, récurrence, parrainage) pour faire grimper la LTV avant de toucher au budget.",
                "Cartographiez votre entonnoir étape par étape : la fuite se trouve rarement là où on pense.",
            ]
        elif ratio < 3:
            verdict = (
                f"Votre ratio LTV/CAC est de {ratio:.1f}x — viable, mais sans marge "
                f"pour une casse (saisonnalité, changement d'algo, perte d'un canal)."
            )
            headline = (
                "Vous êtes en zone 'fragile'. L'acquisition fonctionne mais n'a pas "
                "encore le ressort nécessaire pour absorber un imprévu."
            )
            recos = [
                "Identifiez votre canal le plus stable — et concentrez 70% de vos efforts dessus.",
                "Testez 1 canal de contenu organique (SEO, podcast, newsletter) pour faire baisser le CAC moyen.",
                "Automatisez la relance : 60% des leads perdus ne reviennent pas faute de suivi, pas faute d'intérêt.",
                "Mesurez votre délai d'amortissement (CAC / revenu mensuel par client) — c'est le vrai indicateur de santé.",
            ]
        else:
            verdict = (
                f"Ratio LTV/CAC de {ratio:.1f}x : votre moteur d'acquisition est sain. "
                f"Chaque {_fmt_money(cac)} investi rapporte {_fmt_money(ltv)} sur la durée."
            )
            headline = (
                "Vous pouvez pousser l'accélérateur. La question devient : jusqu'où "
                "votre organisation peut-elle suivre ?"
            )
            recos = [
                "Doublez le budget sur le canal le plus rentable — et mesurez si le CAC reste stable (effet plafond).",
                "Documentez votre entonnoir pour le rendre transférable (SOP, vidéos, check-lists).",
                "Préparez la capacité opérationnelle : qui livre quand vous ferez +50% de clients ?",
                "Investissez dans la LTV (contrats annuels, services complémentaires) avant que la concurrence ne rattrape votre CAC.",
            ]
    if clients and clients == 0:
        headline = headline or (
            "Aucun client n'est acquis avec ces paramètres. Votre entonnoir n'est "
            "pas cassé par endroits — il est bloqué dès la première étape."
        )
        recos = [
            "Vérifiez votre taux de conversion visiteur → lead : s'il est < 1%, votre message ou votre page d'entrée ne parle pas à la bonne audience.",
            "Relancez 3 prospects passés (même tièdes) pour capturer un signal qualitatif avant d'investir plus.",
            "Simulez avec un budget de 500 € sur 1 canal ciblé avant de projeter mensuel.",
        ]
    return {'headline': headline, 'verdict': verdict, 'recommendations': recos}


def _interpret_point_mort(inputs: list, results: list) -> dict:
    _, charges = _find(inputs, 'charges fixes', 'charges mensuelles')
    _, marge = _find(inputs, 'marge')
    _, seuil = _find(results, 'seuil', 'point mort', 'chiffre d\'affaires')
    recos: list[str] = []
    headline = ''
    verdict = ''
    if seuil and charges:
        verdict = (
            f"Vous devez générer {_fmt_money(seuil)} de chiffre d'affaires mensuel "
            f"avant de commencer à vous rémunérer."
        )
        daily = seuil / 22 if seuil else 0
        headline = (
            f"Chaque jour ouvré, c'est {_fmt_money(daily)} à produire juste pour "
            f"tenir les charges. Au-delà, la marge est pour vous."
        )
        recos = [
            f"Listez chaque charge fixe — même les petites. Objectif : identifier {_fmt_money(charges * 0.1)} d'économies réalistes (-10%).",
            "Séparez 'fixe' et 'quasi-fixe' : certains abonnements peuvent passer en variable avec un changement de forfait.",
            "Fixez-vous un seuil psychologique quotidien (tableau visible) — le cerveau optimise ce qu'il voit.",
            "Planifiez un trimestre à {:.0f}% du seuil pour sécuriser, puis scalez.".format(110),
            "Si le seuil paraît inatteignable, le problème n'est pas la vente : c'est la structure de coûts.",
        ]
    return {'headline': headline, 'verdict': verdict, 'recommendations': recos}


def _interpret_generic(inputs: list, results: list) -> dict:
    """Fallback : extrait les 3 KPI les plus parlants pour en faire un headline."""
    if not results:
        return {}
    top = results[:3]
    parts = [f"{r.get('label', '')} : {r.get('value', '')}" for r in top if r.get('value')]
    headline = (
        "Vos chiffres clés : " + " · ".join(parts) + "."
        if parts else ''
    )
    return {'headline': headline, 'verdict': '', 'recommendations': []}


_INTERPRETERS = {
    'cac': _interpret_cac,
    'point-mort': _interpret_point_mort,
}


def interpret(
    tool_slug: str,
    *,
    user_inputs: list | None = None,
    results: list | None = None,
) -> dict:
    """Produit un headline + verdict + recommendations conditionnels sur
    les vraies valeurs saisies / calculées. Retourne ``{}`` si rien à dire.
    """
    user_inputs = user_inputs or []
    results = results or []
    fn = _INTERPRETERS.get(tool_slug or '')
    if fn:
        try:
            out = fn(user_inputs, results) or {}
            if any(out.values()):
                return out
        except Exception:  # noqa: BLE001
            pass
    return _interpret_generic(user_inputs, results)
