# CertiTrack - Guide Docker Entrypoint Optimisé

## 🚀 Démarrage Ultra-Simple

Avec le script `docker-entrypoint.sh` optimisé, vous pouvez maintenant lancer CertiTrack avec une seule commande :

```bash
docker-compose up
```

## ✨ Ce que fait automatiquement l'entrypoint

### 1. **Attente intelligente des services**
- ⏳ Attend PostgreSQL (port 5444)
- ⏳ Attend Redis (port 6379)
- ⏳ Vérifie que Django est prêt

### 2. **Initialisation complète**
- 🗄️ **Migrations** : `python manage.py migrate`
- 📦 **Bootstrap local** : Installation automatique si nécessaire
- 📁 **Fichiers statiques** : `python manage.py collectstatic`
- 👤 **Superutilisateur** : Création automatique (admin/admin)
- 📧 **Règles de notification** : Initialisation des règles par défaut
- ⚙️ **Tâches Celery** : Configuration des tâches planifiées
- 📊 **Jours restants** : Mise à jour des calculs

### 3. **Affichage informatif**
- 🌐 URLs d'accès
- 👤 Identifiants de connexion
- 📋 État des services
- 💡 Commandes utiles

## 🎯 Utilisation

### Démarrage complet
```bash
docker-compose up
```

### Démarrage en arrière-plan
```bash
docker-compose up -d
```

### Reconstruction complète
```bash
docker-compose down
docker-compose up --build
```

## 📋 Services et ports

| Service | Port | Description |
|---------|------|-------------|
| **Web** | 8002 | Application Django |
| **PostgreSQL** | 5444 | Base de données |
| **Redis** | 6379 | Cache et broker Celery |

## 🌐 Accès

- **Application** : http://localhost:8002
- **Dashboard Mural** : http://localhost:8002/dashboard/wall/
- **Admin Django** : http://localhost:8002/admin/

### Identifiants par défaut
- **Utilisateur** : `admin`
- **Mot de passe** : `admin`

## 🔧 Commandes utiles

### Gestion des services
```bash
# Voir l'état des services
docker-compose ps

# Voir les logs
docker-compose logs -f

# Redémarrer un service
docker-compose restart web

# Arrêter tous les services
docker-compose down
```

### Accès aux conteneurs
```bash
# Shell Django
docker-compose exec web python manage.py shell

# Logs en temps réel
docker-compose logs -f web

# Commandes Django
docker-compose exec web python manage.py [commande]
```

## 🛠️ Dépannage

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
# Vérifier PostgreSQL
docker-compose exec db pg_isready -U certitrack_user -d certitrack

# Redémarrer la base
docker-compose restart db
```

### Fichiers statiques manquants
```bash
# Recollecter les statiques
docker-compose exec web python manage.py collectstatic --noinput
```

### Celery ne fonctionne pas
```bash
# Vérifier Redis
docker-compose exec redis redis-cli ping

# Redémarrer Celery
docker-compose restart celery celery-beat
```

## 📝 Logs et monitoring

### Logs en temps réel
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

### Vérification de l'état
```bash
# État des conteneurs
docker-compose ps

# Utilisation des ressources
docker stats
```

## 🎨 Personnalisation

### Variables d'environnement
Modifiez `docker-compose.yml` pour personnaliser :
- Ports d'accès
- Identifiants de base de données
- Configuration Celery
- Variables Django

### Script d'initialisation
Le script `docker-entrypoint.sh` peut être modifié pour :
- Ajouter des commandes personnalisées
- Modifier les messages d'affichage
- Ajouter des vérifications supplémentaires

## ✅ Avantages de cette approche

1. **Simplicité** : Une seule commande pour tout
2. **Robustesse** : Gestion automatique des erreurs
3. **Informatif** : Messages clairs et colorés
4. **Complet** : Toutes les initialisations nécessaires
5. **Fiable** : Attente intelligente des services
6. **Maintenable** : Script modulaire et documenté

---

**CertiTrack** - Initialisation automatique optimisée avec Docker Compose
