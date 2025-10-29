"""
Google Earth Engine Data Extractor for Senegal
Auteur : Alioune MBODJI
Objectif :
Extraire des données agro-météorologiques et de télédétection pour toutes les régions du Sénégal
en utilisant Google Earth Engine.

Variables : précipitation, température, NDVI, EVI, humidité du sol, rayonnement solaire.
"""

import ee
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

# === Initialisation de Google Earth Engine ===
try:
    ee.Initialize()
    print("✅ Google Earth Engine initialisé avec succès")
except Exception as e:
    print(f"❌ Erreur d'initialisation GEE : {e}")
    print("💡 Exécutez 'earthengine authenticate' dans votre terminal")
    exit(1)

# === Définition des régions du Sénégal ===
REGIONS_SENEGAL = {
    "Dakar": {"lat": 14.7167, "lon": -17.4677, "buffer": 0.2},
    "Diourbel": {"lat": 14.6558, "lon": -16.2334, "buffer": 0.3},
    "Fatick": {"lat": 14.3396, "lon": -16.4114, "buffer": 0.3},
    "Kaffrine": {"lat": 14.1050, "lon": -15.5500, "buffer": 0.3},
    "Kaolack": {"lat": 14.1469, "lon": -16.0726, "buffer": 0.3},
    "Kédougou": {"lat": 12.5556, "lon": -12.1744, "buffer": 0.4},
    "Kolda": {"lat": 12.8833, "lon": -14.9500, "buffer": 0.4},
    "Louga": {"lat": 15.6144, "lon": -16.2286, "buffer": 0.4},
    "Matam": {"lat": 15.6600, "lon": -13.2550, "buffer": 0.4},
    "Saint-Louis": {"lat": 16.0179, "lon": -16.4896, "buffer": 0.3},
    "Sédhiou": {"lat": 12.7089, "lon": -15.5561, "buffer": 0.3},
    "Tambacounda": {"lat": 13.7707, "lon": -13.6673, "buffer": 0.5},
    "Thiès": {"lat": 14.7910, "lon": -16.9250, "buffer": 0.3},
    "Ziguinchor": {"lat": 12.5833, "lon": -16.2719, "buffer": 0.3}
}

# === Configuration des paramètres ===
OUTPUT_DIR = "data/gee_senegal"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Période d'étude
START_DATE = '2019-01-01'
END_DATE = '2024-12-31'

# === Fonctions utilitaires ===
def create_region_geometry(lat, lon, buffer):
    """Créer une géométrie rectangulaire autour d'un point"""
    return ee.Geometry.Rectangle([
        lon - buffer, lat - buffer,
        lon + buffer, lat + buffer
    ])

def get_precipitation_data(geometry, start_date, end_date):
    """Extraire les données de précipitation CHIRPS"""
    collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry)
    
    def extract_precip(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9
        )
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'precipitation': stats.get('precipitation')
        })
    
    return collection.map(extract_precip)

def get_temperature_data(geometry, start_date, end_date):
    """Extraire les données de température MODIS"""
    collection = ee.ImageCollection('MODIS/006/MOD11A1') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry) \
        .select(['LST_Day_1km', 'LST_Night_1km'])
    
    def extract_temp(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9
        )
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'temp_day_kelvin': stats.get('LST_Day_1km'),
            'temp_night_kelvin': stats.get('LST_Night_1km')
        })
    
    return collection.map(extract_temp)

def get_vegetation_indices(geometry, start_date, end_date):
    """Extraire NDVI et EVI de MODIS"""
    collection = ee.ImageCollection('MODIS/006/MOD13Q1') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry) \
        .select(['NDVI', 'EVI'])
    
    def extract_vi(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=250,
            maxPixels=1e9
        )
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'ndvi': stats.get('NDVI'),
            'evi': stats.get('EVI')
        })
    
    return collection.map(extract_vi)

def get_soil_moisture(geometry, start_date, end_date):
    """Extraire l'humidité du sol SMAP"""
    collection = ee.ImageCollection('NASA_USDA/HSL/SMAP10KM_soil_moisture') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry) \
        .select('ssm')
    
    def extract_sm(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10000,
            maxPixels=1e9
        )
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'soil_moisture': stats.get('ssm')
        })
    
    return collection.map(extract_sm)

def get_era5_data(geometry, start_date, end_date):
    """Extraire les données météorologiques ERA5"""
    collection = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry) \
        .select([
            'temperature_2m',
            'total_precipitation_sum',
            'surface_solar_radiation_downwards_sum',
            'u_component_of_wind_10m',
            'v_component_of_wind_10m'
        ])
    
    def extract_era5(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=11132,
            maxPixels=1e9
        )
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'temperature_2m': stats.get('temperature_2m'),
            'precipitation_sum': stats.get('total_precipitation_sum'),
            'solar_radiation': stats.get('surface_solar_radiation_downwards_sum'),
            'wind_u': stats.get('u_component_of_wind_10m'),
            'wind_v': stats.get('v_component_of_wind_10m')
        })
    
    return collection.map(extract_era5)

