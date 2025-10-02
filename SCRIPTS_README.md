# 📜 Guide des Scripts CertiTrack

Ce document explique comment utiliser les scripts de déploiement et de gestion de CertiTrack.

## 📦 Scripts Disponibles

| Script | Description | Plateforme |
|--------|-------------|------------|
| `deploy.sh` | Déploiement complet de l'application | Linux/Mac/Ubuntu |
| `deploy.ps1` | Déploiement complet de l'application | Windows PowerShell |
| `install-prereqs.sh` | Installation des prérequis (Docker, etc.) | Ubuntu/Debian |
| `manage-app.sh` | Gestion quotidienne de l'application | Linux/Mac/Ubuntu |

---

## 🚀 Déploiement Initial (Ubuntu/Linux)

### 1. Installation des prérequis (première fois seulement)

```bash
# Rendre le script exécutable
chmod +x install-prereqs.sh

# Installer Docker et Docker Compose
sudo ./install-prereqs.sh

# IMPORTANT: Déconnectez-vous et reconnectez-vous pour que les changements prennent effet
```

### 2. Déployer l'application

```bash
# Rendre le script exécutable
chmod +x deploy.sh

# Déployer
./deploy.sh
```

Le script va :
- ✅ Vérifier que Docker est installé et en cours d'exécution
- ✅ Arrêter les conteneurs existants
- ✅ Builder les images Docker
- ✅ Démarrer tous les services (web, celery, celery-beat, db, redis)
- ✅ Attendre que PostgreSQL soit prêt
- ✅ Appliquer les migrations
- ✅ Collecter les fichiers statiques
- ✅ Initialiser les tâches Celery planifiées

---

## 🛠️ Options de Déploiement

### Déploiement standard
```bash
./deploy.sh
```

### Déploiement rapide (sans rebuild)
```bash
./deploy.sh --no-build
```
Utile quand vous n'avez modifié que du code Python/HTML/CSS.

### Rebuild complet sans cache
```bash
./deploy.sh --no-cache
```
Force un rebuild total. Utile après modification de `requirements.txt` ou `Dockerfile`.

### Mode production
```bash
./deploy.sh --production
```
Active les optimisations de production.

### Déploiement très rapide (dev)
```bash
./deploy.sh --quick
```
Skip rebuild et collectstatic. Pour le développement uniquement.

---

## 🔧 Gestion Quotidienne

Le script `manage-app.sh` facilite les tâches courantes :

```bash
# Rendre le script exécutable (première fois)
chmod +x manage-app.sh
```

### Commandes disponibles

#### Gestion de l'application
```bash
./manage-app.sh start              # Démarrer
./manage-app.sh stop               # Arrêter
./manage-app.sh restart            # Redémarrer
./manage-app.sh status             # Voir le statut
./manage-app.sh logs               # Voir les logs en temps réel
./manage-app.sh logs-service web   # Logs d'un service spécifique
```

#### Base de données
```bash
./manage-app.sh migrate            # Appliquer les migrations
./manage-app.sh makemigrations     # Créer de nouvelles migrations
./manage-app.sh shell-db           # Shell PostgreSQL
./manage-app.sh backup             # Créer un backup
./manage-app.sh restore backup.sql # Restaurer un backup
```

#### Django
```bash
./manage-app.sh shell              # Shell Django
./manage-app.sh createsuperuser    # Créer un admin
./manage-app.sh collectstatic      # Collecter les statiques
```

#### Celery
```bash
./manage-app.sh celery-status       # Statut de Celery
./manage-app.sh init-schedules      # Init les tâches planifiées
./manage-app.sh check-expirations   # Tester les notifications
```

#### Maintenance
```bash
./manage-app.sh clean              # Nettoyer tout
./manage-app.sh rebuild            # Rebuilder les images
./manage-app.sh update             # Mettre à jour (git pull + redeploy)
```

---

## 🎯 Workflows Courants

### Premier déploiement

```bash
# 1. Installer les prérequis
sudo ./install-prereqs.sh

# 2. Se déconnecter/reconnecter (pour le groupe docker)
exit

# 3. Cloner le projet (si pas déjà fait)
git clone <repo-url>
cd certi-track-webapp

# 4. Déployer
chmod +x deploy.sh
./deploy.sh

# 5. Créer un super utilisateur
./manage-app.sh createsuperuser
```

### Mise à jour du code

```bash
# Option 1 : Automatique
./manage-app.sh update

# Option 2 : Manuel
git pull
./deploy.sh --no-cache
```

### Développement quotidien

```bash
# Modification de code Python/Templates
./deploy.sh --quick

# Modification de requirements.txt
./deploy.sh --no-cache

# Voir les logs
./manage-app.sh logs
```

### Backup et restauration

```bash
# Créer un backup
./manage-app.sh backup
# Crée: backup_20251002_093000.sql

# Restaurer un backup
./manage-app.sh restore backup_20251002_093000.sql
```

---

