# Tâches planifiées — équivalent des services cron Render

Sur Render, chaque tâche planifiée était un **service facturé à part** qui
démarrait un conteneur Docker complet à chaque exécution. Le cas le plus
coûteux : `resend-reports` tournait toutes les 15 minutes, soit **96 démarrages
de conteneur par jour** pour une commande qui s'exécute en une seconde.

Sur Coolify, une tâche planifiée s'exécute **dans le conteneur déjà lancé**.
Ces trois services disparaissent donc de la facture, et une quatrième tâche
s'ajoute — la sauvegarde de la base, que Render assurait de son côté.

## Configuration dans Coolify

Interface : `Projet → Ressource → Scheduled Tasks → + Add`.

Pour chacune : **Container** = `web`.

| Nom | Commande | Fréquence (cron) |
|---|---|---|
| `sync-google-reviews` | `python manage.py sync_google_reviews` | `0 */6 * * *` |
| `audit-portfolio` | `python manage.py audit_portfolio_projects` | `0 4 * * 1` |
| `resend-reports` | `python manage.py resend_unsent_simulator_reports` | `*/15 * * * *` |
| `backup-database` | `python manage.py backup_database` | `30 2 * * *` |

Les horaires sont conservés à l'identique de `render.yaml`, à l'exception de
la sauvegarde (nouvelle) placée à 02h30 UTC, hors des heures de trafic.

## Pourquoi le conteneur `web` et non `worker`

Les deux conviendraient techniquement. `web` est retenu parce qu'il est le
seul dont l'indisponibilité est immédiatement visible : si le conteneur ne
tourne pas, le site est déjà tombé et la tâche manquée n'est pas le problème
principal. Le `worker` peut, lui, être redémarré ou redimensionné sans que
cela se voie — une tâche planifiée y serait silencieusement sautée.

## Vérifier après mise en place

```bash
# Exécution manuelle immédiate, dans le conteneur web
docker exec -it <conteneur-web> python manage.py resend_unsent_simulator_reports

# La sauvegarde sans rien envoyer, pour valider pg_dump et les accès
docker exec -it <conteneur-web> python manage.py backup_database --dry-run
```

Coolify conserve la sortie de chaque exécution dans l'onglet *Scheduled Tasks*.
À contrôler le lendemain de la bascule : les quatre tâches doivent y afficher
au moins une exécution réussie.

## Note sur `django-q2`

Le projet utilise `async_task` (`apps/leads`, `apps/einvoicing`, `core/tasks`)
mais **aucun worker `qcluster` ne tournait sur Render** : `core/tasks.py`
retombait sur une exécution synchrone, donc en pleine requête HTTP. Le service
`worker` de `docker-compose.coolify.yml` corrige ce point — les envois d'emails
et les générations de PDF repassent réellement en arrière-plan.

Ces tâches asynchrones sont distinctes des tâches planifiées ci-dessus : elles
sont déclenchées par le code, pas par un horaire.
