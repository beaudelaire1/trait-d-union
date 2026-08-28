# Déploiement Trait d'Union Studio — OVH + Coolify

Cette configuration maintient **un seul service applicatif** : Gunicorn et Django-Q2 tournent dans le même conteneur. PostgreSQL reste une ressource séparée car il s'agit de la base persistante.

## 1. PostgreSQL

Créer une ressource PostgreSQL dans le même projet/environnement Coolify.

- Database: `traitdunion`
- User: `tus_admin`
- Port public: désactivé
- Sauvegardes: activées

Copier l'**Internal URL** fournie par Coolify dans `DATABASE_URL`.

Commencer avec `DB_SSLMODE=prefer` sur le réseau Docker privé. Si TLS PostgreSQL est ensuite activé explicitement, passer à `DB_SSLMODE=require`.

## 2. Application

Créer une Application depuis GitHub :

- Repository: `beaudelaire1/trait-d-union`
- Branch pendant la migration: `deploy/coolify-ovh`
- Build Pack: `Dockerfile`
- Dockerfile: `/Dockerfile.coolify`
- Port exposé: `8000`
- Domaine principal: `https://traitdunion.studio`

Le conteneur démarre `deploy/run_coolify.py`, qui supervise :

- Gunicorn
- Django-Q2 (`qcluster`)

Si l'un de ces processus critiques s'arrête, le conteneur se termine afin que Coolify puisse le redémarrer proprement.

## 3. Variables d'environnement

Importer les clés de `.env.coolify.example` dans Coolify et renseigner les secrets réels.

Valeurs obligatoires au minimum :

```env
DJANGO_SETTINGS_MODULE=config.settings.coolify
DJANGO_SECRET_KEY=<secret stable et long>
DJANGO_ALLOWED_HOSTS=traitdunion.studio,www.traitdunion.studio,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://traitdunion.studio,https://www.traitdunion.studio
CANONICAL_DOMAIN=traitdunion.studio
SITE_URL=https://traitdunion.studio
DATABASE_URL=<internal PostgreSQL URL>
DB_SSLMODE=prefer
Q_WORKERS=1
```

Conserver la même `DJANGO_SECRET_KEY` pendant toute la migration afin de ne pas invalider les sessions à chaque redémarrage.

## 4. Post-déploiement

Configurer comme Post-deployment Command :

```sh
sh ./coolify-postdeploy.sh
```

Le script applique les migrations et normalise les enregistrements django-allauth. La création du superuser est optionnelle et n'est exécutée que si `DJANGO_SUPERUSER_PASSWORD` est défini.

Après la première création du compte administrateur, supprimer `DJANGO_SUPERUSER_PASSWORD` des variables Coolify.

## 5. Tâches planifiées

Créer les Scheduled Tasks sur **la même application**, pas comme services supplémentaires.

### Avis Google Business

```text
0 */6 * * *
python manage.py sync_google_reviews
```

### Audit portfolio

```text
0 4 * * 1
python manage.py audit_portfolio_projects
```

### Rapports simulateur non livrés

```text
*/15 * * * *
python manage.py resend_unsent_simulator_reports
```

Vérifier le fuseau horaire configuré sur le serveur avant de considérer les heures cron comme définitives.

## 6. Médias

La configuration de production actuelle utilise Cloudinary lorsqu'il est configuré. Pour éviter d'ajouter un service de stockage pendant la migration, réutiliser les identifiants Cloudinary de la production actuelle si les médias y sont déjà stockés.

Ne pas basculer le domaine si Cloudinary n'est pas configuré et que l'application contient des médias uploadés nécessaires : le fallback local n'est pas une stratégie de stockage de production suffisante à lui seul.

## 7. Validation avant DNS

Avant de modifier le DNS :

```sh
python manage.py check --deploy --settings=config.settings.coolify
python manage.py showmigrations --settings=config.settings.coolify
```

Puis vérifier :

- `/healthz/` retourne HTTP 200 ;
- la page d'accueil charge ses assets statiques ;
- connexion admin + TOTP ;
- formulaires publics et CAPTCHA ;
- envoi d'un email transactionnel ;
- génération d'un PDF ;
- upload/affichage d'un média ;
- une tâche Django-Q2 test est effectivement consommée ;
- Stripe/webhooks si la fonctionnalité est active.

Le basculement DNS ne doit intervenir qu'après ces contrôles.
