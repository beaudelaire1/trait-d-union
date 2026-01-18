# 🚀 Déploiement sur Render.com - Trait d'Union Studio

## Prérequis

- Compte [Render.com](https://render.com)
- Repository Git (GitHub/GitLab)
- Clés API : Brevo, Stripe, reCAPTCHA

---

## 1. Déploiement Initial

### Option A : Blueprint (Recommandé)

1. **Connecter le repo** : Dashboard Render → "New" → "Blueprint"
2. **Sélectionner le repo** et la branche `main`
3. **Render détecte `render.yaml`** et crée automatiquement :
   - Service Web (`traitdunion-web`)
   - Base de données PostgreSQL (`traitdunion-db`)

### Option B : Manuel

1. **Créer la base de données** :
   - Dashboard → "New" → "PostgreSQL"
   - Nom : `traitdunion-db`
   - Région : Frankfurt

2. **Créer le service Web** :
   - Dashboard → "New" → "Web Service"
   - Runtime : Docker
   - Dockerfile Path : `./Dockerfile`

---

## 2. Variables d'Environnement

### Configurées automatiquement (render.yaml)
| Variable | Valeur |
|----------|--------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | Auto-généré |
| `DATABASE_URL` | Lien vers PostgreSQL |
| `SITE_URL` | `https://traitdunion.it` |
| `DEFAULT_FROM_EMAIL` | `contact@traitdunion.it` |
| `ADMIN_EMAIL` | `admin@traitdunion.it` |

### À configurer manuellement (secrets)

Dans le dashboard Render → Service → Environment :

```
BREVO_API_KEY=xkeysib-xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
RECAPTCHA_SITE_KEY=6Lxxx
RECAPTCHA_SECRET_KEY=6Lxxx
DJANGO_SUPERUSER_PASSWORD=MotDePasseSecure123!
```

---

## 3. Configuration DNS (Hostinger)

### Option A : Domaine principal sur Render

1. Dans Render → Service → Settings → Custom Domains
2. Ajouter `traitdunion.it` et `www.traitdunion.it`
3. Copier les enregistrements DNS fournis

Dans Hostinger DNS :
```
Type    Nom     Valeur
A       @       216.24.57.1  (IP Render)
CNAME   www     traitdunion-web.onrender.com
```

### Option B : Proxy via Cloudflare (recommandé)

1. Ajouter le domaine à Cloudflare
2. Configurer les DNS vers Render
3. Activer le proxy orange (protection DDoS)

---

## 4. Webhook Stripe

1. Dashboard Stripe → Developers → Webhooks
2. Ajouter endpoint : `https://traitdunion.it/factures/webhook/stripe/`
3. Événements à écouter :
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. Copier le **Webhook Secret** (`whsec_xxx`)
5. Ajouter dans Render : `STRIPE_WEBHOOK_SECRET=whsec_xxx`

---

## 5. Stockage Médias (Cloudflare R2)

Pour stocker les PDF et images en production :

1. Créer un bucket R2 sur Cloudflare
2. Générer des tokens API
3. Ajouter les variables :

```
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=traitdunion-media
AWS_S3_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
```

---

## 6. Commandes Utiles

### Accéder au shell Django
```bash
# Via Render Shell (Dashboard → Service → Shell)
python manage.py shell
```

### Créer un superuser manuellement
```bash
python manage.py createsuperuser
```

### Appliquer les migrations
```bash
python manage.py migrate
```

### Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

---

## 7. Monitoring

### Logs
- Dashboard Render → Service → Logs (temps réel)

### Erreurs
- Configurer Sentry (optionnel) :
```
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

### Health Check
- Endpoint : `/` (configuré dans render.yaml)
- Render redémarre automatiquement si échec

---

## 8. Mise à jour

1. Push sur la branche `main`
2. Render détecte et redéploie automatiquement
3. Migrations appliquées via `build.sh`

### Rollback
- Dashboard → Service → Events → Deploy → "Rollback"

---

## 9. Checklist Production

- [ ] Variables d'environnement configurées
- [ ] DNS configuré et propagé
- [ ] SSL actif (automatique avec Render)
- [ ] Webhook Stripe configuré
- [ ] Superuser créé
- [ ] Test email fonctionnel
- [ ] Test paiement fonctionnel
- [ ] Stockage médias configuré (R2/S3)

---

## Support

- Documentation Render : https://render.com/docs
- Stripe : https://stripe.com/docs
- Brevo : https://developers.brevo.com

**Contact** : contact@traitdunion.it
