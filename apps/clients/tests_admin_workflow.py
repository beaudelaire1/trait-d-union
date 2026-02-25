"""Tests pour l'intégration admin des workflow templates.

Valide :
- Création de projet avec workflow → jalons générés automatiquement
- Création de projet sans workflow → jalons manuels
- Actions admin (générer, régénérer)
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from datetime import date

from apps.clients.models import ClientProfile, Project
from apps.clients.models_workflow import WorkflowTemplate, MilestoneTemplate
from apps.clients.admin import ProjectAdmin


def add_middleware_to_request(request, user):
    """Ajoute les middlewares nécessaires à un request de test."""
    # Ajouter session
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    # Ajouter messages
    request._messages = FallbackStorage(request)
    
    # Ajouter user
    request.user = user
    
    return request


class ProjectAdminIntegrationTestCase(TestCase):
    """Tests pour l'intégration admin Project + WorkflowTemplate."""
    
    def setUp(self):
        """Setup initial."""
        # Créer un utilisateur admin
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
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
        for i in range(3):
            MilestoneTemplate.objects.create(
                workflow=self.workflow,
                title=f"Jalon {i+1}",
                order=i,
                estimated_duration_days=7,
                checklist_template=[
                    {"text": f"Tâche {i+1}.1"},
                    {"text": f"Tâche {i+1}.2"},
                ]
            )
        
        # Setup admin
        self.site = AdminSite()
        self.admin = ProjectAdmin(Project, self.site)
        self.factory = RequestFactory()
    
    def test_create_project_with_workflow_generates_milestones(self):
        """Test : Créer un projet avec workflow → jalons générés automatiquement."""
        # Créer un projet avec workflow_template
        project = Project(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        
        # Simuler la sauvegarde via l'admin
        request = self.factory.get('/')
        request = add_middleware_to_request(request, self.user)
        self.admin.save_model(request, project, None, change=False)
        
        # Vérifications
        self.assertEqual(project.milestones.count(), 3)
        self.assertEqual(project.milestones.first().title, "Jalon 1")
        
        # Vérifier qu'une activité a été créée
        activities = project.activities.filter(activity_type='milestone_created')
        self.assertEqual(activities.count(), 1)
        self.assertIn("3 jalons créés", activities.first().description)
    
    def test_create_project_without_workflow_no_milestones(self):
        """Test : Créer un projet sans workflow → aucun jalon généré."""
        # Créer un projet SANS workflow_template
        project = Project(
            client=self.client_profile,
            name="Projet Manuel",
            start_date=date(2025, 2, 1),
        )
        
        # Simuler la sauvegarde via l'admin
        request = self.factory.get('/')
        request = add_middleware_to_request(request, self.user)
        self.admin.save_model(request, project, None, change=False)
        
        # Vérifications
        self.assertEqual(project.milestones.count(), 0)
    
    def test_create_project_with_existing_milestones_no_regeneration(self):
        """Test : Projet avec jalons existants → pas de régénération."""
        # Créer un projet avec workflow
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        
        # Ajouter des jalons manuellement
        from apps.clients.models import ProjectMilestone
        ProjectMilestone.objects.create(
            project=project,
            title="Jalon manuel",
            order=0,
        )
        
        # Simuler la sauvegarde via l'admin (modification)
        request = self.factory.get('/')
        request = add_middleware_to_request(request, self.user)
        self.admin.save_model(request, project, None, change=True)
        
        # Vérifications : pas de nouveaux jalons générés
        self.assertEqual(project.milestones.count(), 1)
        self.assertEqual(project.milestones.first().title, "Jalon manuel")
    
    def test_admin_action_generate_milestones(self):
        """Test : Action admin 'Générer les jalons'."""
        # Créer 3 projets avec workflow mais sans jalons
        projects = []
        for i in range(3):
            project = Project.objects.create(
                client=self.client_profile,
                name=f"Projet {i+1}",
                workflow_template=self.workflow,
                start_date=date(2025, 2, 1),
            )
            projects.append(project)
        
        # Simuler l'action admin
        request = self.factory.get('/')
        request = add_middleware_to_request(request, self.user)
        queryset = Project.objects.filter(id__in=[p.id for p in projects])
        
        self.admin.generate_milestones_action(request, queryset)
        
        # Vérifications
        for project in projects:
            project.refresh_from_db()
            self.assertEqual(project.milestones.count(), 3)
    
    def test_admin_action_regenerate_milestones(self):
        """Test : Action admin 'Régénérer les jalons'."""
        # Créer un projet avec jalons
        project = Project.objects.create(
            client=self.client_profile,
            name="Projet Test",
            workflow_template=self.workflow,
            start_date=date(2025, 2, 1),
        )
        project.generate_milestones_from_template()
        
        # Modifier un jalon
        milestone = project.milestones.first()
        milestone.title = "Jalon modifié"
        milestone.save()
        
        # Simuler l'action admin 'régénérer'
        request = self.factory.get('/')
        request = add_middleware_to_request(request, self.user)
        queryset = Project.objects.filter(id=project.id)
        
        self.admin.regenerate_milestones_action(request, queryset)
        
        # Vérifications : jalons régénérés (pas le titre modifié)
        project.refresh_from_db()
        self.assertEqual(project.milestones.count(), 3)
        self.assertEqual(project.milestones.first().title, "Jalon 1")  # Pas "Jalon modifié"
    
    def test_workflow_used_display(self):
        """Test : Affichage du workflow utilisé dans list_display."""
        # Projet avec workflow
        project_with_workflow = Project.objects.create(
            client=self.client_profile,
            name="Projet avec workflow",
            workflow_template=self.workflow,
        )
        
        # Projet sans workflow
        project_without_workflow = Project.objects.create(
            client=self.client_profile,
            name="Projet manuel",
        )
        
        # Vérifier l'affichage
        self.assertIn("Test Workflow", self.admin.workflow_used(project_with_workflow))
        self.assertIn("Manuel", self.admin.workflow_used(project_without_workflow))
