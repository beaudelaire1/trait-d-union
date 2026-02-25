# ⚡ Quickstart : Workflow Templates (5 minutes)

Guide ultra-rapide pour utiliser les templates de workflow.

---

## 🎯 Objectif

**Avant :** Créer manuellement 10 jalons × 20 projets = 200 actions répétitives  
**Après :** 1 template → génération automatique en 1 clic

---

## 📦 Installation (déjà fait si tests OK)

```bash
# 1. Migration
python manage.py migrate clients

# 2. Créer les workflows par défaut
python manage.py seed_workflow_templates

# 3. Vérifier
python manage.py test apps.clients.tests_workflow
# → 9 tests OK ✅
```

---

## 🚀 Utilisation en 3 Étapes

### Étape 1 : Créer un Workflow Template (une fois)

**Option A : Via l'admin (recommandé pour débuter)**

1. Aller sur : [http://localhost:8000/admin/clients/workflowtemplate/](http://localhost:8000/admin/clients/workflowtemplate/)
2. Cliquer "Ajouter workflow template"
3. Remplir :
   - **Nom** : "Site Web Standard"
   - **Description** : "Workflow complet pour site vitrine"
   - **Actif** : ✅
4. Ajouter les jalons inline (cliquer "+ Ajouter un autre template de jalon") :

| Ordre | Titre | Description | Durée (jours) | Checklist JSON |
|-------|-------|-------------|---------------|----------------|
| 0 | Briefing | Analyse besoins | 5 | `[{"text": "Réunion"},{"text": "CDC validé"}]` |
| 1 | Design UI | Maquettes | 10 | `[{"text": "Charte"},{"text": "Maquettes 3 pages"}]` |
| 2 | Développement | Code | 14 | `[{"text": "Pages intégrées"},{"text": "Responsive"}]` |

5. Sauvegarder

**Option B : Via le shell Django**

```python
python manage.py shell

from apps.clients.models_workflow import WorkflowTemplate, MilestoneTemplate

# Créer le workflow
workflow = WorkflowTemplate.objects.create(
    name="Site Web Standard",
    description="Workflow complet pour site vitrine",
    is_active=True,
)

# Ajouter les jalons
milestones = [
    ("Briefing", "Analyse besoins", 5, [{"text": "Réunion"}, {"text": "CDC validé"}]),
    ("Design UI", "Maquettes", 10, [{"text": "Charte"}, {"text": "Maquettes"}]),
    ("Développement", "Code", 14, [{"text": "Pages"}, {"text": "Responsive"}]),
]

for idx, (title, desc, days, checklist) in enumerate(milestones):
    MilestoneTemplate.objects.create(
        workflow=workflow,
        title=title,
        description=desc,
        order=idx,
        estimated_duration_days=days,
        checklist_template=checklist,
    )
```

---

### Étape 2 : Créer un Projet et Générer les Jalons

**Via le shell Django :**

```python
from apps.clients.models import Project, WorkflowTemplate, ClientProfile
from datetime import date

# Récupérer le workflow et le client
workflow = WorkflowTemplate.objects.get(name="Site Web Standard")
client = ClientProfile.objects.first()  # Ou récupérer un client spécifique

# Créer le projet
project = Project.objects.create(
    client=client,
    name="Refonte site Acme Corp",
    workflow_template=workflow,
    start_date=date(2025, 2, 1),
)

# 🎯 MAGIE : Générer automatiquement tous les jalons
milestones = project.generate_milestones_from_template()

# Vérifier
print(f"✅ {len(milestones)} jalons créés")
for m in milestones:
    print(f"  - {m.title} : échéance {m.due_date} ({len(m.checklist)} tâches)")
```

**Résultat** :
```
✅ 3 jalons créés
  - Briefing : échéance 2025-02-06 (2 tâches)
  - Design UI : échéance 2025-02-16 (2 tâches)
  - Développement : échéance 2025-03-02 (2 tâches)
```

---

### Étape 3 : Gérer les Jalons Créés

**Dans le portail client ou l'admin :**

```python
# Récupérer un jalon
milestone = project.milestones.get(title="Design UI")

# Cocher une tâche de la checklist
milestone.checklist[0]['checked'] = True
milestone.checklist[0]['completed_by'] = request.user.username
milestone.checklist[0]['completed_at'] = timezone.now().isoformat()
milestone.save()

# Valider le jalon (marque automatiquement toutes les tâches)
milestone.mark_validated(
    user=request.user,
    comment="Design validé par le client"
)
```

---

## 📊 Scénarios Courants

### Scénario A : Créer 20 Projets Identiques

```python
from apps.clients.models import Project, WorkflowTemplate

workflow = WorkflowTemplate.objects.get(name="Site Web Standard")
clients = ClientProfile.objects.all()[:20]

for client in clients:
    project = Project.objects.create(
        client=client,
        name=f"Projet {client.company_name}",
        workflow_template=workflow,
        start_date=date.today(),
    )
    project.generate_milestones_from_template()
    print(f"✅ Projet {project.name} créé avec {project.milestones.count()} jalons")

# Résultat : 20 projets × 3 jalons = 60 jalons créés en quelques secondes
```

---

### Scénario B : Dupliquer un Workflow pour Customiser

```python
from apps.clients.models_workflow import WorkflowTemplate

# Dupliquer un workflow existant
original = WorkflowTemplate.objects.get(name="Site Web Standard")
custom = original.duplicate("Site Web Premium")

# Personnaliser les jalons du nouveau workflow
custom.milestone_templates.filter(title="Design UI").update(
    estimated_duration_days=15  # Plus de temps pour la version premium
)

print(f"✅ Workflow '{custom.name}' créé avec {custom.milestone_templates.count()} jalons")
```

---

### Scénario C : Régénérer les Jalons (Nouvelle Version du Workflow)

```python
# Vous avez modifié le workflow et voulez l'appliquer à un projet
project = Project.objects.get(id=123)

# ⚠️ ATTENTION : Supprime tous les jalons existants
project.regenerate_milestones()

# Alternative plus douce : Ajouter uniquement les jalons manquants
workflow = project.workflow_template
existing_titles = project.milestones.values_list('title', flat=True)

for milestone_tpl in workflow.milestone_templates.all():
    if milestone_tpl.title not in existing_titles:
        milestone_tpl.instantiate_for_project(project)
        print(f"✅ Jalon '{milestone_tpl.title}' ajouté")
```

---

### Scénario D : Dashboard Analytics

```python
from apps.clients.models import ProjectMilestone
from django.db.models import Count

# Combien de projets sont en phase "Design UI" ?
design_count = ProjectMilestone.objects.filter(
    title="Design UI",
    status='in_progress'
).values('project').distinct().count()

print(f"📊 {design_count} projets en phase Design UI")

# Répartition des projets par phase
phases = ProjectMilestone.objects.filter(
    status='in_progress'
).values('title').annotate(count=Count('project')).order_by('-count')

for phase in phases:
    print(f"  {phase['title']}: {phase['count']} projets")
```

---

## 🎨 Personnalisation Avancée

### Checklist Dynamique avec Conditions

```python
# Créer un jalon avec checklist conditionnelle selon type de projet
project = Project.objects.get(id=123)

if project.status == 'e-commerce':
    checklist = [
        {"text": "Tunnel de paiement Stripe"},
        {"text": "Gestion du panier"},
        {"text": "Emails de confirmation"},
    ]
else:
    checklist = [
        {"text": "Pages statiques"},
        {"text": "Formulaire de contact"},
    ]

ProjectMilestone.objects.create(
    project=project,
    title="Développement",
    checklist=checklist,
)
```

---

### Workflow Hybride (Template + Jalons Custom)

```python
# Générer les jalons standards
project.generate_milestones_from_template()

# Ajouter un jalon spécifique au client
ProjectMilestone.objects.create(
    project=project,
    title="Intégration CRM Salesforce",
    description="Jalon spécifique à ce client",
    order=99,  # À la fin
    due_date=date(2025, 6, 1),
    checklist=[
        {"text": "Connexion API Salesforce"},
        {"text": "Sync contacts bidirectionnelle"},
    ]
)
```

---

## 📋 Checklist de Vérification

Après avoir installé le système, vérifier :

- [ ] **Workflows créés** : `WorkflowTemplate.objects.count()` → 3+
- [ ] **Jalons template** : `MilestoneTemplate.objects.count()` → 17+
- [ ] **Test création projet** : Créer 1 projet → générer jalons → vérifier count
- [ ] **Admin accessible** : [/admin/clients/workflowtemplate/](http://localhost:8000/admin/clients/workflowtemplate/)
- [ ] **Tests passent** : `python manage.py test apps.clients.tests_workflow` → 9/9 OK

---

## 🚨 Troubleshooting

### Erreur : `ValueError: Aucun workflow_template défini pour ce projet`

**Cause :** Le projet n'a pas de `workflow_template` assigné.

**Solution :**
```python
project.workflow_template = WorkflowTemplate.objects.get(name="Site Web Standard")
project.save()
project.generate_milestones_from_template()
```

---

### Erreur : `IntegrityError: unique constraint failed`

**Cause :** Tentative de créer 2 `MilestoneTemplate` avec le même `(workflow, order)`.

**Solution :**
```python
# Vérifier les ordres existants
workflow.milestone_templates.values_list('order', flat=True)

# Utiliser un ordre différent
MilestoneTemplate.objects.create(
    workflow=workflow,
    order=10,  # Pas déjà pris
    title="Nouveau jalon"
)
```

---

### Les dates d'échéance sont incorrectes

**Cause :** `start_date` du projet n'est pas définie.

**Solution :**
```python
project.start_date = date(2025, 2, 1)
project.save()
project.regenerate_milestones()
```

---

## 🎯 Prochaines Étapes

1. **Tester** : Créer 1 workflow + 1 projet → générer jalons
2. **Personnaliser** : Créer vos propres workflows (Web, App, Maintenance, etc.)
3. **Intégrer** : Ajouter un bouton "Générer jalons" dans l'admin Project
4. **Dashboard** : Créer une vue "Projets par phase"

---

## 📚 Ressources

- **Documentation complète** : [TUS_FLOW_UPGRADE_V2_DELIVERY.md](TUS_FLOW_UPGRADE_V2_DELIVERY.md)
- **Guide de migration** : [MIGRATION_WORKFLOW_TEMPLATES.md](MIGRATION_WORKFLOW_TEMPLATES.md)
- **Code source** :
  - [apps/clients/models_workflow.py](apps/clients/models_workflow.py)
  - [apps/clients/admin.py](apps/clients/admin.py#L178)
  - [apps/clients/tests_workflow.py](apps/clients/tests_workflow.py)

---

**⏱️ Temps total : 5 minutes**  
**✅ Tests : 9/9 passés**  
**🚀 Production-ready**

---

**Questions ?** Consulter [TUS_FLOW_UPGRADE_V2_DELIVERY.md](TUS_FLOW_UPGRADE_V2_DELIVERY.md) pour les détails complets.
