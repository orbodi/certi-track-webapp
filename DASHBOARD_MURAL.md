# 📺 Dashboard Mural CertiTrack

Guide d'utilisation du dashboard pour écran mural.

## 🎯 À Quoi Ça Sert ?

Le dashboard mural est conçu pour être affiché en **permanence sur un écran** dans votre bureau/datacenter pour :
- 👁️ Surveiller en temps réel l'état des certificats
- 🚨 Identifier rapidement les certificats critiques
- 📊 Avoir une vue d'ensemble instantanée
- ⏰ Mise à jour automatique (auto-refresh)

---

## 🚀 Accès au Dashboard

### URL
```
http://localhost:8000/dashboard/wall/
```

### Depuis l'application
1. Connectez-vous à CertiTrack
2. Cliquez sur **"Écran Mural"** dans le menu
3. Le dashboard s'ouvre dans un nouvel onglet

---

## 📊 Ce qui est Affiché

### Section Haut : Statistiques Globales (4 cartes)

| Carte | Icône | Information |
|-------|-------|-------------|
| **Total** | 📊 | Nombre total de certificats |
| **Actifs** | ✅ | Certificats valides (> 30 jours) |
| **Expire Bientôt** | ⚠️ | Certificats expirant dans 30 jours |
| **Expirés** | ❌ | Certificats déjà expirés |

### Colonne Gauche

#### 🚨 URGENT - Moins de 7 jours
- Certificats expirant dans **0 à 7 jours**
- **Couleur rouge** avec animation clignotante
- Badge affichant le nombre de jours restants
- Maximum 10 certificats affichés

#### ⚠️ ATTENTION - 8 à 30 jours
- Certificats expirant dans **8 à 30 jours**
- **Couleur orange**
- Maximum 10 certificats affichés

### Colonne Droite

#### ❌ Expirés Récemment
- Les 5 derniers certificats expirés
- **Couleur grise**
- Badge "EXPIRÉ"

#### 📊 Par Environnement
- Répartition des certificats par environnement
- Production, UAT, Test, Dev

---

## ⚙️ Configuration

### Auto-refresh

Par défaut, le dashboard se rafraîchit toutes les **60 secondes**.

Pour changer l'intervalle, ajoutez le paramètre `?refresh=X` (en secondes) :

```
# Rafraîchir toutes les 30 secondes
http://localhost:8000/dashboard/wall/?refresh=30

# Rafraîchir toutes les 2 minutes
http://localhost:8000/dashboard/wall/?refresh=120

# Rafraîchir toutes les 5 minutes
http://localhost:8000/dashboard/wall/?refresh=300
```

### Mode Plein Écran

1. Ouvrez le dashboard
2. Appuyez sur **F11** (navigateur en plein écran)
3. Le dashboard s'affichera sans barre d'adresse ni menus

---

## 🖥️ Configuration pour Écran Mural

### Matériel Recommandé

- **Écran** : 27" minimum, 4K recommandé
- **Résolution** : 1920x1080 minimum, 4K idéal
- **Dispositif** : Raspberry Pi, mini-PC, ou ancien laptop
- **Connexion** : Câble réseau (plus stable que WiFi)

### Configuration du Navigateur

#### Chrome/Chromium (Recommandé)

```bash
# Mode kiosk (démarrage automatique en plein écran)
chromium-browser --kiosk --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  http://localhost:8000/dashboard/wall/?refresh=60
```

#### Firefox

```bash
firefox --kiosk http://localhost:8000/dashboard/wall/?refresh=60
```

### Empêcher la mise en veille

#### Sur Linux (Ubuntu)
```bash
# Désactiver la mise en veille de l'écran
xset s off
xset -dpms
xset s noblank
```

#### Sur Raspberry Pi
Éditez `/etc/xdg/lxsession/LXDE-pi/autostart` :
```
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk --disable-infobars http://IP_SERVEUR:8000/dashboard/wall/
```

---

## 🎨 Personnalisation

### Modifier l'intervalle de rafraîchissement par défaut

Éditez `dashboard/views.py`, ligne ~49 :

```python
context['refresh_interval'] = self.request.GET.get('refresh', 60)  # 60 = secondes
```

### Modifier le nombre de certificats affichés

Éditez `dashboard/views.py` :

```python
# Certificats critiques (ligne ~26)
context['critical_certs'] = Certificate.objects.filter(
    days_remaining__lte=7,
    days_remaining__gte=0
).order_by('days_remaining')[:10]  # Changer [:10] pour afficher plus/moins
```

### Changer les couleurs

Éditez `templates/dashboard/wall_display.html`, section `<style>` :

```css
:root {
    --atos-blue: #0066B3;        /* Couleur principale */
    --color-success: #52B788;    /* Vert */
    --color-warning: #F4A261;    /* Orange */
    --color-danger: #E76F51;     /* Rouge */
}
```

---

## 🔧 Cas d'Usage

### Scénario 1 : Salle de Contrôle
- Écran 50" monté au mur
- Refresh : 30 secondes
- Vue permanente pour l'équipe IT

### Scénario 2 : Bureau Manager
- Écran secondaire sur le bureau
- Refresh : 60 secondes
- Supervision passive

### Scénario 3 : NOC (Network Operations Center)
- Multiple écrans
- Refresh : 10 secondes
- Surveillance active 24/7

---

## 🎯 Raccourcis Clavier

| Touche | Action |
|--------|--------|
| **F11** | Plein écran |
| **F5** | Rafraîchir manuellement |
| **Ctrl + +** | Zoomer |
| **Ctrl + -** | Dézoomer |
| **Ctrl + 0** | Reset zoom |

---

## 📱 Responsive

Le dashboard s'adapte automatiquement :
- **Desktop** : 2 colonnes
- **Tablette** : 2 colonnes compactes
- **Mobile** : 1 colonne

---

## 🐛 Dépannage

### Le dashboard ne se rafraîchit pas

1. Vérifiez que la meta refresh est présente :
   - Ouvrez les outils de développement (F12)
   - Onglet "Console" → pas d'erreurs ?

2. Testez avec un intervalle différent :
   ```
   ?refresh=10
   ```

### Les certificats ne s'affichent pas

1. Vérifiez que les certificats ont des dates d'expiration valides
2. Vérifiez que `days_remaining` est rempli :
   ```bash
   docker-compose exec web python manage.py update_days_remaining
   ```

### L'écran se met en veille

Configurez votre système d'exploitation pour empêcher la mise en veille (voir section "Configuration").

---

## 🎨 Améliorations Futures Possibles

- [ ] Graphiques en temps réel (Chart.js)
- [ ] Mode sombre/clair
- [ ] Alertes sonores pour certificats critiques
- [ ] Export PDF du dashboard
- [ ] Historique des changements
- [ ] Vue par datacenter/zone géographique

---

## 📚 Voir Aussi

- [README.md](README.md) - Documentation générale
- [SCRIPTS_README.md](SCRIPTS_README.md) - Scripts de déploiement
- [NOUVELLES_FONCTIONNALITES.md](NOUVELLES_FONCTIONNALITES.md) - Fonctionnalités ajoutées

---

**Profitez de votre dashboard mural ! 📺**

