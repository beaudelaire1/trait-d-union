# Requirements Document

## Introduction

Ce document définit les exigences pour le site vitrine officiel de **Trait d'Union Studio (TUS)**, une agence web premium spécialisée dans la création de sites vitrines, e-commerce, plateformes web et mini-ERP. Le site doit présenter l'offre de manière sobre et crédible, inspirer confiance dès la première visite, et générer des demandes qualifiées via un formulaire de contact intelligent.

**Slogan officiel** : « Quand l'élégance se conçoit, la performance se déploie. »

**Positionnement** : Humble au démarrage, ton sobre et précis, sans promesses exagérées.

## Glossary

- **TUS** : Trait d'Union Studio, l'agence web propriétaire du site
- **Site_Vitrine** : Site web de présentation sans fonctionnalité e-commerce
- **Design_System** : Ensemble cohérent de composants UI, couleurs, typographies et règles de design
- **HTMX** : Bibliothèque JavaScript légère permettant des interactions dynamiques via attributs HTML
- **CTA** : Call-to-Action, élément incitant l'utilisateur à effectuer une action
- **Lead** : Contact qualifié généré via le formulaire
- **Partial** : Fragment de template Django réutilisable
- **MVP** : Minimum Viable Product, version minimale fonctionnelle du produit
- **Formulaire_Intelligent** : Formulaire dont les champs s'adaptent dynamiquement selon le type de projet sélectionné
- **Charte_Graphique** : Ensemble des règles visuelles définissant l'identité de marque

## Requirements

### Requirement 1: Page d'Accueil

**User Story:** As a visiteur, I want to comprendre rapidement l'offre de TUS dès la page d'accueil, so that I can décider si l'agence correspond à mes besoins.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page d'accueil, THE Site_Vitrine SHALL afficher le slogan officiel « Quand l'élégance se conçoit, la performance se déploie. »
2. WHEN la page d'accueil est chargée, THE Site_Vitrine SHALL présenter un aperçu des 3 offres principales (Vitrine, Commerce, Système)
3. WHEN un visiteur consulte la page d'accueil, THE Site_Vitrine SHALL afficher des preuves de qualité (méthode, performance, rigueur)
4. WHEN un visiteur est sur la page d'accueil, THE Site_Vitrine SHALL proposer des CTA vers Services, Méthode, Contact et Ressources
5. THE Site_Vitrine SHALL utiliser la couleur de fond principale #07080A sur la page d'accueil
6. THE Site_Vitrine SHALL utiliser la typographie Space Grotesk pour les titres avec un poids de 600-700

---

### Requirement 2: Page Services

**User Story:** As a prospect, I want to consulter le détail des offres de TUS, so that I can identifier la solution adaptée à mon projet.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page Services, THE Site_Vitrine SHALL afficher 3 blocs d'offre distincts (Vitrine, E-commerce, Plateforme/Mini-ERP)
2. WHEN un bloc d'offre est affiché, THE Site_Vitrine SHALL présenter clairement « Ce que vous recevez » et les options disponibles
3. WHEN un visiteur consulte un service, THE Site_Vitrine SHALL proposer un CTA « Demander une estimation » ou « Nous écrire »
4. THE Site_Vitrine SHALL maintenir un ton sobre et concret sans surpromettre sur les capacités

---

### Requirement 3: Page Réalisations (Portfolio)

**User Story:** As a prospect, I want to voir des exemples de projets réalisés par TUS, so that I can évaluer la qualité du travail de l'agence.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page Réalisations, THE Site_Vitrine SHALL afficher entre 2 et 4 démonstrations de projets
2. WHEN un projet est affiché, THE Site_Vitrine SHALL présenter une fiche courte avec objectif, solution et résultat
3. WHEN un visiteur souhaite filtrer les réalisations, THE Site_Vitrine SHALL permettre un filtrage par type (Vitrine, Commerce, Système) via HTMX
4. WHEN un visiteur clique sur un projet, THE Site_Vitrine SHALL afficher les détails (contexte, fonctionnalités, stack technique, captures)
5. THE Site_Vitrine SHALL proposer des CTA « Voir un exemple » et « Nous écrire »

---

### Requirement 4: Page Méthode

