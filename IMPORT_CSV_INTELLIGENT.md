# Import CSV Intelligent - Documentation

## 📋 Vue d'ensemble

Le système d'import CSV a été amélioré avec une **analyse intelligente** qui détecte automatiquement :
- ✅ **Nouveaux certificats** à créer
- 🔄 **Mises à jour** (certificats renouvelés avec date plus récente)
- ⏭️ **Doublons exacts** à ignorer
- ⚠️ **Conflits** (versions plus anciennes à ignorer)

## 🎯 Problématique résolue

### Avant
- Création de doublons à chaque import
- Ancien et nouveau certificat coexistaient dans la base
- Confusion sur quelle version était active
- Pas de visibilité sur les actions effectuées

### Maintenant
- **Détection automatique** des certificats existants
- **Archivage intelligent** des anciennes versions
- **Prévisualisation complète** avant confirmation
- **Transparence totale** sur les actions à effectuer

## 🚀 Fonctionnement

### 1. Upload du fichier CSV
Chargez votre fichier CSV contenant les certificats (avec ou sans doublons).

### 2. Analyse automatique
Le système analyse chaque certificat et le compare avec la base de données :

#### ✅ **NOUVEAU**
- **Condition** : Le `common_name` n'existe pas en base
- **Action** : Le certificat sera créé
- **Badge** : 🟢 Nouveau

#### 🔄 **MISE À JOUR**
- **Condition** : Le `common_name` existe avec une date d'expiration antérieure
- **Action** : 
  1. L'ancien certificat est **archivé** (pas supprimé)
  2. Le nouveau certificat est créé
- **Badge** : 🔵 Mise à jour
- **Exemple** :
  ```
  Base de données : jenkins.eid.local → expire le 08/10/2025
  CSV             : jenkins.eid.local → expire le 08/10/2026
  → Mise à jour détectée (2026 > 2025)
  ```

#### ⏭️ **DOUBLON**
- **Condition** : Le certificat existe avec la **même date** d'expiration
- **Action** : Sera ignoré (déjà présent)
- **Badge** : ⚪ Doublon

#### ⚠️ **CONFLIT**
- **Condition** : Le CSV contient une version **plus ancienne** que celle en base
- **Action** : Sera ignoré (version obsolète)
- **Badge** : 🟠 Conflit
- **Exemple** :
  ```
  Base de données : gitlab.eid.local → expire le 09/10/2026
  CSV             : gitlab.eid.local → expire le 09/10/2025
  → Conflit détecté (2025 < 2026) → ignoré
  ```

### 3. Prévisualisation détaillée
Une interface visuelle affiche :
- **Résumé global** : compteurs par type d'action
- **Tableau détaillé** : ligne par ligne avec :
  - Action proposée (badge coloré)
  - Données du CSV
  - Date d'expiration du CSV
  - Certificat existant (si applicable)
  - Explication et recommandation

### 4. Confirmation et exécution
Une fois validé, le système applique les actions :
- Création des nouveaux
- Archivage + création pour les mises à jour
- Ignoré pour les doublons et conflits

### 5. Message de résultat
Message récapitulatif :
```
✅ Import réussi : 
- 15 nouveau(x)
- 8 mis à jour
- 12 archivé(s)
- 5 ignoré(s)
```

## 📊 Archivage

### Qu'est-ce que l'archivage ?
- Les certificats **ne sont jamais supprimés**
- Les anciennes versions sont marquées comme `archived = True`
- Ils disparaissent des listes principales mais restent en base

### Champs d'archivage
```python
archived = True/False          # Booléen, indexé
archived_at = DateTime         # Date d'archivage
archived_reason = "Remplacé par certificat plus récent (exp: 08/10/2026)"
```

### Avantages
- ✅ **Historique complet** préservé
- ✅ **Traçabilité** des renouvellements
- ✅ **Récupération** possible si besoin
- ✅ **Audit** facilité

## 🔍 Filtrage des certificats archivés

Par défaut, les certificats archivés sont **exclus** :
- Liste des certificats
- Dashboard principal
- Écran mural
- Statistiques

