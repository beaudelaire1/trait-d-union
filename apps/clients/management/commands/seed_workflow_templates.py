"""Commande pour créer des templates de workflow par défaut.

Usage:
    python manage.py seed_workflow_templates

Crée 3 workflows standards :
- Site Web Standard (8 jalons)
- App Mobile MVP (5 jalons)
- Refonte UX (4 jalons)
"""
from django.core.management.base import BaseCommand
from apps.clients.models_workflow import WorkflowTemplate, MilestoneTemplate


class Command(BaseCommand):
    help = "Crée des templates de workflow par défaut pour TUS"
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des templates de workflow...")
        
        # ============================================================
        # Workflow 1 : Site Web Standard
        # ============================================================
        workflow_web, created = WorkflowTemplate.objects.get_or_create(
            name="Site Web Standard",
            defaults={
                'description': "Workflow complet pour un site web vitrine ou e-commerce",
                'is_active': True,
            }
        )
        
        if created:
            milestones_web = [
                ("Briefing & Analyse", "Recueil des besoins, analyse fonctionnelle", 5, [
                    {"text": "Réunion de lancement effectuée"},
                    {"text": "Cahier des charges validé par le client"},
                    {"text": "Planning projet défini et communiqué"},
                ]),
                ("Architecture & UX", "Arborescence, wireframes, parcours utilisateur", 7, [
                    {"text": "Arborescence du site validée"},
                    {"text": "Wireframes desktop créés"},
                    {"text": "Wireframes mobile créés"},
                    {"text": "Parcours utilisateur documenté"},
                ]),
                ("Design UI", "Maquettes graphiques HD", 10, [
                    {"text": "Charte graphique validée"},
                    {"text": "Maquettes desktop (3 pages minimum)"},
                    {"text": "Maquettes mobile responsives"},
                    {"text": "Design system (boutons, typo, couleurs)"},
                ]),
                ("Développement Front", "Intégration HTML/CSS/JS", 14, [
                    {"text": "Pages statiques intégrées"},
                    {"text": "Version responsive testée"},
                    {"text": "Animations & interactions implémentées"},
                    {"text": "Compatibilité cross-browser validée"},
                ]),
                ("Développement Back", "Backend Django, base de données", 10, [
                    {"text": "Modèles & admin configurés"},
                    {"text": "API/endpoints créés et documentés"},
                    {"text": "Formulaires fonctionnels avec validation"},
                    {"text": "Gestion des erreurs et sécurité"},
                ]),
                ("Contenu & SEO", "Rédaction, optimisation référencement", 5, [
                    {"text": "Textes intégrés et corrigés"},
                    {"text": "Images optimisées (poids < 200kb)"},
                    {"text": "Balises meta & Open Graph configurées"},
                    {"text": "Sitemap XML généré"},
                ]),
                ("Tests & Recette", "Validation fonctionnelle et technique", 7, [
                    {"text": "Tests cross-browser (Chrome, Firefox, Safari)"},
                    {"text": "Tests mobile (iOS/Android)"},
                    {"text": "Performance (Lighthouse > 90)"},
                    {"text": "Corrections client intégrées"},
                ]),
                ("Livraison & Formation", "Mise en ligne et passation", 3, [
                    {"text": "Mise en production effectuée"},
                    {"text": "Formation client dispensée"},
                    {"text": "Documentation technique remise"},
                    {"text": "Garantie et maintenance planifiées"},
                ]),
            ]
            
            for idx, (title, desc, days, checklist) in enumerate(milestones_web):
                MilestoneTemplate.objects.create(
                    workflow=workflow_web,
                    title=title,
                    description=desc,
                    order=idx,
                    estimated_duration_days=days,
                    checklist_template=checklist,
                )
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Workflow '{workflow_web.name}' créé avec {len(milestones_web)} jalons"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Workflow '{workflow_web.name}' existe déjà"
            ))
        
        # ============================================================
        # Workflow 2 : App Mobile MVP
        # ============================================================
        workflow_app, created = WorkflowTemplate.objects.get_or_create(
            name="App Mobile MVP",
            defaults={
                'description': "Workflow pour une application mobile MVP (React Native / Flutter)",
                'is_active': True,
            }
        )
        
        if created:
            milestones_app = [
                ("Product Discovery", "Définition du MVP et features", 5, [
                    {"text": "User stories définies et priorisées"},
                    {"text": "Périmètre MVP validé"},
                    {"text": "Architecture technique choisie"},
                ]),
                ("Design UX/UI", "Prototypes interactifs", 10, [
                    {"text": "Wireframes iOS/Android créés"},
                    {"text": "Design system mobile (composants)"},
                    {"text": "Prototype cliquable (Figma/Sketch)"},
                    {"text": "Tests utilisateurs effectués"},
                ]),
                ("Développement", "Code natif ou cross-platform", 21, [
                    {"text": "Architecture technique implémentée"},
                    {"text": "Écrans principaux développés"},
                    {"text": "API backend connectée"},
                    {"text": "Authentification & sécurité"},
                    {"text": "Notifications push configurées"},
                ]),
                ("Tests & Beta", "Tests utilisateurs", 7, [
                    {"text": "Build TestFlight (iOS) déployé"},
                    {"text": "Build Play Console (Android) déployé"},
                    {"text": "Feedback beta-testeurs collecté"},
                    {"text": "Corrections bugs critiques"},
                ]),
                ("Lancement", "Publication stores", 3, [
                    {"text": "Soumission App Store effectuée"},
                    {"text": "Soumission Google Play effectuée"},
                    {"text": "Assets stores (screenshots, vidéo, description)"},
                    {"text": "Plan de communication lancé"},
                ]),
            ]
            
            for idx, (title, desc, days, checklist) in enumerate(milestones_app):
                MilestoneTemplate.objects.create(
                    workflow=workflow_app,
                    title=title,
                    description=desc,
                    order=idx,
                    estimated_duration_days=days,
                    checklist_template=checklist,
                )
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Workflow '{workflow_app.name}' créé avec {len(milestones_app)} jalons"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Workflow '{workflow_app.name}' existe déjà"
            ))
        
        # ============================================================
        # Workflow 3 : Refonte UX
        # ============================================================
        workflow_ux, created = WorkflowTemplate.objects.get_or_create(
            name="Refonte UX / Audit Design",
            defaults={
                'description': "Workflow court pour audit UX et refonte design d'un site existant",
                'is_active': True,
            }
        )
        
        if created:
            milestones_ux = [
                ("Audit Existant", "Analyse de l'existant et pain points", 3, [
                    {"text": "Audit heuristique effectué"},
                    {"text": "Tests utilisateurs (5-8 personnes)"},
                    {"text": "Rapport d'audit remis"},
                ]),
                ("Recommandations UX", "Propositions d'amélioration", 5, [
                    {"text": "Parcours utilisateur optimisés"},
                    {"text": "Nouveaux wireframes créés"},
                    {"text": "Quick wins identifiés"},
                ]),
                ("Design UI Refondu", "Nouvelles maquettes graphiques", 7, [
                    {"text": "Nouvelle charte graphique"},
                    {"text": "Maquettes pages clés refaites"},
                    {"text": "Design system mis à jour"},
                ]),
                ("A/B Testing & Livraison", "Tests et déploiement", 5, [
                    {"text": "Setup A/B test (version actuelle vs refonte)"},
                    {"text": "Analyse des résultats"},
                    {"text": "Intégration version gagnante"},
                    {"text": "Documentation des changements"},
                ]),
            ]
            
            for idx, (title, desc, days, checklist) in enumerate(milestones_ux):
                MilestoneTemplate.objects.create(
                    workflow=workflow_ux,
                    title=title,
                    description=desc,
                    order=idx,
                    estimated_duration_days=days,
                    checklist_template=checklist,
                )
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Workflow '{workflow_ux.name}' créé avec {len(milestones_ux)} jalons"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Workflow '{workflow_ux.name}' existe déjà"
            ))
        
        # ============================================================
        # Résumé final
        # ============================================================
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🎉 SEED TERMINÉ"))
        self.stdout.write("=" * 60)
        
        total_workflows = WorkflowTemplate.objects.count()
        total_milestones = MilestoneTemplate.objects.count()
        
        self.stdout.write(f"\n📊 Statistiques:")
        self.stdout.write(f"   - {total_workflows} workflows disponibles")
        self.stdout.write(f"   - {total_milestones} templates de jalons au total")
        
        self.stdout.write(f"\n📝 Prochaines étapes:")
        self.stdout.write(f"   1. Vérifier dans l'admin : /admin/clients/workflowtemplate/")
        self.stdout.write(f"   2. Créer un projet et lui assigner un workflow")
        self.stdout.write(f"   3. Appeler project.generate_milestones_from_template()")
        self.stdout.write(f"\n✨ Fini ! Vos workflows sont prêts.\n")
