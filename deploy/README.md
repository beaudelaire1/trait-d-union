# Migration Render → OVH + Coolify

Runbook de bascule de l'hébergement, motivé par le coût (5 services Render
facturés) et par les performances (plan *starter* : 512 Mo de RAM et 0,5 vCPU,
insuffisants pour le rendu PDF WeasyPrint).

**Principe directeur : Render reste en production et intact jusqu'à l'étape 7.**
Toutes les étapes précédentes sont préparatoires et réversibles. En cas de
problème après bascule, le retour arrière consiste à remettre le DNS — Render
n'a pas été touché.

---

## Ce qui change

| | Render | OVH + Coolify |
|---|---|---|
| Web | 1 service *starter* (512 Mo) | Conteneur sur VPS 4 vCPU / 12 Go |
| Tâches planifiées | 3 services facturés | Tâches planifiées Coolify (inclus) |
| Worker asynchrone | **aucun** | Conteneur `worker` (qcluster) |
| PostgreSQL | Managé, sauvegardé | Conteneur + sauvegarde vers Object Storage |
| Redis | **non provisionné** | Conteneur |
| Médias | Cloudinary | OVH Object Storage |
| TLS / proxy | Load balancer Render | Traefik intégré à Coolify |

Deux manques de la configuration Render sont corrigés au passage : l'absence de
Redis (le cache retombait sur LocMem, cloisonné par worker gunicorn, et le
rate limiting fonctionnait en mode dégradé) et l'absence de worker `qcluster`
(les tâches censées être asynchrones s'exécutaient en pleine requête HTTP).

---

## 1. Provisionner le VPS

VPS OVH **4 vCPU / 12 Go** (gamme Comfort ou Elite), Debian 12, datacenter
Gravelines ou Strasbourg.

```bash
ssh debian@<ip-du-vps>
sudo apt update && sudo apt upgrade -y

# Pare-feu : seuls SSH, HTTP et HTTPS sont ouverts.
# Postgres et Redis restent sur le réseau interne Docker.
sudo apt install -y ufw
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
sudo ufw --force enable
```

> Le port 8000 n'est **jamais** ouvert : Traefik est le seul point d'entrée.

## 2. Installer Coolify

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
```

L'interface répond ensuite sur `http://<ip-du-vps>:8000`. Créer le compte
administrateur **immédiatement** — l'inscription est ouverte tant que personne
ne l'a fait. Activer ensuite la double authentification.

## 3. Créer le stockage objet OVH

Espace client OVH → *Public Cloud* → *Object Storage* → conteneur S3, région
`gra`, **deux conteneurs** :

- `tus-media` — médias, **accès public en lecture** (servis aux visiteurs) ;
- `tus-backups` — sauvegardes, **strictement privé**.

Créer un utilisateur S3 et noter la clé d'accès et la clé secrète.

> Vérifier que `tus-backups` est bien privé. Un conteneur de sauvegardes
> exposé publiquement, c'est toute la base clients — leads, devis, factures —
> accessible en une URL.

## 4. Déployer la stack dans Coolify

*+ New* → *Docker Compose* → dépôt `beaudelaire1/trait-d-union`, branche `main`,
fichier `docker-compose.coolify.yml`.

Renseigner les variables d'environnement (onglet *Environment Variables*) :

```bash
# ── Obligatoires ───────────────────────────────────────────────
DJANGO_SECRET_KEY=          # openssl rand -base64 48
POSTGRES_PASSWORD=          # openssl rand -base64 32
REDIS_PASSWORD=             # openssl rand -base64 32
POSTGRES_VERSION=16         # DOIT correspondre à la version Render (étape 5)

# ── Domaines ───────────────────────────────────────────────────
DJANGO_ALLOWED_HOSTS=traitdunion.it,www.traitdunion.it
CANONICAL_DOMAIN=www.traitdunion.it
SITE_URL=https://www.traitdunion.it

# ── Médias (OVH Object Storage) ────────────────────────────────
S3_BUCKET_NAME=tus-media
S3_ENDPOINT_URL=https://s3.gra.io.cloud.ovh.net
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_REGION_NAME=gra

# ── Sauvegardes ────────────────────────────────────────────────
BACKUP_S3_BUCKET=tus-backups
BACKUP_ENCRYPTION_KEY=      # openssl rand -base64 32 — À CONSERVER HORS DU VPS
BACKUP_RETENTION_DAYS=30

# ── Secrets repris de Render (Environment → onglet du service web) ──
BREVO_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
GOOGLE_PLACES_API_KEY=
GOOGLE_PLACE_ID=
PAGESPEED_API_KEY=
SENTRY_DSN=
```

> `BACKUP_ENCRYPTION_KEY` doit être stockée **ailleurs que sur le VPS** (gestionnaire
> de mots de passe). Perdue, les sauvegardes chiffrées deviennent illisibles —
> et une sauvegarde conservée à côté de sa clé sur la même machine ne protège
> pas du scénario qu'elle est censée couvrir.

Ne pas encore associer le domaine de production : déployer d'abord sur le
sous-domaine temporaire fourni par Coolify, pour valider avant bascule.

## 5. Migrer les données PostgreSQL

Vérifier d'abord la version majeure côté Render — un dump PostgreSQL 16 ne se
restaure pas dans un PostgreSQL 15 :

```bash
psql "$RENDER_DATABASE_URL" -c "SELECT version();"
```

Ajuster `POSTGRES_VERSION` dans Coolify si nécessaire, puis :

```bash
# Depuis le VPS — dump de la base Render (URL externe, dashboard Render)
pg_dump --format=custom --no-owner --no-privileges \
        --file=render.dump "$RENDER_DATABASE_URL"

# Restauration dans le conteneur Postgres de la stack
docker cp render.dump <conteneur-postgres>:/tmp/render.dump
docker exec -it <conteneur-postgres> \
    pg_restore --no-owner --no-privileges --clean --if-exists \
               -U tus_admin -d traitdunion /tmp/render.dump
```

Contrôler ensuite que le compte des tables principales correspond à Render :

```bash
docker exec -it <conteneur-web> python manage.py shell -c "
from apps.leads.models import Lead
from apps.devis.models import Quote
from apps.factures.models import Invoice
print('leads', Lead.objects.count())
print('devis', Quote.objects.count())
print('factures', Invoice.objects.count())
"
```

## 6. Migrer les médias

À lancer **pendant que Cloudinary est encore actif** — la commande lit chez
Cloudinary et écrit chez OVH, sans jamais modifier la base :

```bash
# Inventaire, sans rien transférer
docker exec -it <conteneur-web> python manage.py migrate_media_to_s3 --dry-run

# Échantillon de 5 fichiers, pour valider les accès S3
docker exec -it <conteneur-web> python manage.py migrate_media_to_s3 --limit 5

# Transfert complet (relançable : les fichiers déjà copiés sont ignorés)
docker exec -it <conteneur-web> python manage.py migrate_media_to_s3
```

Les chemins stockés en base sont conservés à l'identique. C'est ce qui rend
l'opération réversible : retirer les variables `S3_*` suffit à revenir à
Cloudinary.

Garder les variables `CLOUDINARY_*` renseignées pendant toute la migration.
`config/settings/production.py` donne la priorité à S3 quand les deux sont
présents — Cloudinary reste donc un filet, sans effet tant que S3 répond.

## 7. Basculer le DNS

Étape irréversible côté visiteurs. Ne la faire qu'après avoir validé le site
complet sur le sous-domaine temporaire Coolify : page d'accueil, simulateurs,
génération de PDF, envoi d'un devis, tunnel de paiement Stripe.

1. Associer `traitdunion.it` et `www.traitdunion.it` à la ressource dans
   Coolify (le certificat Let's Encrypt est émis automatiquement).
2. Chez le registrar, abaisser le TTL à 300 s **au moins une heure avant**.
3. Faire pointer l'enregistrement `A` vers l'IP du VPS.
4. Surveiller la propagation, puis remonter le TTL une fois stabilisé.

Mettre à jour l'URL du webhook Stripe vers le nouveau domaine — c'est l'oubli
classique : les paiements aboutissent mais les factures ne se marquent jamais
comme payées.

## 8. Après bascule

- Vérifier les quatre tâches planifiées (voir `scheduled-tasks.md`).
- Déclencher une sauvegarde manuelle **et tester une restauration** :
  une sauvegarde jamais restaurée n'est pas une sauvegarde.
- Laisser Render actif quelques jours, puis supprimer les services.

---

## Restaurer une sauvegarde

```bash
# Récupérer depuis Object Storage
aws s3 cp s3://tus-backups/postgres/<fichier>.dump.enc . \
    --endpoint-url https://s3.gra.io.cloud.ovh.net

# Déchiffrer
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
    -in <fichier>.dump.enc -out restore.dump \
    -pass pass:"$BACKUP_ENCRYPTION_KEY"

# Restaurer — À FAIRE D'ABORD SUR UNE BASE DE TEST
docker exec -i <conteneur-postgres> \
    pg_restore --no-owner --no-privileges --clean --if-exists \
               -U tus_admin -d traitdunion < restore.dump
```

> `--clean --if-exists` supprime les tables existantes avant de les recréer.
> Sur la base de production, cette commande détruit les données actuelles :
> toujours valider la restauration sur une base jetable avant.

## Retour arrière

Tant que les services Render n'ont pas été supprimés :

1. Remettre l'enregistrement DNS `A` vers Render.
2. Restaurer l'URL du webhook Stripe.

Les données écrites sur OVH depuis la bascule ne remonteront pas vers Render :
ce retour arrière n'est propre que dans les premières heures. Passé ce délai,
mieux vaut réparer la nouvelle installation que revenir en arrière.
