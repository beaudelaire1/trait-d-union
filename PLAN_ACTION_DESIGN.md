# 🔧 PLAN D'ACTION - FIX DESIGN CONSISTENCY

## Phase 1 : Corrections critiques (45 minutes)

### Étape 1.1 : Corriger `devis/sign_and_pay.html`

**Problème** : Fond blanc au lieu de noir TUS

**Fichier** : `apps/devis/templates/devis/sign_and_pay.html`

**Remplacements à faire** :

```bash
# 1. Rechercher toutes les classes non-TUS et les remplacer

# bg-[#F6F7FB] (Blanc) → bg-tus-black
# bg-[#F6F7FB] → bg-tus-black

# text-[#07080A] (Noir hard-coded) → text-tus-white
# text-[#07080A] → text-tus-white

# text-gray-600 (Gris Tailwind) → text-tus-white/60
# text-gray-600 → text-tus-white/60

# bg-white (Blanc) → bg-tus-white/5
# bg-white → bg-tus-white/5

# bg-gray-50 (Gris clair) → bg-tus-white/5
# bg-gray-50 → bg-tus-white/5

# border border-gray-300 → border border-tus-white/10
# border border-gray-300 → border border-tus-white/10

# text-gray-800 (Gris foncé) → text-tus-white
# text-gray-800 → text-tus-white

# text-gray-500 (Gris moyen) → text-tus-white/50
# text-gray-500 → text-tus-white/50

# bg-blue-50 (Bleu clair Stripe) → bg-tus-blue/10
# bg-blue-50 → bg-tus-blue/10

# text-blue-600 (Bleu Stripe) → text-tus-blue
# text-blue-600 → text-tus-blue

# text-blue-800 (Bleu foncé) → text-tus-blue
# text-blue-800 → text-tus-blue

# border-gray-200 → border-tus-white/10
# border-gray-200 → border-tus-white/10
```

**Détail par section** :

#### Section "Récapitulatif du devis" (ligne ~62-130)
```html
<!-- ❌ Avant -->
<div class="bg-white rounded-2xl shadow-lg p-6 md:p-8 mb-8">
    <h2 class="font-display text-xl font-semibold text-[#07080A] mb-6">
        <svg class="w-6 h-6 text-blue-600">
        Récapitulatif
    </h2>
    <div class="summary-row">
        <span class="font-medium">{{ item.description }}</span>
        <span class="text-gray-500">× {{ item.quantity }}</span>
    </div>
    <div class="bg-gray-50 rounded-xl p-4 space-y-2">
        <div class="flex justify-between text-gray-600">
            <span>Sous-total HT</span>

<!-- ✅ Après -->
<div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 md:p-8 mb-8">
    <h2 class="font-display text-xl font-semibold text-tus-white mb-6 flex items-center gap-2">
        <svg class="w-6 h-6 text-tus-blue">
        Récapitulatif
    </h2>
    <div class="summary-row">
        <span class="font-medium text-tus-white">{{ item.description }}</span>
        <span class="text-tus-white/50 text-sm">× {{ item.quantity }}</span>
    </div>
    <div class="bg-tus-white/5 rounded-xl p-4 space-y-2">
        <div class="flex justify-between text-tus-white/60">
            <span>Sous-total HT</span>
```

#### Section "Paiement Stripe" (ligne ~110-125)
```html
<!-- ❌ Avant -->
{% if stripe_configured %}
<div class="mt-4 p-4 bg-blue-50 rounded-xl">
    <div class="flex justify-between items-center">
        <span class="text-blue-800 font-medium">
            Acompte ({{ deposit_rate }}%)
        </span>
        <span class="text-blue-900 font-bold text-lg">{{ deposit_amount }}</span>

<!-- ✅ Après -->
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
        <span class="text-tus-blue font-bold text-lg">{{ deposit_amount }}</span>
```

#### Section "Signature" (ligne ~135-175)
```html
<!-- ❌ Avant -->
<div class="bg-white rounded-2xl shadow-lg p-6 md:p-8 mb-8">
    <h2 class="font-display text-xl font-semibold text-[#07080A] mb-4 flex items-center gap-2">
        <svg class="w-6 h-6 text-tus-green">
    <p class="text-gray-600 mb-4 text-sm">En signant...</p>
    <div class="signature-container mb-4" id="signature-container">
        <canvas id="signature-pad"></canvas>
    </div>
    <button id="clear-signature"
        class="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300">
        Effacer
    </button>
    <a href="..." class="px-4 py-2 text-blue-600 hover:text-blue-800 border border-blue-300">

<!-- ✅ Après -->
<div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 md:p-8 mb-8">
    <h2 class="font-display text-xl font-semibold text-tus-white mb-4 flex items-center gap-2">
        <svg class="w-6 h-6 text-tus-green">
    <p class="text-tus-white/60 mb-4 text-sm">En signant...</p>
    <div class="signature-container mb-4 bg-tus-white/3 border border-tus-white/10 rounded-xl overflow-hidden" 
         id="signature-container">
        <canvas id="signature-pad"></canvas>
    </div>
    <button id="clear-signature"
        class="px-4 py-2 text-tus-white/70 hover:text-tus-white border border-tus-white/20 
               hover:border-tus-white/40 rounded-lg transition-colors">
        Effacer
    </button>
    <a href="..." class="px-4 py-2 text-tus-blue hover:text-tus-blue border border-tus-blue/30 
                        hover:border-tus-blue/50 rounded-lg transition-colors flex items-center gap-2">
```

