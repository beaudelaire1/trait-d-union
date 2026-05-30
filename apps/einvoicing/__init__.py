"""
apps.einvoicing — Conformité facturation électronique France 2026/2027.

App pivot fournissant :
- Codes réglementaires (VAT, VATEX, unités UN/ECE, types transaction)
- Validators (SIREN/SIRET Luhn, TVA intracom, Peppol Participant ID)
- Audit lifecycle des factures (modèle immuable signé)
- Builders XML EN 16931 (UBL 2.1, CII) + Factur-X PDF/A-3      [Phase 2]
- Couche PDP swappable, adapters IOPOLE (défaut) + B2BRouter             [Phase 3]
- API REST Django Ninja                                         [Phase 4]
"""
