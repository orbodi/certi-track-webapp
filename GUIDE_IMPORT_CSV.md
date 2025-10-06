# Guide d'utilisation : Import CSV Intelligent

## 🎯 Objectif
Ce guide vous explique comment utiliser la nouvelle fonctionnalité d'import CSV intelligent pour gérer vos certificats sans créer de doublons.

## 📋 Prérequis
- Accès à l'interface web CertiTrack
- Fichier CSV des certificats (exporté depuis votre autorité de certification)

## 🚀 Étapes d'utilisation

### 1. Accéder à l'import CSV
```
Menu Navigation → Certificats → Importer (CSV)
```
Ou directement : `http://votre-serveur/certificates/import/csv/`

### 2. Préparer votre fichier CSV

#### Format attendu
Le fichier doit contenir les colonnes suivantes (séparées par tabulation) :
```
Délivré à | Délivré par | Date d'expiration | Rôles prévus | Nom convivial | Statut | Modèle de certificat
```

#### Exemple de contenu
```
jenkins.eid.local	eid-CA-01-CA	08/10/2025	Authentification du serveur	Jenkins	Émis	CertSSLIdemia
gitlab.eid.local	eid-CA-01-CA	09/10/2025	Authentification du serveur	GitLab	Émis	CertSSLIdemia
```

### 3. Uploader le fichier

#### Options disponibles
- **Fichier CSV** : Sélectionnez votre fichier
- **Délimiteur** : Tabulation (par défaut) ou Point-virgule
- **Environnement par défaut** : Production, UAT, Test, ou Dev
- **Ignorer la première ligne** : Cochez si votre CSV a un en-tête
- **Auto-enrichir** : Cochez pour scanner automatiquement les certificats après import

#### Bouton "Prévisualiser"
Cliquez sur **Prévisualiser** pour lancer l'analyse.

### 4. Analyser la prévisualisation

#### Résumé global
Vous verrez 4 compteurs :
```
📊 Analyse de l'import CSV
100 certificat(s) détecté(s) :

   15          8           5           2
Nouveaux    Mises à    Doublons   Conflits
            jour
```

#### Interprétation

**🟢 Nouveaux (15)** 
- Ces certificats n'existent pas dans votre base
- ✅ **Ils seront créés**

**🔵 Mises à jour (8)**
- Ces certificats existent avec une date d'expiration antérieure
- 🔄 **L'ancienne version sera archivée**
- ✅ **La nouvelle version sera créée**
- Exemple : 
  ```
  Actuel : expire le 08/10/2025
  CSV    : expire le 08/10/2026
  → Mise à jour détectée
  ```

**⚪ Doublons (5)**
- Ces certificats sont déjà présents avec la même date
- ⏭️ **Ils seront ignorés**

**🟠 Conflits (2)**
- Le CSV contient une version plus ancienne que celle en base
- ⚠️ **Ils seront ignorés**
- Raison : Votre base contient déjà la version la plus récente

### 5. Vérifier le tableau détaillé

Le tableau affiche ligne par ligne :
- **#** : Numéro de ligne
- **Action** : Badge coloré (Nouveau/MàJ/Doublon/Conflit)
- **Certificat CSV** : Nom + émetteur
- **Date d'expiration** : Date du CSV
- **Certificat existant** : Date d'expiration en base (si existant)
- **Détails** : Explication + recommandation

#### Exemple de ligne
```
| 5 | 🔵 Mise à jour | jenkins.eid.local        | 08/10/2026 | Exp: 08/10/2025 | Date plus récente       |
|   |                | eid-CA-01-CA             |            | Créé: 15/05/2024| Ancien archivé, nouveau créé |
```

### 6. Confirmer l'import

Si tout est correct :
1. Cliquez sur **Confirmer l'import**
2. Le système exécute les actions
3. Un message de confirmation s'affiche

#### Message de succès
```
✅ Import réussi : 15 nouveau(x), 8 mis à jour, 12 archivé(s), 5 ignoré(s)
```

### 7. Vérifier les résultats

Accédez à la liste des certificats :
```
Menu Navigation → Certificats → Liste
```

Vous verrez :
- ✅ Les nouveaux certificats créés
- ✅ Les certificats mis à jour (avec nouvelles dates)
- ❌ Les anciennes versions **n'apparaissent plus** (archivées, pas supprimées)

## 💡 Cas d'usage pratiques

### Cas 1 : Import initial
**Situation** : Première importation de votre base de certificats  
**Résultat** : Tous les certificats sont créés (badges 🟢 Nouveaux)

