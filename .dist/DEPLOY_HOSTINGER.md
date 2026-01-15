# Déploiement sur Hostinger - traitdunion.it

## Prérequis Hostinger

Votre hébergement Hostinger doit supporter :
- Python 3.10+
- MySQL
- Accès SSH (recommandé)

---

## Étapes de déploiement

### 1. Préparation des fichiers

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer le package de déploiement
# Copier tout sauf: venv/, __pycache__/, .env, db.sqlite3
```

### 2. Upload sur Hostinger

Via **File Manager** ou **FTP/SFTP** :
1. Uploadez tous les fichiers dans `public_html/`
2. Le fichier `passenger_wsgi.py` doit être à la racine

### 3. Configuration de la base de données

Dans le panel Hostinger :
1. **Bases de données** → Créer une base MySQL
2. Notez : nom_base, utilisateur, mot_de_passe

### 4. Configuration des variables d'environnement

Créez le fichier `.env` sur le serveur avec :

```env
DJANGO_SECRET_KEY=votre_cle_secrete_generee
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_ALLOWED_HOSTS=traitdunion.it,www.traitdunion.it

DB_ENGINE=django.db.backends.mysql
DB_NAME=votre_base
DB_USER=votre_user
DB_PASSWORD=votre_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=contact@traitdunion.it
EMAIL_HOST_PASSWORD=votre_password

ADMIN_EMAIL=contact@traitdunion.it

RECAPTCHA_SITE_KEY=6LcDgEssAAAAAEsrYSEbJbfzyg2vhbAHdRbG0WhZ
RECAPTCHA_SECRET_KEY=6LcDgEssAAAAAGcCZG0eqkfQp-JIP-kV0z1au6Lt
```

### 5. Migrations

Via SSH :
```bash
cd ~/public_html
python manage.py migrate
python manage.py createsuperuser
```

### 6. Configuration Python App (si disponible)

Dans Hostinger → **Avancé** → **Python** :
- Application root: `/public_html`
- Application startup file: `passenger_wsgi.py`
- Application entry point: `application`

---

## Structure des fichiers sur le serveur

```
public_html/
├── passenger_wsgi.py      ← Point d'entrée WSGI
├── manage.py
├── .env                   ← Variables (NE PAS VERSIONNER)
├── config/
├── apps/
├── templates/
├── static/                ← Fichiers source
└── staticfiles/           ← Fichiers collectés
```

---

## Vérifications post-déploiement

- [ ] Site accessible sur https://traitdunion.it
- [ ] Certificat SSL actif
- [ ] Formulaire de contact fonctionne
- [ ] Admin accessible sur /admin/
- [ ] Images portfolio s'affichent

---

## Commandes utiles (SSH)

```bash
# Voir les logs
tail -f ~/logs/error.log

# Redémarrer l'application
touch ~/public_html/tmp/restart.txt

# Générer une nouvelle clé secrète
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Support Hostinger

- Documentation: https://support.hostinger.com/
- Chat: Panel Hostinger → Support
