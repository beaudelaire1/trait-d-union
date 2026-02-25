"""Modèles pour les templates de workflow et jalons réutilisables.

Architecture scalable :
- WorkflowTemplate : template de workflow (ex: "Site Web Standard", "App Mobile")
- MilestoneTemplate : template de jalon réutilisable
- Project.generate_milestones_from_template() : auto-génération
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class WorkflowTemplate(models.Model):
    """Template de workflow réutilisable pour les projets.
    
    Exemples :
    - "Site Web Standard" : 8 jalons (Analyse → Design → Dev → Recette → Livraison)
    - "App Mobile MVP" : 6 jalons
    - "Refonte UX" : 4 jalons
    """
    
    name = models.CharField(
        "Nom du workflow",
        max_length=200,
        unique=True,
        help_text="Ex: Site Web Standard, App Mobile, Refonte UX"
    )
    
    description = models.TextField(
        "Description",
        blank=True,
        help_text="Description du workflow et cas d'usage"
    )
    
    is_active = models.BooleanField(
        "Actif",
        default=True,
        help_text="Workflow disponible pour les nouveaux projets"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de workflow"
        verbose_name_plural = "Templates de workflows"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def duplicate(self, new_name: str) -> "WorkflowTemplate":
        """Duplique ce workflow avec un nouveau nom."""
        new_workflow = WorkflowTemplate.objects.create(
            name=new_name,
            description=f"Copie de {self.name}",
            is_active=True,
        )
        
        # Dupliquer les jalons
        for milestone_tpl in self.milestone_templates.all():
            MilestoneTemplate.objects.create(
                workflow=new_workflow,
                title=milestone_tpl.title,
                description=milestone_tpl.description,
                order=milestone_tpl.order,
                checklist_template=milestone_tpl.checklist_template,
                estimated_duration_days=milestone_tpl.estimated_duration_days,
            )
        
        return new_workflow


class MilestoneTemplate(models.Model):
    """Template de jalon réutilisable.
    
    Un jalon template définit :
    - Titre et description
    - Checklist par défaut
    - Ordre dans le workflow
    - Durée estimée
    """
    
    workflow = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name='milestone_templates',
        verbose_name="Workflow"
    )
    
    title = models.CharField(
        "Titre du jalon",
        max_length=200,
        help_text="Ex: Analyse des besoins, Design UI/UX, Développement"
    )
    
    description = models.TextField(
        "Description",
        blank=True,
        help_text="Description du jalon et livrables attendus"
    )
    
    order = models.PositiveIntegerField(
        "Ordre",
        default=0,
        help_text="Position dans le workflow (0 = premier)"
    )
    
    checklist_template = models.JSONField(
        "Checklist template",
        default=list,
        blank=True,
        help_text="Liste des tâches par défaut : [{text: 'Tâche 1'}, ...]"
    )
    
    estimated_duration_days = models.PositiveIntegerField(
        "Durée estimée (jours)",
        default=7,
        help_text="Durée estimée en jours pour ce jalon"
    )
    
    class Meta:
        verbose_name = "Template de jalon"
        verbose_name_plural = "Templates de jalons"
        ordering = ['workflow', 'order']
        unique_together = ['workflow', 'order']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.order}. {self.title}"
    
    def instantiate_for_project(self, project, start_date=None):
        """Crée une instance ProjectMilestone pour un projet.
        
        Args:
            project: Instance de Project
            start_date: Date de début (optionnel)
        
        Returns:
            ProjectMilestone créée
        """
        from datetime import timedelta
        from django.utils import timezone
        from .models import ProjectMilestone
        
        if start_date is None:
            start_date = timezone.now().date()
        
        # Calculer la date d'échéance
        due_date = start_date + timedelta(days=self.estimated_duration_days)
        
        # Préparer la checklist (copie du template)
        checklist = [
            {
                'id': idx,
                'text': item.get('text', ''),
                'checked': False,
                'completed_by': None,
                'completed_at': None,
            }
            for idx, item in enumerate(self.checklist_template)
        ]
        
        milestone = ProjectMilestone.objects.create(
            project=project,
            title=self.title,
            description=self.description,
            order=self.order,
            due_date=due_date,
            checklist=checklist,
            status='pending',
        )
        
        return milestone


# Extension du modèle Project (à ajouter dans apps/clients/models.py)
# Ou créer un mixin

class ProjectWithWorkflowMixin:
    """Mixin pour ajouter les workflows aux projets.
    
    À intégrer dans le modèle Project existant.
    """
    
    def generate_milestones_from_template(self, workflow_template, start_date=None):
        """Génère tous les jalons depuis un WorkflowTemplate.
        
        Args:
            workflow_template: Instance de WorkflowTemplate
            start_date: Date de début du premier jalon (optionnel)
        
        Returns:
            Liste des ProjectMilestone créées
        """
        from datetime import timedelta
        from django.utils import timezone
        
        if start_date is None:
            start_date = timezone.now().date()
        
        milestones = []
        current_date = start_date
        
        for milestone_tpl in workflow_template.milestone_templates.all().order_by('order'):
            milestone = milestone_tpl.instantiate_for_project(
                project=self,
                start_date=current_date
            )
            milestones.append(milestone)
            
            # Date de début du prochain jalon = date d'échéance du précédent
            current_date = milestone.due_date
        
        return milestones
    
    def reset_milestones(self):
        """Supprime tous les jalons du projet (utile avant régénération)."""
        self.milestones.all().delete()
    
    def regenerate_milestones(self, workflow_template, start_date=None):
        """Supprime et régénère tous les jalons."""
        self.reset_milestones()
        return self.generate_milestones_from_template(workflow_template, start_date)