### Cas 2 : Re-import régulier (mensuel)
**Situation** : Vous exportez tous les certificats chaque mois  
**Résultat** :
- Nouveaux domaines → 🟢 Créés
- Certificats renouvelés → 🔵 Mis à jour
- Certificats inchangés → ⚪ Ignorés (doublons)

### Cas 3 : Import avec duplicats
**Situation** : Votre export contient l'ancien ET le nouveau certificat  
**Résultat** :
- Nouveau certificat → 🔵 Mis à jour
- Ancien certificat → 🟠 Ignoré (conflit)
- **Vous gardez toujours la version la plus récente**

### Cas 4 : Re-import d'un ancien export par erreur
**Situation** : Vous uploadez un CSV de l'année dernière  
**Résultat** : Tout en 🟠 Conflits (ignorés)  
**Protection** : Aucun certificat récent n'est écrasé

## 🛡️ Protections en place

### 1. Pas de suppression
- Les anciennes versions sont **archivées**, jamais supprimées
- L'historique est préservé

### 2. Pas d'écrasement accidentel
- Si vous importez une version plus ancienne, elle est ignorée
- Votre version récente est protégée

### 3. Prévisualisation obligatoire
- Vous **voyez** toutes les actions avant de valider
- Aucune surprise

### 4. Transaction atomique
- Soit tout réussit, soit rien
- Pas d'état incohérent

## 🔍 Dépannage

### Problème : Tous mes certificats sont en "Doublon"
**Cause** : Vous réimportez le même fichier sans changement  
**Solution** : C'est normal ! Aucune action nécessaire

### Problème : Certificats en "Conflit" alors qu'ils sont plus récents
**Cause** : Format de date non reconnu  
**Solution** : Vérifier le format de date dans le CSV (attendu : JJ/MM/AAAA)

### Problème : Erreur "Date manquante"
**Cause** : Colonne "Date d'expiration" vide ou mal formatée  
**Solution** : Corriger le CSV et réimporter

### Problème : Aucun certificat détecté
**Cause** : Mauvais délimiteur ou en-tête non ignoré  
**Solution** : 
- Essayer délimiteur "Point-virgule" si vous utilisez "Tabulation"
- Cocher "Ignorer la première ligne" si votre CSV a un en-tête

## 📊 Comprendre l'archivage

### Qu'arrive-t-il aux certificats archivés ?
- Ils restent en base de données
- Ils n'apparaissent plus dans les listes
- Ils conservent leur historique
- Champs ajoutés :
  - `archived = True`
  - `archived_at = 2025-10-06 13:00:00`
  - `archived_reason = "Remplacé par certificat plus récent (exp: 08/10/2026)"`

### Peut-on les voir ?
- Pas encore via l'interface (amélioration future)
- Via la base de données : `SELECT * FROM certificates WHERE archived = True`

### Peut-on les restaurer ?
- Pas encore via l'interface (amélioration future)
- Manuellement via la base : `UPDATE certificates SET archived = False WHERE id = X`

## ✅ Bonnes pratiques

### 1. Importer régulièrement
- **Fréquence recommandée** : Mensuel
- Permet de détecter rapidement les renouvellements

### 2. Vérifier la prévisualisation
- Toujours prendre quelques secondes pour vérifier
- Regarder particulièrement les conflits (rouges)

### 3. Garder une copie du CSV
- Utile pour comparaison en cas de doute
- Backup de votre export

### 4. Utiliser l'environnement par défaut
- Gagne du temps si tous les certificats sont du même environnement
- Peut être modifié individuellement après import

## 🎓 Récapitulatif

| Symbole | Type | Action | Quand ? |
|---------|------|--------|---------|
| 🟢 | Nouveau | Créé | Certificat inexistant |
| 🔵 | Mise à jour | Ancien archivé, nouveau créé | Date CSV > Date DB |
| ⚪ | Doublon | Ignoré | Date CSV = Date DB |
| 🟠 | Conflit | Ignoré | Date CSV < Date DB |

## 🚀 Prêt à importer ?

1. Préparez votre CSV
2. Allez sur Import CSV
3. Uploadez et prévisualisez
4. Vérifiez l'analyse
5. Confirmez
6. Vérifiez les résultats

**C'est aussi simple que ça !** 🎉

---

**Besoin d'aide ?**  
Consultez `IMPORT_CSV_INTELLIGENT.md` pour la documentation technique complète.