### Pour voir les certificats archivés
Une future amélioration permettra d'ajouter un filtre "Afficher archivés".

## 📝 Cas d'usage typiques

### Cas 1 : Premier import
```
CSV : 100 certificats
Résultat : 100 nouveau(x)
```

### Cas 2 : Re-import complet (sans changement)
```
CSV : 100 certificats (identiques)
Résultat : 100 ignoré(s) (doublons)
```

### Cas 3 : Import avec renouvellements
```
CSV : 100 certificats
- 70 identiques (dates)
- 25 renouvelés (dates plus récentes)
- 5 nouveaux domaines

Résultat :
- 5 nouveau(x)
- 25 mis à jour
- 25 archivé(s)
- 70 ignoré(s)
```

### Cas 4 : Export ancien mélangé avec récent
```
CSV : 100 certificats
- 50 déjà en base avec dates plus récentes
- 50 OK

Résultat :
- 50 nouveau(x) ou mis à jour
- 50 ignoré(s) (conflits - versions obsolètes)
```

## 🎨 Interface utilisateur

### Résumé visuel
```
╔═══════════════════════════════════════════════╗
║  📊 Analyse de l'import CSV                   ║
║  100 certificat(s) détecté(s) :               ║
║                                               ║
║    🟢 15    🔵 8    ⚪ 5    🟠 2              ║
║  Nouveaux  MàJ  Doublons  Conflits           ║
╚═══════════════════════════════════════════════╝
```

### Légende
```
🟢 Nouveau       : Sera créé
🔵 Mise à jour   : Ancienne version archivée, nouvelle créée
⚪ Doublon       : Sera ignoré (déjà en base)
🟠 Conflit       : Date antérieure, sera ignoré
```

### Tableau de prévisualisation
| # | Action | Certificat CSV | Date exp. | Existant | Détails |
|---|--------|----------------|-----------|----------|---------|
| 1 | 🟢 Nouveau | jenkins.local | 08/10/2026 | - | Certificat non présent |
| 2 | 🔵 MàJ | gitlab.local | 09/10/2026 | Exp: 09/10/2025 | Date plus récente |
| 3 | ⚪ Doublon | jira.local | 09/10/2025 | Exp: 09/10/2025 | Identique |

## ⚙️ Technique

### Fichiers modifiés
- `certificates/models.py` : Champs d'archivage
- `certificates/csv_analyzer.py` : Service d'analyse (nouveau)
- `certificates/views.py` : Logique d'import modifiée
- `templates/certificates/certificate_import_csv.html` : Interface améliorée
- `certificates/migrations/0004_*.py` : Migration des champs

### Architecture
```
CSV Upload
    ↓
CSVAnalyzer.analyze_batch()
    ↓ Compare avec DB
Génération des actions
    ↓ Stockage session
Prévisualisation
    ↓ Utilisateur valide
handle_confirmation()
    ↓ Transaction atomique
- Archivage (si MàJ)
- Création (Nouveau/MàJ)
- Ignore (Doublon/Conflit)
```

## 🔮 Améliorations futures

### Possibles
1. **Gestion manuelle des conflits** : Laisser l'utilisateur choisir
2. **Vue des certificats archivés** : Page dédiée avec filtre
3. **Restauration** : Désarchiver un certificat
4. **Statistiques d'archivage** : Graphiques de renouvellement
5. **Export historique** : CSV incluant les versions archivées
6. **Comparaison visuelle** : Diff entre ancien et nouveau certificat

## 📞 Support

En cas de problème :
1. Vérifier les logs Django : `docker-compose logs web`
2. Consulter les messages d'erreur dans l'interface
3. Vérifier que les migrations sont appliquées : `python manage.py migrate certificates`

## 🎉 Résumé

L'import CSV intelligent transforme une opération risquée en un processus **sûr, transparent et contrôlé** :

✅ **Plus de doublons accidentels**  
✅ **Archivage automatique des anciennes versions**  
✅ **Prévisualisation complète avant action**  
✅ **Traçabilité totale**  
✅ **Interface intuitive**  

**Profitez de vos imports CSV en toute sérénité !** 🚀

