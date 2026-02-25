"""Tests pour le système de templates de workflow.

Valide :
- Création de WorkflowTemplate
- Génération de jalons depuis un template
- Duplication de workflow
- Régénération de jalons
"""
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from apps.clients.models import ClientProfile, Project
from apps.clients.models_workflow import WorkflowTemplate, MilestoneTemplate


class WorkflowTemplateTestCase(TestCase):
    """Tests pour WorkflowTemplate et MilestoneTemplate."""
    
    def setUp(self):
        """Setup initial pour les tests."""
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un client
        self.client_profile = ClientProfile.objects.create(
            user=self.user,
            company_name="Test Company"
        )
        
        # Créer un workflow template
        self.workflow = WorkflowTemplate.objects.create(
            name="Test Workflow",
            description="Workflow de test",
            is_active=True,
        )
        
        # Ajouter 3 jalons
        self.milestone1 = MilestoneTemplate.objects.create(
            workflow=self.workflow,
            title="Jalon 1",
            description="Premier jalon",
            order=0,
            estimated_duration_days=7,
            checklist_template=[
                {"text": "Tâche 1"},
                {"text": "Tâche 2"},
            ]
        )
        
        self.milestone2 = MilestoneTemplate.objects.create(
            workflow=self.workflow,
            title="Jalon 2",
            description="Deuxième jalon",
            order=1,
            estimated_duration_days=10,
            checklist_template=[
                {"text": "Tâche A"},
                {"text": "Tâche B"},
                {"text": "Tâche C"},
            ]
        )
        
        self.milestone3 = MilestoneTemplate.objects.create(
            workflow=self.workflow,
            title="Jalon 3",
            description="Troisième jalon",
            order=2,
            estimated_duration_days=5,
            checklist_template=[]
        )
    
    def test_workflow_creation(self):
        """Test : Création d'un workflow template."""
        self.assertEqual(self.workflow.name, "Test Workflow")
        self.assertEqual(self.workflow.milestone_templates.count(), 3)
        self.assertTrue(self.workflow.is_active)
    
    def test_milestone_ordering(self):
        """Test : Les jalons sont bien ordonnés."""
        milestones = self.workflow.milestone_templates.all()
        self.assertEqual(milestones[0].title, "Jalon 1")
        self.assertEqual(milestones[1].title, "Jalon 2")
        self.assertEqual(milestones[2].title, "Jalon 3")
    
    def test_generate_milestones_from_template(self):
        """Test : Génération de jalons depuis un template."""
        # Créer un projet
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        
        # Générer les jalons
        milestones = project.generate_milestones_from_template()
        
        # Vérifications
        self.assertEqual(len(milestones), 3)
        self.assertEqual(project.milestones.count(), 3)
        
        # Vérifier le premier jalon
        m1 = milestones[0]
        self.assertEqual(m1.title, "Jalon 1")
        self.assertEqual(m1.due_date, date(2025, 2, 8))  # 7 jours après le 1er février
        self.assertEqual(len(m1.checklist), 2)
        self.assertFalse(m1.checklist[0]['checked'])
        
        # Vérifier le deuxième jalon (date = date d'échéance du précédent)
        m2 = milestones[1]
        self.assertEqual(m2.title, "Jalon 2")
        self.assertEqual(m2.due_date, date(2025, 2, 18))  # 10 jours après le 8 février
        self.assertEqual(len(m2.checklist), 3)
        
        # Vérifier le troisième jalon
        m3 = milestones[2]
        self.assertEqual(m3.title, "Jalon 3")
        self.assertEqual(m3.due_date, date(2025, 2, 23))  # 5 jours après le 18 février
        self.assertEqual(len(m3.checklist), 0)
    
    def test_instantiate_milestone_for_project(self):
        """Test : Instanciation d'un jalon template pour un projet."""
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            start_date=date(2025, 3, 1),
        )
        
        milestone = self.milestone1.instantiate_for_project(
            project=project,
            start_date=date(2025, 3, 1)
        )
        
        self.assertEqual(milestone.project, project)
        self.assertEqual(milestone.title, "Jalon 1")
        self.assertEqual(milestone.due_date, date(2025, 3, 8))  # +7 jours
        self.assertEqual(len(milestone.checklist), 2)
    
    def test_reset_milestones(self):
        """Test : Suppression de tous les jalons d'un projet."""
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        
        # Générer les jalons
        project.generate_milestones_from_template()
        self.assertEqual(project.milestones.count(), 3)
        
        # Réinitialiser
        project.reset_milestones()
        self.assertEqual(project.milestones.count(), 0)
    
    def test_regenerate_milestones(self):
        """Test : Régénération complète des jalons."""
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        
        # Première génération
        project.generate_milestones_from_template()
        self.assertEqual(project.milestones.count(), 3)
        
        # Régénérer (doit supprimer et recréer)
        project.regenerate_milestones()
        self.assertEqual(project.milestones.count(), 3)
        
        # Vérifier que les jalons sont bien nouveaux (pas modifiés)
        first_milestone = project.milestones.first()
        self.assertEqual(first_milestone.title, "Jalon 1")
    
    def test_duplicate_workflow(self):
        """Test : Duplication d'un workflow avec ses jalons."""
        # Dupliquer le workflow
        new_workflow = self.workflow.duplicate("Test Workflow (Copie)")
        
        # Vérifications
        self.assertEqual(new_workflow.name, "Test Workflow (Copie)")
        self.assertEqual(new_workflow.milestone_templates.count(), 3)
        
        # Vérifier que les jalons sont différents (pas les mêmes instances)
        original_milestones = self.workflow.milestone_templates.all()
        duplicated_milestones = new_workflow.milestone_templates.all()
        
        for orig, dup in zip(original_milestones, duplicated_milestones):
            self.assertNotEqual(orig.id, dup.id)
            self.assertEqual(orig.title, dup.title)
            self.assertEqual(orig.order, dup.order)
    
    def test_workflow_without_template_raises_error(self):
        """Test : Erreur si projet sans workflow_template."""
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            start_date=date(2025, 2, 1),
        )
        
        with self.assertRaises(ValueError):
            project.generate_milestones_from_template()
    
    def test_scalability_20_projects(self):
        """Test : Créer 20 projets avec le même workflow (200 jalons au total)."""
        # Créer 20 projets
        projects = []
        for i in range(20):
            project = Project.objects.create(
                client=self.client_profile,
                name=f"Projet {i+1}",
                workflow_template=self.workflow,
                start_date=date(2025, 2, 1),
            )
            project.generate_milestones_from_template()
            projects.append(project)
        
        # Vérifications
        self.assertEqual(len(projects), 20)
        
        # Chaque projet a 3 jalons
        for project in projects:
            self.assertEqual(project.milestones.count(), 3)
        
        # Total : 60 jalons créés (20 × 3)
        from apps.clients.models import ProjectMilestone
        total_milestones = ProjectMilestone.objects.filter(project__in=projects).count()
        self.assertEqual(total_milestones, 60)
        
        # Vérifier qu'on peut modifier le template sans affecter les projets existants
        self.workflow.name = "Test Workflow (Modifié)"
        self.workflow.save()
        
        # Les jalons existants ne sont pas affectés
        self.assertEqual(projects[0].milestones.first().title, "Jalon 1")
