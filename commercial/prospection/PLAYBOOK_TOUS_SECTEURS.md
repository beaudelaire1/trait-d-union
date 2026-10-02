# Playbook de prospection TUS, tous secteurs et tous profils

**Principe** : on ne prospecte pas un secteur, on prospecte une **situation**.
Un prospect n'entre dans le fichier que s'il a un **signal d'achat observable**
(ouverture, recrutement, échéance, prix remporté, nouvel outil…). Le secteur
sert seulement à choisir l'accroche et le module d'entrée
(voir [matrice_secteurs.csv](./matrice_secteurs.csv)).

Les codes secteur (21) et profil (6) sont ceux du diagnostic terrain du site
(`apps/diagnostic/field_questions.py`) : un prospect qualifié passe directement
en diagnostic, sans retraduction.

---

## 1. Profils : quelle offre d'entrée pour qui

| Code | Profil | Douleur dominante | Offre d'entrée TUS | Ticket | Cycle | Outil gratuit pour ouvrir |
|---|---|---|---|---|---|---|
| `solo` | Indépendant | Le temps ne se transforme pas en CA ; devis et relances le soir | Présence web + demande de devis structurée | 1–3 k€ | 1–2 sem. | `/simulateur/capacite/` |
| `tpe` | 1 à 9 salariés | Tout passe par le dirigeant ; outils empilés | Module métier ciblé (devis-facture, RDV, stock) | 3–8 k€ | 2–4 sem. | `/simulateur/fragmentation/` |
| `pme` | 10 à 50 | Pilotage au ressenti, ressaisies entre services | Infrastructure métier (CRM, mini-ERP, portails) | 8–25 k€ | 4–8 sem. | `/simulateur/acse/` |
| `croissance` | Forte croissance | L'organisation ne tient pas la charge, trésorerie tendue | Socle métier + automatisations + pilotage | 10–25 k€ | 3–6 sem. | `/simulateur/tresorerie/` |
| `reprise` | Création ou reprise < 3 ans | Tout est à poser ; outils hérités ou absents | Diagnostic terrain → socle minimal évolutif | 3–12 k€ | 2–6 sem. | `/simulateur/point-mort/` |
| `strategique` | Pivot, croissance externe, cession | Décision structurante sans données fiables | Diagnostic + tableau de bord de pilotage | 5–15 k€ | 6–12 sem. | `/simulateur/valeur-sortie/` |

