# Réorganisation des Outils - Documentation

## Nouvelle Architecture (Juillet 2025)

### 🔄 **traitement_photos_2.py** - Traitement Principal
**Rôle** : Traitement principal des photos Google Photos
**Fonctionnalités** :
- ✅ Import des métadonnées depuis les fichiers JSON
- ✅ Correction des dates de création (fonction principale)
- ✅ Import des coordonnées GPS depuis JSON → EXIF
- ✅ Renommage des fichiers avec dates
- ✅ Traitement par lot des photos
- ❌ **SUPPRIMÉ** : Géocodage (conversion coordonnées → noms de lieux)

### 📊 **analyze-modify_metadata.py** - Analyse et Modification Avancée
**Rôle** : Outil principal pour l'analyse et la modification des métadonnées
**Fonctionnalités** :
- ✅ Analyse complète des métadonnées (dates, GPS, localisation)
- ✅ **Géocodage GPS** (coordonnées → noms de lieux via API OpenStreetMap)
- ✅ Écriture des informations de localisation dans EXIF
- ✅ Vérification des informations de localisation existantes
- ✅ Cache intelligent pour optimiser les appels API
- ✅ Rapports détaillés et statistiques
- ✅ Export des rapports en JSON

## Workflow Recommandé

1. **Étape 1** : Utiliser `traitement_photos_2.py` pour le traitement principal
   - Import des dates depuis JSON
   - Import des coordonnées GPS depuis JSON
   - Renommage des fichiers

2. **Étape 2** : Utiliser `analyze-modify_metadata.py` pour les opérations avancées
   - Analyse de la qualité des métadonnées
   - Géocodage des coordonnées GPS
   - Ajout des noms de lieux dans les métadonnées
   - Vérification finale avant upload OneDrive

## Avantages de cette Séparation

- **Performance** : `traitement_photos_2.py` plus rapide sans les appels API
- **Flexibilité** : Géocodage optionnel et séparé
- **Maintenance** : Code plus modulaire et spécialisé
- **Sécurité** : Géocodage sans risque d'affecter le traitement principal
- **Optimisation** : Cache intelligent et détection des localisations existantes

## Notes Importantes

- Le géocodage nécessite une connexion internet
- Les appels API respectent les limites de débit (1 seconde entre chaque appel)
- Les fichiers sont sauvegardés automatiquement avant modification
- Compatible avec les données existantes

---
*Mise à jour : Juillet 2025*
*Auteur : Stephan Alluchon*
