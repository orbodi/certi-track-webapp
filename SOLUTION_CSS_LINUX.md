# 🔧 Solution : CSS Cassé sur Linux

## 🎯 Le Problème

Après avoir déployé CertiTrack sur un serveur Linux, l'application affiche **"0 static files copied"** et le CSS est complètement cassé.

### Cause Racine

Les fichiers Bootstrap locaux (`static/vendor/bootstrap/` et `static/vendor/bootstrap-icons/`) n'ont **pas été transférés** sur le serveur Linux lors du déploiement.

## ✅ Solution Immédiate (3 minutes)

Sur votre **serveur Linux**, exécutez :

```bash
# 1. Aller dans le dossier du projet
cd /chemin/vers/certi-track-webapp

# 2. Installer Bootstrap en local
chmod +x scripts/install-bootstrap-local.sh
./scripts/install-bootstrap-local.sh

# 3. Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput

# 4. Redémarrer le service web
docker-compose restart web
```

**Résultat attendu :**
```
✅ Bootstrap installé localement
📦 175+ fichiers statiques collectés
🎨 CSS fonctionne correctement
```

## 🚀 Solution Automatique (Recommandé)

Le script `deploy.sh` a été mis à jour pour installer automatiquement Bootstrap :

```bash
# Sur votre serveur Linux
cd /chemin/vers/certi-track-webapp
./deploy.sh
```

Le script détectera automatiquement si Bootstrap manque et l'installera.

## 📦 Ce qui est Installé

Le script télécharge automatiquement depuis les CDN officiels :

| Fichier | Taille | Description |
|---------|--------|-------------|
| `bootstrap.min.css` | ~200 KB | Styles Bootstrap |
| `bootstrap.bundle.min.js` | ~80 KB | JavaScript Bootstrap |
| `bootstrap-icons.css` | ~100 KB | Styles des icônes |
| `bootstrap-icons.woff2` | ~150 KB | Police des icônes |

**Total : ~530 KB** (téléchargement unique)

## 🔍 Vérification

### 1. Vérifier que Bootstrap est présent

```bash
ls -lh static/vendor/bootstrap/
```

Vous devriez voir :
```
bootstrap.min.css
bootstrap.min.css.map
bootstrap.bundle.min.js
bootstrap.bundle.min.js.map
```

### 2. Vérifier que les fichiers sont collectés

```bash
docker-compose exec web ls /app/staticfiles/vendor/bootstrap/
```

Vous devriez voir les mêmes fichiers.

### 3. Tester dans le navigateur

1. Ouvrez `http://VOTRE-IP:8000`
2. Inspectez la page (F12)
3. Onglet **Network** → Actualisez (Ctrl+R)
4. Vérifiez que `bootstrap.min.css` retourne **200 OK** (pas 404)

## 🎨 Pourquoi Bootstrap en Local ?

### Avantages

✅ **Fonctionne offline** - Pas besoin d'internet  
✅ **Plus rapide** - Pas d'appel CDN externe  
✅ **Plus fiable** - Pas de dépendance externe  
✅ **Compliance** - Contrôle total sur les versions  
✅ **Sécurisé** - Pas de requêtes tierces

### Ancien Système (CDN)

```html
<!-- ❌ Ne fonctionne PAS offline -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/..." rel="stylesheet">
```

### Nouveau Système (Local)

```html
<!-- ✅ Fonctionne offline -->
<link href="{% static 'vendor/bootstrap/bootstrap.min.css' %}" rel="stylesheet">
```

## 🐛 Dépannage Complet

### Problème : "0 static files copied"

**Cause :** Les fichiers dans `static/` sont déjà à jour.

**Solution :** Forcer avec `--clear`

```bash
docker-compose exec web python manage.py collectstatic --noinput --clear
```

### Problème : CSS toujours cassé

**Solution étape par étape :**

```bash
# 1. Vérifier que Bootstrap existe
ls static/vendor/bootstrap/bootstrap.min.css
# Si erreur "No such file", installer Bootstrap :
./scripts/install-bootstrap-local.sh

# 2. Re-collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput --clear

# 3. Redémarrer tous les services
docker-compose restart

# 4. Vider le cache du navigateur
# Chrome/Firefox : Ctrl+Shift+Delete → Cocher "Images et fichiers en cache"

# 5. Hard refresh de la page
# Ctrl+F5 (Windows/Linux) ou Cmd+Shift+R (Mac)
```

### Problème : curl n'est pas installé

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y curl

# RHEL/CentOS/Rocky
sudo yum install -y curl

# Alpine Linux
apk add --no-cache curl
```

### Problème : Permission denied

```bash
chmod +x scripts/install-bootstrap-local.sh
chmod +x deploy.sh
./scripts/install-bootstrap-local.sh
```

## 📝 Workflow Complet de Déploiement

### Sur votre Machine Locale (Windows)

```bash
# 1. Commiter vos changements
git add .
git commit -m "Ajout Bootstrap local"
git push origin main
```

### Sur le Serveur Linux

```bash
# 2. Cloner ou mettre à jour
git clone <repo> certi-track-webapp
# OU
cd certi-track-webapp && git pull origin main

# 3. Déployer (installe automatiquement Bootstrap)
chmod +x deploy.sh
./deploy.sh

# 4. Créer un super utilisateur (première fois uniquement)
chmod +x manage-app.sh
./manage-app.sh createsuperuser
```

## 🎉 Résultat Final

Une fois la solution appliquée :

✅ **Interface Web** : CSS Bootstrap chargé correctement  
✅ **Dashboard Mural** : Affichage complet avec styles  
✅ **Icônes** : Bootstrap Icons fonctionnelles  
✅ **Responsive** : Mobile et desktop  
✅ **Offline** : Fonctionne sans internet  

## 📞 Support

Si le problème persiste après avoir suivi ce guide :

1. **Logs du service web :**
   ```bash
   docker-compose logs web
   ```

2. **Vérifier les fichiers statiques :**
   ```bash
   docker-compose exec web find /app/staticfiles -name "bootstrap.min.css"
   ```

3. **Inspecter le navigateur (F12) :**
   - Onglet **Console** → Erreurs ?
   - Onglet **Network** → 404 sur quels fichiers ?

## 🔄 Mise à Jour Future

Pour toute mise à jour future du projet :

```bash
cd /chemin/vers/certi-track-webapp
git pull origin main
./deploy.sh  # Bootstrap sera vérifié automatiquement
```

---

**Problème résolu ! 🎊**

Votre application CertiTrack devrait maintenant fonctionner parfaitement sur Linux avec tous les styles Bootstrap appliqués.

