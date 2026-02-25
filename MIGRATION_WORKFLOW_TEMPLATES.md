# 🔄 Migration Workflow Templates

Guide pour migrer vers le système de templates de workflow réutilisables.

---

## 📋 Vue d'ensemble

**Avant :**  
- Créer manuellement 10 jalons × 20 projets = **200 jalons**
- Modifier un titre = **éditer 20 jalons individuellement**
- Aucune cohérence entre projets similaires

**Après :**  
- Créer **1 template** avec 10 jalons
- Appliquer le template à **20 projets** = **1 clic par projet**
- Modifier le template = **propagation automatique** (optionnel)

---

## 🚀 Étapes de déploiement

### 1. **Créer les migrations**

```bash
python manage.py makemigrations clients
python manage.py migrate
```

### 2. **Créer vos premiers templates de workflow**

#### Option A : Via l'admin Django

1. Aller dans **Admin > Workflow Templates > Ajouter**
2. Créer un workflow : "Site Web Standard"
3. Ajouter les jalons inline :
   - Jalon 1 : Analyse des besoins (7 jours)
   - Jalon 2 : Design UI/UX (10 jours)
   - Jalon 3 : Développement Front (14 jours)
   - etc.

#### Option B : Script de seed (recommandé)

```python
# apps/clients/management/commands/seed_workflow_templates.py
from django.core.management.base import BaseCommand
from apps.clients.models import WorkflowTemplate, MilestoneTemplate


class Command(BaseCommand):
    help = "Crée des templates de workflow par défaut"
    
    def handle(self, *args, **options):
        # Workflow : Site Web Standard
        workflow_web = WorkflowTemplate.objects.create(
            name="Site Web Standard",
            description="Workflow complet pour un site web vitrine ou e-commerce",
            is_active=True,
        )
        
        milestones_web = [
            ("Briefing & Analyse", "Recueil des besoins, analyse fonctionnelle", 5, [
                {"text": "Réunion de lancement"},
                {"text": "Cahier des charges validé"},
                {"text": "Planning projet défini"},
            ]),
            ("Architecture & UX", "Arborescence, wireframes, parcours utilisateur", 7, [
                {"text": "Arborescence validée"},
                {"text": "Wireframes desktop"},
                {"text": "Wireframes mobile"},
            ]),
            ("Design UI", "Maquettes graphiques HD", 10, [
                {"text": "Charte graphique validée"},
                {"text": "Maquettes desktop (3 pages min)"},
                {"text": "Maquettes mobile"},
                {"text": "Design system (boutons, typo, couleurs)"},
            ]),
            ("Développement Front", "Intégration HTML/CSS/JS", 14, [
                {"text": "Pages statiques intégrées"},
                {"text": "Version responsive testée"},
                {"text": "Animations & interactions"},
            ]),
            ("Développement Back", "Backend Django, base de données", 10, [
                {"text": "Modèles & admin configurés"},
                {"text": "API/endpoints créés"},
                {"text": "Formulaires fonctionnels"},
            ]),
            ("Contenu & SEO", "Rédaction, optimisation référencement", 5, [
                {"text": "Textes intégrés"},
                {"text": "Images optimisées"},
                {"text": "Balises meta & Open Graph"},
            ]),
            ("Tests & Recette", "Validation fonctionnelle et technique", 7, [
                {"text": "Tests cross-browser"},
                {"text": "Tests mobile (iOS/Android)"},
                {"text": "Performance (Lighthouse)"},
                {"text": "Corrections client"},
            ]),
            ("Livraison & Formation", "Mise en ligne et passation", 3, [
                {"text": "Mise en production"},
                {"text": "Formation client"},
                {"text": "Documentation remise"},
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
        
        # Workflow : App Mobile MVP
        workflow_app = WorkflowTemplate.objects.create(
            name="App Mobile MVP",
            description="Workflow pour une application mobile MVP (React Native / Flutter)",
            is_active=True,
        )
        
        milestones_app = [
            ("Product Discovery", "Définition du MVP et features", 5, [
                {"text": "User stories définies"},
                {"text": "Périmètre MVP validé"},
            ]),
            ("Design UX/UI", "Prototypes interactifs", 10, [
                {"text": "Wireframes iOS/Android"},
                {"text": "Design system mobile"},
                {"text": "Prototype cliquable"},
            ]),
            ("Développement", "Code natif ou cross-platform", 21, [
                {"text": "Architecture technique"},
                {"text": "Écrans principaux développés"},
                {"text": "API backend connectée"},
            ]),
            ("Tests & Beta", "Tests utilisateurs", 7, [
                {"text": "TestFlight / Play Console"},
                {"text": "Feedback beta-testeurs"},
                {"text": "Corrections bugs critiques"},
            ]),
            ("Lancement", "Publication stores", 3, [
                {"text": "Soumission App Store"},
                {"text": "Soumission Google Play"},
                {"text": "Assets stores (screenshots, vidéo)"},
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
```

**Lancer le seed :**

```bash
python manage.py seed_workflow_templates
```

---

## 🎯 Utilisation

### Créer un projet avec workflow