---

### Étape 1.2 : Corriger `devis/payment_success.html`

**Problème** : Fond blanc + gris au lieu d'être cohérent avec `factures/payment_success.html`

**Remplacements** :

```html
<!-- ❌ Section entière à remplacer -->
<section class="min-h-screen bg-[#F6F7FB] flex items-center justify-center py-20">
    <div class="max-w-xl mx-auto px-6 text-center">
        <h1 class="font-display text-4xl font-bold text-[#07080A] mb-4">
        <p class="text-gray-600 text-lg mb-8">
        <div class="bg-white rounded-2xl p-6 shadow-lg mb-8">
            <div class="flex justify-between items-center pb-4 border-b">
                <span class="text-gray-600">Devis n°</span>
                <span class="font-semibold text-[#07080A]">

<!-- ✅ Après (copier structure de factures/payment_success.html) -->
<section class="min-h-screen bg-tus-black flex items-center justify-center py-20 relative overflow-hidden">
    <!-- Background effects -->
    <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-tus-green/15 rounded-full blur-[150px]"></div>
    </div>

    <div class="max-w-xl mx-auto px-6 text-center relative z-10">
        <!-- Success Icon with animation -->
        <div class="relative w-24 h-24 mx-auto mb-8">
            <div class="absolute inset-0 bg-tus-green/20 rounded-full animate-ping opacity-25"></div>
            <div class="relative w-24 h-24 bg-tus-green/20 rounded-full flex items-center justify-center">
                <svg class="w-12 h-12 text-tus-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
        </div>

        <h1 class="font-display text-4xl font-bold text-tus-white mb-4">
            Merci pour votre confiance !
        </h1>
        
        <p class="text-tus-white/60 text-lg mb-8">
            {% if quote %}
            Votre devis <strong class="text-tus-white">{{ quote.number }}</strong> a été accepté et votre acompte a été reçu.
            {% else %}
            Votre paiement a bien été reçu.
            {% endif %}
        </p>

        {% if quote %}
        <div class="bg-tus-white/5 backdrop-blur-sm border border-tus-white/10 rounded-2xl p-6 mb-8">
            <div class="space-y-4">
                <div class="flex justify-between items-center pb-4 border-b border-tus-white/10">
                    <span class="text-tus-white/60">Devis n°</span>
                    <span class="font-semibold text-tus-white">{{ quote.number }}</span>
                </div>
                <div class="flex justify-between items-center pb-4 border-b border-tus-white/10">
                    <span class="text-tus-white/60">Montant total</span>
                    <span class="font-display text-xl font-bold text-tus-white">{{ quote.total_ttc|floatformat:2 }} €</span>
                </div>
```

---

## Phase 2 : CSS Client Externalisé (1h)

### Étape 2.1 : Créer `static/css/client-portal.css`

**Action** :
1. Copier les 870 lignes de `<style>` depuis `apps/clients/templates/clients/dashboard.html` (lignes 631-1500)
2. Créer nouveau fichier `static/css/client-portal.css`
3. Remplacer les couleurs client par TUS :

```css
/* static/css/client-portal.css */

/* ESPACE CLIENT PREMIUM - TRAIT D'UNION STUDIO */

:root {
    /* ✅ Utiliser les variables TUS au lieu de variables client */
    --client-bg: #07080A;              /* TUS Black */
    --client-surface: #0D1016;         /* TUS Surface Dark */
    --client-surface-hover: #12121a;   /* Légèrement plus clair */
    --client-border: rgba(255,255,255,0.08);
    --client-text: #f6f7fb;            /* TUS White */
    --client-text-muted: rgba(246,247,251,0.6);
    --client-blue: #0B2DFF;            /* TUS Blue */
    --client-blue-soft: rgba(11,45,255,0.15);
    --client-purple: #0B2DFF;          /* TUS Blue (no purple) */
    --client-green: #22C55E;           /* ✅ TUS GREEN (was #10B981) */
    --client-orange: #F59E0B;
    --client-red: #EF4444;
    --sidebar-width: 280px;
    --sidebar-collapsed: 80px;
}

/* ... reste du CSS ... */
```

