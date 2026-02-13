#!/usr/bin/env python
"""
Script de validation : Audit UX/Design Trait d'Union Studio
Vérifie les incohérences de couleurs et de styles dans les templates
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Couleurs TUS officielles
TUS_COLORS = {
    'black': '#07080A',
    'white': '#F6F7FB',
    'blue': '#0B2DFF',
    'green': '#22C55E',
}

# Couleurs non-TUS (à éviter)
FORBIDDEN_COLORS = {
    '#F6F7FB': ('white TUS hard-coded', 'use `text-tus-white` class'),
    '#07080A': ('black TUS hard-coded', 'use `text-tus-black` class'),
    '#0a0a0f': ('client bg (not TUS)', 'use `bg-tus-black` instead'),
    '#12121a': ('client surface (not TUS)', 'use `bg-tus-white/5` instead'),
    '#10B981': ('client green (not TUS!)', 'use TUS Green #22C55E'),
    'gray-600': ('Tailwind gray (not TUS)', 'use `text-tus-white/60`'),
    'gray-50': ('Gray background (not TUS)', 'use `bg-tus-white/5`'),
    'blue-50': ('Blue-50 background (not TUS)', 'use `bg-tus-blue/10`'),
    'blue-600': ('Blue-600 (not TUS)', 'use `text-tus-blue`'),
    'blue-800': ('Blue-800 (not TUS)', 'use `text-tus-blue`'),
    'white': ('white (not TUS class)', 'use `bg-tus-white/5` or `text-tus-white`'),
}

# Patterns à rechercher
PATTERNS = {
    'HTML_COLORS': re.compile(r'(?:bg|text)-\[#([0-9A-Fa-f]{6})\]'),  # bg-[#F6F7FB]
    'INLINE_COLORS': re.compile(r'color:\s*#([0-9A-Fa-f]{6})'),        # color: #F6F7FB
    'FORBIDDEN_CLASSES': re.compile(r'(?:bg|text|border)?-?(gray-\d+|blue-\d+|red-\d+|white|black)(?:\s|"|\]|/|>)'),
    'INLINE_STYLES': re.compile(r'style="[^"]*[^T](#[0-9A-Fa-f]{6}|rgb\(|gray-|blue-)[^"]*"'),
}

class DesignAudit:
    def __init__(self, root_dir='apps'):
        self.root_dir = root_dir
        self.results = defaultdict(list)
        self.templates = []
        self.colors_found = defaultdict(list)
        
    def find_templates(self):
        """Trouver tous les fichiers HTML"""
        self.templates = list(Path(self.root_dir).rglob('*.html'))
        return self.templates
    
    def audit_file(self, filepath):
        """Auditer un fichier HTML pour les incohérences"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return
        
        issues = []
        
        # Chercher les hard-coded colors
        for color_code, (issue, fix) in FORBIDDEN_COLORS.items():
            if color_code in content:
                # Compter les occurrences
                count = content.count(color_code)
                if count > 0:
                    issues.append({
                        'type': 'HARD-CODED COLOR',
                        'color': color_code,
                        'issue': issue,
                        'fix': fix,
                        'count': count,
                        'severity': 'CRITICAL' if color_code in ['#F6F7FB', '#07080A', '#10B981'] else 'MAJOR'
                    })
                    self.colors_found[color_code].append(filepath)
        
        # Chercher les classes Tailwind non-TUS
        tailwind_non_tus = [
            'text-gray-600', 'text-gray-500', 'text-gray-800',
            'bg-white', 'bg-gray-50', 'bg-blue-50',
            'border-gray-300', 'border-gray-200',
            'text-blue-600', 'text-blue-800', 'text-blue-900',
        ]
        
        for tailwind_class in tailwind_non_tus:
            if tailwind_class in content:
                count = content.count(tailwind_class)
                if count > 0:
                    issues.append({
                        'type': 'TAILWIND NON-TUS',
                        'class': tailwind_class,
                        'issue': f'Uses {tailwind_class} instead of TUS',
                        'count': count,
                        'severity': 'MAJOR'
                    })
        
        # Chercher les <style> inline (détecte CSS non mutualisé)
        if '<style>' in content:
            # Compter les lignes de CSS
            style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
            if style_match:
                css_content = style_match.group(1)
                css_lines = len(css_content.split('\n'))
                issues.append({
                    'type': 'INLINE CSS',
                    'issue': f'CSS non mutualisé: {css_lines} lignes',
                    'fix': 'Externaliser dans static/css/client-portal.css',
                    'lines': css_lines,
                    'severity': 'MAJOR' if css_lines > 300 else 'MINOR'
                })
        
        if issues:
            self.results[str(filepath)] = issues
    
    def run(self):
        """Exécuter l'audit complet"""
        self.find_templates()
        print(f"🔍 Audit de {len(self.templates)} templates...")
        
        for filepath in self.templates:
            self.audit_file(filepath)
        
        return self.results
    
    def print_report(self):
        """Afficher le rapport"""
        print("\n" + "="*80)
        print("🎨 AUDIT UX/DESIGN - TRAIT D'UNION STUDIO")
        print("="*80)
        
        if not self.results:
            print("✅ Aucun problème trouvé!")
            return
        
        critical_count = 0
        major_count = 0
        minor_count = 0
        
        for filepath, issues in sorted(self.results.items()):
            print(f"\n📄 {filepath}")
            print("-" * 80)
            
            for issue in issues:
                severity = issue.get('severity', 'INFO')
                
                if 'color' in issue:
                    print(f"  🔴 [{severity}] {issue['type']}")
                    print(f"     Color: {issue['color']} ({issue['issue']})")
                    print(f"     Found: {issue['count']}x")
                    print(f"     Fix: {issue['fix']}")
                    
                    if severity == 'CRITICAL':
                        critical_count += 1
                    else:
                        major_count += 1
                
                elif 'class' in issue:
                    print(f"  🟠 [{severity}] {issue['type']}")
                    print(f"     Class: {issue['class']}")
                    print(f"     Found: {issue['count']}x")
                    if severity == 'MAJOR':
                        major_count += 1
                    else:
                        minor_count += 1
                
                elif 'INLINE CSS' in issue['type']:
                    print(f"  🟠 [{severity}] {issue['type']}")
                    print(f"     {issue['issue']}")
                    print(f"     Fix: {issue['fix']}")
                    major_count += 1
        
        # Résumé
        print("\n" + "="*80)
        print("📊 RÉSUMÉ")
        print("="*80)
        print(f"🔴 CRITICAL: {critical_count}")
        print(f"🟠 MAJOR: {major_count}")
        print(f"🟡 MINOR: {minor_count}")
        print(f"Total: {critical_count + major_count + minor_count} problèmes")
        
        # Top offenders
        if self.colors_found:
            print("\n" + "="*80)
            print("🎨 COULEURS LES PLUS PROBLÉMATIQUES")
            print("="*80)
            for color, files in sorted(self.colors_found.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                print(f"\n{color} - Trouvé dans {len(files)} fichier(s)")
                for f in files[:3]:
                    print(f"  • {f}")
                if len(files) > 3:
                    print(f"  ... et {len(files)-3} autres")
        
        # Recommandations
        print("\n" + "="*80)
        print("✅ RECOMMANDATIONS")
        print("="*80)
        if critical_count > 0:
            print("1. 🔴 PRIORITÉ CRITIQUE: Corriger les pages de paiement/signature")
            print("   - devis/sign_and_pay.html")
            print("   - devis/payment_success.html")
        if major_count > 0:
            print("2. 🟠 PRIORITÉ IMPORTANTE: Externaliser CSS client")
            print("   - Créer static/css/client-portal.css")
            print("   - Supprimer <style> des 5 templates clients")
        print("3. 📚 Vérifier: AUDIT_UX_DESIGN.md et PLAN_ACTION_DESIGN.md")

if __name__ == '__main__':
    # Chercher le répertoire apps
    for root_option in ['apps', './apps', '../apps']:
        if Path(root_option).exists():
            audit = DesignAudit(root_dir=root_option)
            audit.run()
            audit.print_report()
            break
    else:
        print("❌ Impossible de trouver le répertoire 'apps/'")
        print("Utilisation: python audit_design.py (depuis la racine du projet)")
