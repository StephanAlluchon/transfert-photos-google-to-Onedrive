# Traitement de Photos Google Photos

Un script Python pour traiter et organiser vos photos et vidéos exportées depuis Google Photos, avec intégration complète des métadonnées JSON dans les fichiers EXIF.

## 🎯 Objectif

Ce programme permet de traiter automatiquement les exports de Google Photos en :
- Intégrant les métadonnées JSON dans les fichiers EXIF des images
- Gérant les doublons de manière interactive
- Préservant l'organisation des dossiers
- Offrant des options de renommage flexibles

## 📋 Fonctionnalités

### 1. Analyse et Statistiques
- **Scan récursif** de tous les sous-dossiers
- **Comptage automatique** des fichiers par type
- **Détection des associations** photo/vidéo ↔ JSON
- **Rapport détaillé** des fichiers avec/sans métadonnées

### 2. Gestion des Doublons
- **Détection automatique** des fichiers identiques dans différents dossiers
- **Traitement interactif** avec choix manuel
- **Suppression sécurisée** des doublons non désirés
- **Support** des formats JPG/JPEG et MP4

### 3. Traitement des Métadonnées
- **Intégration EXIF** complète depuis les fichiers JSON
- **Données temporelles** : date/heure de prise de vue
- **Géolocalisation** : coordonnées GPS (latitude/longitude)
- **Informations descriptives** : titre, description, mots-clés
- **Reconnaissance faciale** : noms des personnes identifiées

### 4. Options de Renommage
- **Renommage optionnel** avec préfixe de date (YYYY-MM-DD)
- **Conservation** des noms originaux si désiré
- **Nettoyage** des caractères spéciaux dans les noms
- **Troncature** automatique des noms trop longs

## 🗂️ Extensions Supportées

### Formats d'Images
- **`.jpg`** / **`.jpeg`** : Images principales
- **`.json`** : Métadonnées associées

### Formats de Vidéos
- **`.mp4`** : Fichiers vidéo
- **`.jpg`** : Miniatures des vidéos

### Types de Fichiers JSON
- **`.supplemental-metadata.json`** : Métadonnées complètes des photos
- **`.sup.json`** : Métadonnées supplémentaires
- **`.mp4.supplemental-metadata.json`** : Métadonnées des vidéos

## 🔄 Processus de Traitement

### Étape 1 : Indexation
```
📁 Scan récursif des dossiers
├── Identification des fichiers par nom de base
├── Association photo/vidéo ↔ JSON
└── Comptage et classification
```

### Étape 2 : Analyse des Doublons
```
🔍 Détection des doublons
├── Recherche par nom de fichier identique
├── Localisation dans différents dossiers
└── Présentation interactive des choix
```

### Étape 3 : Traitement Interactive
```
❓ Questions à l'utilisateur
├── Traiter les doublons ? (o/n)
├── Lancer le traitement principal ? (o/n)
└── Renommer avec préfixe de date ? (o/n)
```

### Étape 4 : Processing Principal
```
⚙️ Traitement des fichiers
├── Photos avec JSON → Intégration EXIF + renommage optionnel
├── Photos sans JSON → Copie simple
├── Vidéos avec JSON → Copie + mise à jour date/heure
└── Miniatures → Copie avec vidéo parente
```

## 📝 Modifications des Noms de Fichiers

### Avec Renommage Activé
```
Original  : IMG_20231215_142830.jpg
Nouveau   : 2023-12-15_IMG_20231215_142830.jpg
```

### Sans Renommage
```
Original  : IMG_20231215_142830.jpg
Nouveau   : IMG_20231215_142830.jpg (nom conservé)
```

### Règles de Nettoyage
- **Espaces** → remplacés par `_`
- **Longueur** → limitée à 30 caractères
- **Caractères spéciaux** → supprimés/remplacés

## 🗄️ Structure des Métadonnées Intégrées

### Informations Temporelles
- **DateTimeOriginal** : Date/heure de prise de vue
- **DateTimeDigitized** : Date de numérisation
- **DateTime** : Date de modification

### Données de Géolocalisation
- **GPSLatitude** / **GPSLongitude** : Coordonnées GPS
- **GPSLatitudeRef** / **GPSLongitudeRef** : Références N/S/E/W

### Informations Descriptives
- **ImageDescription** : Description de l'image
- **XPTitle** : Titre de l'image
- **XPKeywords** : Noms des personnes identifiées

## 🚀 Utilisation

### Prérequis
```bash
pip install pillow piexif
```

### Exécution
```bash
python traitement_photos_2.py
```

### Configuration
- **Dossier source** : `D:/SAuvegardephotos/GooglePhotos` (par défaut)
- **Dossier destination** : `D:/Sauvegardephotos/GooglePhotos2` (par défaut)
- Possibilité de personnaliser les chemins à l'exécution

## 📊 Rapport Final

Le programme fournit un rapport détaillé :
- ✅ **Nombre de photos traitées** avec métadonnées JSON
- 📁 **Nombre de photos copiées** sans métadonnées
- 🎬 **Nombre de vidéos copiées** avec miniatures
- ⚠️ **Vérification de cohérence** des comptages

## 🔧 Fonctionnalités Avancées

### Gestion des Dates de Fichiers
- **Modification automatique** des timestamps système
- **Support Windows** avec `pywin32` (optionnel)
- **Cohérence** entre métadonnées EXIF et dates système

### Robustesse
- **Gestion d'erreurs** complète avec messages explicites
- **Validation** des données JSON
- **Préservation** de la structure des dossiers
- **Sauvegarde** automatique des fichiers originaux

## 💡 Cas d'Usage

✅ **Idéal pour :**
- Archivage long terme de photos Google Photos
- Migration vers d'autres plateformes/logiciels
- Préservation des métadonnées perdues lors d'exports
- Organisation et nettoyage de collections photos

⚠️ **Limitations :**
- Nécessite les fichiers JSON de Google Photos
- Traitement séquentiel (pas de parallélisation)
- Dépendant de la structure d'export Google Photos

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités
- Améliorer la documentation

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
