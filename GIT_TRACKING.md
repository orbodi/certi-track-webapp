# 📦 Git Tracking - Ce qui est versionné

## ✅ Fichiers Bootstrap Locaux (IMPORTANT)

Ces fichiers **DOIVENT** être versionnés pour que l'application fonctionne offline sur le serveur Linux :

```
static/vendor/bootstrap/
├── bootstrap.min.css             ✅ Tracké
├── bootstrap.min.css.map         ✅ Tracké
├── bootstrap.bundle.min.js       ✅ Tracké
└── bootstrap.bundle.min.js.map   ✅ Tracké

static/vendor/bootstrap-icons/
├── bootstrap-icons.css           ✅ Tracké
└── fonts/
    ├── bootstrap-icons.woff      ✅ Tracké
    └── bootstrap-icons.woff2     ✅ Tracké
```

## ✅ Scripts de Déploiement

```
scripts/
├── install-bootstrap-local.sh    ✅ Tracké (Installation Bootstrap)
├── fix_load_static.py            ⚠️  Non tracké (utilitaire optionnel)
└── autres scripts .bat           ✅ Trackés
```

## ✅ Documentation

```
├── README.md                     ✅ Tracké
├── SCRIPTS_README.md             ✅ Tracké
├── DEPLOIEMENT_LINUX.md          ✅ Tracké
├── SOLUTION_CSS_LINUX.md         ✅ Tracké
├── DASHBOARD_MURAL.md            ✅ Tracké
└── GIT_TRACKING.md               ⚠️  Nouveau fichier
```

## ❌ Fichiers Ignorés (Normal)

Ces fichiers sont générés automatiquement et **ne doivent PAS** être versionnés :

### Django
- `staticfiles/` - Généré par `collectstatic`
- `media/` - Fichiers uploadés par les utilisateurs
- `db.sqlite3` - Base de données de développement
- `*.log` - Fichiers de logs
- `*.pyc`, `__pycache__/` - Bytecode Python

### Environnement
- `.env` - Variables d'environnement sensibles
- `venv/`, `env/`, `ENV/` - Environnements virtuels Python

### IDE
- `.vscode/`, `.idea/` - Configuration éditeurs
- `*.swp`, `*.swo` - Fichiers temporaires

### OS
- `.DS_Store` (Mac), `Thumbs.db` (Windows)

### Celery
- `celerybeat-schedule` - Planification Celery
- `celerybeat.pid` - Process ID Celery

## 📋 Vérification Rapide

Pour vérifier que tout est bien tracké :

```bash
# Vérifier les fichiers Bootstrap
git ls-files static/vendor/

# Vérifier tous les fichiers trackés
git ls-files

# Voir les fichiers non trackés
git status --short
```

## 🚀 Workflow Git Recommandé

### 1. Avant de Pousser sur le Serveur

```bash
# Vérifier l'état
git status

# Ajouter les nouveaux fichiers si nécessaire
git add static/vendor/  # Bootstrap (déjà tracké normalement)
git add scripts/        # Nouveaux scripts
git add *.md            # Nouvelle documentation

# Commiter
git commit -m "Update: Description des changements"

# Pousser vers le dépôt
git push origin main
```

### 2. Sur le Serveur Linux

```bash
# Cloner (première fois)
git clone <votre-repo> certi-track-webapp
cd certi-track-webapp

# OU Mettre à jour (après push)
cd certi-track-webapp
git pull origin main

# Déployer avec le script automatique
./deploy.sh
```

## ⚠️ Important : Bootstrap Local

### Pourquoi versionner Bootstrap ?

❌ **Avant** : CDN externe → Ne fonctionne PAS offline
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/...">
```

✅ **Maintenant** : Fichiers locaux versionnés → Fonctionne offline
```html
<link href="{% static 'vendor/bootstrap/bootstrap.min.css' %}">
```

### Avantages

1. ✅ **Offline** - Fonctionne sans internet
2. ✅ **Rapide** - Pas d'appel CDN
3. ✅ **Fiable** - Pas de dépendance externe
4. ✅ **Sécurisé** - Contrôle des versions
5. ✅ **Portable** - Un seul `git clone` suffit

## 🔍 Diagnostic

### Problème : "CSS cassé sur Linux"

**Cause probable** : Bootstrap local non présent sur le serveur

**Vérification** :
```bash
# Sur le serveur Linux
cd /chemin/vers/certi-track-webapp
ls -la static/vendor/bootstrap/
```

**Si le dossier est vide :**
```bash
# Les fichiers Bootstrap n'ont pas été clonés

# Solution 1 : Vérifier qu'ils sont bien dans Git
git ls-files static/vendor/

# Solution 2 : Les réinstaller
./scripts/install-bootstrap-local.sh
git add static/vendor/
git commit -m "Add Bootstrap local files"
git push origin main
```

### Problème : "0 static files copied"

**Cause** : Les fichiers sont déjà collectés et à jour

**Solution** : Forcer avec `--clear`
```bash
docker-compose exec web python manage.py collectstatic --noinput --clear
```

## 📝 Checklist Déploiement

Avant de déployer sur un nouveau serveur :

- [ ] ✅ Bootstrap local tracké dans Git
- [ ] ✅ Scripts de déploiement présents
- [ ] ✅ Documentation à jour
- [ ] ✅ `.gitignore` configuré correctement
- [ ] ✅ Variables sensibles dans `.env` (non versionné)
- [ ] ✅ `deploy.sh` exécutable
- [ ] ✅ PostgreSQL configuré dans `docker-compose.yml`

## 🎯 Résumé

### ✅ Ce qui EST versionné (et doit l'être)

- Code source Python/Django
- Templates HTML
- Fichiers CSS/JS custom
- **Bootstrap local (`static/vendor/`)**
- Scripts de déploiement
- Documentation
- Configuration Docker
- Fichiers de requirements

### ❌ Ce qui N'EST PAS versionné (et ne doit pas l'être)

- Fichiers générés (`staticfiles/`, `__pycache__/`)
- Base de données locale (`db.sqlite3`)
- Variables d'environnement sensibles (`.env`)
- Logs et fichiers temporaires
- Environnements virtuels Python
- Configuration IDE personnelle

---

**Tout est correctement configuré ! 🎉**

Votre projet est prêt à être cloné sur n'importe quel serveur Linux et l'application fonctionnera offline avec tous ses styles Bootstrap.

