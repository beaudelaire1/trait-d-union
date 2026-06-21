# Trait d’Union Studio — Site vitrine

Ce dépôt contient le code source du site vitrine de **Trait d’Union Studio** (TUS). Il s’agit d’un projet Django modulaire utilisant HTMX pour les interactions dynamiques et Tailwind CSS pour le design.

## Structure du projet

```
trait-d-union/
├── config/            # Configuration (settings, urls, middleware, wsgi, sitemaps)
├── apps/              # Applications Django (pages, portfolio, leads, devis, factures, …)
├── core/              # Services transverses (email, paiement, PDF, captcha, storage)
├── services/          # Catalogue de services (modèle Service)
├── templates/         # Gabarits Django (base, partials, pages, etc.)
├── static/            # Fichiers statiques (CSS, JS, images)
├── tests/             # Suite de tests transverses (pytest)
└── manage.py          # Point d’entrée Django
```

## Prérequis

* Python 3.12 (version CI ; 3.11 reste compatible)
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

Avant de soumettre un correctif ou une fonctionnalité, merci de mettre à jour les tests en conséquence et de vérifier que la suite `pytest` ainsi que `python manage.py check` passent. Les contributions se font via des branches et Pull Requests.

## Licence

Ce projet est fourni « tel quel » uniquement à des fins de formation ou de démonstration. Le contenu reste la propriété de Trait d’Union Studio.