def extract_region_data(region_name, region_info):
    """Extraire toutes les données pour une région"""
    print(f"🌍 Extraction des données pour {region_name}...")
    
    # Créer la géométrie de la région
    geometry = create_region_geometry(
        region_info['lat'], 
        region_info['lon'], 
        region_info['buffer']
    )
    
    try:
        # Extraire les différents types de données
        print(f"  📊 Extraction des données ERA5...")
        era5_features = get_era5_data(geometry, START_DATE, END_DATE)
        era5_data = era5_features.getInfo()
        
        print(f"  🌧️ Extraction des précipitations CHIRPS...")
        precip_features = get_precipitation_data(geometry, START_DATE, END_DATE)
        precip_data = precip_features.getInfo()
        
        print(f"  🌡️ Extraction des températures MODIS...")
        temp_features = get_temperature_data(geometry, START_DATE, END_DATE)
        temp_data = temp_features.getInfo()
        
        print(f"  🌱 Extraction des indices de végétation...")
        vi_features = get_vegetation_indices(geometry, START_DATE, END_DATE)
        vi_data = vi_features.getInfo()
        
        print(f"  💧 Extraction de l'humidité du sol...")
        sm_features = get_soil_moisture(geometry, START_DATE, END_DATE)
        sm_data = sm_features.getInfo()
        
        # Convertir en DataFrames
        dfs = []
        
        # ERA5 data
        if era5_data['features']:
            era5_df = pd.DataFrame([f['properties'] for f in era5_data['features']])
            era5_df['data_source'] = 'ERA5'
            dfs.append(era5_df)
        
        # CHIRPS precipitation
        if precip_data['features']:
            precip_df = pd.DataFrame([f['properties'] for f in precip_data['features']])
            precip_df['data_source'] = 'CHIRPS'
            dfs.append(precip_df)
        
        # MODIS temperature
        if temp_data['features']:
            temp_df = pd.DataFrame([f['properties'] for f in temp_data['features']])
            # Convertir Kelvin en Celsius
            temp_df['temp_day_celsius'] = temp_df['temp_day_kelvin'] - 273.15
            temp_df['temp_night_celsius'] = temp_df['temp_night_kelvin'] - 273.15
            temp_df['data_source'] = 'MODIS_TEMP'
            dfs.append(temp_df)
        
        # MODIS vegetation indices
        if vi_data['features']:
            vi_df = pd.DataFrame([f['properties'] for f in vi_data['features']])
            # Normaliser NDVI et EVI (diviser par 10000)
            vi_df['ndvi_normalized'] = vi_df['ndvi'] / 10000
            vi_df['evi_normalized'] = vi_df['evi'] / 10000
            vi_df['data_source'] = 'MODIS_VI'
            dfs.append(vi_df)
        
        # SMAP soil moisture
        if sm_data['features']:
            sm_df = pd.DataFrame([f['properties'] for f in sm_data['features']])
            sm_df['data_source'] = 'SMAP'
            dfs.append(sm_df)
        
        # Fusionner toutes les données par date
        if dfs:
            # Ajouter les informations de région
            for df in dfs:
                df['region'] = region_name
                df['latitude'] = region_info['lat']
                df['longitude'] = region_info['lon']
                df['date'] = pd.to_datetime(df['date'])
            
            # Sauvegarder chaque source de données séparément
            for df in dfs:
                source = df['data_source'].iloc[0]
                filename = f"{region_name.lower()}_{source.lower()}_data.csv"
                filepath = os.path.join(OUTPUT_DIR, filename)
                df.to_csv(filepath, index=False)
                print(f"  ✅ Sauvegardé : {filepath}")
            
            # Créer un fichier consolidé pour la région
            consolidated_df = dfs[0]
            for df in dfs[1:]:
                consolidated_df = pd.merge(
                    consolidated_df, df, 
                    on=['date', 'region', 'latitude', 'longitude'], 
                    how='outer', 
                    suffixes=('', '_y')
                )
            
            # Nettoyer les colonnes dupliquées
            consolidated_df = consolidated_df.loc[:, ~consolidated_df.columns.str.endswith('_y')]
            
            consolidated_filename = f"{region_name.lower()}_consolidated_data.csv"
            consolidated_filepath = os.path.join(OUTPUT_DIR, consolidated_filename)
            consolidated_df.to_csv(consolidated_filepath, index=False)
            print(f"  ✅ Fichier consolidé : {consolidated_filepath}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur pour {region_name}: {e}")
        return False

# === Exécution principale ===
def main():
    print("🚀 Début de l'extraction des données GEE pour le Sénégal")
    print(f"📅 Période : {START_DATE} à {END_DATE}")
    print(f"🗂️ Répertoire de sortie : {OUTPUT_DIR}")
    print(f"🌍 Nombre de régions : {len(REGIONS_SENEGAL)}")
    
    successful_extractions = 0
    failed_extractions = 0
    
    for region_name, region_info in REGIONS_SENEGAL.items():
        success = extract_region_data(region_name, region_info)
        if success:
            successful_extractions += 1
        else:
            failed_extractions += 1
    
    print(f"\n📊 Résumé de l'extraction :")
    print(f"  ✅ Réussies : {successful_extractions}")
    print(f"  ❌ Échouées : {failed_extractions}")
    print(f"  📁 Fichiers sauvegardés dans : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()