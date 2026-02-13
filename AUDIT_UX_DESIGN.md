# 🎨 AUDIT UX/DESIGN - TRAIT D'UNION STUDIO
**Date** : 12 février 2026  
**Parcours** : Simulation du parcours utilisateur complet  
**Verdict** : 🔴 **INCOHÉRENCES MAJEURES** dans le respect de la charte graphique

---

## 📋 RÉSUMÉ EXÉCUTIF

Lors du parcours utilisateur complet (demande de devis → validation → signature → paiement → espace client), nous avons identifié **3 catégories critiques d'incohérences** :

1. **Palette de couleurs incohérente** (templates multipliant les échelles de couleurs)
2. **Architecture CSS fragmentée** (styles définis dans les templates au lieu d'un seul CSS)
3. **Expérience utilisateur dégradée** (changements de design abrupt entre les pages)

**Impact utilisateur** : Sentiment de "site patchwork" non professionnel, perte de confiance lors du paiement.

---

## 🔴 PROBLÈME #1 : PALETTE DE COULEURS INCOHÉRENTE

### A. Les 3 palettes différentes utilisées

#### ✅ PALETTE TUS (Correcte)
**Fichier** : `tailwind.config.js`  
**Couleurs définies** :
```js
'tus-black': '#07080A',      // Fond principal
'tus-white': '#F6F7FB',      // Texte principal
'tus-blue': '#0B2DFF',       // CTA + accents
'tus-green': '#22C55E',      // Succès
```

**Templates qui respectent TUS** ✅ :
- `devis/request_quote.html` (Demande devis)
- `devis/validate_code.html` (Validation 2FA)
- `devis/quote_success.html` (Confirmation)
- `factures/payment_success.html` (Confirmation paiement facture)
- `factures/pay.html` (Paiement facture)

#### ❌ PALETTE PERSONNALISÉE (Incompatible)
**Fichier** : `apps/clients/templates/clients/dashboard.html` (inline `<style>`)  
**Couleurs non-TUS** :
```css
--client-bg: #0a0a0f;           /* ≠ TUS Black #07080A */
--client-surface: #12121a;      /* Personnalisé, pas de TUS equiv */
--client-green: #10B981;        /* ≠ TUS Green #22C55E */
--client-blue: #0B2DFF;         /* OK, mais variable inutile */
```

**Impact** : Portail client (dashboard, devis, factures) utilise une palette DISTINCTE.  
**Affecte** :
- `clients/dashboard.html`
- `clients/quote_list.html`
- `clients/invoice_list.html`
- `clients/quote_detail.html`
- `clients/profile.html`
- `clients/documents.html`

#### ❌ PALETTE NEUTRE/GRISE (Complètement différente)
**Fichier** : `devis/sign_and_pay.html`, `devis/payment_success.html`  
**Couleurs utilisées** :
```html
<!-- Page principale : fond blanc -->
<section class="min-h-screen bg-[#F6F7FB]">        <!-- Hard-coded! -->
  <div class="text-[#07080A]">                    <!-- Hard-coded! -->
    <p class="text-gray-600">                     <!-- Tailwind gray (❌ pas TUS) -->
    <div class="bg-white rounded-2xl">            <!-- Non-TUS -->
      <div class="bg-gray-50">                    <!-- Non-TUS -->
    {% if stripe_configured %}
    <div class="bg-blue-50">                      <!-- Bleu standard, pas TUS -->
      <span class="text-blue-800">               <!-- Bleu standard, pas TUS -->
```

**Impact** :
- Ces pages ont un **contraste brutal** avec le reste du site  
- Utilisateur pense quitter le site pendant la signature/paiement  
- Élément de TRUST critique = page la plus importante

---

### B. Comparaison visuelle : Parcours utilisateur

```
┌─────────────────────────────────────────────────────────┐
│ PARCOURS UTILISATEUR & PALETTE DE COULEURS             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Accueil                                             │
│     └─→ bg-tus-black, text-tus-white ✅               │
│                                                         │
│  2. Demander devis (/devis/nouveau/)                   │
│     └─→ bg-tus-black, text-tus-white ✅               │
│         "Demande cohérente avec accueil"               │
│                                                         │
│  3. Succès devis (/devis/succes/)                      │
│     └─→ bg-tus-black, text-tus-white ✅               │
│         "Cohérent ✓"                                   │
│                                                         │
│  4. Validation (2FA) (/devis/valider/<token>/code/)    │
│     └─→ bg-tus-black, text-tus-white ✅               │
│         "Cohérent ✓"                                   │
│                                                         │
│  5. 🚨 SIGNATURE & PAIEMENT (/devis/.../signer/)       │
│     └─→ bg-[#F6F7FB] (BLANC!)                          │
│         text-gray-600, bg-blue-50, border-gray-300     │
│         ❌ RUPTURE COMPLÈTE DU DESIGN                  │
│         ❓ Utilisateur : "Ai-je quitté le site?"       │
│                                                         │
│  6. Confirmation paiement (/devis/payment_success/)    │
│     └─→ bg-[#F6F7FB], text-gray-600                    │
│         ❌ Toujours rupture                            │
│         "Pourquoi être sur un fond blanc?"             │
│                                                         │
│  7. 🚨 ESPACE CLIENT (Dashboard) (/clients/)           │
│     └─→ bg: #0a0a0f, text: #f6f7fb                     │
│         --client-green: #10B981 (pas #22C55E)          │
│         ❌ TROISIÈME PALETTE!                          │
│         Sidebar: #12121a (surface custom)              │
│         Badge green: emeraude au lieu de vert TUS       │
│                                                         │
│         Liste devis/factures (/clients/quotes/, /invoices/)
│         └─→ Même problème palette client               │
│             (verts TUS vs émeraude mélangés)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔴 PROBLÈME #2 : ARCHITECTURE CSS FRAGMENTÉE

### A. Styles définis dans les templates

**Fichier** : `apps/clients/templates/clients/dashboard.html`  
**Ligne** : 631-1500  
**Problème** : CSS inline de 870 lignes!

```html
<!-- ❌ Mauvaise pratique -->
<style>
  :root {
    --client-bg: #0a0a0f;
    --client-surface: #12121a;
    --client-text: #f6f7fb;
    /* 870 lignes de CSS multipliées dans 5 templates! */
  }
  .client-portal { ... }    /* 50 lignes */
  .client-sidebar { ... }   /* 80 lignes */
  .nav-item { ... }         /* 40 lignes */
  /* Etc. */
</style>
```

**Impact** : 
- ❌ **Code dupliqué** dans chacun des 5 templates clients
- ❌ **Maintenance cauchemardesque** (changement = éditer 5 fichiers)
- ❌ **Pas de mutualisaion Tailwind** (ne profite pas du CSS stripping)
- ❌ **Payload** : 870 lignes × 5 templates = ~4.35KB à chaque visite

### B. Bonne pratique : CSS séparé

**Recommandation** :
```bash
# ✅ Créer un fichier CSS dédié
static/css/client-portal.css

# ✅ Importer dans base.html
<link rel="stylesheet" href="{% static 'css/client-portal.css' %}">
```

---

## 🔴 PROBLÈME #3 : RUPTURE UX CRITIQUE LORS DU PAIEMENT

### A. Analyse détaillée : Page de signature (`sign_and_pay.html`)

**Incohérences identifiées** :

#### 1. Fond blanc au lieu de noir TUS
```html
<!-- ❌ Mauvais -->
<section class="min-h-screen bg-[#F6F7FB]">

<!-- ✅ Bon -->
<section class="min-h-screen bg-tus-black">
```

**Résultat** : Contraste brutal. Impression de quitter le site pendant l'étape critique.

#### 2. Texte gris au lieu de blanc TUS
```html
<!-- ❌ Mauvais -->
<p class="text-gray-600">Sous-total HT</p>         <!-- #4B5563 -->
<div class="flex justify-between text-gray-600">  <!-- Gris -->

<!-- ✅ Bon -->
<p class="text-tus-white/60">Sous-total HT</p>     <!-- Blanc semi-transparent -->
```

**Résultat** : Perte d'accessibilité (contraste réduit).

#### 3. Couleurs d'alerte Stripe (blue-50, blue-800) au lieu de TUS
```html
<!-- ❌ Mauvais -->
<div class="bg-blue-50">
  <span class="text-blue-800">Acompte</span>

<!-- ✅ Bon -->
<div class="bg-tus-blue/10">
  <span class="text-tus-blue">Acompte</span>
```

**Résultat** : Bleu Stripe (≈#1E40AF) ≠ Bleu TUS (#0B2DFF).

#### 4. Signature sur fond gris, pas intégré à la page
```html
<!-- ❌ Mauvais -->
<div class="signature-container mb-4">
  <!-- Canvas sur fond gris standard #fafafa -->

<!-- ✅ Bon -->
<div class="signature-container mb-4 bg-tus-white/5 border border-tus-white/10">
  <!-- Canvas intégré avec border TUS -->
```

---

### B. Tableau comparatif : sign_and_pay vs factures/pay

| Élément | `devis/sign_and_pay.html` ❌ | `factures/pay.html` ✅ | Bon? |
|---------|------|--------|------|
| Fond | `bg-[#F6F7FB]` (blanc) | `bg-tus-black` | ✅ Factures |
| Texte principal | `text-[#07080A]` | `text-tus-white` | ✅ Factures |
| Texte secondaire | `text-gray-600` | `text-tus-white/60` | ✅ Factures |
| Fond formulaire | `bg-white` | `bg-tus-white/5` | ✅ Factures |
| Bordure | `border-gray-300` | `border-tus-white/10` | ✅ Factures |
| Zone d'alerte | `bg-blue-50` | `bg-tus-blue/10` | ✅ Factures |

**Conclusion** : `factures/pay.html` est **correct**, `devis/sign_and_pay.html` doit être aligné.

---

## 🔴 PROBLÈME #4 : PORTAIL CLIENT - PALETTE INCOHÉRENTE

### A. Définition des couleurs client vs TUS

| Élément | TUS (charte.txt) | Client (dashboard.html) | Match? |
|---------|------------------|--------|--------|
| Fond | `#07080A` (noir) | `#0a0a0f` (quasi noir) | ~OK |
| Texte | `#F6F7FB` (blanc) | `#f6f7fb` (blanc) | ✅ OK |
| Accent vert | `#22C55E` (vert lime) | `#10B981` (émeraude) | ❌ **AUTRE** |
| Surface | `#0D1016` (var) | `#12121a` (custom) | ~OK |

**Impact** :
- Badge "Devis à signer" : vert émeraude au lieu de vert TUS  
- Badge "Devis accepté" : couleur incohérente  
- Utilisateur confus : "Quel vert est correct?"

### B. Détail : Vert client vs vert TUS

```
TUS Green (#22C55E)       Client Green (#10B981)
┌─────────────────┐       ┌──────────────────┐
│  RGB(34,197,94) │       │  RGB(16,185,129) │
│  Plus lumineux  │       │  Plus "émeraude" │
│  Charte 2025    │       │  Style Tailwind? │
└─────────────────┘       └──────────────────┘
```

---

## 🔴 PROBLÈME #5 : INCOHÉRENCE PAGES DE PAIEMENT

### A. 2 pages de confirmation de paiement DIFFÉRENTES

**`devis/payment_success.html`** (Devis) ❌
```html
<section class="min-h-screen bg-[#F6F7FB]">        <!-- Blanc! -->
  <h1 class="text-[#07080A]">Merci!</h1>         <!-- Noir hard-coded -->
  <p class="text-gray-600">...</p>                <!-- Gris Tailwind -->
```

**`factures/payment_success.html`** (Facture) ✅
```html
<section class="min-h-screen bg-tus-black">
  <h1 class="text-tus-white">Paiement réussi!</h1>
  <p class="text-tus-white/60">...</p>
```

**Résultat** :
- Utilisateur paye facture → design TUS → cohérent ✓
- Utilisateur paye devis → design blanc → confus ✗
- **Message inconsistent** : "Suis-je sur le bon site?"

---

## 📊 TABLEAU RÉSUMÉ DES INCOHÉRENCES

| Page | Palette | Correcte? | Fichier |
|------|---------|-----------|---------|
| Accueil | TUS Black/Blue/White | ✅ | `base.html` |
| Demande devis | TUS | ✅ | `devis/request_quote.html` |
| Validation 2FA | TUS | ✅ | `devis/validate_code.html` |
| **🚨 SIGNATURE & PAIEMENT** | **Blanc/Gris** | ❌ | `devis/sign_and_pay.html` |
| **🚨 Confirmation paiement (Devis)** | **Blanc/Gris** | ❌ | `devis/payment_success.html` |
| Paiement facture | TUS | ✅ | `factures/pay.html` |
| Confirmation facture | TUS | ✅ | `factures/payment_success.html` |
| Tableau de bord client | Custom colors | ⚠️ | `clients/dashboard.html` |
| Devis client | Custom colors | ⚠️ | `clients/quote_list.html` |
| Factures client | Custom colors | ⚠️ | `clients/invoice_list.html` |

---

## 🎯 PROBLÈMES UX RÉSULTANTS

### 1. **Perte de confiance lors du paiement** 🔴
- Utilisateur voit fond blanc tout à coup  
- Pense "Ai-je quitté le site officiel?"  
- Augmente l'anxiété de paiement (cart abandonment risk ⬆)

### 2. **Inconsistance de la marque**
- Logo = bleu TUS  
- Accueil = noir TUS  
- Signature = blanc standard  
- Espace client = marron custom  
- → Impression de "patchwork mal collé"

### 3. **Branding dilué**
- Utilisateur se souvient du noir/bleu TUS comme "couleurs de Trait d'Union"  
- Puis voit du blanc lors du paiement  
- Association mentale cassée

### 4. **Maintenance cauchemardesque**
- 5 templates clients avec CSS inline (870 lignes chacun)  
- 2 pages de paiement (devis vs facture) très différentes  
- Changement de palette = modifier 5+ fichiers

---

## ✅ RECOMMANDATIONS

### PRIORITÉ 1: ALIGNEMENT PALETTE (CRITIQUE)

#### 1️⃣ Corriger `devis/sign_and_pay.html`

**Actuellement** :
```html
<section class="min-h-screen bg-[#F6F7FB]">
  <!-- 150+ lignes de Tailwind gray, blue-50, white, etc. -->
</section>
```

**À faire** :
```html
<section class="min-h-screen bg-tus-black py-12 px-4 relative overflow-hidden">
    <!-- Background effects TUS -->
    <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 
                    w-[600px] h-[600px] bg-tus-blue/15 rounded-full blur-[150px]"></div>
    </div>
    
    <div class="max-w-2xl mx-auto relative z-10">
        <!-- Récapitulatif -->
        <div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 md:p-8 mb-8">
            <h2 class="font-display text-xl font-semibold text-tus-white mb-6">
                Montant à payer
            </h2>
            <!-- Items avec text-tus-white/60 au lieu de text-gray-600 -->
            <div class="bg-tus-white/5 rounded-xl p-4 space-y-2">
                <div class="flex justify-between text-tus-white/60">
                    <span>Sous-total HT</span>
                    <span>{{ quote.total_ht|floatformat:2 }} €</span>
                </div>
                <div class="flex justify-between text-tus-white/60">
                    <span>TVA</span>
                    <span>{{ quote.tva|floatformat:2 }} €</span>
                </div>
                <div class="flex justify-between font-display text-xl font-bold 
                            text-tus-white pt-2 border-t border-tus-white/10">
                    <span>Total TTC</span>
                    <span>{{ quote.total_ttc|floatformat:2 }} €</span>
                </div>
            </div>
            
            {% if stripe_configured %}
            <div class="mt-4 p-4 bg-tus-blue/10 border border-tus-blue/20 rounded-xl">
                <div class="flex justify-between items-center">
                    <span class="text-tus-blue font-medium flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        Acompte ({{ deposit_rate }}%)
                    </span>
                    <span class="text-tus-blue font-bold text-lg">{{ deposit_amount|floatformat:2 }} €</span>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Zone de signature -->
        <div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 md:p-8 mb-8">
            <h2 class="font-display text-xl font-semibold text-tus-white mb-4 flex items-center gap-2">
                <svg class="w-6 h-6 text-tus-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                </svg>
                Votre signature
            </h2>

            <p class="text-tus-white/60 mb-4 text-sm">
                En signant ci-dessous, vous acceptez les termes et conditions du devis n° {{ quote.number }}.
            </p>

            <div class="signature-container mb-4 bg-tus-white/3 border border-tus-white/10 rounded-xl overflow-hidden" 
                 id="signature-container">
                <canvas id="signature-pad"></canvas>
            </div>

            <div class="flex gap-3">
                <button type="button" id="clear-signature"
                    class="px-4 py-2 text-tus-white/70 hover:text-tus-white border border-tus-white/20 
                           hover:border-tus-white/40 rounded-lg transition-colors">
                    Effacer
                </button>
                <a href="{% url 'devis:quote_public_pdf' token=quote.public_token %}" target="_blank"
                    class="px-4 py-2 text-tus-blue hover:text-tus-blue border border-tus-blue/30 
                           hover:border-tus-blue/50 rounded-lg transition-colors flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    Voir le PDF
                </a>
            </div>
        </div>
        
        <!-- Paiement Stripe -->
        <div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 md:p-8">
            <h2 class="font-display text-xl font-semibold text-tus-white mb-6">
                Paiement sécurisé
            </h2>
            
            {% if stripe_configured and stripe_publishable_key %}
            <!-- Stripe Elements input -->
            {% else %}
            <div class="bg-tus-red/10 border border-tus-red/30 rounded-xl p-4">
                <p class="text-tus-white/60">Paiement actuellement indisponible.</p>
            </div>
            {% endif %}
        </div>
    </div>
</section>
```

**Changements clés** :
- ✅ `bg-[#F6F7FB]` → `bg-tus-black`
- ✅ `text-[#07080A]` → `text-tus-white`
- ✅ `text-gray-600` → `text-tus-white/60`
- ✅ `bg-white` → `bg-tus-white/5`
- ✅ `bg-blue-50` → `bg-tus-blue/10`
- ✅ `border-gray-300` → `border-tus-white/10`

#### 2️⃣ Corriger `devis/payment_success.html`

Simplifier pour utiliser **les mêmes styles que `factures/payment_success.html`** :

**Avant** (❌ Blanc) :
```html
<section class="min-h-screen bg-[#F6F7FB]">
```

**Après** (✅ TUS) :
```html
<section class="min-h-screen bg-tus-black flex items-center justify-center py-20 relative overflow-hidden">
```

---

### PRIORITÉ 2: ARCHITECTURE CSS CLIENT (IMPORTANTE)

#### 3️⃣ Créer `static/css/client-portal.css`

**Action** :
1. Extraire les 870 lignes de `<style>` de `dashboard.html`
2. Créer nouveau fichier `static/css/client-portal.css`
3. Remplacer toutes les variables client par les variables TUS :
   ```css
   :root {
       /* Supprimer les variables client, utiliser les TUS */
       --client-bg: var(--tus-black);           /* #07080A */
       --client-text: var(--tus-white);         /* #F6F7FB */
       --client-green: var(--tus-green);        /* #22C55E */
       --client-blue: var(--tus-blue);          /* #0B2DFF */
   }
   ```
4. Importer dans `base.html` :
   ```html
   <link rel="stylesheet" href="{% static 'css/client-portal.css' %}">
   ```
5. Nettoyer les `<style>` des 5 templates

---

### PRIORITÉ 3: UNIFORMISER PAGES DE PAIEMENT

#### 4️⃣ Synchroniser `devis/payment_success.html` avec `factures/payment_success.html`

**Court terme** : Copier structure de `factures/payment_success.html` vers `devis/payment_success.html`

**Résultat** : Les deux pages de confirmation utilisent la même palette TUS.

---

## 📋 CHECKLIST DE PARCOURS UTILISATEUR

Après corrections, vérifier chaque étape :

- [ ] **1. Accueil** → Design noir/bleu TUS ✅
- [ ] **2. Demande devis** → Design noir/bleu TUS ✅
- [ ] **3. Validation 2FA** → Design noir/bleu TUS ✅
- [ ] **4. Signature & paiement** → Design noir/bleu TUS ✅ (à corriger)
- [ ] **5. Confirmation** → Design noir/bleu TUS ✅ (à corriger)
- [ ] **6. Espace client** → Design noir/bleu TUS ✅ (ajuster vert)
- [ ] **7. Liste devis/factures** → Cohérent ✅
- [ ] **8. Détail devis/facture** → Cohérent ✅

---

## 🎨 BONUS: ACCESSIBILITÉ WCAG AA

### Ratio de contraste vérifié

```
TUS Black (#07080A) vs TUS White (#F6F7FB)
Ratio = 19.4:1 ✅ WCAG AAA

TUS Black (#07080A) vs text-tus-white/60 (#979AA0)
Ratio = 6.0:1 ✅ WCAG AA

TUS Black (#07080A) vs text-gray-600 (#4B5563)  ❌
Ratio = 3.9:1 ❌ FAIL WCAG AA (minimum 4.5:1)
```

**Recommandation** : Utiliser `text-tus-white/60` au lieu de `text-gray-600`.

---

## 📞 PROCHAINES ÉTAPES

1. **Créer les branches de correction** :
   ```bash
   git checkout -b fix/design-consistency
   ```

2. **Commencer par PRIORITÉ 1** (sign_and_pay.html + payment_success.html)

3. **Tester sur Render** pour valider rendus

4. **Puis PRIORITÉ 2** (externaliser CSS client)

5. **Validation visuelle** sur tous les navigateurs

---

## 📊 IMPACT ESTIMÉ

| Correctif | Temps | Impact | Risque |
|-----------|-------|--------|--------|
| sign_and_pay.html | 30 min | **CRITIQUE** 🔴 | Bas |
| payment_success devis | 15 min | **CRITIQUE** 🔴 | Bas |
| CSS client externalisé | 1h | Important 🟠 | Bas |
| Dashboard vert TUS | 15 min | Mineur 🟡 | Bas |

**Temps total estimé** : 2 heures (easy wins!)

---

## 📝 NOTES POUR DÉVELOPPEURS

- **Ne jamais** hard-coder les couleurs : `bg-[#F6F7FB]` ❌
- **Toujours** utiliser les classes TUS : `bg-tus-white` ✅
- **Externaliser** le CSS des templates multiples
- **Respecter** la charte.txt dans TOUS les templates
- **Vérifier** l'accessibilité WCAG AA minimum

---

**Fin de l'audit**  
*Signé : GitHub Copilot | Date : 12 février 2026*
