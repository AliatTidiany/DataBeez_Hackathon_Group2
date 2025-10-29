# Données Brutes (Raw Data)

Ce dossier contient les données brutes extraites directement de Google Earth Engine.

## Structure
- **ERA5_Land/** : Données météorologiques ERA5-Land
- **CHIRPS/** : Données de précipitations CHIRPS
- **MODIS_Temperature/** : Données de température MODIS
- **MODIS_Vegetation/** : Indices de végétation MODIS (NDVI, EVI)
- **SMAP_SoilMoisture/** : Données d'humidité du sol SMAP

## Format
- Fichiers CSV avec colonnes : date, région, latitude, longitude, variables
- Un fichier par région et par source de données
- Données non traitées, telles qu'extraites de GEE