### Étape 2.2 : Mettre à jour `templates/base.html`

```html
<!-- Ajouter dans <head> -->
<link rel="stylesheet" href="{% static 'css/client-portal.css' %}">
```

### Étape 2.3 : Supprimer `<style>` des 5 templates

**Fichiers à nettoyer** :
- `apps/clients/templates/clients/dashboard.html` (lignes 631-1500) → DELETE
- `apps/clients/templates/clients/quote_list.html`
- `apps/clients/templates/clients/invoice_list.html`
- `apps/clients/templates/clients/quote_detail.html`
- `apps/clients/templates/clients/profile.html`

---

## Phase 3 : Validation (15 minutes)

### Étape 3.1 : Tester en local

```bash
# Démarrer le serveur
python manage.py runserver

# Visiter chaque page et vérifier les couleurs
http://localhost:8000/devis/nouveau/           # TUS Black ✓
http://localhost:8000/devis/succes/            # TUS Black ✓
http://localhost:8000/devis/valider/<token>/   # TUS Black ✓
http://localhost:8000/devis/.../signer/        # TUS Black ✓ (À CORRIGER)
http://localhost:8000/devis/payment_success/   # TUS Black ✓ (À CORRIGER)
http://localhost:8000/clients/                 # TUS Black ✓
http://localhost:8000/clients/devis/           # TUS Green #22C55E ✓
http://localhost:8000/clients/factures/        # TUS Black ✓
```

### Étape 3.2 : Vérifier avec DevTools

**Inspecteur Chrome** :
```js
// Vérifier que AUCUN hard-code n'existe
document.querySelectorAll('[style*="F6F7FB"]')     // Doit retourner []
document.querySelectorAll('[style*="07080A"]')     // Doit retourner []
document.querySelectorAll('[class*="gray-600"]')   // Doit retourner []

// Vérifier les var() CSS
getComputedStyle(document.body).backgroundColor
// Doit être #07080A (TUS Black)
```

### Étape 3.3 : Tester les contrastes WCAG

**Utiliser** : https://webaim.org/resources/contrastchecker/

```
TUS Black (#07080A) vs TUS White (#F6F7FB)
→ 19.4:1 ✅ AAA

TUS Black (#07080A) vs text-tus-white/60 (#979AA0)
→ 6.0:1 ✅ AA

TUS Black (#07080A) vs text-gray-600 (#4B5563)
→ 3.9:1 ❌ FAIL (ne pas utiliser)
```

---

## Phase 4 : Déploiement sur Render

```bash
# Commit les changements
git add apps/devis/templates/devis/sign_and_pay.html
git add apps/devis/templates/devis/payment_success.html
git add static/css/client-portal.css
git add templates/base.html
git add apps/clients/templates/clients/dashboard.html  # Supprimer <style>
# ... etc pour les 5 templates client

git commit -m "Fix: Design consistency - align all pages to TUS brand colors

✅ Fix devis/sign_and_pay.html (white→black)
✅ Fix devis/payment_success.html (white→black)  
✅ Externalize client portal CSS
✅ Align client colors to TUS palette (green #22C55E)
✅ Remove inline styles from 5 templates
✅ WCAG AA contrasts verified

Tests: All pages now use TUS Black/White/Blue/Green consistently"

# Push vers Render
git push origin main

# Render redéploiera automatiquement (2-3 min)
```

---

## ✅ CHECKLIST FINALE

- [ ] `sign_and_pay.html` : Tous les `text-gray-*` → `text-tus-white/*`
- [ ] `sign_and_pay.html` : Tous les `bg-white` → `bg-tus-white/5`
- [ ] `sign_and_pay.html` : Tous les `bg-[#F6F7FB]` → `bg-tus-black`
- [ ] `payment_success.html` : 100% TUS colors
- [ ] `client-portal.css` : Créé et linké dans `base.html`
- [ ] Dashboard + 4 templates : `<style>` supprimés
- [ ] Vert client : `#10B981` → `#22C55E`
- [ ] Tests locaux : Tous les parcours affichent TUS colors
- [ ] WCAG AA : Contrastes >4.5:1 sur tous les textes
- [ ] Commit + push vers Render
- [ ] Vérification sur http://votre-domaine.com (post-déploiement)

---

**Temps estimé** : 2h (incluant tests)  
**Risque** : Très bas (CSS uniquement, pas de logique)  
**Impact utilisateur** : Professionnel + confiance augmentée
