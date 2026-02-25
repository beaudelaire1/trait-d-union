# ⚡ Création de Projet avec Jalons Automatiques

Guide ultra-rapide pour le nouveau workflow intégré.

---

## 🎯 Ce qui a changé

**AVANT (2 étapes séparées) :**
```python
# Étape 1 : Créer le projet
project = Project.objects.create(...)

# Étape 2 : Générer les jalons
project.generate_milestones_from_template()
```

**MAINTENANT (1 seule étape) :**
```python
# Créer le projet avec workflow_template
# → Les jalons sont générés automatiquement 🎉
project = Project.objects.create(
    client=client,
    name="Refonte Acme",
    workflow_template=workflow,  # ← Ça suffit !
)
```

---

## 📋 Utilisation dans l'Admin Django

### Scénario A : Créer un projet avec workflow (jalons automatiques)

1. **Aller dans Admin > Projects > Ajouter un projet**

2. **Remplir le formulaire :**
   - Client : Acme Corp
   - Nom : Refonte site Acme
   - Description : ...
   - **Workflow template : "Site Web Standard"** ← Sélectionner ici
   - Date de début : 01/02/2025

3. **Cliquer sur "Enregistrer"**

4. **🎉 Magie : 8 jalons créés automatiquement !**
   - Message : "✅ 8 jalons générés automatiquement depuis le workflow 'Site Web Standard'"
   - Les jalons apparaissent immédiatement dans l'onglet "Jalons"

### Scénario B : Créer un projet sans workflow (jalons manuels)

1. **Aller dans Admin > Projects > Ajouter un projet**

2. **Remplir le formulaire :**
   - Client : Acme Corp
   - Nom : Projet custom
   - **Workflow template : (vide)** ← Ne rien sélectionner
   - Date de début : 01/02/2025

3. **Ajouter des jalons manuellement dans l'inline :**
   - Jalon 1 : Briefing
   - Jalon 2 : Design
   - Jalon 3 : Développement

4. **Cliquer sur "Enregistrer"**

5. **Résultat : Jalons manuels créés**

### Scénario C : Générer les jalons après coup

Si vous avez créé un projet sans workflow et voulez générer les jalons plus tard :

1. **Aller dans Admin > Projects**

2. **Cocher les projets concernés**

3. **Action : "🎯 Générer les jalons depuis workflow"**

4. **Cliquer sur "Go"**

5. **Résultat : Jalons générés pour tous les projets sélectionnés**

---

## 🔄 Actions Admin Disponibles

### Action 1 : Générer les jalons

**Utilité :** Génère les jalons depuis le workflow_template si aucun jalon n'existe.

**Conditions :**
- Le projet doit avoir un `workflow_template` assigné
- Le projet ne doit pas avoir de jalons existants

**Comportement :**
- ✅ Génère les jalons automatiquement
- ✅ Log une activité dans le projet
- ⚠️ Ignore les projets sans workflow ou avec jalons existants

### Action 2 : Régénérer les jalons

**Utilité :** Supprime TOUS les jalons existants et les régénère depuis le workflow_template.

**⚠️ ATTENTION : Cette action est destructive !**

**Conditions :**
- Le projet doit avoir un `workflow_template` assigné

**Comportement :**
- 🗑️ Supprime tous les jalons existants (validés ou non)
- ✅ Régénère les jalons depuis le template
- ✅ Log une activité dans le projet

**Cas d'usage :**
- Vous avez modifié le workflow_template et voulez l'appliquer aux projets existants
- Vous voulez "réinitialiser" un projet

---

## 📊 Interface Admin

### Liste des projets

**Nouvelles colonnes :**
- **Workflow** : Affiche "✅ Site Web Standard" ou "❌ Manuel"

**Filtres :**
- Par workflow template
- Par statut
- Par date de création

### Formulaire de création/édition

**Section "Workflow & Jalons" :**
```
┌──────────────────────────────────────────────────────────┐
│ Workflow & Jalons                                        │
├──────────────────────────────────────────────────────────┤
│ 💡 Conseil : Sélectionnez un workflow pour générer      │
│    automatiquement les jalons.                           │
│    Les jalons seront créés lors de la sauvegarde si      │
│    aucun jalon n'existe déjà.                            │
│    Vous pouvez aussi ajouter des jalons manuellement     │
│    ci-dessous.                                            │
│                                                           │
│ Workflow template : [Site Web Standard ▼]               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ Jalons (ProjectMilestone)                                │
├──────────────────────────────────────────────────────────┤
│ Ordre │ Titre      │ Description │ Statut  │ Échéance   │
│ 0     │ Briefing   │ ...         │ pending │ 2025-02-06 │
│ 1     │ Design UI  │ ...         │ pending │ 2025-02-16 │
│ 2     │ Développement│ ...       │ pending │ 2025-03-02 │
└──────────────────────────────────────────────────────────┘
```

---

## 🧪 Exemples Concrets

### Exemple 1 : Créer 5 projets avec le même workflow