## 🆕 Gestion des Tâches Celery via l'Interface Web

Avec la nouvelle fonctionnalité, vous pouvez gérer les tâches Celery directement depuis l'interface :

### Accès
- URL : `http://localhost:8000/notifications/schedules/`

### Fonctionnalités

#### ➕ Créer une nouvelle tâche
1. Cliquez sur **"Nouvelle Tâche"**
2. Remplissez le formulaire :
   - **Nom** : Nom descriptif
   - **Tâche** : `app.module.fonction` (ex: `notifications.tasks.check_certificate_expirations`)
   - **Type** : Crontab (horaire fixe) ou Intervalle (répétitif)
   - **Horaire** : Selon le type choisi
3. **Enregistrez**

#### ✏️ Modifier une tâche
1. Cliquez sur l'icône **crayon** <i class="bi bi-pencil"></i>
2. Modifiez les paramètres
3. **Enregistrez**

#### 🔄 Activer/Désactiver rapidement
- Cliquez sur l'icône **pause/play** pour activer/désactiver instantanément

#### 🗑️ Supprimer une tâche
1. Cliquez sur l'icône **poubelle** <i class="bi bi-trash"></i>
2. Confirmez la suppression

---

## 📊 Surveillance

### Voir les logs en temps réel

```bash
# Tous les services
./manage-app.sh logs

# Un service spécifique
./manage-app.sh logs-service celery
./manage-app.sh logs-service celery-beat
./manage-app.sh logs-service web
```

### Vérifier le statut

```bash
./manage-app.sh status
```

### Voir les logs du déploiement

```bash
cat deploy.log
```

---

## 🐛 Dépannage

### Les conteneurs ne démarrent pas

```bash
# Voir les logs
./manage-app.sh logs

# Nettoyer et redémarrer
./manage-app.sh clean
./deploy.sh
```

### Problème avec la base de données

```bash
# Vérifier que PostgreSQL est prêt
docker-compose exec db pg_isready -U postgres

# Accéder au shell PostgreSQL
./manage-app.sh shell-db

# Recréer complètement
docker-compose down -v
./deploy.sh
```

### Celery ne fonctionne pas

```bash
# Vérifier les logs
./manage-app.sh logs-service celery
./manage-app.sh logs-service celery-beat

# Réinitialiser les tâches
./manage-app.sh init-schedules

# Redémarrer Celery
docker-compose restart celery celery-beat
```

### Les fichiers statiques ne se chargent pas

```bash
# Recollcter les statiques
./manage-app.sh collectstatic

# Redémarrer le service web
docker-compose restart web
```

---

## 🔐 Sécurité en Production

### Créer un fichier `.env`

```bash
cat > .env << 'EOF'
# Django
SECRET_KEY=changez-moi-par-une-cle-securisee-longue-et-aleatoire
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# Base de données
POSTGRES_DB=certitrack
POSTGRES_USER=certitrack_user
POSTGRES_PASSWORD=mot-de-passe-tres-securise

# Redis
REDIS_PASSWORD=mot-de-passe-redis-securise

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
EOF
```

### Déployer en mode production

```bash
./deploy.sh --production --no-cache
```

---

## 📁 Structure du Projet

```
certi-track-webapp/
├── deploy.sh                  # Script de déploiement Linux
├── deploy.ps1                 # Script de déploiement Windows
├── install-prereqs.sh         # Installation des prérequis
├── manage-app.sh              # Gestion quotidienne
├── docker-compose.yml         # Configuration Docker
├── Dockerfile                 # Image Docker
├── requirements.txt           # Dépendances Python
├── manage.py                  # Django management
├── config/                    # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── certificates/              # App certificats
├── notifications/             # App notifications
├── templates/                 # Templates HTML
└── static/                    # Fichiers statiques
```

---

## ✅ Checklist de Déploiement

Avant de déployer en production :

- [ ] Modifier `.env` avec vos vraies valeurs
- [ ] Changer `SECRET_KEY` en production
- [ ] Configurer `ALLOWED_HOSTS`
- [ ] Désactiver `DEBUG=False`
- [ ] Configurer SMTP pour les emails
- [ ] Créer un super utilisateur
- [ ] Tester les notifications
- [ ] Configurer les règles de notification
- [ ] Configurer les horaires Celery
- [ ] Faire un backup initial
- [ ] Configurer un pare-feu
- [ ] Activer HTTPS (reverse proxy)

---

## 📚 Documentation

- [README.md](README.md) - Documentation générale
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guide de déploiement complet
- [docker-compose.yml](docker-compose.yml) - Configuration Docker

---

## 🆘 Support

Si vous rencontrez des problèmes :

1. **Consultez les logs** : `./manage-app.sh logs`
2. **Vérifiez le statut** : `./manage-app.sh status`
3. **Consultez la documentation** : `DEPLOYMENT.md`
4. **Vérifiez les fichiers de log** : `cat deploy.log`

---

**Bon déploiement ! 🚀**

