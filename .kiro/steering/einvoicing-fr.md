---
inclusion: fileMatch
fileMatchPattern: 'apps/(einvoicing|factures|devis|clients)/**'
---

# Facturation électronique France — Règles du chantier TUS

Document de pilotage du chantier de mise en conformité avec la réforme française de la facturation électronique (entrée en vigueur 1er sept 2026 / 1er sept 2027 pour les TPE comme TUS). Ce fichier prévaut sur les conventions générales pour tout ce qui touche aux apps `einvoicing`, `factures`, `devis`, `clients`.

## 1. Cadre réglementaire (à respecter sans interprétation)

- **Norme socle** : EN 16931 (sémantique européenne).
- **Formats acceptés FR** : Factur-X (PDF/A-3 + XML CII), UBL 2.1, CII pur. **Cible TUS = Factur-X profil EN 16931** (extended si nécessaire).
- **Standards AFNOR** : XP Z12-012 (formats/profils), XP Z12-013 (API PDP), XP Z12-014 (cas d'usage B2B).
- **Acheminement obligatoire** : via PA (Plateforme Agréée, ex-PDP). Le PPF n'est plus une plateforme de facturation depuis oct 2024.
- **PA cible** : **IOPOLE** (https://iopole.fr) — Plateforme Agréée DGFiP, API REST conforme XP Z12-013. Adapter `apps/einvoicing/pdp/iopole.py`. B2BRouter reste supporté en secours via le même contrat `PDPClient` (swap via `EINVOICING_PDP_PROVIDER=b2brouter`).
- **TUS = micro entreprise en franchise en base TVA** (art. 293 B CGI). Mapping XML : `VAT category E` + raison `VATEX-EU-79-C`.
- **Échéance émission obligatoire pour TUS** : 1er septembre 2027.
- **Réception obligatoire** : 1er septembre 2026 (toutes entreprises FR).
- **E-reporting B2C / cross-border** : obligatoire en parallèle (TUS facture aussi des particuliers via Stripe).
- **Sanctions** : 15 €/facture non conforme, plafond 15 000 €/an.

## 2. Mentions obligatoires (mémo non négociable)

À chaque émission, doivent figurer dans la facture (PDF ET XML) :

| Champ | Source modèle | Obligatoire si |
|---|---|---|
| Numéro séquentiel | `Invoice.number` | Toujours |
| Date d'émission | `Invoice.issue_date` | Toujours |
| Date livraison/exécution | `Invoice.delivery_date` | Différente de l'émission |
| Identité émetteur (nom, forme juridique, SIREN/SIRET, adresse) | `settings.INVOICING['EMITTER']` | Toujours |
| TVA intracom émetteur | `EMITTER['vat_intra']` | Si assujetti |
| Mention « TVA non applicable, art. 293 B du CGI » | code `VATEX-EU-79-C` | Franchise en base |
| Identité destinataire | `Invoice.client` (`ClientProfile`) | Toujours |
| **SIREN du client** | `ClientProfile.siren` | B2B (nouveau dès 2026) |
| Adresse de livraison si ≠ facturation | `delivery_address_*` | Si différente |
| **Type de transaction** | `Invoice.transaction_type` ∈ {GOODS, SERVICES, MIXED} | Nouveau dès 2026 |
| **Option TVA d'après les débits** | `Invoice.vat_payment_basis` | Si applicable |
| Référence bon de commande | `Invoice.purchase_order_ref` | Si fournie |
| Référence acheteur (Buyer reference) | `Invoice.buyer_reference` | Si fournie |
| Désignation de chaque ligne, qté, PU HT, taux TVA, total | `InvoiceItem.*` | Toujours |
| Totaux HT, TVA détaillée par taux, TTC | `Invoice.total_*` | Toujours |
| Conditions de paiement, escompte, pénalités de retard, indemnité 40 € | `Invoice.payment_terms`, footer | Toujours |

## 3. Architecture cible (5 phases)

```
apps/einvoicing/                 ← nouvelle app pivot
├── codelists.py                 ← VAT, VATEX, UN/ECE units, transactions
├── validators.py                ← Luhn SIREN/SIRET, TVA, Peppol
├── models.py                    ← InvoiceLifecycleEvent (audit immuable)
├── builders/
│   ├── ubl.py                   ← UBL 2.1 → bytes XML
│   ├── cii.py                   ← UN/CEFACT CII → bytes XML
│   └── facturx.py               ← Factur-X PDF/A-3 (PDF + XML CII)
├── pdp/
│   ├── base.py                  ← Interface PDPClient abstraite
│   ├── iopole.py                ← Adapter IOPOLE (par défaut, OAuth2)
│   ├── b2brouter.py             ← Adapter B2BRouter (secours, X-B2B-API-Key)
│   └── xpz12013.py              ← Adapter générique XP Z12-013
├── tasks.py                     ← django-q2 (envoi async, polling)
├── api/                         ← Django Ninja (Phase 4)
│   ├── routers.py
│   ├── schemas.py
│   └── auth.py
└── tests/
```

## 4. Discipline de livraison (issue de FOUNDATION PRIME)

- **Patch-first**. Aucune réécriture des modèles existants. Toute évolution = migration additive avec valeurs par défaut compatibles.
- **Numérotation des factures** : la séquence existante `FAC-AAAA-XXX` est SACRÉE (art. 289 CGI : intangibilité). Les avoirs ont leur propre séquence `AVO-AAAA-XXXXX`.
- **Aucune modification visuelle** avant Phase 5 explicite. Les templates `quote_pdf.html` et `invoice_pdf.html` sont gelés jusqu'à Phase 5.
- **Toutes les chaînes réglementées** (codes VAT, VATEX, unités) doivent venir de `apps.einvoicing.codelists` — jamais en dur.
- **Audit immuable** : `InvoiceLifecycleEvent` ne permet pas l'`UPDATE` ni le `DELETE` (vérifié en `save()` et au niveau migration). Hash chaîné SHA-256 sur événement précédent.
- **Tests obligatoires** sur : validators, lifecycle, conversions devis→facture, builders XML, idempotence webhook PDP.
- **Secrets PDP** : exclusivement via env vars `EINVOICING_PDP_*`. Jamais en commit. Rotation possible.

## 5. Codes de référence à utiliser

**VAT category (UNTDID 5305)** :
- `S` Standard rate, `Z` Zero rate, `E` Exempt, `AE` Reverse charge, `K` Intra-community supply, `G` Export outside EU, `O` Outside scope of VAT.

**VATEX (motifs d'exemption EN 16931)** :
- `VATEX-EU-79-C` Franchise en base (TUS).
- `VATEX-EU-AE` Reverse charge.
- `VATEX-EU-IC` Livraison intracommunautaire.
- `VATEX-EU-G` Exportation hors UE.
- `VATEX-EU-132` Exemptions article 132 (services médicaux/éducation).
- `VATEX-EU-O` Hors champ TVA.

**Codes unité** : UN/ECE Recommendation 20, ex. `C62` (unité par défaut), `HUR` (heure), `DAY` (jour), `MTR` (mètre), `MTK` (m²), `MTQ` (m³), `KGM` (kilogramme), `LS` (forfait/lump sum).

**Type de transaction (FR)** : `GOODS`, `SERVICES`, `MIXED`.

**Base de paiement TVA** : `DEBITS` (sur les débits) ou `RECEIPTS` (sur les encaissements — défaut prestataires).

## 6. Sources officielles à consulter

- Service-public.fr — Mentions obligatoires : https://entreprendre.service-public.fr/vosdroits/F31808
- Service-public.fr — Réforme : https://entreprendre.service-public.fr/actualites/A15683
- AFNOR XP Z12-012/013/014 — payant (résumés Comarch / Tradeshift)
- EN 16931 — https://standards.cen.eu/
- Factur-X — http://fnfe-mpe.org/factur-x/
- B2BRouter API — https://www.b2brouter.net/global/
- IOPOLE — https://iopole.fr (PA DGFiP, doc dev fournie à l'inscription)

## 7. Anti-patterns à refuser

- ❌ Stocker la TVA en `Decimal` arrondi avant calcul (perte de précision).
- ❌ Concaténer du XML à la main → toujours `lxml.etree`.
- ❌ Envoyer un PDF non PDF/A-3 comme Factur-X.
- ❌ Logger un secret PDP, un access_token, ou le contenu intégral d'une facture.
- ❌ Modifier le numéro d'une facture émise (UPDATE bloqué).
- ❌ Supprimer une facture émise (DELETE bloqué : utiliser AVOIR).
- ❌ Mettre du code de calcul de TVA hors `apps.einvoicing.taxation`.