**User Story:** As a prospect, I want to comprendre le processus de travail de TUS, so that I can avoir confiance dans la rigueur de l'agence.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page Méthode, THE Site_Vitrine SHALL présenter le processus en 5 étapes : Cadrage, Conception, Développement, QA, Déploiement
2. WHEN une étape est affichée, THE Site_Vitrine SHALL décrire les livrables associés (passation, documentation)
3. THE Site_Vitrine SHALL proposer un CTA « Télécharger la checklist projet » vers la page Ressources
4. THE Site_Vitrine SHALL proposer un CTA « Poser une question » vers le formulaire de contact

---

### Requirement 5: Page Contact avec Formulaire Intelligent

**User Story:** As a prospect, I want to contacter TUS facilement avec un formulaire adapté à mon type de projet, so that I can initier une collaboration.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page Contact, THE Formulaire_Intelligent SHALL afficher les champs de base : Nom, Email, Type de projet, Message
2. WHEN un visiteur sélectionne un type de projet (Vitrine, E-commerce, Plateforme), THE Formulaire_Intelligent SHALL adapter dynamiquement les champs affichés via HTMX
3. WHEN un visiteur remplit le formulaire, THE Formulaire_Intelligent SHALL permettre d'ajouter optionnellement : Budget indicatif, Lien existant, Pièce jointe
4. WHEN un visiteur soumet le formulaire avec des données valides, THE Site_Vitrine SHALL envoyer un email de confirmation au visiteur
5. WHEN un formulaire est soumis, THE Site_Vitrine SHALL envoyer une notification email à l'administrateur TUS
6. WHEN un visiteur tente de soumettre un formulaire invalide, THE Formulaire_Intelligent SHALL afficher des messages d'erreur clairs avec focus rings bleus
7. IF un spam est détecté via honeypot ou rate limiting, THEN THE Formulaire_Intelligent SHALL rejeter la soumission silencieusement
8. WHEN une pièce jointe est uploadée, THE Site_Vitrine SHALL valider le type de fichier (PDF, DOC, DOCX) et la taille maximale (5 Mo)

---

### Requirement 6: Page Ressources

**User Story:** As a prospect, I want to télécharger des ressources utiles pour préparer mon projet, so that I can mieux cadrer mes besoins avant de contacter TUS.

#### Acceptance Criteria

1. WHEN un visiteur accède à la page Ressources, THE Site_Vitrine SHALL afficher la « Checklist projet web premium » en téléchargement PDF
2. WHEN un visiteur accède à la page Ressources, THE Site_Vitrine SHALL afficher le « Modèle de cahier des charges » en téléchargement PDF
3. WHEN un visiteur clique sur un bouton de téléchargement, THE Site_Vitrine SHALL servir le fichier PDF correspondant
4. THE Site_Vitrine SHALL proposer des CTA « Télécharger la checklist » et « Télécharger le modèle de cahier des charges »

---

### Requirement 7: Navigation et Structure

**User Story:** As a visiteur, I want to naviguer facilement entre les pages du site, so that I can trouver rapidement l'information recherchée.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL afficher un menu de navigation avec les liens : Accueil, Services, Réalisations, Méthode, Contact, Ressources
2. THE Site_Vitrine SHALL afficher un footer avec liens rapides, mentions légales et politique de confidentialité
3. WHEN un visiteur navigue sur mobile, THE Site_Vitrine SHALL adapter la navigation en menu responsive
4. WHEN un visiteur utilise le clavier pour naviguer, THE Site_Vitrine SHALL afficher un focus visible sur les éléments interactifs
5. THE Site_Vitrine SHALL utiliser des URL propres et lisibles pour chaque page

---

### Requirement 8: Design System TUS

**User Story:** As a développeur, I want to disposer d'un design system cohérent, so that I can maintenir une identité visuelle uniforme sur tout le site.

#### Acceptance Criteria

1. THE Design_System SHALL définir les couleurs officielles : Noir profond #07080A, Blanc profond #F6F7FB, Bleu accent #0B2DFF
2. THE Design_System SHALL limiter l'utilisation du bleu accent à 10-15% maximum de la surface visuelle
3. THE Design_System SHALL utiliser Space Grotesk (600-700) pour les titres et Inter (400-500) pour le texte
4. THE Design_System SHALL définir des boutons : primary (bleu), secondary (outline), ghost
5. THE Design_System SHALL définir des cartes avec fond sombre, bordure fine et hover discret
6. THE Design_System SHALL utiliser des animations de durée 150-280ms avec courbe cubic-bezier(0.2, 0.8, 0.2, 1)
7. THE Design_System SHALL appliquer des effets fade + slide léger (8-12px) sans bounce agressif

---

### Requirement 9: Logo et Identité Visuelle

