# CertiTrack - Initialisation Automatique

Ce guide explique comment utiliser les scripts d'initialisation automatique pour CertiTrack.

## 🚀 Démarrage Rapide

### Linux/macOS
```bash
./docker-compose-init.sh
```

### Windows
```cmd
docker-compose-init.bat
```

## 📋 Ce que fait le script

Le script d'initialisation automatique effectue toutes les étapes nécessaires au démarrage de CertiTrack :

### 1. Vérification des prérequis
- ✅ Docker installé et accessible
- ✅ Docker Compose installé et accessible

### 2. Construction et démarrage
- 🔨 Construction des images Docker (avec --no-cache)
- 🚀 Démarrage de tous les services en arrière-plan

### 3. Attente des services
- ⏳ PostgreSQL prêt et accessible
- ⏳ Redis prêt et accessible
- ⏳ Application Django prête

### 4. Installation et configuration
- 📦 Installation de Bootstrap local (si nécessaire)
- 🗄️ Exécution des migrations de base de données
- 📁 Collecte des fichiers statiques
- ⚙️ Initialisation des tâches Celery
- 📊 Mise à jour des jours restants

### 5. Vérification finale
- ✅ Vérification que tous les services sont actifs
- ✅ Test de l'accessibilité de l'application

## 🌐 Accès aux services

Une fois l'initialisation terminée, vous pouvez accéder à :

- **Application Web** : http://localhost:8000
- **Dashboard Mural** : http://localhost:8000/dashboard/wall/
- **Admin Django** : http://localhost:8000/admin/

## 💡 Commandes utiles

```bash
# Arrêter tous les services
docker-compose down

# Voir les logs en temps réel
docker-compose logs -f

# Redémarrer un service spécifique
docker-compose restart web

# Accéder au shell Django
docker-compose exec web python manage.py shell

# Voir l'état des services
docker-compose ps
```

## 🔧 Dépannage

### Erreur de permissions (Linux/macOS)
```bash
chmod +x docker-compose-init.sh
```

### Services qui ne démarrent pas
```bash
# Voir les logs détaillés
docker-compose logs

# Redémarrer depuis zéro
docker-compose down
docker-compose up --build
```

### Base de données non accessible
```bash
# Vérifier l'état de PostgreSQL
docker-compose exec db pg_isready -U certitrack_user -d certitrack

# Redémarrer la base de données
docker-compose restart db
```

### Fichiers statiques manquants
```bash
# Recollecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput
```

## 📝 Notes importantes

1. **Première utilisation** : Le script peut prendre 5-10 minutes pour la première construction
2. **Ports utilisés** : Assurez-vous que les ports 8000, 5432, 6379 sont libres
3. **Ressources** : CertiTrack nécessite au moins 2GB de RAM disponible
4. **Bootstrap local** : Sur Windows, l'installation de Bootstrap local peut nécessiter WSL ou Git Bash

## 🆘 Support

En cas de problème :

1. Vérifiez les logs : `docker-compose logs`
2. Redémarrez les services : `docker-compose restart`
3. Consultez la documentation : `README.md`
4. Utilisez le script de déploiement manuel : `deploy.sh`

---

**CertiTrack** - Gestion des Certificats SSL/TLS avec initialisation automatique
