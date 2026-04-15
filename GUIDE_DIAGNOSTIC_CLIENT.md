# Guide de Diagnostic Client — Trait d'Union Studio

> **Usage** : Ce document est le protocole opérationnel pour réaliser un diagnostic complet
> de l'activité et/ou du site web d'un client. Il couvre les deux cas :
> activité sans site, site sans accès au code source, ou les deux.
>
> **Durée estimée** : 2 à 4 heures (diagnostic complet) · 1 heure (diagnostic ciblé)

---

## Table des matières

1. [Phase 0 — Prise de contact & qualification](#phase-0--prise-de-contact--qualification)
2. [Phase 1 — Entretien de découverte](#phase-1--entretien-de-découverte)
3. [Phase 2 — Diagnostic Activité (les 29 simulateurs TUS)](#phase-2--diagnostic-activité)
4. [Phase 3 — Diagnostic Site Web (sans accès au code source)](#phase-3--diagnostic-site-web)
5. [Phase 4 — Synthèse & scoring](#phase-4--synthèse--scoring)
6. [Phase 5 — Livrable & proposition](#phase-5--livrable--proposition)
7. [Annexes — Outils externes & checklist terrain](#annexes)

---

## Phase 0 — Prise de contact & qualification

Avant tout diagnostic, qualifier le besoin du client :

| Question | Pourquoi |
|----------|----------|
| Quel est votre secteur d'activité ? | Adapter les simulateurs pertinents |
| Avez-vous un site web existant ? Si oui, l'URL ? | Savoir si on fait un diagnostic site en plus |
| Sur quelle plateforme est-il construit (WordPress, Wix, Shopify, sur-mesure) ? | Adapter les outils d'analyse |
| Quel est votre objectif principal ? (plus de clients, mieux structurer, refondre le site, vendre en ligne…) | Cadrer le périmètre du diagnostic |
| Depuis combien de temps l'activité existe-t-elle ? | Contextualiser les chiffres |
| Êtes-vous seul ou avez-vous une équipe ? | Impact sur les simulateurs RH/délégation |

**Résultat** : on sait si on fait un diagnostic activité, un diagnostic site, ou les deux.

---

## Phase 1 — Entretien de découverte

Entretien structuré de 30 à 45 minutes avec le client. **Ne pas envoyer de questionnaire froid** — c'est une conversation qui fait partie de l'expérience TUS.

### Données à recueillir — Activité

| Donnée | Exemple | Utilisée dans |
|--------|---------|---------------|
| CA mensuel moyen | 12 000 € | Seuil de rentabilité, Atterrissage, Plafond de verre |
| Charges fixes mensuelles | 6 500 € | Seuil de rentabilité, Couverture charges fixes |
| Charges variables (% du CA) | 25% | Seuil de rentabilité, Mix produits |
| Nombre de clients actifs | 18 | Dépendance commerciale, Jumeaux clients |
| Panier moyen | 650 € | CAC, Elasticité-prix, Prix psychologique |
| Nombre de devis envoyés / mois | 8 | Taux de conversion |
| Nombre de devis signés / mois | 3 | Taux de conversion |
| Budget marketing mensuel | 400 € | CAC, ROI marketing |
| Nombre de nouveaux clients / mois | 2 | CAC, Rétention |
| Délai moyen de paiement client | 38 jours | DSO / trésorerie |
| % CA récurrent vs ponctuel | 30/70 | Stabilité du modèle |
| Heures travaillées / semaine | 55h | Capacité facturable |
| Heures facturées / semaine | 25h | Capacité facturable |
| Nombre d'outils SaaS utilisés | 12 | Fragmentation |
| Part du plus gros client dans le CA | 40% | Dépendance commerciale |
| Nombre de prestations/produits différents | 6 | Mix produits, Corrélation |
| Effectif (si applicable) | 3 | Seuil de délégation |
| Saisonnalité perçue | "creux en janvier-février" | Saisonnalité |

### Données à recueillir — Site web (si existant)

| Donnée | À demander au client |
|--------|---------------------|
| URL du site | www.exemple.gf |
| Objectif du site | Vitrine ? Prise de RDV ? Vente ? |
| Qui l'a construit et quand ? | Agence, freelance, lui-même, depuis quand |
| A-t-il Google Analytics / Search Console ? | Si oui, peut-il donner un accès lecteur ? |
| Nombre de visiteurs / mois (s'il sait) | Approximation OK |
| D'où viennent ses clients ? (bouche à oreille, Google, réseaux…) | Comprendre le rôle du site |
| A-t-il déjà investi en publicité en ligne ? | Google Ads, Facebook Ads, etc. |
| Quels sont ses concurrents directs ? (URL si possible) | Benchmark |

---

## Phase 2 — Diagnostic Activité

### La méthode des 6 indicateurs vitaux

Avant de lancer les simulateurs, poser les **6 KPIs de santé** qui forment le socle du diagnostic :

| # | Indicateur | Calcul rapide | Zone danger |
|---|-----------|--------------|-------------|
| 1 | **Trésorerie prévisionnelle à 30 jours** | Solde actuel + encaissements attendus − décaissements certains | Négatif |
| 2 | **DSO** (délai moyen de paiement client) | (Créances clients / CA) × 30 | > 45 jours |
| 3 | **Taux de marge brute** | (CA − coûts directs) / CA | En baisse sur 2 mois |
| 4 | **Taux de conversion** | Devis signés / devis envoyés | < 25% |
| 5 | **Répartition CA récurrent / ponctuel** | % de CA sous contrat ou récurrent | < 20% récurrent |
| 6 | **Couverture des charges fixes** | Charges fixes / marge brute | > 85% |

### Règle des signaux simultanés

| Situation | Niveau | Action |
|-----------|--------|--------|
| 1 indicateur en zone danger | ⚠️ Avertissement | À surveiller, mentionner dans le rapport |
| 2 indicateurs simultanément dégradés | 🚨 Alerte | Recommandation d'action prioritaire |
| 3+ indicateurs dégradés | 🚨🚨🚨 Urgence | Réunion stratégique proposée dans la semaine |

### Sélection des simulateurs TUS selon le profil

Ne pas utiliser les 29 simulateurs pour chaque client. Sélectionner les **8 à 12 plus pertinents** selon le profil.

#### Profil A — TPE solo / freelance
| Simulateur | Ce qu'on cherche |
|-----------|-----------------|
| Seuil de Rentabilité | Quel CA minimum pour couvrir les charges ? |
| Capacité Maximale Facturable | Combien peut-il facturer au max avec ses heures dispo ? |
| Plafond de Verre | À quel CA l'activité va plafonner structurellement ? |
| Friction Opérationnelle | Combien coûtent le chaos et les processus cassés ? |
| Indice de Fragmentation | Trop d'outils ? Lesquels éliminer ? |
| Élasticité-Prix | Peut-il augmenter ses tarifs sans perdre de clients ? |
| Prix Psychologique | Où se situe le prix perçu comme "juste" ? |
| Coût d'Inaction | Combien coûte le fait de ne rien changer ? |
| Vallée de la Mort | Est-il dans une phase critique de croissance ? |

#### Profil B — PME 3-15 personnes
| Simulateur | Ce qu'on cherche |
|-----------|-----------------|
| Seuil de Rentabilité | Point mort mensuel |
| Atterrissage Trimestriel / Annuel | Va-t-on atteindre l'objectif ? |
| Atterrissage Mensuel Trésorerie | Tension de trésorerie imminente ? |
| Radar de Dépendance Commerciale | Un client représente trop du CA ? |
| Seuil de Délégation | Faut-il embaucher ou externaliser ? |
| Optimiseur de Mix Produits/Services | Quelle prestation prioriser ? |
| Jumeaux Clients | Quels segments clients sont les plus rentables ? |
| Corrélation Produits/Services | Quels produits s'achètent ensemble ? |
| Impact Saisonnalité | Comment lisser les creux d'activité ? |
| Coût de la Non-Qualité | Combien coûtent les retours, SAV, erreurs ? |
| Matrice Effort / Impact | Quels projets lancer en priorité ? |

#### Profil C — Entreprise en réflexion stratégique
| Simulateur | Ce qu'on cherche |
|-----------|-----------------|
| Scénario Pivot | Et si on changeait de modèle ? |
| Taille de Marché Accessible | Le marché local est-il assez grand ? |
| Valeur de Sortie | Combien vaut l'entreprise aujourd'hui ? |
| Pricing par Paliers | Comment structurer l'offre en gammes ? |
| Vulnérabilité Fournisseur | Dépendance critique à un fournisseur ? |
| ROI Campagne Marketing | Les pubs ont-elles rapporté ? |
| Coût d'une Promotion | Ce -20%, ça coûte combien vraiment ? |

#### Rappel — Liste complète des 29 simulateurs TUS

<details>
<summary>Voir la liste complète</summary>

**Outils historiques (9)**
1. Seuil de Rentabilité (Point Mort)
2. Coût d'Acquisition (CAC)
3. Friction Opérationnelle
4. Indice de Fragmentation
5. Flux A.C.S.E
6. Plafond de Verre
7. Élasticité-Prix
8. Vallée de la Mort
9. Effet Rétention

**Nouveaux outils (20)**
10. Optimiseur de Mix Produits/Services
11. Atterrissage Trimestriel / Annuel
12. Atterrissage Mensuel Trésorerie
13. Simulateur de Jumeaux Clients
14. Corrélation Produits/Services
15. Seuil de Délégation
16. Prix Psychologique
17. Radar de Dépendance Commerciale
18. Capacité Maximale Facturable
19. Impact Saisonnalité
20. Vrai Coût d'une Promotion
21. Valeur de Sortie
22. Matrice Effort / Impact
23. Coût d'Inaction
24. Scénario Pivot
25. ROI Campagne Marketing
26. Pricing par Paliers
27. Taille de Marché Accessible
28. Vulnérabilité Fournisseur
29. Coût de la Non-Qualité

</details>

---

## Phase 3 — Diagnostic Site Web

> **Prérequis** : uniquement l'URL du site. Aucun accès au code source nécessaire.

### 3.1 — Performance & Vitesse

| Outil | URL | Gratuit | Ce qu'on mesure |
|-------|-----|---------|----------------|
| **Google PageSpeed Insights** | pagespeed.web.dev | ✅ | Core Web Vitals : LCP, INP, CLS — scores mobile et desktop |
| **GTmetrix** | gtmetrix.com | ✅ | Temps de chargement complet, waterfall, recommandations d'optimisation |
| **WebPageTest** | webpagetest.org | ✅ | TTFB, First Byte, Speed Index, comparaison multi-emplacements |
| **Pingdom Tools** | tools.pingdom.com | ✅ | Temps de réponse, taille de la page, nombre de requêtes |

**Ce qu'on note dans le rapport :**
- [ ] Score PageSpeed Mobile (objectif : > 70)
- [ ] Score PageSpeed Desktop (objectif : > 85)
- [ ] LCP — Largest Contentful Paint (objectif : < 2.5s)
- [ ] INP — Interaction to Next Paint (objectif : < 200ms)
- [ ] CLS — Cumulative Layout Shift (objectif : < 0.1)
- [ ] TTFB — Time To First Byte (objectif : < 800ms)
- [ ] Poids total de la page (objectif : < 3 Mo)
- [ ] Nombre de requêtes HTTP (objectif : < 50)
- [ ] Images non optimisées (format, compression, dimensions)
- [ ] Cache navigateur configuré ?
- [ ] Compression GZIP/Brotli activée ?

### 3.2 — SEO (Référencement naturel)

| Outil | URL | Gratuit | Ce qu'on mesure |
|-------|-----|---------|----------------|
| **Google Search Console** | search.google.com/search-console | ✅ (accès client requis) | Indexation, erreurs de crawl, requêtes, position moyenne |
| **Screaming Frog SEO Spider** | screamingfrog.co.uk | ✅ (< 500 URLs) | Crawl complet : titres, méta-descriptions, H1, liens cassés, redirections |
| **Ahrefs Webmaster Tools** | ahrefs.com/webmaster-tools | ✅ | Backlinks, domaines référents, santé technique |
| **Ubersuggest** | neilpatel.com/ubersuggest | ✅ (limité) | Volume de recherche, mots-clés positionnés, audit SEO |
| **Rich Results Test** | search.google.com/test/rich-results | ✅ | Données structurées (schema.org) |

**Ce qu'on note dans le rapport :**
- [ ] Le site est-il indexé par Google ? (`site:domaine.com`)
- [ ] Nombre de pages indexées vs nombre de pages réelles
- [ ] Chaque page a-t-elle un `<title>` unique et pertinent ? (< 60 caractères)
- [ ] Chaque page a-t-elle une `<meta description>` unique ? (< 160 caractères)
- [ ] Structure des titres correcte ? (un seul H1 par page, hiérarchie H2 > H3)
- [ ] Images avec attribut `alt` renseigné ?
- [ ] URLs propres et lisibles ? (pas de `?p=123`)
- [ ] Sitemap XML présent et soumis ?
- [ ] Fichier `robots.txt` présent et correct ?
- [ ] Liens internes cohérents ? Liens cassés (404) ?
- [ ] Redirections 301 en place si refonte précédente ?
- [ ] Données structurées (LocalBusiness, FAQ, Breadcrumb…) ?
- [ ] Vitesse de chargement (facteur SEO depuis 2021)
- [ ] Mobile-first indexing OK ?

### 3.3 — Sécurité (sans accès au code)

| Outil | URL | Gratuit | Ce qu'on mesure |
|-------|-----|---------|----------------|
| **SSL Labs** | ssllabs.com/ssltest | ✅ | Certificat HTTPS, configuration TLS, note A à F |
| **Security Headers** | securityheaders.com | ✅ | En-têtes de sécurité HTTP (CSP, HSTS, X-Frame-Options) |
| **Mozilla Observatory** | observatory.mozilla.org | ✅ | Score de sécurité global, bonnes pratiques |
| **Sucuri SiteCheck** | sitecheck.sucuri.net | ✅ | Malware, blacklist, CMS obsolète |
| **WPScan** (si WordPress) | wpscan.com | ✅ (limité) | Vulnérabilités plugins/thème, version WP exposée |

**Ce qu'on note dans le rapport :**
- [ ] HTTPS actif ? Certificat valide et non expiré ?
- [ ] Note SSL Labs (objectif : A ou A+)
- [ ] Redirection HTTP → HTTPS en place ?
- [ ] En-tête HSTS activé ?
- [ ] En-tête Content-Security-Policy présent ?
- [ ] En-tête X-Frame-Options présent ?
- [ ] En-tête X-Content-Type-Options présent ?
- [ ] Version du CMS exposée publiquement ? (risque si WordPress non à jour)
- [ ] Plugins/extensions avec vulnérabilités connues ?
- [ ] Page de login par défaut accessible ? (`/wp-admin`, `/wp-login.php`)
- [ ] Fichiers sensibles accessibles ? (`/readme.html`, `/xmlrpc.php`, `/.env`)
- [ ] Le site est-il sur des listes noires ? (vérification Sucuri)

### 3.4 — Accessibilité (WCAG)

| Outil | URL | Gratuit | Ce qu'on mesure |
|-------|-----|---------|----------------|
| **WAVE** | wave.webaim.org | ✅ | Erreurs et alertes WCAG, contrastes, ARIA |
| **axe DevTools** | Extension Chrome/Firefox | ✅ | Audit WCAG automatisé, violations par gravité |
| **Lighthouse** | Intégré à Chrome DevTools | ✅ | Score accessibilité, bonnes pratiques |
| **Contrast Checker** | webaim.org/resources/contrastchecker | ✅ | Ratio de contraste texte/fond |

**Ce qu'on note dans le rapport :**
- [ ] Score Lighthouse Accessibilité (objectif : > 85)
- [ ] Nombre d'erreurs WAVE (objectif : 0 erreur critique)
- [ ] Navigation au clavier fonctionnelle ? (Tab, Enter, Escape)
- [ ] Focus visible sur les éléments interactifs ?
- [ ] Contrastes texte/fond suffisants ? (ratio 4.5:1 minimum)
- [ ] Textes alternatifs sur toutes les images ?
- [ ] Formulaires avec labels associés ?
- [ ] Langue de la page déclarée (`<html lang="fr">`) ?
- [ ] Hiérarchie des titres logique ?
- [ ] Le site est-il utilisable sans JavaScript ?

### 3.5 — Mobile & Responsive

| Outil | URL | Gratuit | Ce qu'on mesure |
|-------|-----|---------|----------------|
| **Google Mobile-Friendly Test** | search.google.com/test/mobile-friendly | ✅ | Le site est-il compatible mobile ? |
| **Responsively App** | responsively.app | ✅ | Prévisualisation multi-écrans simultanée |
| **Chrome DevTools** | F12 > Toggle device | ✅ | Simulation de résolutions |

**Ce qu'on note dans le rapport :**
- [ ] Le site est-il responsive ? (s'adapte à toutes les tailles d'écran)
- [ ] Texte lisible sans zoom sur mobile ?
- [ ] Boutons/liens assez espacés pour le tactile ? (min 44×44 px)
- [ ] Pas de défilement horizontal ?
- [ ] Menu de navigation utilisable sur mobile ?
- [ ] Formulaires faciles à remplir sur mobile ?
- [ ] Images qui s'adaptent (pas de débordement) ?
- [ ] Viewport meta tag présent ?

### 3.6 — UX / Design / Contenu (inspection manuelle)

Pas d'outil automatisé — c'est l'œil du professionnel qui parle.

**Première impression (test des 5 secondes)**
- [ ] En 5 secondes, comprend-on ce que fait l'entreprise ?
- [ ] La proposition de valeur est-elle visible immédiatement ?
- [ ] Le CTA principal est-il évident ?

**Navigation & architecture**
- [ ] Le menu est-il clair et logique ? (< 7 items)
- [ ] Peut-on accéder à n'importe quelle page en 3 clics maximum ?
- [ ] Fil d'Ariane présent ?
- [ ] Page 404 personnalisée ?
- [ ] Recherche interne disponible (si > 20 pages) ?

**Contenu**
- [ ] Textes clairs, sans jargon, orientés bénéfice client ?
- [ ] Orthographe et grammaire impeccables ?
- [ ] Témoignages / avis clients présents ?
- [ ] Preuves sociales (logos clients, certifications, chiffres clés) ?
- [ ] Visuels de qualité professionnelle ? (pas de stock photos évidentes)
- [ ] Cohérence graphique (couleurs, typos, espacements) ?

**Conversion**
- [ ] Combien de clics pour contacter / demander un devis ? (objectif : ≤ 2)
- [ ] Numéro de téléphone cliquable sur mobile ?
- [ ] Formulaire de contact fonctionnel et simple ? (< 5 champs)
- [ ] CTA visibles et contrastés sur chaque page ?
- [ ] Réassurance présente ? (garanties, délais, processus)

**Conformité légale**
- [ ] Mentions légales présentes et complètes ?
- [ ] Politique de confidentialité / RGPD ?
- [ ] Bandeau cookies conforme ?
- [ ] CGV si e-commerce ?
- [ ] Conditions d'utilisation si nécessaire ?

---

## Phase 4 — Synthèse & scoring

### Grille de scoring du diagnostic

| Domaine | Poids | Note /10 | Score pondéré |
|---------|-------|----------|--------------|
| **Santé financière** (6 KPIs vitaux) | 25% | ___ | ___ |
| **Stratégie & positionnement** (simulateurs) | 15% | ___ | ___ |
| **Performance site** (vitesse, Core Web Vitals) | 15% | ___ | ___ |
| **SEO** (référencement, indexation) | 15% | ___ | ___ |
| **Sécurité** (HTTPS, headers, CMS) | 10% | ___ | ___ |
| **Mobile & responsive** | 5% | ___ | ___ |
| **Accessibilité** | 5% | ___ | ___ |
| **UX / Design / Contenu** | 5% | ___ | ___ |
| **Conformité légale** | 5% | ___ | ___ |
| **SCORE GLOBAL** | **100%** | | **/10** |

### Barème de notation par domaine

| Note | Signification |
|------|--------------|
| 9-10 | Excellent — rien à signaler, maintenir |
| 7-8 | Bon — améliorations mineures possibles |
| 5-6 | Passable — plusieurs points à corriger |
| 3-4 | Faible — problèmes significatifs |
| 1-2 | Critique — intervention urgente nécessaire |

### Classification des recommandations

| Priorité | Critère | Exemple |
|----------|---------|---------|
| 🔴 **Critique** | Impact direct sur le CA ou la sécurité | Site non HTTPS, formulaire cassé, trésorerie négative à 30j |
| 🟠 **Important** | Frein significatif à la croissance | Page Speed < 40, pas de SEO, dépendance à 1 client > 50% |
| 🟡 **Recommandé** | Amélioration notable | Optimiser les images, ajouter des témoignages, structurer les données |
| 🟢 **Bonus** | Finition, différenciation | Micro-animations, données structurées avancées, A/B testing |

---

## Phase 5 — Livrable & proposition

### Structure du rapport diagnostic

```
1. Page de garde
   - Logo TUS + logo client
   - "Diagnostic [Activité / Site Web / Complet]"
   - Date + nom du client

2. Résumé exécutif (1 page)
   - Score global /10
   - Les 3 forces principales
   - Les 3 faiblesses critiques
   - Recommandation prioritaire n°1

3. Diagnostic Activité (si applicable)
   - Tableau des 6 KPIs vitaux avec voyants vert/orange/rouge
   - Résultats des simulateurs sélectionnés (captures + interprétation)
   - Signaux d'alerte identifiés

4. Diagnostic Site Web (si applicable)
   - Résultats par domaine (Performance, SEO, Sécurité, etc.)
   - Captures d'écran annotées des problèmes
   - Scores des outils utilisés

5. Plan d'action (classé par priorité)
   - Actions 🔴 Critiques — à faire immédiatement
   - Actions 🟠 Importantes — dans les 30 jours
   - Actions 🟡 Recommandées — dans les 90 jours
   - Actions 🟢 Bonus — quand le reste est en place

6. Proposition d'accompagnement TUS
   - Lien vers les services TUS adaptés au diagnostic
   - Devis personnalisé
```

### Comment présenter le rapport

1. **Jamais par email seul** — toujours en visio ou en présentiel
2. **Commencer par les forces** — le client doit entendre ce qui marche avant ce qui ne marche pas
3. **Chiffrer l'impact** — utiliser le simulateur "Coût d'Inaction" pour montrer combien l'inaction coûte
4. **Proposer 3 niveaux d'intervention** — essentiel / recommandé / premium
5. **Le diagnostic est offert ou facturé ?** — à définir selon la stratégie commerciale

---

## Annexes

### A. Checklist terrain express (version imprimable)

```
CLIENT : ___________________________  DATE : ___________  URL : ___________________________

ACTIVITÉ
□ CA mensuel : ________    □ Charges fixes : ________    □ Marge brute : ________%
□ Tréso prévisionnelle 30j : ________    □ DSO : ________ jours
□ Taux conversion : ________%    □ CA récurrent : ________%    □ Couverture CF : ________%
→ Signaux simultanés : □ 0  □ 1 ⚠️  □ 2 🚨  □ 3+ 🚨🚨🚨

PERFORMANCE SITE
□ PageSpeed Mobile : ___/100    □ PageSpeed Desktop : ___/100
□ LCP : ___s    □ INP : ___ms    □ CLS : ___    □ TTFB : ___ms
□ Poids page : ___ Mo    □ Requêtes : ___

SEO
□ Indexé Google : □ Oui □ Non    □ Pages indexées : ___
□ Titles uniques : □ Oui □ Non    □ Méta desc : □ Oui □ Non
□ H1 unique/page : □ Oui □ Non    □ Sitemap : □ Oui □ Non
□ Alt images : □ Oui □ Non    □ Liens cassés : ___

SÉCURITÉ
□ HTTPS : □ Oui □ Non    □ SSL Labs : ___    □ Security Headers : ___
□ CMS à jour : □ Oui □ Non □ N/A    □ Infos sensibles exposées : □ Oui □ Non

ACCESSIBILITÉ
□ Lighthouse : ___/100    □ Erreurs WAVE : ___    □ Contrastes OK : □ Oui □ Non
□ Navigation clavier : □ Oui □ Non    □ lang="fr" : □ Oui □ Non

MOBILE
□ Mobile-friendly : □ Oui □ Non    □ Texte lisible : □ Oui □ Non
□ Boutons touch OK : □ Oui □ Non    □ Pas de scroll H : □ Oui □ Non

UX / CONTENU
□ Proposition valeur claire : □ Oui □ Non    □ CTA visible : □ Oui □ Non
□ Contact en ≤ 2 clics : □ Oui □ Non    □ Témoignages : □ Oui □ Non
□ Mentions légales : □ Oui □ Non    □ RGPD/cookies : □ Oui □ Non

SCORE GLOBAL : ___/10
```

### B. Outils externes — récapitulatif

| Outil | Catégorie | URL | Coût |
|-------|-----------|-----|------|
| Google PageSpeed Insights | Performance | pagespeed.web.dev | Gratuit |
| GTmetrix | Performance | gtmetrix.com | Gratuit |
| WebPageTest | Performance | webpagetest.org | Gratuit |
| Pingdom Tools | Performance | tools.pingdom.com | Gratuit |
| Google Search Console | SEO | search.google.com/search-console | Gratuit |
| Screaming Frog | SEO | screamingfrog.co.uk | Gratuit < 500 URLs |
| Ahrefs Webmaster Tools | SEO | ahrefs.com/webmaster-tools | Gratuit |
| Ubersuggest | SEO | neilpatel.com/ubersuggest | Freemium |
| Rich Results Test | SEO | search.google.com/test/rich-results | Gratuit |
| SSL Labs | Sécurité | ssllabs.com/ssltest | Gratuit |
| Security Headers | Sécurité | securityheaders.com | Gratuit |
| Mozilla Observatory | Sécurité | observatory.mozilla.org | Gratuit |
| Sucuri SiteCheck | Sécurité | sitecheck.sucuri.net | Gratuit |
| WPScan | Sécurité (WP) | wpscan.com | Freemium |
| WAVE | Accessibilité | wave.webaim.org | Gratuit |
| axe DevTools | Accessibilité | Extension navigateur | Gratuit |
| Lighthouse | Perf + Access + SEO | Chrome DevTools (F12) | Gratuit |
| Contrast Checker | Accessibilité | webaim.org/resources/contrastchecker | Gratuit |
| Google Mobile-Friendly | Mobile | search.google.com/test/mobile-friendly | Gratuit |
| Responsively | Mobile | responsively.app | Gratuit |

### C. Correspondance simulateurs TUS ↔ problèmes diagnostiqués

| Problème identifié | Simulateur TUS à utiliser |
|-------------------|--------------------------|
| Le client ne sait pas s'il gagne de l'argent | Seuil de Rentabilité |
| Il dépense en pub sans savoir si ça marche | CAC + ROI Campagne Marketing |
| Il perd du temps dans des process manuels | Friction Opérationnelle |
| Il a 15 outils SaaS qui ne communiquent pas | Indice de Fragmentation |
| Il ne sait pas quelle prestation prioriser | Mix Produits + Matrice Effort/Impact |
| Il hésite à embaucher | Seuil de Délégation |
| Il ne sait pas fixer ses prix | Élasticité-Prix + Prix Psychologique + Pricing Paliers |
| Un client représente 50%+ de son CA | Radar de Dépendance Commerciale |
| Il travaille 60h mais facture 30% | Capacité Maximale Facturable |
| Il a des creux d'activité saisonniers | Impact Saisonnalité |
| Il veut faire une promo mais hésite | Vrai Coût d'une Promotion |
| Il pense à vendre ou transmettre | Valeur de Sortie |
| Il a plusieurs projets et ne sait pas lequel lancer | Matrice Effort / Impact |
| Il repousse des décisions importantes | Coût d'Inaction |
| Il envisage un changement de modèle | Scénario Pivot |
| Il veut structurer son offre en gammes | Pricing par Paliers |
| Il se demande si son marché est assez grand | Taille de Marché Accessible |
| Il dépend d'un fournisseur unique | Vulnérabilité Fournisseur |
| Il a beaucoup de SAV / retours / erreurs | Coût de la Non-Qualité |
| Il ne sait pas quels clients fidéliser | Jumeaux Clients + Effet Rétention |
| Il veut savoir quels produits vont ensemble | Corrélation Produits/Services |
| Sa croissance stagne sans raison apparente | Plafond de Verre + Vallée de la Mort |
| Son process de vente est lent/bloqué | Flux A.C.S.E |
| Il ne sait pas s'il va finir l'année à l'objectif | Atterrissage Trimestriel / Annuel |
| Il a peur de ne pas passer le mois | Atterrissage Mensuel Trésorerie |

---

> **Dernière mise à jour** : Avril 2026
> **Auteur** : Trait d'Union Studio