```python
from apps.clients.models import Project, WorkflowTemplate
from datetime import date

# 1. Récupérer un workflow
workflow = WorkflowTemplate.objects.get(name="Site Web Standard")

# 2. Créer un projet
project = Project.objects.create(
    client=client_profile,
    name="Refonte site Acme Corp",
    workflow_template=workflow,
    start_date=date(2025, 2, 1),
)

# 3. Générer automatiquement les jalons
milestones = project.generate_milestones_from_template()

# Résultat : 8 jalons créés automatiquement avec leurs checklists
```

### Régénérer les jalons d'un projet

```python
# Supprimer tous les jalons et les recréer
project.regenerate_milestones()

# Ou changer de workflow
new_workflow = WorkflowTemplate.objects.get(name="App Mobile MVP")
project.workflow_template = new_workflow
project.save()
project.regenerate_milestones()
```

---

## 📊 Dashboard & Analytics

### Vue d'ensemble des projets par phase

```python
from django.db.models import Count
from apps.clients.models import ProjectMilestone

# Combien de projets sont en phase "Design UI" ?
design_projects = ProjectMilestone.objects.filter(
    title="Design UI",
    status='in_progress'
).values('project__name').distinct()

print(f"{design_projects.count()} projets en Design")
```

### Durée moyenne par workflow

```python
from django.db.models import Avg
from apps.clients.models import Project

# Durée moyenne de livraison pour "Site Web Standard"
avg_days = Project.objects.filter(
    workflow_template__name="Site Web Standard",
    delivered_at__isnull=False
).annotate(
    duration=(models.F('delivered_at') - models.F('start_date'))
).aggregate(Avg('duration'))
```

---

## 🔧 Actions admin utiles

### Dupliquer un workflow

1. Aller dans **Admin > Workflow Templates**
2. Cocher le workflow à dupliquer
3. Action : **"Dupliquer les workflows sélectionnés"**
4. Renommer la copie

### Appliquer un template à un projet existant

```python
# Dans un admin action ou une vue
def apply_workflow_to_project(project, workflow_template):
    """Applique un workflow à un projet existant."""
    project.workflow_template = workflow_template
    project.save()
    
    # Option 1 : Régénérer (supprime les jalons actuels)
    project.regenerate_milestones()
    
    # Option 2 : Ajouter uniquement les jalons manquants
    existing_titles = project.milestones.values_list('title', flat=True)
    for milestone_tpl in workflow_template.milestone_templates.all():
        if milestone_tpl.title not in existing_titles:
            milestone_tpl.instantiate_for_project(project)
```

---

## 📉 Migration des projets existants

Si vous avez déjà des projets avec des jalons manuels :

```python
from apps.clients.models import Project, WorkflowTemplate

# Récupérer tous les projets sans workflow
projects = Project.objects.filter(workflow_template__isnull=True)

# Assigner un workflow par défaut
default_workflow = WorkflowTemplate.objects.get(name="Site Web Standard")

for project in projects:
    # NE PAS régénérer si jalons existants
    if project.milestones.count() == 0:
        project.workflow_template = default_workflow
        project.save()
        project.generate_milestones_from_template()
    else:
        # Juste assigner le template sans regénérer
        project.workflow_template = default_workflow
        project.save()
```

---

## 🎨 Personnalisation par projet

Même avec un template, chaque projet peut personnaliser :

- **Titre du jalon** : Éditer directement dans `ProjectMilestone`
- **Checklist** : Ajouter/supprimer des tâches dans le JSON
- **Date d'échéance** : Ajuster manuellement
- **Responsable** : Assigner un collaborateur

Le template est un **point de départ**, pas une contrainte.

---

## 📚 Cas d'usage avancés

### Workflow hybride

```python
# Générer les jalons de base
project.generate_milestones_from_template()

# Ajouter un jalon custom
ProjectMilestone.objects.create(
    project=project,
    title="Intégration CRM Salesforce",
    description="Jalon spécifique au client",
    order=99,  # À la fin
    due_date=date(2025, 6, 1),
)
```

### Workflow conditionnel

```python
# Workflow différent selon type de client
if client.subscription_tier == 'premium':
    workflow = WorkflowTemplate.objects.get(name="Site Web Premium")
else:
    workflow = WorkflowTemplate.objects.get(name="Site Web Standard")

project.generate_milestones_from_template(workflow)
```

---

## ✅ Checklist de déploiement

- [ ] Migrations appliquées
- [ ] Script de seed exécuté
- [ ] 2-3 templates créés (Site Web, App Mobile, etc.)
- [ ] Test : créer 1 projet et générer les jalons
- [ ] Vérifier dans l'admin : jalons bien créés avec checklists
- [ ] Former l'équipe sur l'utilisation des templates
- [ ] Documenter les workflows spécifiques de votre studio

---

## 🚨 Points d'attention

1. **Ne pas dupliquer les templates** : Créer avec `duplicate()` pour copier les jalons
2. **Éviter la régénération brutale** : Utiliser `reset_milestones()` seulement si nécessaire
3. **Préserver les validations** : Les jalons validés doivent rester intacts
4. **Tester les scripts** : Toujours tester sur un projet test avant de régénérer en masse

---

## 📞 Support

En cas de problème :

1. Vérifier les logs : `python manage.py check`
2. Test unitaire : `python manage.py test apps.clients.tests_workflow`
3. Rollback : `python manage.py migrate clients <numéro_migration_précédente>`