Tickets indicatifs cohérents avec la page Solutions (vitrine à partir de 1 000 €, e-commerce 5 000–8 500 €, infrastructure sur devis) et avec le [guide d'acquisition](../GUIDE_ACQUISITION.md).

---

## 2. Les 12 signaux d'achat à surveiller

| # | Signal | Où le détecter | Ce qu'il révèle |
|---|---|---|---|
| 1 | Ouverture, inauguration, nouvel établissement | La 1ère, France-Guyane, Cap Infos, RCI, Outremers360, Bâtisseurs Outre-mer | Les outils se choisissent **avant** l'ouverture |
| 2 | Recrutement administratif ou facturation | Indeed, Hellowork, France Travail, Jooble, FOMAT | Surcharge de process manuels |
| 3 | Recrutement massif (10 postes ou plus) | Pages carrières, StaffSocial | Onboarding, planning, coordination |
| 4 | Création ou reprise récente | BODACC / annuaire-entreprises.data.gouv.fr, Initiative, Réseau Entreprendre, CCI « Transmission 2026 » | Socle à construire |
| 5 | Prix, concours, levée | EDF Pulse, Challenge Innov'Ultramarin, French Tech, GDI, Technopole Martinique | Projet financé à réaliser |
| 6 | Nouvel outil partiel déployé (WMS, caisse, PMS) | Presse spécialisée (Voxlog, Supply Chain Magazine), communiqués éditeurs | Besoin d'intégration et de portail client |
| 7 | Marché public remporté | Avis d'attribution (PLACE, e-marchespublics) | Montée en charge, preuves à fournir |
| 8 | Facture électronique | Toute entreprise d'Hexagone, de Martinique, de Guadeloupe ou de La Réunion | Chaîne devis-facture à revoir avant 09/2027 |
| 9 | Aide numérique ouverte | Chèque TIC Guadeloupe (jusqu'au 31/10/2026), Pass Numérique Martinique, Kap Numérik | Le projet est finançable maintenant |
| 10 | Site absent, obsolète ou non mobile | Test manuel, PageSpeed, avis Google | Porte d'entrée « présence web » |
| 11 | Avis clients qui se plaignent de délais ou de réponses | Google Maps, TripAdvisor | Processus de réponse cassé |
| 12 | Audit ou certification (Qualiopi, ISO, HACCP) | Liste publique Qualiopi, sites des organismes | Preuves et traçabilité récurrentes |

---

## 3. Grille de qualification (score sur 100)

| Critère | 0 | Moyen | Max |
|---|---|---|---|
| **Signal** (fraîcheur, force) | aucun | signal générique (10) | signal daté de moins de 6 mois (30) |
| **Adéquation offre** | pas de flux à structurer | un module (10) | plusieurs flux à relier (20) |
| **Capacité de financement** | inconnue | budget plausible (10) | aide mobilisable ou budget annoncé (20) |
| **Accès au décideur** | inconnu | entreprise joignable (5) | décideur nommé et joignable (15) |
| **Urgence** | aucune | échéance à plus de 6 mois (5) | échéance à moins de 3 mois (15) |

**A ≥ 70** : contact cette semaine, en personne si possible · **B 45–69** : séquence standard · **C < 45** : veille, re-scorer au prochain signal.

---

## 4. Rituel hebdomadaire (≈ 6 h par semaine)

| Jour | Action | Durée |
|---|---|---|
| Lundi | Veille des signaux (sources du §2) : ajouter 5 à 10 lignes au fichier prospects, avec l'URL source | 1 h 30 |
| Mardi | 10 premiers contacts (LinkedIn et email) sur les prospects A et B | 1 h 30 |
| Mercredi | 2 à 3 visites terrain ou appels (A uniquement) + 1 prescripteur | 1 h 30 |
| Jeudi | Veille marchés publics (§5) + relances J+7 | 1 h |
| Vendredi | Mise à jour du statut dans le CSV, calcul des KPI (§9) | 30 min |

---

## 5. Veille marchés publics

**Plateformes** : [PLACE](https://www.marches-publics.gouv.fr/) (État, et plateforme unique d'ici 2030), e-marchespublics (CTG, Communauté de communes de l'Ouest guyanais, Comité Martiniquais du Tourisme), [CTG — marchés publics](https://www.ctguyane.fr/marches-publics/), [Région Guadeloupe](https://www.regionguadeloupe.fr/), [CDG Martinique](https://www.cdg-martinique.fr/cdg-martinique/marches-publics/).

**Mots-clés** : `site internet`, `refonte`, `portail`, `application`, `logiciel`, `plateforme`, `dématérialisation`, `téléservice`, `prise de rendez-vous`, `billetterie`, `système d'information`.

**Règle** : répondre seulement si le lot fait moins de 90 k€ HT et si on peut produire une référence réelle comparable (NetExpress). Sinon, se positionner en **sous-traitant** de l'attributaire.

---

## 6. Messages

Règles : 120 mots maximum, uniquement des références clients réelles (NetExpress ; jamais la démo TitanTech), un signal réel cité, une question, une petite demande. Jamais de pièce jointe au premier message. Trois messages au maximum par séquence (J0, J+7, J+18).

### 6.1 Premier message universel (à adapter à chaque signal)

> Objet : [Entreprise] — [signal en 4 mots]
>
> Bonjour [Prénom],
>
> J'ai vu [signal précis : « l'ouverture de votre unité de production », « vos 22 postes ouverts »…].
> À ce stade, beaucoup d'entreprises de [secteur] butent sur [douleur de la matrice secteurs].
>
> Chez Trait d'Union Studio, nous construisons à Cayenne des outils métier sur mesure (devis, commandes, portails clients, pilotage). Exemple : pour NetExpress, une seule plateforme relie la demande, le devis, le chantier, la facture et le cabinet comptable, avec quatre espaces dédiés.
>
> Seriez-vous ouvert à 20 minutes pour voir si c'est pertinent pour [Entreprise] ?
>
> [Signature] · traitdunion.studio
> *Vous ne souhaitez plus recevoir de message de notre part ? Répondez « stop ».*

### 6.2 Campagne Guadeloupe — Chèque TIC (jusqu'au 31/10/2026)

> Objet : Chèque TIC : jusqu'à 80 % de votre projet numérique, dépôt avant le 31 octobre
>
> Bonjour [Prénom],
>
> La Région Guadeloupe finance jusqu'à 80 % d'un projet numérique de TPE-PME (plafond 10 000 €), avec des dossiers à déposer avant le **31 octobre**.
> Pour [Entreprise], cela peut couvrir [site + prise de commande / module devis-facture / portail client].
>
> Nous chiffrons le projet et vous remettons un devis conforme au dossier sous 72 h. Un échange de 15 minutes cette semaine ?

*À vérifier avant envoi : éligibilité exacte (effectif, secteur, dépenses éligibles) sur la [page officielle du Chèque TIC](https://www.regionguadeloupe.fr/les-aides-les-services/guide-des-aides/detail/actualites/aide-cheque-tic/categorie/administrations-et-demarches/).*

### 6.3 Campagne Antilles et Hexagone — facture électronique

> Objet : Facture électronique : votre émission devient obligatoire en septembre 2027
>
> Bonjour [Prénom],
>
> Depuis le 1er septembre, [Entreprise] doit pouvoir **recevoir** des factures électroniques ; en septembre 2027, elle devra aussi les **émettre** (Factur-X, UBL ou CII, via une plateforme agréée).
> Le vrai sujet n'est pas le format : c'est la chaîne devis → facture → encaissement qui doit être propre.
>
> Testez une de vos factures gratuitement : traitdunion.studio/simulateur/conformite-facture/ (analyse EN 16931, rien n'est conservé).
> Si des points ressortent, je vous propose 20 minutes pour prioriser.

**Ne jamais envoyer cette campagne en Guyane ou à Mayotte** (hors champ : TVA non applicable). Voir le §1.1 de l'[analyse de marché](./ANALYSE_MARCHE_2026.md).

### 6.4 Guyane — message « fluidité » (sans argument réglementaire)

> Bonjour [Prénom], entre le devis, le bon de commande, la facture et la relance, combien de fois la même information est-elle ressaisie chez [Entreprise] ?
> Le diagnostic gratuit en 2 minutes (traitdunion.studio/simulateur/acse/) montre où votre activité se coince : attirer, convertir, structurer ou exécuter. Je vous le commente ensuite en 15 minutes si vous voulez.

### 6.5 Lauréats et porteurs de projets innovants

> Félicitations pour [prix] ! Après le prix vient la construction : si la plateforme [nom] a besoin d'être développée ou renforcée, nous livrons des portails sur mesure en Antilles-Guyane (architecture documentée, code transmis). Un atelier de cadrage d'une heure, offert, pour poser le MVP ?

### 6.6 Script téléphone de 60 secondes (numéros professionnels uniquement)

1. « Bonjour [Prénom], [Nom] de Trait d'Union Studio à Cayenne. Je vous appelle à propos de [signal]. Vous avez 45 secondes ? »
2. « On voit souvent qu'au moment de [signal], [douleur]. C'est un sujet chez vous ? »
3. Si oui : « Je vous propose 20 minutes pour regarder vos flux, sans présentation commerciale. Mardi ou jeudi ? »
4. Si non : « Merci. Qu'est-ce qui vous prend le plus de temps administratif aujourd'hui ? » (écouter, noter, re-scorer)

### 6.7 Objections fréquentes

| Objection | Réponse |
|---|---|
| « On a déjà un logiciel. » | « Très bien. Qu'est-ce qu'il ne fait pas, que vous refaites à la main dans Excel ou WhatsApp ? On se branche dessus, on ne remplace pas ce qui marche. » |
| « C'est trop cher. » | « Qu'est-ce que vous coûte le statu quo ? » (outil `/simulateur/cout-inaction/`) + aides du territoire (§1.2 de l'analyse). |
| « Pas le temps. » | « Justement : le diagnostic prend 2 minutes en ligne, je vous rappelle seulement si le résultat le justifie. » |
| « On verra l'an prochain. » | Antilles : « L'émission de factures électroniques est obligatoire en septembre 2027 ; un projet se prépare en 4 à 8 semaines. » Guadeloupe : « Le Chèque TIC ferme le 31 octobre. » |
| « Vous êtes trop petits. » | « Code documenté et transmis, et vous restez propriétaire. Voici NetExpress : quatre portails (administration, client, ouvrier, cabinet comptable) sur un même référentiel. » |

### 6.8 Prescripteurs (fédérations et réseaux)

> Bonjour [Prénom], [fédération] accompagne [X] entreprises qui, pour beaucoup, empilent les outils sans vision consolidée. Nous proposons à vos adhérents un atelier gratuit de 1 h 30 : « Structurer sa PME en 90 jours », avec un diagnostic en direct. Seriez-vous d'accord pour l'inscrire à votre agenda de [mois] ?

Cibles prioritaires : MPI Guyane, AMPI Martinique, UEBS (CSG), ARAPL Antilles-Guyane, Initiative Centre Est Guyane, Martinique Développement (voir [partenaires_antilles_guyane.csv](../partenaires_antilles_guyane.csv)).

---

## 7. Conformité : RGPD et démarchage

- **Email B2B à froid** : autorisé sans consentement préalable si le message concerne la fonction professionnelle du destinataire ; identifier l'expéditeur, informer de l'usage des données et offrir un désabonnement simple dans **chaque** message (règles CNIL).
- **Indépendants utilisant une adresse personnelle** : les traiter comme des particuliers, donc pas d'email à froid. Passer par un formulaire public ou un contact en personne.
- **Téléphone** : n'appeler que des numéros professionnels publiés par l'entreprise. Pour les particuliers, le démarchage téléphonique exige un consentement préalable depuis le 11 août 2026 (loi n° 2025-594 du 30 juin 2025).
- **Fichier prospects** : données professionnelles uniquement, source notée pour chaque ligne, suppression immédiate sur opposition, conservation de 3 ans au plus après le dernier contact.
- **LinkedIn** : pas d'extraction automatisée (contraire aux conditions d'utilisation) ; messages rédigés et envoyés à la main.

---

## 8. Du prospect au client : raccordement au back-office TUS

1. Premier échange positif : créer le **Lead** dans l'admin (statut « Contacté », notes = signal + URL source).
2. RDV obtenu : lancer un **diagnostic terrain** (module diagnostic du back-office) avec le code secteur et le code profil du fichier prospects.
3. Rapport PDF remis : passer le Lead en « Qualifié » et envoyer le devis depuis le module devis.
4. Signature : convertir le Lead en client (statut « Converti ») et mettre le CSV à jour.

---

## 9. Objectifs à 90 jours (octobre à décembre 2026)

| Indicateur | Octobre | Novembre | Décembre | Cumul |
|---|---|---|---|---|
| Prospects qualifiés dans le fichier | 40 | 30 | 30 | 100 |
| Premiers contacts envoyés | 60 | 50 | 40 | 150 |
| RDV réalisés | 8 | 10 | 7 | 25 |
| Diagnostics terrain | 3 | 4 | 3 | 10 |
| Propositions envoyées | 2 | 3 | 2 | 7 |
| Signatures | 1 | 1 | 1 | **3** |

Taux de référence à suivre : contact → RDV 15 à 20 % ; RDV → diagnostic 40 % ; proposition → signature 35 à 45 %.

---

## 10. Plan d'action

**Semaine du 28 septembre 2026**
- Contacter les trois prospects A du [fichier](./prospects_2026-09.csv) : Guymargua Restauration (visite), Golden Tulip Toukana (note d'une page « 5 services locaux avant ouverture »), Kultur Karaib (atelier MVP).
- Construire une liste de 50 TPE guadeloupéennes éligibles au Chèque TIC (CCI Îles de Guadeloupe, Pages Jaunes par secteur) et lancer la campagne 6.2.
- Écrire à MPI Guyane et à l'UEBS pour proposer un atelier aux sous-traitants du CSG.

**Octobre** : campagne Chèque TIC jusqu'au 31/10 · campagne facture électronique aux Antilles · offre verticale « formation Qualiopi » (P10 à P12).

**Novembre** : hôtellerie et tourisme avant la haute saison (décembre à avril) · BTP et industrie (pilotage de marge) · relance des lauréats.

**Décembre** : bilan des KPI · nettoyage du fichier · préparation de la campagne « J-9 mois » sur l'émission de factures électroniques (échéance 09/2027).

---

## 11. Enrichir le fichier : méthode

1. Choisir un signal du §2 et une zone.
2. Rechercher avec des requêtes datées, par exemple : `ouverture [secteur] Cayenne 2026`, `[territoire] entreprise recrute assistant administratif`, `lauréats [concours] 2026`, `[commune] inauguration entreprise`.
3. Vérifier l'entreprise sur annuaire-entreprises.data.gouv.fr (SIREN, effectif, dirigeant déclaré).
4. Ajouter la ligne au CSV **avec l'URL source**, scorer (§3), attribuer la priorité.
5. Aucune ligne sans source : on ne prospecte pas une entreprise supposée.
