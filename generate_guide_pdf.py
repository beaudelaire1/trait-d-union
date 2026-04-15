"""Génère le Guide Diagnostic Client TUS en PDF via WeasyPrint."""
from weasyprint import HTML

html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 2cm 2.2cm;
    @bottom-center {
      content: "Trait d'Union Studio — Guide Diagnostic Client";
      font-size: 8pt;
      color: #6B7280;
      font-family: 'Segoe UI', sans-serif;
    }
    @bottom-right {
      content: counter(page) " / " counter(pages);
      font-size: 8pt;
      color: #6B7280;
      font-family: 'Segoe UI', sans-serif;
    }
  }
  @page :first { @bottom-center { content: none; } @bottom-right { content: none; } }

  * { box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', 'Calibri', sans-serif;
    font-size: 10pt;
    color: #07080A;
    line-height: 1.55;
  }
  h1 { font-size: 18pt; color: #0B2DFF; border-bottom: 2px solid #0B2DFF; padding-bottom: 4px; margin-top: 28px; page-break-after: avoid; }
  h2 { font-size: 14pt; color: #0B2DFF; margin-top: 20px; page-break-after: avoid; }
  h3 { font-size: 11.5pt; color: #07080A; margin-top: 14px; page-break-after: avoid; }
  h4 { font-size: 10.5pt; color: #07080A; margin-top: 10px; }

  table { width: 100%; border-collapse: collapse; margin: 10px 0 14px 0; font-size: 9pt; }
  th { background: #0B2DFF; color: #fff; text-align: left; padding: 6px 8px; font-weight: 600; }
  td { padding: 5px 8px; border-bottom: 1px solid #E5E7EB; vertical-align: top; }
  tr:nth-child(even) td { background: #F0F4FF; }

  .checklist { list-style: none; padding-left: 0; margin: 6px 0; }
  .checklist li { padding: 2px 0; font-size: 9.5pt; }
  .checklist li::before { content: "☐  "; font-size: 11pt; }

  .quote { margin: 10px 0; padding: 8px 14px; border-left: 3px solid #0B2DFF; background: #F0F4FF; font-style: italic; color: #374151; font-size: 9.5pt; }

  .cover { text-align: center; padding-top: 160px; page-break-after: always; }
  .cover .studio { font-size: 13pt; color: #0B2DFF; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
  .cover .title { font-size: 28pt; color: #07080A; font-weight: 700; margin: 24px 0 12px 0; line-height: 1.2; }
  .cover .subtitle { font-size: 11.5pt; color: #6B7280; line-height: 1.5; }
  .cover .date { font-size: 10.5pt; color: #0B2DFF; margin-top: 40px; }
  .cover .duration { font-size: 9.5pt; color: #6B7280; margin-top: 6px; }

  .toc { page-break-after: always; }
  .toc h1 { border: none; }
  .toc ol { font-size: 11pt; line-height: 2; }
  .toc ol li { color: #07080A; }

  .page-break { page-break-before: always; }

  .badge-red { display: inline-block; background: #FEE2E2; color: #DC2626; padding: 1px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 600; }
  .badge-orange { display: inline-block; background: #FFEDD5; color: #EA580C; padding: 1px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 600; }
  .badge-yellow { display: inline-block; background: #FEF9C3; color: #A16207; padding: 1px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 600; }
  .badge-green { display: inline-block; background: #DCFCE7; color: #16A34A; padding: 1px 8px; border-radius: 4px; font-size: 8.5pt; font-weight: 600; }

  .field-line { font-family: 'Consolas', 'Courier New', monospace; font-size: 8.5pt; margin: 2px 0; }
  .section-label { font-weight: 700; color: #0B2DFF; font-size: 10pt; margin-top: 10px; }
  .score-final { font-size: 16pt; font-weight: 700; color: #0B2DFF; text-align: center; margin-top: 14px; }

  strong { font-weight: 600; }
  .small { font-size: 9pt; color: #6B7280; }
</style>
</head>
<body>

<!-- ═══════════════ PAGE DE GARDE ═══════════════ -->
<div class="cover">
  <div class="studio">Trait d'Union Studio</div>
  <div class="title">Guide de Diagnostic Client</div>
  <div class="subtitle">Protocole opérationnel pour réaliser un diagnostic complet<br>de l'activité et/ou du site web d'un client</div>
  <div class="date">Avril 2026</div>
  <div class="duration">Durée estimée : 2 à 4 heures (complet) · 1 heure (ciblé)</div>
</div>

<!-- ═══════════════ TABLE DES MATIÈRES ═══════════════ -->
<div class="toc">
  <h1>Table des matières</h1>
  <ol>
    <li>Phase 0 — Prise de contact &amp; qualification</li>
    <li>Phase 1 — Entretien de découverte</li>
    <li>Phase 2 — Diagnostic Activité (les 29 simulateurs TUS)</li>
    <li>Phase 3 — Diagnostic Site Web (sans accès au code source)</li>
    <li>Phase 4 — Synthèse &amp; scoring</li>
    <li>Phase 5 — Livrable &amp; proposition</li>
    <li>Annexes — Outils externes &amp; checklist terrain</li>
  </ol>
</div>

<!-- ═══════════════ PHASE 0 ═══════════════ -->
<h1>Phase 0 — Prise de contact &amp; qualification</h1>
<p>Avant tout diagnostic, qualifier le besoin du client :</p>
<table>
  <tr><th>Question</th><th>Pourquoi</th></tr>
  <tr><td>Quel est votre secteur d'activité ?</td><td>Adapter les simulateurs pertinents</td></tr>
  <tr><td>Avez-vous un site web existant ? Si oui, l'URL ?</td><td>Savoir si on fait un diagnostic site en plus</td></tr>
  <tr><td>Sur quelle plateforme est-il construit ? (WordPress, Wix, Shopify, sur-mesure…)</td><td>Adapter les outils d'analyse</td></tr>
  <tr><td>Quel est votre objectif principal ? (plus de clients, mieux structurer, refondre le site…)</td><td>Cadrer le périmètre du diagnostic</td></tr>
  <tr><td>Depuis combien de temps l'activité existe-t-elle ?</td><td>Contextualiser les chiffres</td></tr>
  <tr><td>Êtes-vous seul ou avez-vous une équipe ?</td><td>Impact sur les simulateurs RH/délégation</td></tr>
</table>
<p><strong>Résultat :</strong> on sait si on fait un diagnostic activité, un diagnostic site, ou les deux.</p>

<!-- ═══════════════ PHASE 1 ═══════════════ -->
<div class="page-break"></div>
<h1>Phase 1 — Entretien de découverte</h1>
<p>Entretien structuré de <strong>30 à 45 minutes</strong> avec le client. Ne pas envoyer de questionnaire froid — c'est une conversation qui fait partie de l'expérience TUS.</p>

<h2>Données à recueillir — Activité</h2>
<table>
  <tr><th>Donnée</th><th>Exemple</th><th>Utilisée dans</th></tr>
  <tr><td>CA mensuel moyen</td><td>12 000 €</td><td>Seuil de rentabilité, Atterrissage, Plafond</td></tr>
  <tr><td>Charges fixes mensuelles</td><td>6 500 €</td><td>Seuil de rentabilité, Couverture CF</td></tr>
  <tr><td>Charges variables (% du CA)</td><td>25%</td><td>Seuil de rentabilité, Mix produits</td></tr>
  <tr><td>Nombre de clients actifs</td><td>18</td><td>Dépendance commerciale, Jumeaux clients</td></tr>
  <tr><td>Panier moyen</td><td>650 €</td><td>CAC, Élasticité-prix, Prix psychologique</td></tr>
  <tr><td>Devis envoyés / mois</td><td>8</td><td>Taux de conversion</td></tr>
  <tr><td>Devis signés / mois</td><td>3</td><td>Taux de conversion</td></tr>
  <tr><td>Budget marketing mensuel</td><td>400 €</td><td>CAC, ROI marketing</td></tr>
  <tr><td>Nouveaux clients / mois</td><td>2</td><td>CAC, Rétention</td></tr>
  <tr><td>Délai moyen paiement client</td><td>38 jours</td><td>DSO / trésorerie</td></tr>
  <tr><td>% CA récurrent vs ponctuel</td><td>30/70</td><td>Stabilité du modèle</td></tr>
  <tr><td>Heures travaillées / semaine</td><td>55h</td><td>Capacité facturable</td></tr>
  <tr><td>Heures facturées / semaine</td><td>25h</td><td>Capacité facturable</td></tr>
  <tr><td>Nombre d'outils SaaS</td><td>12</td><td>Fragmentation</td></tr>
  <tr><td>Part du plus gros client</td><td>40%</td><td>Dépendance commerciale</td></tr>
  <tr><td>Nombre de prestations différentes</td><td>6</td><td>Mix produits, Corrélation</td></tr>
  <tr><td>Effectif</td><td>3</td><td>Seuil de délégation</td></tr>
  <tr><td>Saisonnalité perçue</td><td>"creux janv-fév"</td><td>Saisonnalité</td></tr>
</table>

<h2>Données à recueillir — Site web</h2>
<table>
  <tr><th>Donnée</th><th>À demander au client</th></tr>
  <tr><td>URL du site</td><td>www.exemple.gf</td></tr>
  <tr><td>Objectif du site</td><td>Vitrine ? Prise de RDV ? Vente en ligne ?</td></tr>
  <tr><td>Qui l'a construit et quand ?</td><td>Agence, freelance, lui-même</td></tr>
  <tr><td>Google Analytics / Search Console ?</td><td>Si oui, accès lecteur possible ?</td></tr>
  <tr><td>Nombre de visiteurs / mois</td><td>Approximation OK</td></tr>
  <tr><td>D'où viennent ses clients ?</td><td>Bouche à oreille, Google, réseaux…</td></tr>
  <tr><td>Publicité en ligne déjà faite ?</td><td>Google Ads, Facebook Ads, etc.</td></tr>
  <tr><td>Concurrents directs ?</td><td>URL si possible pour benchmark</td></tr>
</table>

<!-- ═══════════════ PHASE 2 ═══════════════ -->
<div class="page-break"></div>
<h1>Phase 2 — Diagnostic Activité</h1>

<h2>Les 6 indicateurs vitaux</h2>
<p>Avant de lancer les simulateurs, poser les <strong>6 KPIs de santé</strong> qui forment le socle du diagnostic :</p>
<table>
  <tr><th>#</th><th>Indicateur</th><th>Calcul rapide</th><th>Zone danger</th></tr>
  <tr><td>1</td><td><strong>Trésorerie prévisionnelle à 30j</strong></td><td>Solde actuel + encaissements attendus − décaissements certains</td><td>Négatif</td></tr>
  <tr><td>2</td><td><strong>DSO</strong> (délai paiement client)</td><td>(Créances clients / CA) × 30</td><td>&gt; 45 jours</td></tr>
  <tr><td>3</td><td><strong>Taux de marge brute</strong></td><td>(CA − coûts directs) / CA</td><td>En baisse sur 2 mois</td></tr>
  <tr><td>4</td><td><strong>Taux de conversion</strong></td><td>Devis signés / devis envoyés</td><td>&lt; 25%</td></tr>
  <tr><td>5</td><td><strong>Répartition CA récurrent / ponctuel</strong></td><td>% de CA sous contrat ou récurrent</td><td>&lt; 20% récurrent</td></tr>
  <tr><td>6</td><td><strong>Couverture charges fixes</strong></td><td>Charges fixes / marge brute</td><td>&gt; 85%</td></tr>
</table>

<h2>Règle des signaux simultanés</h2>
<table>
  <tr><th>Situation</th><th>Niveau</th><th>Action</th></tr>
  <tr><td>1 indicateur en zone danger</td><td>⚠️ Avertissement</td><td>Surveiller, mentionner dans le rapport</td></tr>
  <tr><td>2 indicateurs simultanément dégradés</td><td>🚨 Alerte</td><td>Recommandation d'action prioritaire</td></tr>
  <tr><td>3+ indicateurs dégradés</td><td>🚨🚨🚨 Urgence</td><td>Réunion stratégique proposée dans la semaine</td></tr>
</table>

<h2>Sélection des simulateurs selon le profil</h2>
<p>Ne pas utiliser les 29 simulateurs pour chaque client. Sélectionner les <strong>8 à 12 plus pertinents</strong> selon le profil.</p>

<h3>Profil A — TPE solo / freelance</h3>
<table>
  <tr><th>Simulateur TUS</th><th>Ce qu'on cherche</th></tr>
  <tr><td>Seuil de Rentabilité</td><td>Quel CA minimum pour couvrir les charges ?</td></tr>
  <tr><td>Capacité Maximale Facturable</td><td>Combien peut-il facturer au max avec ses heures dispo ?</td></tr>
  <tr><td>Plafond de Verre</td><td>À quel CA l'activité va plafonner structurellement ?</td></tr>
  <tr><td>Friction Opérationnelle</td><td>Combien coûtent le chaos et les processus cassés ?</td></tr>
  <tr><td>Indice de Fragmentation</td><td>Trop d'outils SaaS ? Lesquels éliminer ?</td></tr>
  <tr><td>Élasticité-Prix</td><td>Peut-il augmenter ses tarifs sans perdre de clients ?</td></tr>
  <tr><td>Prix Psychologique</td><td>Où se situe le prix perçu comme « juste » ?</td></tr>
  <tr><td>Coût d'Inaction</td><td>Combien coûte le fait de ne rien changer ?</td></tr>
  <tr><td>Vallée de la Mort</td><td>Est-il dans une phase critique de croissance ?</td></tr>
</table>

<h3>Profil B — PME 3-15 personnes</h3>
<table>
  <tr><th>Simulateur TUS</th><th>Ce qu'on cherche</th></tr>
  <tr><td>Seuil de Rentabilité</td><td>Point mort mensuel</td></tr>
  <tr><td>Atterrissage Trimestriel / Annuel</td><td>Va-t-on atteindre l'objectif ?</td></tr>
  <tr><td>Atterrissage Mensuel Trésorerie</td><td>Tension de trésorerie imminente ?</td></tr>
  <tr><td>Radar de Dépendance Commerciale</td><td>Un client représente trop du CA ?</td></tr>
  <tr><td>Seuil de Délégation</td><td>Faut-il embaucher ou externaliser ?</td></tr>
  <tr><td>Optimiseur de Mix Produits</td><td>Quelle prestation prioriser ?</td></tr>
  <tr><td>Jumeaux Clients</td><td>Quels segments clients sont les plus rentables ?</td></tr>
  <tr><td>Corrélation Produits/Services</td><td>Quels produits s'achètent ensemble ?</td></tr>
  <tr><td>Impact Saisonnalité</td><td>Comment lisser les creux d'activité ?</td></tr>
  <tr><td>Coût de la Non-Qualité</td><td>Combien coûtent retours, SAV, erreurs ?</td></tr>
  <tr><td>Matrice Effort / Impact</td><td>Quels projets lancer en priorité ?</td></tr>
</table>

<h3>Profil C — Entreprise en réflexion stratégique</h3>
<table>
  <tr><th>Simulateur TUS</th><th>Ce qu'on cherche</th></tr>
  <tr><td>Scénario Pivot</td><td>Et si on changeait de modèle ?</td></tr>
  <tr><td>Taille de Marché Accessible</td><td>Le marché local est-il assez grand ?</td></tr>
  <tr><td>Valeur de Sortie</td><td>Combien vaut l'entreprise aujourd'hui ?</td></tr>
  <tr><td>Pricing par Paliers</td><td>Comment structurer l'offre en gammes ?</td></tr>
  <tr><td>Vulnérabilité Fournisseur</td><td>Dépendance critique à un fournisseur ?</td></tr>
  <tr><td>ROI Campagne Marketing</td><td>Les pubs ont-elles rapporté ?</td></tr>
  <tr><td>Vrai Coût d'une Promotion</td><td>Ce -20%, ça coûte combien vraiment ?</td></tr>
</table>

<h3>Liste complète des 29 simulateurs TUS</h3>
<p><strong>Outils historiques (9)</strong></p>
<ol>
  <li>Seuil de Rentabilité (Point Mort)</li>
  <li>Coût d'Acquisition (CAC)</li>
  <li>Friction Opérationnelle</li>
  <li>Indice de Fragmentation</li>
  <li>Flux A.C.S.E</li>
  <li>Plafond de Verre</li>
  <li>Élasticité-Prix</li>
  <li>Vallée de la Mort</li>
  <li>Effet Rétention</li>
</ol>
<p><strong>Nouveaux outils (20)</strong></p>
<ol start="10">
  <li>Optimiseur de Mix Produits/Services</li>
  <li>Atterrissage Trimestriel / Annuel</li>
  <li>Atterrissage Mensuel Trésorerie</li>
  <li>Simulateur de Jumeaux Clients</li>
  <li>Corrélation Produits/Services</li>
  <li>Seuil de Délégation</li>
  <li>Prix Psychologique</li>
  <li>Radar de Dépendance Commerciale</li>
  <li>Capacité Maximale Facturable</li>
  <li>Impact Saisonnalité</li>
  <li>Vrai Coût d'une Promotion</li>
  <li>Valeur de Sortie</li>
  <li>Matrice Effort / Impact</li>
  <li>Coût d'Inaction</li>
  <li>Scénario Pivot</li>
  <li>ROI Campagne Marketing</li>
  <li>Pricing par Paliers</li>
  <li>Taille de Marché Accessible</li>
  <li>Vulnérabilité Fournisseur</li>
  <li>Coût de la Non-Qualité</li>
</ol>

<!-- ═══════════════ PHASE 3 ═══════════════ -->
<div class="page-break"></div>
<h1>Phase 3 — Diagnostic Site Web (sans accès au code source)</h1>
<p><strong>Prérequis :</strong> uniquement l'URL du site. Aucun accès au code source nécessaire.</p>

<h2>3.1 — Performance &amp; Vitesse</h2>
<table>
  <tr><th>Outil</th><th>URL</th><th>Gratuit</th><th>Ce qu'on mesure</th></tr>
  <tr><td>Google PageSpeed Insights</td><td>pagespeed.web.dev</td><td>✅</td><td>Core Web Vitals : LCP, INP, CLS — scores mobile et desktop</td></tr>
  <tr><td>GTmetrix</td><td>gtmetrix.com</td><td>✅</td><td>Temps de chargement complet, waterfall, recommandations</td></tr>
  <tr><td>WebPageTest</td><td>webpagetest.org</td><td>✅</td><td>TTFB, First Byte, Speed Index, comparaison multi-emplacements</td></tr>
  <tr><td>Pingdom Tools</td><td>tools.pingdom.com</td><td>✅</td><td>Temps de réponse, taille de la page, nombre de requêtes</td></tr>
</table>

<p><strong>Points à noter dans le rapport :</strong></p>
<ul class="checklist">
  <li>Score PageSpeed Mobile (objectif : &gt; 70)</li>
  <li>Score PageSpeed Desktop (objectif : &gt; 85)</li>
  <li>LCP — Largest Contentful Paint (objectif : &lt; 2.5s)</li>
  <li>INP — Interaction to Next Paint (objectif : &lt; 200ms)</li>
  <li>CLS — Cumulative Layout Shift (objectif : &lt; 0.1)</li>
  <li>TTFB — Time To First Byte (objectif : &lt; 800ms)</li>
  <li>Poids total de la page (objectif : &lt; 3 Mo)</li>
  <li>Nombre de requêtes HTTP (objectif : &lt; 50)</li>
  <li>Images non optimisées (format, compression, dimensions)</li>
  <li>Cache navigateur configuré ?</li>
  <li>Compression GZIP/Brotli activée ?</li>
</ul>

<h2>3.2 — SEO (Référencement naturel)</h2>
<table>
  <tr><th>Outil</th><th>URL</th><th>Gratuit</th><th>Ce qu'on mesure</th></tr>
  <tr><td>Google Search Console</td><td>search.google.com/search-console</td><td>✅ (accès client)</td><td>Indexation, erreurs de crawl, requêtes, position</td></tr>
  <tr><td>Screaming Frog SEO Spider</td><td>screamingfrog.co.uk</td><td>✅ &lt; 500 URLs</td><td>Crawl complet : titres, méta, H1, liens cassés, redirections</td></tr>
  <tr><td>Ahrefs Webmaster Tools</td><td>ahrefs.com/webmaster-tools</td><td>✅</td><td>Backlinks, domaines référents, santé technique</td></tr>
  <tr><td>Ubersuggest</td><td>neilpatel.com/ubersuggest</td><td>Freemium</td><td>Volume de recherche, mots-clés positionnés, audit SEO</td></tr>
  <tr><td>Rich Results Test</td><td>search.google.com/test/rich-results</td><td>✅</td><td>Données structurées (schema.org)</td></tr>
</table>

<p><strong>Points à noter dans le rapport :</strong></p>
<ul class="checklist">
  <li>Le site est-il indexé par Google ? (site:domaine.com)</li>
  <li>Nombre de pages indexées vs nombre de pages réelles</li>
  <li>Chaque page a-t-elle un &lt;title&gt; unique et pertinent ? (&lt; 60 car.)</li>
  <li>Chaque page a-t-elle une &lt;meta description&gt; unique ? (&lt; 160 car.)</li>
  <li>Structure des titres correcte ? (un seul H1 par page, hiérarchie H2 &gt; H3)</li>
  <li>Images avec attribut alt renseigné ?</li>
  <li>URLs propres et lisibles ? (pas de ?p=123)</li>
  <li>Sitemap XML présent et soumis ?</li>
  <li>Fichier robots.txt présent et correct ?</li>
  <li>Liens internes cohérents ? Liens cassés (404) ?</li>
  <li>Redirections 301 en place si refonte précédente ?</li>
  <li>Données structurées (LocalBusiness, FAQ, Breadcrumb…) ?</li>
  <li>Mobile-first indexing OK ?</li>
</ul>

<h2>3.3 — Sécurité (sans accès au code)</h2>
<table>
  <tr><th>Outil</th><th>URL</th><th>Gratuit</th><th>Ce qu'on vérifie</th></tr>
  <tr><td>SSL Labs</td><td>ssllabs.com/ssltest</td><td>✅</td><td>Certificat HTTPS, configuration TLS, note A à F</td></tr>
  <tr><td>Security Headers</td><td>securityheaders.com</td><td>✅</td><td>En-têtes HTTP (CSP, HSTS, X-Frame-Options…)</td></tr>
  <tr><td>Mozilla Observatory</td><td>observatory.mozilla.org</td><td>✅</td><td>Score de sécurité global, bonnes pratiques</td></tr>
  <tr><td>Sucuri SiteCheck</td><td>sitecheck.sucuri.net</td><td>✅</td><td>Malware, blacklist, CMS obsolète</td></tr>
  <tr><td>WPScan (si WordPress)</td><td>wpscan.com</td><td>Freemium</td><td>Vulnérabilités plugins/thème, version WP exposée</td></tr>
</table>

<p><strong>Points à noter dans le rapport :</strong></p>
<ul class="checklist">
  <li>HTTPS actif ? Certificat valide et non expiré ?</li>
  <li>Note SSL Labs (objectif : A ou A+)</li>
  <li>Redirection HTTP → HTTPS en place ?</li>
  <li>En-tête HSTS activé ?</li>
  <li>En-tête Content-Security-Policy présent ?</li>
  <li>En-tête X-Frame-Options présent ?</li>
  <li>En-tête X-Content-Type-Options présent ?</li>
  <li>Version du CMS exposée publiquement ? (risque si non à jour)</li>
  <li>Plugins/extensions avec vulnérabilités connues ?</li>
  <li>Page de login par défaut accessible ? (/wp-admin, /wp-login.php)</li>
  <li>Fichiers sensibles accessibles ? (/readme.html, /xmlrpc.php, /.env)</li>
  <li>Le site est-il sur des listes noires ?</li>
</ul>

<h2>3.4 — Accessibilité (WCAG)</h2>
<table>
  <tr><th>Outil</th><th>URL</th><th>Gratuit</th><th>Ce qu'on mesure</th></tr>
  <tr><td>WAVE</td><td>wave.webaim.org</td><td>✅</td><td>Erreurs et alertes WCAG, contrastes, ARIA</td></tr>
  <tr><td>axe DevTools</td><td>Extension Chrome/Firefox</td><td>✅</td><td>Audit WCAG automatisé, violations par gravité</td></tr>
  <tr><td>Lighthouse</td><td>Chrome DevTools (F12)</td><td>✅</td><td>Score accessibilité, bonnes pratiques</td></tr>
  <tr><td>Contrast Checker</td><td>webaim.org/resources/contrastchecker</td><td>✅</td><td>Ratio de contraste texte/fond</td></tr>
</table>

<p><strong>Points à noter dans le rapport :</strong></p>
<ul class="checklist">
  <li>Score Lighthouse Accessibilité (objectif : &gt; 85)</li>
  <li>Nombre d'erreurs WAVE (objectif : 0 erreur critique)</li>
  <li>Navigation au clavier fonctionnelle ? (Tab, Enter, Escape)</li>
  <li>Focus visible sur les éléments interactifs ?</li>
  <li>Contrastes texte/fond suffisants ? (ratio 4.5:1 minimum)</li>
  <li>Textes alternatifs sur toutes les images ?</li>
  <li>Formulaires avec labels associés ?</li>
  <li>Langue de la page déclarée (&lt;html lang="fr"&gt;) ?</li>
  <li>Hiérarchie des titres logique ?</li>
</ul>

<h2>3.5 — Mobile &amp; Responsive</h2>
<table>
  <tr><th>Outil</th><th>URL</th><th>Gratuit</th><th>Ce qu'on mesure</th></tr>
  <tr><td>Google Mobile-Friendly Test</td><td>search.google.com/test/mobile-friendly</td><td>✅</td><td>Le site est-il compatible mobile ?</td></tr>
  <tr><td>Responsively App</td><td>responsively.app</td><td>✅</td><td>Prévisualisation multi-écrans simultanée</td></tr>
  <tr><td>Chrome DevTools</td><td>F12 &gt; Toggle device</td><td>✅</td><td>Simulation de résolutions</td></tr>
</table>

<p><strong>Points à noter dans le rapport :</strong></p>
<ul class="checklist">
  <li>Le site est-il responsive ? (s'adapte à toutes les tailles d'écran)</li>
  <li>Texte lisible sans zoom sur mobile ?</li>
  <li>Boutons/liens assez espacés pour le tactile ? (min 44×44 px)</li>
  <li>Pas de défilement horizontal ?</li>
  <li>Menu de navigation utilisable sur mobile ?</li>
  <li>Formulaires faciles à remplir sur mobile ?</li>
  <li>Images qui s'adaptent (pas de débordement) ?</li>
  <li>Viewport meta tag présent ?</li>
</ul>

<h2>3.6 — UX / Design / Contenu (inspection manuelle)</h2>
<p><em>Pas d'outil automatisé — c'est l'œil du professionnel qui parle.</em></p>

<h3>Première impression (test des 5 secondes)</h3>
<ul class="checklist">
  <li>En 5 secondes, comprend-on ce que fait l'entreprise ?</li>
  <li>La proposition de valeur est-elle visible immédiatement ?</li>
  <li>Le CTA principal est-il évident ?</li>
</ul>

<h3>Navigation &amp; architecture</h3>
<ul class="checklist">
  <li>Le menu est-il clair et logique ? (&lt; 7 items)</li>
  <li>Peut-on accéder à n'importe quelle page en 3 clics maximum ?</li>
  <li>Fil d'Ariane présent ?</li>
  <li>Page 404 personnalisée ?</li>
  <li>Recherche interne disponible (si &gt; 20 pages) ?</li>
</ul>

<h3>Contenu</h3>
<ul class="checklist">
  <li>Textes clairs, sans jargon, orientés bénéfice client ?</li>
  <li>Orthographe et grammaire impeccables ?</li>
  <li>Témoignages / avis clients présents ?</li>
  <li>Preuves sociales (logos clients, certifications, chiffres clés) ?</li>
  <li>Visuels de qualité professionnelle ? (pas de stock photos évidentes)</li>
  <li>Cohérence graphique (couleurs, typos, espacements) ?</li>
</ul>

<h3>Conversion</h3>
<ul class="checklist">
  <li>Combien de clics pour contacter / demander un devis ? (objectif : ≤ 2)</li>
  <li>Numéro de téléphone cliquable sur mobile ?</li>
  <li>Formulaire de contact fonctionnel et simple ? (&lt; 5 champs)</li>
  <li>CTA visibles et contrastés sur chaque page ?</li>
  <li>Réassurance présente ? (garanties, délais, processus)</li>
</ul>

<h3>Conformité légale</h3>
<ul class="checklist">
  <li>Mentions légales présentes et complètes ?</li>
  <li>Politique de confidentialité / RGPD ?</li>
  <li>Bandeau cookies conforme ?</li>
  <li>CGV si e-commerce ?</li>
</ul>

<!-- ═══════════════ PHASE 4 ═══════════════ -->
<div class="page-break"></div>
<h1>Phase 4 — Synthèse &amp; scoring</h1>

<h2>Grille de scoring du diagnostic</h2>
<table>
  <tr><th>Domaine</th><th>Poids</th><th>Note /10</th><th>Score pondéré</th></tr>
  <tr><td><strong>Santé financière</strong> (6 KPIs vitaux)</td><td>25%</td><td></td><td></td></tr>
  <tr><td><strong>Stratégie &amp; positionnement</strong> (simulateurs)</td><td>15%</td><td></td><td></td></tr>
  <tr><td><strong>Performance site</strong> (vitesse, Core Web Vitals)</td><td>15%</td><td></td><td></td></tr>
  <tr><td><strong>SEO</strong> (référencement, indexation)</td><td>15%</td><td></td><td></td></tr>
  <tr><td><strong>Sécurité</strong> (HTTPS, headers, CMS)</td><td>10%</td><td></td><td></td></tr>
  <tr><td><strong>Mobile &amp; responsive</strong></td><td>5%</td><td></td><td></td></tr>
  <tr><td><strong>Accessibilité</strong></td><td>5%</td><td></td><td></td></tr>
  <tr><td><strong>UX / Design / Contenu</strong></td><td>5%</td><td></td><td></td></tr>
  <tr><td><strong>Conformité légale</strong></td><td>5%</td><td></td><td></td></tr>
  <tr><td><strong>SCORE GLOBAL</strong></td><td><strong>100%</strong></td><td></td><td><strong>/10</strong></td></tr>
</table>

<h2>Barème de notation</h2>
<table>
  <tr><th>Note</th><th>Signification</th></tr>
  <tr><td><strong>9-10</strong></td><td>Excellent — rien à signaler, maintenir</td></tr>
  <tr><td><strong>7-8</strong></td><td>Bon — améliorations mineures possibles</td></tr>
  <tr><td><strong>5-6</strong></td><td>Passable — plusieurs points à corriger</td></tr>
  <tr><td><strong>3-4</strong></td><td>Faible — problèmes significatifs</td></tr>
  <tr><td><strong>1-2</strong></td><td>Critique — intervention urgente nécessaire</td></tr>
</table>

<h2>Classification des recommandations</h2>
<table>
  <tr><th>Priorité</th><th>Critère</th><th>Exemple</th></tr>
  <tr><td><span class="badge-red">🔴 Critique</span></td><td>Impact direct sur le CA ou la sécurité</td><td>Site non HTTPS, formulaire cassé, trésorerie négative à 30j</td></tr>
  <tr><td><span class="badge-orange">🟠 Important</span></td><td>Frein significatif à la croissance</td><td>PageSpeed &lt; 40, pas de SEO, dépendance 1 client &gt; 50%</td></tr>
  <tr><td><span class="badge-yellow">🟡 Recommandé</span></td><td>Amélioration notable</td><td>Optimiser les images, ajouter des témoignages, données structurées</td></tr>
  <tr><td><span class="badge-green">🟢 Bonus</span></td><td>Finition, différenciation</td><td>Micro-animations, données structurées avancées, A/B testing</td></tr>
</table>

<!-- ═══════════════ PHASE 5 ═══════════════ -->
<div class="page-break"></div>
<h1>Phase 5 — Livrable &amp; proposition</h1>

<h2>Structure du rapport diagnostic</h2>
<table>
  <tr><th>Section</th><th>Contenu</th></tr>
  <tr><td><strong>1. Page de garde</strong></td><td>Logo TUS + logo client, titre, date, nom du client</td></tr>
  <tr><td><strong>2. Résumé exécutif (1 page)</strong></td><td>Score global /10, les 3 forces principales, les 3 faiblesses critiques, recommandation prioritaire n°1</td></tr>
  <tr><td><strong>3. Diagnostic Activité</strong></td><td>Tableau des 6 KPIs avec voyants vert/orange/rouge, résultats des simulateurs sélectionnés, signaux d'alerte</td></tr>
  <tr><td><strong>4. Diagnostic Site Web</strong></td><td>Résultats par domaine (Performance, SEO, Sécurité…), captures d'écran annotées des problèmes, scores des outils</td></tr>
  <tr><td><strong>5. Plan d'action</strong></td><td>Actions 🔴 Critiques → 🟠 Importantes → 🟡 Recommandées → 🟢 Bonus</td></tr>
  <tr><td><strong>6. Proposition TUS</strong></td><td>Lien vers les services TUS adaptés, devis personnalisé</td></tr>
</table>

<h2>Comment présenter le rapport</h2>
<ol>
  <li><strong>Jamais par email seul</strong> — toujours en visio ou en présentiel</li>
  <li><strong>Commencer par les forces</strong> — le client doit entendre ce qui marche avant ce qui ne marche pas</li>
  <li><strong>Chiffrer l'impact</strong> — utiliser le simulateur « Coût d'Inaction » pour montrer combien l'inaction coûte</li>
  <li><strong>Proposer 3 niveaux d'intervention</strong> — essentiel / recommandé / premium</li>
</ol>

<!-- ═══════════════ ANNEXES ═══════════════ -->
<div class="page-break"></div>
<h1>Annexes</h1>

<h2>A. Checklist terrain express</h2>
<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 14px 18px; margin: 10px 0;">
  <p class="field-line"><strong>CLIENT :</strong> ________________________&nbsp;&nbsp;&nbsp;<strong>DATE :</strong> ___________&nbsp;&nbsp;&nbsp;<strong>URL :</strong> ________________________</p>

  <p class="section-label">ACTIVITÉ</p>
  <p class="field-line">☐ CA mensuel : ________&nbsp;&nbsp;☐ Charges fixes : ________&nbsp;&nbsp;☐ Marge brute : ________%</p>
  <p class="field-line">☐ Tréso prév. 30j : ________&nbsp;&nbsp;☐ DSO : ________ jours</p>
  <p class="field-line">☐ Taux conversion : ________%&nbsp;&nbsp;☐ CA récurrent : ________%&nbsp;&nbsp;☐ Couverture CF : ________%</p>
  <p class="field-line">→ Signaux simultanés : ☐ 0&nbsp;&nbsp;☐ 1 ⚠️&nbsp;&nbsp;☐ 2 🚨&nbsp;&nbsp;☐ 3+ 🚨🚨🚨</p>

  <p class="section-label">PERFORMANCE SITE</p>
  <p class="field-line">☐ PageSpeed Mobile : ___/100&nbsp;&nbsp;☐ Desktop : ___/100</p>
  <p class="field-line">☐ LCP : ___s&nbsp;&nbsp;☐ INP : ___ms&nbsp;&nbsp;☐ CLS : ___&nbsp;&nbsp;☐ TTFB : ___ms</p>
  <p class="field-line">☐ Poids page : ___ Mo&nbsp;&nbsp;☐ Requêtes : ___</p>

  <p class="section-label">SEO</p>
  <p class="field-line">☐ Indexé Google : Oui / Non&nbsp;&nbsp;☐ Pages indexées : ___</p>
  <p class="field-line">☐ Titles uniques : Oui / Non&nbsp;&nbsp;☐ Méta desc : Oui / Non</p>
  <p class="field-line">☐ H1 unique/page : Oui / Non&nbsp;&nbsp;☐ Sitemap : Oui / Non&nbsp;&nbsp;☐ Liens cassés : ___</p>

  <p class="section-label">SÉCURITÉ</p>
  <p class="field-line">☐ HTTPS : Oui / Non&nbsp;&nbsp;☐ SSL Labs : ___&nbsp;&nbsp;☐ Security Headers : ___</p>
  <p class="field-line">☐ CMS à jour : Oui / Non / N/A&nbsp;&nbsp;☐ Infos sensibles exposées : Oui / Non</p>

  <p class="section-label">ACCESSIBILITÉ</p>
  <p class="field-line">☐ Lighthouse : ___/100&nbsp;&nbsp;☐ Erreurs WAVE : ___&nbsp;&nbsp;☐ Contrastes OK : Oui / Non</p>
  <p class="field-line">☐ Navigation clavier : Oui / Non&nbsp;&nbsp;☐ lang="fr" : Oui / Non</p>

  <p class="section-label">MOBILE</p>
  <p class="field-line">☐ Mobile-friendly : Oui / Non&nbsp;&nbsp;☐ Texte lisible : Oui / Non</p>
  <p class="field-line">☐ Boutons touch OK : Oui / Non&nbsp;&nbsp;☐ Pas de scroll H : Oui / Non</p>

  <p class="section-label">UX / CONTENU</p>
  <p class="field-line">☐ Proposition valeur claire : Oui / Non&nbsp;&nbsp;☐ CTA visible : Oui / Non</p>
  <p class="field-line">☐ Contact en ≤ 2 clics : Oui / Non&nbsp;&nbsp;☐ Témoignages : Oui / Non</p>
  <p class="field-line">☐ Mentions légales : Oui / Non&nbsp;&nbsp;☐ RGPD/cookies : Oui / Non</p>

  <p class="score-final">SCORE GLOBAL : ___ / 10</p>
</div>

<h2>B. Outils externes — récapitulatif</h2>
<table>
  <tr><th>Outil</th><th>Catégorie</th><th>URL</th><th>Coût</th></tr>
  <tr><td>Google PageSpeed Insights</td><td>Performance</td><td>pagespeed.web.dev</td><td>Gratuit</td></tr>
  <tr><td>GTmetrix</td><td>Performance</td><td>gtmetrix.com</td><td>Gratuit</td></tr>
  <tr><td>WebPageTest</td><td>Performance</td><td>webpagetest.org</td><td>Gratuit</td></tr>
  <tr><td>Pingdom Tools</td><td>Performance</td><td>tools.pingdom.com</td><td>Gratuit</td></tr>
  <tr><td>Google Search Console</td><td>SEO</td><td>search.google.com/search-console</td><td>Gratuit</td></tr>
  <tr><td>Screaming Frog</td><td>SEO</td><td>screamingfrog.co.uk</td><td>Gratuit &lt; 500</td></tr>
  <tr><td>Ahrefs Webmaster Tools</td><td>SEO</td><td>ahrefs.com/webmaster-tools</td><td>Gratuit</td></tr>
  <tr><td>Ubersuggest</td><td>SEO</td><td>neilpatel.com/ubersuggest</td><td>Freemium</td></tr>
  <tr><td>Rich Results Test</td><td>SEO</td><td>search.google.com/test/rich-results</td><td>Gratuit</td></tr>
  <tr><td>SSL Labs</td><td>Sécurité</td><td>ssllabs.com/ssltest</td><td>Gratuit</td></tr>
  <tr><td>Security Headers</td><td>Sécurité</td><td>securityheaders.com</td><td>Gratuit</td></tr>
  <tr><td>Mozilla Observatory</td><td>Sécurité</td><td>observatory.mozilla.org</td><td>Gratuit</td></tr>
  <tr><td>Sucuri SiteCheck</td><td>Sécurité</td><td>sitecheck.sucuri.net</td><td>Gratuit</td></tr>
  <tr><td>WPScan</td><td>Sécurité (WP)</td><td>wpscan.com</td><td>Freemium</td></tr>
  <tr><td>WAVE</td><td>Accessibilité</td><td>wave.webaim.org</td><td>Gratuit</td></tr>
  <tr><td>axe DevTools</td><td>Accessibilité</td><td>Extension navigateur</td><td>Gratuit</td></tr>
  <tr><td>Lighthouse</td><td>Perf+Access+SEO</td><td>Chrome DevTools (F12)</td><td>Gratuit</td></tr>
  <tr><td>Contrast Checker</td><td>Accessibilité</td><td>webaim.org/resources/contrastchecker</td><td>Gratuit</td></tr>
  <tr><td>Google Mobile-Friendly</td><td>Mobile</td><td>search.google.com/test/mobile-friendly</td><td>Gratuit</td></tr>
  <tr><td>Responsively App</td><td>Mobile</td><td>responsively.app</td><td>Gratuit</td></tr>
</table>

<h2>C. Correspondance problème → simulateur TUS</h2>
<table>
  <tr><th>Problème identifié</th><th>Simulateur(s) TUS</th></tr>
  <tr><td>Ne sait pas s'il gagne de l'argent</td><td>Seuil de Rentabilité</td></tr>
  <tr><td>Dépense en pub sans savoir si ça marche</td><td>CAC + ROI Campagne Marketing</td></tr>
  <tr><td>Perd du temps dans des process manuels</td><td>Friction Opérationnelle</td></tr>
  <tr><td>15 outils SaaS qui ne communiquent pas</td><td>Indice de Fragmentation</td></tr>
  <tr><td>Ne sait pas quelle prestation prioriser</td><td>Mix Produits + Matrice Effort/Impact</td></tr>
  <tr><td>Hésite à embaucher</td><td>Seuil de Délégation</td></tr>
  <tr><td>Ne sait pas fixer ses prix</td><td>Élasticité + Prix Psycho + Pricing Paliers</td></tr>
  <tr><td>Un client = 50%+ du CA</td><td>Radar de Dépendance Commerciale</td></tr>
  <tr><td>Travaille 60h mais facture 30%</td><td>Capacité Maximale Facturable</td></tr>
  <tr><td>Creux d'activité saisonniers</td><td>Impact Saisonnalité</td></tr>
  <tr><td>Veut faire une promo mais hésite</td><td>Vrai Coût d'une Promotion</td></tr>
  <tr><td>Pense à vendre ou transmettre</td><td>Valeur de Sortie</td></tr>
  <tr><td>Plusieurs projets, ne sait pas lequel lancer</td><td>Matrice Effort / Impact</td></tr>
  <tr><td>Repousse des décisions importantes</td><td>Coût d'Inaction</td></tr>
  <tr><td>Envisage un changement de modèle</td><td>Scénario Pivot</td></tr>
  <tr><td>Veut structurer l'offre en gammes</td><td>Pricing par Paliers</td></tr>
  <tr><td>Se demande si le marché est assez grand</td><td>Taille de Marché Accessible</td></tr>
  <tr><td>Dépend d'un fournisseur unique</td><td>Vulnérabilité Fournisseur</td></tr>
  <tr><td>Beaucoup de SAV / retours / erreurs</td><td>Coût de la Non-Qualité</td></tr>
  <tr><td>Ne sait pas quels clients fidéliser</td><td>Jumeaux Clients + Effet Rétention</td></tr>
  <tr><td>Quels produits s'achètent ensemble ?</td><td>Corrélation Produits/Services</td></tr>
  <tr><td>Croissance stagne sans raison apparente</td><td>Plafond de Verre + Vallée de la Mort</td></tr>
  <tr><td>Process de vente lent / bloqué</td><td>Flux A.C.S.E</td></tr>
  <tr><td>Ne sait pas s'il atteindra l'objectif annuel</td><td>Atterrissage Trimestriel / Annuel</td></tr>
  <tr><td>Peur de ne pas passer le mois</td><td>Atterrissage Mensuel Trésorerie</td></tr>
</table>

<div style="text-align: center; margin-top: 30px; color: #6B7280; font-size: 9pt; font-style: italic;">
  Trait d'Union Studio — Avril 2026
</div>

</body>
</html>"""

output = r'c:\Users\vilme\OneDrive\Bureau\ressources_websites\trait_d_union_studio\src\GUIDE_DIAGNOSTIC_CLIENT.pdf'
HTML(string=html).write_pdf(output)
print(f'✅ PDF généré : {output}')
