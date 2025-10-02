# 🐧 Déploiement sur Linux - Guide Complet

## 🎯 Résolution du Problème CSS Cassé

Si après avoir déployé l'application sur Linux, vous constatez que le CSS est cassé (Bootstrap ne fonctionne pas), c'est que les fichiers Bootstrap locaux n'ont pas été transférés.

## ✅ Solution Rapide

### Option 1 : Script Automatique (Recommandé)

Le script `deploy.sh` inclut maintenant une étape automatique qui vérifie et installe Bootstrap si nécessaire :

```bash
cd /chemin/vers/certi-track-webapp
chmod +x deploy.sh
./deploy.sh
```

Le script va automatiquement :
1. Détecter si Bootstrap est manquant
2. Télécharger Bootstrap en local
3. Collecter les fichiers statiques
4. Démarrer l'application

### Option 2 : Installation Manuelle

Si vous préférez installer Bootstrap manuellement :

```bash
# 1. Rendre le script exécutable
chmod +x scripts/install-bootstrap-local.sh

# 2. Exécuter le script
./scripts/install-bootstrap-local.sh

# 3. Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput

# 4. Redémarrer
docker-compose restart web
```

## 📦 Fichiers Téléchargés

Le script `install-bootstrap-local.sh` télécharge automatiquement :

```
static/vendor/
├── bootstrap/
│   ├── bootstrap.min.css          (CSS Bootstrap)
│   ├── bootstrap.min.css.map      (Source map CSS)
│   ├── bootstrap.bundle.min.js    (JS Bootstrap)
│   └── bootstrap.bundle.min.js.map (Source map JS)
└── bootstrap-icons/
    ├── bootstrap-icons.css         (CSS des icônes)
    └── fonts/
        ├── bootstrap-icons.woff    (Font WOFF)
        └── bootstrap-icons.woff2   (Font WOFF2)
```

## 🔍 Vérification

Pour vérifier que Bootstrap est correctement installé :

```bash
# Vérifier que les fichiers existent
ls -lh static/vendor/bootstrap/
ls -lh static/vendor/bootstrap-icons/

# Vérifier que les fichiers sont collectés
docker-compose exec web ls -lh /app/staticfiles/vendor/bootstrap/
```

Vous devriez voir :
```
✅ bootstrap.min.css       (~200KB)
✅ bootstrap.bundle.min.js (~80KB)
✅ bootstrap-icons.css     (~100KB)
✅ bootstrap-icons.woff2   (~150KB)
```

## 🚀 Déploiement Complet depuis Zéro

### 1. Préparer le Serveur

```bash
# Installer les prérequis (Docker, Docker Compose)
chmod +x install-prereqs.sh
sudo ./install-prereqs.sh
```

### 2. Cloner le Projet

```bash
git clone <votre-repo> certi-track-webapp
cd certi-track-webapp
```

### 3. Configurer l'Environnement (Optionnel)

Modifiez `docker-compose.yml` si nécessaire :
- Port d'exposition (défaut: 8000)
- Mots de passe PostgreSQL
- Variables d'environnement

### 4. Déployer

```bash
chmod +x deploy.sh
./deploy.sh
```

Le script va :
- ✅ Vérifier Docker
- ✅ Construire les images
- ✅ Démarrer les conteneurs
- ✅ Attendre PostgreSQL
- ✅ Appliquer les migrations
- ✅ **Installer Bootstrap en local** (si manquant)
- ✅ Collecter les fichiers statiques
- ✅ Initialiser les tâches Celery

### 5. Créer un Super Utilisateur

```bash
chmod +x manage-app.sh
./manage-app.sh createsuperuser
```

## 🌐 Accès à l'Application

Une fois déployé, accédez à :

- **Application principale** : `http://VOTRE-IP:8000`
- **Admin Django** : `http://VOTRE-IP:8000/admin`
- **Dashboard mural** : `http://VOTRE-IP:8000/dashboard/wall/`

## 🐛 Dépannage

### Problème : CSS toujours cassé après deploy.sh

```bash
# 1. Vérifier que Bootstrap existe
ls static/vendor/bootstrap/bootstrap.min.css

# Si le fichier n'existe pas :
./scripts/install-bootstrap-local.sh

# 2. Forcer la re-collecte des fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput --clear

# 3. Redémarrer
docker-compose restart web

# 4. Vider le cache du navigateur (Ctrl+Shift+Delete)
```

### Problème : "0 static files copied"

Cela signifie que les fichiers dans `static/` n'ont pas changé depuis la dernière collecte.

```bash
# Forcer avec --clear
docker-compose exec web python manage.py collectstatic --noinput --clear
```

### Problème : Permission denied sur scripts

```bash
chmod +x deploy.sh
chmod +x install-prereqs.sh
chmod +x manage-app.sh
chmod +x scripts/install-bootstrap-local.sh
```

### Problème : curl n'est pas installé

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y curl

# RHEL/CentOS
sudo yum install -y curl
```

## 📝 Mode Offline Complet

L'application fonctionne **100% offline** une fois Bootstrap installé localement.

Plus besoin d'internet pour :
- ✅ Charger Bootstrap CSS/JS
- ✅ Charger Bootstrap Icons
- ✅ Utiliser l'interface web
- ✅ Afficher le dashboard mural

## 🔄 Mise à Jour de l'Application

Pour mettre à jour l'application après un `git pull` :

```bash
cd /chemin/vers/certi-track-webapp
git pull origin main
./deploy.sh
```

Le script redéploiera automatiquement avec les nouvelles modifications.

## 📊 Monitoring

Pour voir les logs en temps réel :

```bash
# Tous les services
docker-compose logs -f

# Service web uniquement
docker-compose logs -f web

# Celery worker
docker-compose logs -f celery

# Celery beat
docker-compose logs -f celery-beat
```

## 🛡️ Sécurité Production

Pour un déploiement en production :

1. **Modifier le SECRET_KEY** dans `docker-compose.yml`
2. **Utiliser HTTPS** avec un reverse proxy (Nginx/Traefik)
3. **Changer les mots de passe** PostgreSQL
4. **Configurer un pare-feu** (ufw, firewalld)
5. **Activer le mode production** :

```bash
./deploy.sh --production
```

## 🎉 Félicitations !

Votre application CertiTrack est maintenant déployée sur Linux avec Bootstrap en local ! 🚀

