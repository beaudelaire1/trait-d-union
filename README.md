# Trait d’Union Studio — Site vitrine

Ce dépôt contient le code source du site vitrine de **Trait d’Union Studio** (TUS). Il s’agit d’un projet Django modulaire utilisant HTMX pour les interactions dynamiques et Tailwind CSS pour le design.

## Structure du projet

```
tus_website/
├── config/            # Configuration (settings, urls, middleware, wsgi)
├── apps/              # Applications Django (pages, portfolio, leads, resources)
├── templates/         # Gabarits Django (base, partials, pages, etc.)
├── static/            # Fichiers statiques (CSS, JS, images)
├── media/             # Fichiers uploadés par les utilisateurs
├── manage.py          # Point d’entrée Django
├── requirement.md     # Cahier des exigences
├── design.md          # Document de design
└── tasks.md           # Plan détaillé des tâches
```

## Prérequis

* Python 3.11
* [Pipenv](https://pipenv.pypa.io/) ou `pip` pour la gestion des dépendances
* [Node.js](https://nodejs.org/) et `npm`/`yarn` pour construire Tailwind CSS (facultatif si vous utilisez `django-tailwind`)

## Installation

1. **Cloner le dépôt** :

```bash
git clone <repo_url>
cd tus_website
```

2. **Créer l’environnement virtuel et installer les dépendances Python** :

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configurer Tailwind CSS** :

Si vous utilisez `django-tailwind`, suivez la documentation pour installer et compiler les fichiers CSS. Sinon, utilisez un outil comme PostCSS :

```bash
npm install
npm run build
```

4. **Créer la base de données et lancer les migrations** :

```bash
python manage.py migrate --settings=config.settings.development
```

5. **Démarrer le serveur de développement** :

```bash
python manage.py runserver --settings=config.settings.development
```

6. **Accéder au site** : ouvrez [http://localhost:8000](http://localhost:8000) dans votre navigateur.

## Exécution des tests

Les tests utilisent `pytest` et `pytest-django`. Pour les exécuter :

```bash
pip install -r requirements-dev.txt
pytest
```

Les tests property‑based reposent sur `hypothesis` et sont configurés dans `conftest.py`.

## Contribution

Le projet suit les exigences décrites dans `requirements.md`, le document de design `design.md` et le plan d’implémentation `tasks.md`. Avant de soumettre un correctif ou une fonctionnalité, merci de consulter ces documents et de mettre à jour les tests en conséquence. Les contributions sont les bienvenues via des branches et Pull Requests.

## Licence

Ce projet est fourni « tel quel » uniquement à des fins de formation ou de démonstration. Le contenu reste la propriété de Trait d’Union Studio.