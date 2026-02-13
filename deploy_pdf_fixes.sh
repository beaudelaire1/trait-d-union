#!/bin/bash
# 🚀 Script de déploiement et test des fixes PDF
# Usage: bash deploy_pdf_fixes.sh

set -e

echo "═══════════════════════════════════════════════════════════"
echo "   🔧 ATLAS PRIME — Déploiement PDF Fixes  "
echo "═══════════════════════════════════════════════════════════"
echo ""

# Configuration
PROJECT_DIR="."
DJANGO_SETTINGS="config.settings"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonctions helpers
log_section() {
    echo -e "${YELLOW}>>> $1${NC}"
}

log_ok() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 1. Vérifier l'environnement
log_section "1️⃣  Vérification de l'environnement"
if ! command -v python &> /dev/null; then
    log_error "Python n'est pas installé"
    exit 1
fi
log_ok "Python trouvé: $(python --version)"

if ! python -c "import django" &> /dev/null; then
    log_error "Django n'est pas installé"
    exit 1
fi
log_ok "Django installé"

# 2. Vérifier les dépendances
log_section "2️⃣  Vérification des dépendances PDF"
if ! python -c "import weasyprint" &> /dev/null; then
    log_error "WeasyPrint n'est pas installé"
    log_section "Installation de WeasyPrint..."
    pip install weasyprint>=60.0
    log_ok "WeasyPrint installé"
else
    log_ok "WeasyPrint installé"
fi

# 3. Migration (aucune migration requise pour ce fix)
log_section "3️⃣  Vérification des migrations"
log_ok "Aucune migration requise (fix templates/services uniquement)"

# 4. Exécuter les tests
log_section "4️⃣  Exécution des tests PDF"
if python manage.py test apps.factures.tests_pdf --verbosity=2; then
    log_ok "Tests unitaires passés ✓"
else
    log_error "Des tests ont échoué"
    exit 1
fi

# 5. Tester la génération PDF en local
log_section "5️⃣  Test de génération PDF (CLI)"
if python manage.py test_pdf_generation --both; then
    log_ok "Génération PDF réussie ✓"
else
    log_error "Erreur lors de la génération PDF"
    exit 1
fi

# 6. Afficher le résumé
log_section "6️⃣  Résumé des changements"
echo ""
echo "📝 Fichiers modifiés:"
echo "  • apps/devis/templates/devis/quote_pdf.html"
echo "  • apps/factures/templates/factures/invoice_pdf.html"
echo "  • apps/factures/views.py"
echo "  • core/services/document_generator.py"
echo ""
echo "📝 Fichiers ajoutés:"
echo "  • apps/factures/tests_pdf.py (tests unitaires)"
echo "  • apps/factures/management/commands/test_pdf_generation.py (test CLI)"
echo "  • BUGFIX_PDF_DOCUMENTATION.md (documentation)"
echo ""
echo "🐛 Bugs corrigés:"
echo "  1. item.vat_rate → item.tax_rate"
echo "  2. Suppression item.detail (inexistant)"
echo "  3. quote.items.all → quote.quote_items.all"
echo "  4. Google Fonts → Fallback CSS local"
echo "  5. Invoice.create_from_quote() → create_invoice_from_quote() service"
echo "  6. Null checks pour branding fields"
echo ""

# 7. Instructions de déploiement
log_section "7️⃣  Prochaines étapes (production Render)"
echo ""
echo "1. Commit les changements:"
echo "   git add apps/ core/ BUGFIX_PDF_DOCUMENTATION.md"
echo "   git commit -m 'Fix: 5 bugs critiques génération PDF (vat_rate, fonts, etc)'"
echo ""
echo "2. Push vers main:"
echo "   git push origin main"
echo ""
echo "3. Render redeploy (auto):"
echo "   → Render détectera les changements et redéploiera"
echo "   → Aucune action requise"
echo ""
echo "4. Vérification en production:"
echo "   → Admin: créer un devis → générer PDF → télécharger"
echo "   → Admin: convertir devis en facture → vérifier PDF"
echo ""

log_ok "✓ Tous les tests sont passés !"
log_ok "✓ Prêt pour le déploiement en production"
echo ""
echo "═══════════════════════════════════════════════════════════"