```python
from apps.clients.models import Project, WorkflowTemplate, ClientProfile

workflow = WorkflowTemplate.objects.get(name="Site Web Standard")
clients = ClientProfile.objects.all()[:5]

for client in clients:
    project = Project.objects.create(
        client=client,
        name=f"Projet {client.company_name}",
        workflow_template=workflow,  # ← Jalons générés auto
        start_date=date.today(),
    )
    print(f"✅ {project.name} : {project.milestones.count()} jalons créés")

# Résultat :
# ✅ Projet Acme Corp : 8 jalons créés
# ✅ Projet TechCorp : 8 jalons créés
# ✅ Projet WebAgency : 8 jalons créés
# ✅ Projet StartupXYZ : 8 jalons créés
# ✅ Projet BigClient : 8 jalons créés
```

### Exemple 2 : Créer un projet avec jalons custom

```python
# Créer un projet sans workflow
project = Project.objects.create(
    client=client,
    name="Projet Custom",
    # workflow_template=None  ← Pas de workflow
)

# Ajouter des jalons manuellement
from apps.clients.models import ProjectMilestone

ProjectMilestone.objects.create(
    project=project,
    title="Phase 1 : Custom",
    order=0,
    due_date=date(2025, 3, 1),
    checklist=[
        {"id": 0, "text": "Tâche custom 1", "checked": False},
        {"id": 1, "text": "Tâche custom 2", "checked": False},
    ]
)
```

### Exemple 3 : Workflow hybride (template + jalons custom)

```python
# Créer un projet avec workflow standard
project = Project.objects.create(
    client=client,
    name="Projet Hybride",
    workflow_template=workflow,  # ← 8 jalons générés
)

# Ajouter un jalon custom spécifique au client
ProjectMilestone.objects.create(
    project=project,
    title="Intégration CRM Salesforce",
    description="Jalon spécifique à ce client",
    order=99,  # À la fin
    due_date=date(2025, 6, 1),
    checklist=[
        {"id": 0, "text": "Connexion API Salesforce", "checked": False},
        {"id": 1, "text": "Sync bidirectionnelle", "checked": False},
    ]
)

# Résultat : 8 jalons standards + 1 jalon custom
```

---

## 🎨 Personnalisation

### Changer de workflow après création

```python
# Projet créé avec "Site Web Standard"
project = Project.objects.get(id=123)

# Changer pour "App Mobile MVP"
new_workflow = WorkflowTemplate.objects.get(name="App Mobile MVP")
project.workflow_template = new_workflow
project.save()

# Régénérer les jalons (⚠️ supprime les existants)
project.regenerate_milestones()
```

### Modifier les jalons générés

```python
# Récupérer un jalon
milestone = project.milestones.get(title="Design UI")

# Modifier le titre
milestone.title = "Design UI/UX + Prototype"
milestone.save()

# Ajouter une tâche custom
milestone.checklist.append({
    'id': len(milestone.checklist),
    'text': "Validation client par vidéo",
    'checked': False,
})
milestone.save()
```

---

## 🚀 Workflow Recommandé

### Pour un nouveau projet type (ex: site web)

1. **Admin > Projects > Ajouter**
2. **Sélectionner workflow : "Site Web Standard"**
3. **Enregistrer**
4. **🎉 8 jalons créés automatiquement**
5. **(Optionnel) Personnaliser les jalons si besoin**

### Pour un projet custom

1. **Admin > Projects > Ajouter**
2. **Workflow template : (vide)**
3. **Ajouter les jalons manuellement dans l'inline**
4. **Enregistrer**

### Pour un projet hybride

1. **Admin > Projects > Ajouter**
2. **Sélectionner workflow de base**
3. **Enregistrer** (jalons générés)
4. **Modifier le projet**
5. **Ajouter des jalons custom dans l'inline**
6. **Enregistrer**

---

## 📊 Avantages

| Aspect | Avant | Maintenant | Gain |
|--------|-------|------------|------|
| **Création projet** | 2 étapes séparées | 1 étape | **50%** ↓ |
| **Jalons générés** | Manuellement après création | Automatiquement à la création | **100%** ↑ |
| **Interface** | Code Python nécessaire | Interface admin intuitive | **∞** ↑ |
| **Flexibilité** | Template OU manuel | Template ET manuel (hybride) | **100%** ↑ |

---

## ✅ Checklist

Après avoir créé un projet, vérifier :

- [ ] **Projet créé** : Visible dans Admin > Projects
- [ ] **Jalons générés** : Onglet "Jalons" contient les jalons
- [ ] **Activité logged** : Onglet "Activités" contient "Jalons générés automatiquement"
- [ ] **Workflow assigné** : Colonne "Workflow" affiche "✅ [nom du workflow]"

---

## 🎯 Résumé

**1 seule action : Sélectionner un workflow à la création du projet**

→ Les jalons sont générés automatiquement 🎉

**Pas besoin de code Python, tout se fait dans l'interface admin.**

**Workflow hybride possible : Template + jalons custom**

---

**Temps de création d'un projet avec 10 jalons :**
- Avant : **5-10 minutes** (création + génération manuelle)
- Maintenant : **30 secondes** (1 formulaire)

**Gain de temps : 90% 🚀**