**User Story:** As a visiteur, I want to identifier clairement la marque TUS via son logo, so that I can mémoriser l'identité de l'agence.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL afficher le logo wordmark TUS avec trait d'union signature (dégradé bleu → blanc) dans la navbar
2. THE Site_Vitrine SHALL disposer de variantes logo : navbar (fond sombre), documents (fond blanc), print-safe monochrome
3. WHEN le logo est affiché sur fond sombre, THE Site_Vitrine SHALL utiliser un dégradé plus prononcé et trait plus épais
4. WHEN le logo est utilisé pour documents, THE Site_Vitrine SHALL utiliser texte noir avec trait dégradé visible

---

### Requirement 10: Performance et Optimisation

**User Story:** As a visiteur, I want to charger le site rapidement, so that I can consulter le contenu sans attente frustrante.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL optimiser les images (compression, formats modernes)
2. THE Site_Vitrine SHALL implémenter le lazy loading pour les images hors viewport
3. THE Site_Vitrine SHALL charger les fonts avec preconnect et display=swap
4. THE Site_Vitrine SHALL minimiser le JavaScript (HTMX + vanilla JS léger uniquement)
5. THE Site_Vitrine SHALL implémenter un système de cache approprié

---

### Requirement 11: SEO Technique

**User Story:** As a propriétaire du site, I want to optimiser le référencement naturel, so that I can améliorer la visibilité de TUS sur les moteurs de recherche.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL définir des balises title et meta description uniques par page
2. THE Site_Vitrine SHALL générer un fichier sitemap.xml valide
3. THE Site_Vitrine SHALL générer un fichier robots.txt approprié
4. THE Site_Vitrine SHALL implémenter les balises OpenGraph pour la prévisualisation sur réseaux sociaux
5. THE Site_Vitrine SHALL implémenter des données structurées Schema.org (Organisation/LocalBusiness)

---

### Requirement 12: Sécurité

**User Story:** As a administrateur, I want to protéger le site contre les attaques courantes, so that I can garantir la sécurité des données et du service.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL implémenter la protection CSRF sur tous les formulaires
2. THE Site_Vitrine SHALL configurer des sessions sécurisées
3. THE Site_Vitrine SHALL configurer les headers de sécurité (SECURE_*, HSTS en production)
4. THE Site_Vitrine SHALL implémenter une protection anti-spam (honeypot + rate limiting) sur le formulaire de contact
5. WHEN un fichier est uploadé, THE Site_Vitrine SHALL valider le type MIME et la taille du fichier

---

### Requirement 13: Pages Légales et RGPD

**User Story:** As a visiteur, I want to consulter les informations légales et la politique de confidentialité, so that I can comprendre comment mes données sont traitées.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL afficher une page Mentions Légales accessible depuis le footer
2. THE Site_Vitrine SHALL afficher une page Politique de Confidentialité accessible depuis le footer
3. IF des cookies analytics sont utilisés, THEN THE Site_Vitrine SHALL afficher un bandeau de consentement cookies
4. THE Site_Vitrine SHALL informer les utilisateurs du délai de réponse attendu (24-48h ouvrées) sur la page Contact

---

### Requirement 14: Accessibilité

**User Story:** As a utilisateur avec handicap, I want to naviguer sur le site de manière accessible, so that I can consulter le contenu sans barrière.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL maintenir un contraste élevé sur fond noir (#07080A)
2. THE Site_Vitrine SHALL utiliser une taille de texte minimale de 16-18px
3. THE Site_Vitrine SHALL afficher un focus visible pour la navigation clavier
4. THE Site_Vitrine SHALL utiliser des labels explicites sur tous les champs de formulaire
5. THE Site_Vitrine SHALL utiliser des attributs ARIA appropriés pour les éléments interactifs

---

### Requirement 15: Architecture Django

**User Story:** As a développeur, I want to disposer d'une architecture Django claire et modulaire, so that I can maintenir et faire évoluer le site facilement.

#### Acceptance Criteria

1. THE Site_Vitrine SHALL organiser le code en apps Django distinctes : pages, portfolio, leads, resources
2. THE Site_Vitrine SHALL utiliser des templates modulaires avec partials réutilisables (navbar, footer, cards, forms)
3. THE Site_Vitrine SHALL définir des endpoints HTMX dédiés pour les fragments et les pages complètes
4. THE Site_Vitrine SHALL utiliser SQLite en développement et PostgreSQL en production
5. THE Site_Vitrine SHALL fournir un README de déploiement (local + production)
