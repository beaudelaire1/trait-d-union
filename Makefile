# ============================================
# Makefile — Trait d'Union Studio
# ============================================
.DEFAULT_GOAL := help

PYTHON ?= python
MANAGE = $(PYTHON) manage.py

.PHONY: help dev test lint migrate build collectstatic check shell

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

dev: ## Lance le serveur de développement
	$(MANAGE) runserver --settings=config.settings.development

test: ## Lance les tests avec pytest
	$(PYTHON) -m pytest -v --tb=short

lint: ## Lint Python (flake8) + check Django
	$(PYTHON) -m flake8 apps/ config/ core/ services/ --max-line-length=120 --exclude=migrations
	$(MANAGE) check --settings=config.settings.development

migrate: ## Applique les migrations
	$(MANAGE) migrate --settings=config.settings.development

build: ## Build de production (collectstatic + check)
	$(MANAGE) collectstatic --noinput --settings=config.settings.production
	$(MANAGE) check --deploy --settings=config.settings.production

collectstatic: ## Collecte les fichiers statiques
	$(MANAGE) collectstatic --noinput --settings=config.settings.development

check: ## Vérification Django (settings, templates, etc.)
	$(MANAGE) check --settings=config.settings.development

shell: ## Shell Django interactif
	$(MANAGE) shell --settings=config.settings.development
