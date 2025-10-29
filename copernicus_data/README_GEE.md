# Google Earth Engine - Extraction de Données pour le Sénégal

Ce projet utilise Google Earth Engine (GEE) pour extraire des données agro-météorologiques et de télédétection pour toutes les régions du Sénégal.

## 🎯 Objectifs

- Extraire des données satellitaires pour les 14 régions du Sénégal
- Analyser les tendances climatiques et agricoles
- Créer des visualisations et des rapports

## 📊 Sources de Données

### Données Météorologiques
- **ERA5-Land** : Température, précipitations, rayonnement solaire, vent
- **CHIRPS** : Précipitations quotidiennes haute résolution

### Données de Télédétection
- **MODIS Terra** : Température de surface (jour/nuit)
- **MODIS Vegetation Indices** : NDVI, EVI (indices de végétation)
- **SMAP** : Humidité du sol

### Régions Couvertes
- Dakar, Diourbel, Fatick, Kaffrine, Kaolack
- Kédougou, Kolda, Louga, Matam, Saint-Louis
- Sédhiou, Tambacounda, Thiès, Ziguinchor

## 🚀 Installation et Configuration

### 1. Prérequis
```bash
# Python 3.7+
# Compte Google avec accès à Google Earth Engine
```

### 2. Installation des dépendances
```bash
# Exécuter le script de configuration
python setup_gee.py

# Ou installer manuellement
pip install -r requirements_gee.txt
```

### 3. Authentification Google Earth Engine
```bash
# Authentification (une seule fois)
earthengine authenticate

# Suivre les instructions dans le navigateur
```

### 4. Vérification de l'installation
```bash
python main_gee_pipeline.py --check-auth
```

## 📋 Utilisation

### Pipeline Complet
```bash
# Exécuter tout le pipeline (recommandé)
python main_gee_pipeline.py --all
```

### Étapes Individuelles
```bash
# Configuration uniquement
python main_gee_pipeline.py --setup

# Extraction des données uniquement
python main_gee_pipeline.py --extract

# Analyse des données uniquement
python main_gee_pipeline.py --analyze
```

### Scripts Individuels
```bash
# Extraction directe
python google_earth_engine_senegal.py

# Analyse directe
python analyze_gee_data.py
```

## 📁 Structure des Fichiers

```
copernicus_data/
├── google_earth_engine_senegal.py  # Script principal d'extraction
├── setup_gee.py                    # Configuration et installation
├── analyze_gee_data.py             # Analyse et visualisation
├── main_gee_pipeline.py            # Pipeline orchestrateur
├── requirements_gee.txt            # Dépendances Python
└── README_GEE.md                   # Cette documentation

data/gee_senegal/
├── raw/                            # Données brutes par région
├── processed/                      # Données traitées
├── analysis/                       # Résultats d'analyse
├── *_consolidated_data.csv         # Données consolidées par région
├── summary_statistics.csv          # Statistiques descriptives
├── *.png                          # Graphiques d'analyse
├── senegal_regions_map.html       # Carte interactive
└── analysis_report.md             # Rapport complet
```

## 📊 Données Extraites

### Variables Météorologiques
- `temperature_2m` : Température à 2m (ERA5)
- `precipitation_sum` : Précipitations cumulées (ERA5)
- `solar_radiation` : Rayonnement solaire (ERA5)
- `wind_u`, `wind_v` : Composantes du vent (ERA5)
- `precipitation` : Précipitations CHIRPS

### Variables de Télédétection
- `temp_day_celsius` : Température diurne MODIS (°C)
- `temp_night_celsius` : Température nocturne MODIS (°C)
- `ndvi_normalized` : Indice de végétation NDVI
- `evi_normalized` : Indice de végétation EVI
- `soil_moisture` : Humidité du sol SMAP

### Métadonnées
- `date` : Date de l'observation
- `region` : Nom de la région
- `latitude`, `longitude` : Coordonnées
- `data_source` : Source des données

## 📈 Analyses Disponibles

### Statistiques Descriptives
- Moyennes, écarts-types, min/max par région
- Comptage des observations disponibles

### Visualisations
1. **Tendances de Température**
   - Cycles annuels par région
   - Comparaison jour/nuit
   - Évolution temporelle

2. **Analyse des Précipitations**
   - Précipitations annuelles moyennes
   - Cycles saisonniers
   - Distributions par région

3. **Indices de Végétation**
   - NDVI/EVI moyens par région
   - Cycles saisonniers
   - Corrélations avec les précipitations

4. **Carte Interactive**
   - Localisation des régions
   - Statistiques par région
   - Interface web interactive

## ⚙️ Configuration Avancée

### Modification de la Période
```python
# Dans google_earth_engine_senegal.py
START_DATE = '2015-01-01'  # Date de début
END_DATE = '2024-12-31'    # Date de fin
```

### Ajout de Régions
```python
# Dans google_earth_engine_senegal.py
REGIONS_SENEGAL = {
    "Nouvelle_Region": {
        "lat": 14.0, 
        "lon": -16.0, 
        "buffer": 0.3
    }
}
```

### Modification des Variables
```python
# Ajouter d'autres collections GEE
def get_new_variable(geometry, start_date, end_date):
    collection = ee.ImageCollection('COLLECTION_NAME')
    # ... logique d'extraction
```

## 🔧 Dépannage

### Erreurs Communes

1. **Erreur d'authentification**
   ```bash
   earthengine authenticate
   ```

2. **Quota GEE dépassé**
   - Réduire la période d'analyse
   - Augmenter l'échelle spatiale
   - Traiter moins de régions simultanément

3. **Données manquantes**
   - Vérifier la disponibilité des collections
   - Ajuster les dates selon la couverture

4. **Erreurs de mémoire**
   - Réduire la résolution spatiale
   - Traiter par petites périodes

### Optimisation des Performances
- Utiliser des filtres temporels stricts
- Optimiser la résolution spatiale
- Traiter les régions en parallèle

## 📞 Support

Pour les problèmes liés à :
- **Google Earth Engine** : [Documentation officielle](https://developers.google.com/earth-engine)
- **Authentification** : [Guide GEE](https://developers.google.com/earth-engine/guides/auth)
- **Collections de données** : [Catalogue GEE](https://developers.google.com/earth-engine/datasets)

## 📝 Notes Importantes

1. **Limites de Quota** : GEE a des limites d'utilisation quotidiennes
2. **Résolution Temporelle** : Varie selon les collections (quotidienne à mensuelle)
3. **Couverture Géographique** : Toutes les collections ne couvrent pas toutes les périodes
4. **Format des Données** : Les données sont sauvegardées en CSV pour faciliter l'analyse

## 🎉 Résultats Attendus

Après exécution complète, vous obtiendrez :
- ✅ Données extraites pour 14 régions du Sénégal
- ✅ Statistiques descriptives complètes
- ✅ Graphiques d'analyse temporelle et spatiale
- ✅ Carte interactive des régions
- ✅ Rapport d'analyse détaillé
- ✅ Données prêtes pour modélisation agricole