"""
load_to_postgres.py (Version Unifiée)

Chargement unifié de toutes les données dans PostgreSQL/TimescaleDB
------------------------------------------------------------------
- Crée les tables si elles n'existent pas (FAO, Météo, et GEE Sénégal)
- Supprime les anciennes données pour éviter les doublons
- Insère les données depuis :
    - data/clean_fao.csv
    - data/clean_weather.csv
    - copernicus_data/data/gee_senegal/ (données GEE consolidées)
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
import glob
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv non installé. Installez avec: pip install python-dotenv")
    print("   Ou définissez manuellement les variables d'environnement")

# --- Paramètres de connexion PostgreSQL ---
DB_NAME = os.getenv("DB_NAME", "projet_DataBeez")
USER = os.getenv("DB_USER", "your_db_username")
PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
HOST = os.getenv("DB_HOST", "localhost")
PORT = os.getenv("DB_PORT", "5432")

# --- Fichiers CSV nettoyés ---
BASE_DIR = Path(__file__).parent.parent
FAO_CSV = BASE_DIR / "data" / "clean" / "clean_fao.csv"
WEATHER_CSV = BASE_DIR / "data" / "clean" / "clean_weather.csv"
GEE_DATA_DIR = BASE_DIR / "copernicus_data" / "data" / "gee_senegal"

# --- Variables GEE pertinentes pour la modélisation ---
MODEL_VARIABLES = {
    'temperature_2m': 'temperature_era5_k', 
    'precipitation_sum': 'precipitation_era5_mm',
    'precipitation': 'precipitation_chirps_mm',
    'solar_radiation': 'solar_radiation_j_m2',
    'wind_u': 'wind_u_component_ms',
    'wind_v': 'wind_v_component_ms',
    'temp_day_celsius': 'temperature_day_modis_c',
    'temp_night_celsius': 'temperature_night_modis_c',
    'ndvi_normalized': 'ndvi_modis',
    'evi_normalized': 'evi_modis',
    'soil_moisture': 'soil_moisture_smap_percent',
}

# --- Connexion SQLAlchemy ---
engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}")

def create_tables():
    """Création de toutes les tables (FAO, Météo, GEE)"""
    print("📋 Création des tables...")
    
    with engine.begin() as conn:
        # Table FAO
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fao_data (
            id SERIAL PRIMARY KEY,
            element VARCHAR(100),
            item VARCHAR(200),
            year INT NOT NULL,
            unit VARCHAR(50),
            value DOUBLE PRECISION NOT NULL,
            source VARCHAR(100)
        );
        """))
        
        # Table Météo
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            ville VARCHAR(100) NOT NULL,
            type VARCHAR(50),
            date DATE NOT NULL,
            temperature_c DOUBLE PRECISION,
            humidity_percent DOUBLE PRECISION,
            pressure_hpa DOUBLE PRECISION,
            wind_m_s DOUBLE PRECISION,
            precipitation_mm DOUBLE PRECISION,
            weather_description TEXT
        );
        """))
        
        # Table GEE Sénégal
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS gee_senegal_agro_data (
            id SERIAL PRIMARY KEY,
            
            -- Métadonnées spatiales et temporelles
            region VARCHAR(50) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            date DATE NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            day_of_year INTEGER,
            
            -- Variables météorologiques ERA5
            temperature_era5_k DOUBLE PRECISION,
            temperature_era5_c DOUBLE PRECISION,
            precipitation_era5_mm DOUBLE PRECISION,
            solar_radiation_j_m2 DOUBLE PRECISION,
            solar_radiation_mj_m2 DOUBLE PRECISION,
            wind_u_component_ms DOUBLE PRECISION,
            wind_v_component_ms DOUBLE PRECISION,
            wind_speed_ms DOUBLE PRECISION,
            wind_direction_deg DOUBLE PRECISION,
            
            -- Variables de précipitations CHIRPS
            precipitation_chirps_mm DOUBLE PRECISION,
            
            -- Variables de température MODIS
            temperature_day_modis_c DOUBLE PRECISION,
            temperature_night_modis_c DOUBLE PRECISION,
            temperature_amplitude_c DOUBLE PRECISION,
            
            -- Indices de végétation MODIS
            ndvi_modis DOUBLE PRECISION,
            evi_modis DOUBLE PRECISION,
            vegetation_health_index DOUBLE PRECISION,
            
            -- Humidité du sol SMAP
            soil_moisture_smap_percent DOUBLE PRECISION,
            
            -- Variables dérivées pour la modélisation
            growing_degree_days DOUBLE PRECISION,
            precipitation_cumulative_30d DOUBLE PRECISION,
            temperature_mean_7d DOUBLE PRECISION,
            ndvi_anomaly DOUBLE PRECISION,
            drought_index DOUBLE PRECISION,
            
            -- Indicateurs de saison
            is_rainy_season BOOLEAN,
            is_dry_season BOOLEAN,
            season VARCHAR(20),
            
            -- Métadonnées de qualité
            data_completeness_score DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        
        # Index pour optimiser les requêtes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_gee_region_date ON gee_senegal_agro_data(region, date);",
            "CREATE INDEX IF NOT EXISTS idx_gee_date ON gee_senegal_agro_data(date);",
            "CREATE INDEX IF NOT EXISTS idx_gee_region ON gee_senegal_agro_data(region);",
            "CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date);",
            "CREATE INDEX IF NOT EXISTS idx_fao_year ON fao_data(year);"
        ]
        
        for index_sql in indexes:
            conn.execute(text(index_sql))
    
    print("✅ Toutes les tables créées")

def clear_tables():
    """Supprime les anciennes données pour éviter les doublons"""
    print("🗑️ Suppression des anciennes données...")
    
    with engine.begin() as conn:
        # Drop and recreate FAO table to fix schema issues
        conn.execute(text("DROP TABLE IF EXISTS fao_data CASCADE;"))
        conn.execute(text("""
        CREATE TABLE fao_data (
            id SERIAL PRIMARY KEY,
            element VARCHAR(100),
            item VARCHAR(200),
            year INT NOT NULL,
            unit VARCHAR(50),
            value DOUBLE PRECISION NOT NULL,
            source VARCHAR(100)
        );
        """))
        
        conn.execute(text("TRUNCATE TABLE weather_data RESTART IDENTITY;"))
        conn.execute(text("TRUNCATE TABLE gee_senegal_agro_data RESTART IDENTITY;"))
    
    print("✅ Anciennes données supprimées")

def load_fao_weather_data():
    """Chargement des données FAO et Météo"""
    print("📥 Chargement des données FAO et Météo...")
    
    loaded_count = 0
    
    # Charger FAO si disponible
    if FAO_CSV.exists():
        try:
            df_fao = pd.read_csv(FAO_CSV)
            df_fao.columns = [c.lower() for c in df_fao.columns]
            # Supprimer la colonne domain si elle existe
            if 'domain' in df_fao.columns:
                df_fao = df_fao.drop('domain', axis=1)
            df_fao.to_sql("fao_data", engine, if_exists="append", index=False)
            print(f"  ✅ FAO: {len(df_fao):,} enregistrements")
            loaded_count += 1
        except Exception as e:
            print(f"  ❌ Erreur FAO: {e}")
    else:
        print(f"  ⚠️ Fichier FAO non trouvé: {FAO_CSV}")
    
    # Charger Météo si disponible
    if WEATHER_CSV.exists():
        try:
            df_weather = pd.read_csv(WEATHER_CSV)
            df_weather.columns = [c.lower() for c in df_weather.columns]
            df_weather.to_sql("weather_data", engine, if_exists="append", index=False)
            print(f"  ✅ Météo: {len(df_weather):,} enregistrements")
            loaded_count += 1
        except Exception as e:
            print(f"  ❌ Erreur Météo: {e}")
    else:
        print(f"  ⚠️ Fichier Météo non trouvé: {WEATHER_CSV}")
    
    return loaded_count > 0

def calculate_derived_variables(df):
    """Calculer les variables dérivées pour la modélisation"""
    
    # Conversion température Kelvin → Celsius
    if 'temperature_era5_k' in df.columns:
        df['temperature_era5_c'] = df['temperature_era5_k'] - 273.15
    
    # Conversion rayonnement J/m² → MJ/m²
    if 'solar_radiation_j_m2' in df.columns:
        df['solar_radiation_mj_m2'] = df['solar_radiation_j_m2'] / 1_000_000
    
    # Vitesse et direction du vent
    if 'wind_u_component_ms' in df.columns and 'wind_v_component_ms' in df.columns:
        df['wind_speed_ms'] = np.sqrt(df['wind_u_component_ms']**2 + df['wind_v_component_ms']**2)
        df['wind_direction_deg'] = np.degrees(np.arctan2(df['wind_v_component_ms'], df['wind_u_component_ms']))
        df['wind_direction_deg'] = (df['wind_direction_deg'] + 360) % 360
    
    # Amplitude température jour-nuit
    if 'temperature_day_modis_c' in df.columns and 'temperature_night_modis_c' in df.columns:
        df['temperature_amplitude_c'] = df['temperature_day_modis_c'] - df['temperature_night_modis_c']
    
    # Indice de santé végétale
    if 'ndvi_modis' in df.columns and 'evi_modis' in df.columns:
        df['vegetation_health_index'] = (df['ndvi_modis'] + df['evi_modis']) / 2
    
    # Degrés-jours de croissance (base 10°C)
    if 'temperature_era5_c' in df.columns:
        df['growing_degree_days'] = np.maximum(0, df['temperature_era5_c'] - 10)
    
    # Variables temporelles
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['month'] = pd.to_datetime(df['date']).dt.month
    df['day'] = pd.to_datetime(df['date']).dt.day
    df['day_of_year'] = pd.to_datetime(df['date']).dt.dayofyear
    
    # Indicateurs saisonniers
    df['is_rainy_season'] = df['month'].isin([6, 7, 8, 9, 10])
    df['is_dry_season'] = ~df['is_rainy_season']
    df['season'] = df['is_rainy_season'].map({True: 'Rainy', False: 'Dry'})
    
    return df

def calculate_rolling_variables(df):
    """Calculer les variables mobiles par région"""
    
    df = df.sort_values(['region', 'date'])
    
    for region in df['region'].unique():
        mask = df['region'] == region
        region_data = df[mask].copy()
        
        # Précipitations cumulées 30 jours
        if 'precipitation_era5_mm' in region_data.columns:
            df.loc[mask, 'precipitation_cumulative_30d'] = region_data['precipitation_era5_mm'].rolling(
                window=30, min_periods=1
            ).sum()
        
        # Température moyenne 7 jours
        if 'temperature_era5_c' in region_data.columns:
            df.loc[mask, 'temperature_mean_7d'] = region_data['temperature_era5_c'].rolling(
                window=7, min_periods=1
            ).mean()
        
        # Anomalie NDVI
        if 'ndvi_modis' in region_data.columns:
            ndvi_mean = region_data['ndvi_modis'].mean()
            df.loc[mask, 'ndvi_anomaly'] = region_data['ndvi_modis'] - ndvi_mean
    
    # Indice de sécheresse simple
    if 'precipitation_cumulative_30d' in df.columns and 'temperature_mean_7d' in df.columns:
        precip_norm = df['precipitation_cumulative_30d'] / (df['precipitation_cumulative_30d'].max() + 1e-6)
        temp_norm = df['temperature_mean_7d'] / df['temperature_mean_7d'].max()
        df['drought_index'] = temp_norm / (precip_norm + 0.1)
    
    # Score de complétude
    key_vars = ['temperature_era5_c', 'precipitation_era5_mm', 'ndvi_modis']
    available_vars = [var for var in key_vars if var in df.columns]
    if available_vars:
        df['data_completeness_score'] = df[available_vars].notna().mean(axis=1)
    else:
        df['data_completeness_score'] = 0.0
    
    return df

def load_gee_data():
    """Chargement des données GEE Sénégal"""
    print("📥 Chargement des données GEE Sénégal...")
    
    # Chercher les fichiers consolidés
    processed_dir = GEE_DATA_DIR / "processed"
    if not processed_dir.exists():
        processed_dir = GEE_DATA_DIR
    
    consolidated_files = list(processed_dir.glob("*_consolidated_data.csv"))
    
    if not consolidated_files:
        print(f"  ⚠️ Aucun fichier GEE trouvé dans {processed_dir}")
        return False
    
    print(f"  📁 Trouvé {len(consolidated_files)} fichiers GEE")
    
    all_data = []
    
    for file_path in consolidated_files:
        try:
            region_name = file_path.stem.replace('_consolidated_data', '').title()
            
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            df['region'] = region_name
            
            # Renommer selon le mapping
            df = df.rename(columns=MODEL_VARIABLES)
            
            print(f"    ✅ {region_name}: {len(df)} enregistrements")
            all_data.append(df)
            
        except Exception as e:
            print(f"    ❌ Erreur {file_path.name}: {e}")
    
    if not all_data:
        return False
    
    # Combiner et traiter
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"  📊 Total: {len(combined_df)} enregistrements")
    
    # Calculer les variables dérivées
    print("  🧮 Calcul des variables dérivées...")
    combined_df = calculate_derived_variables(combined_df)
    combined_df = calculate_rolling_variables(combined_df)
    
    # Sélectionner les colonnes de la table
    table_columns = [
        'region', 'latitude', 'longitude', 'date', 'year', 'month', 'day', 'day_of_year',
        'temperature_era5_k', 'temperature_era5_c', 'precipitation_era5_mm',
        'solar_radiation_j_m2', 'solar_radiation_mj_m2', 'wind_u_component_ms',
        'wind_v_component_ms', 'wind_speed_ms', 'wind_direction_deg',
        'precipitation_chirps_mm', 'temperature_day_modis_c', 'temperature_night_modis_c',
        'temperature_amplitude_c', 'ndvi_modis', 'evi_modis', 'vegetation_health_index',
        'soil_moisture_smap_percent', 'growing_degree_days', 'precipitation_cumulative_30d',
        'temperature_mean_7d', 'ndvi_anomaly', 'drought_index', 'is_rainy_season',
        'is_dry_season', 'season', 'data_completeness_score'
    ]
    
    available_columns = [col for col in table_columns if col in combined_df.columns]
    df_final = combined_df[available_columns].copy()
    
    # Nettoyer
    df_final = df_final.replace([np.inf, -np.inf], np.nan)
    
    # Charger en chunks
    print("  📦 Chargement en base...")
    chunk_size = 1000
    total_chunks = len(df_final) // chunk_size + 1
    
    try:
        for i, chunk_start in enumerate(range(0, len(df_final), chunk_size)):
            chunk_end = min(chunk_start + chunk_size, len(df_final))
            chunk_df = df_final.iloc[chunk_start:chunk_end]
            
            chunk_df.to_sql(
                'gee_senegal_agro_data',
                engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            if (i + 1) % 10 == 0 or i == total_chunks - 1:
                print(f"    📦 Chunk {i+1}/{total_chunks}")
        
        print(f"  ✅ GEE chargé: {len(df_final):,} enregistrements")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur chargement GEE: {e}")
        return False

def create_views():
    """Créer des vues utiles pour l'analyse"""
    print("📋 Création des vues d'analyse...")
    
    views = [
        # Vue résumé général
        """
        CREATE OR REPLACE VIEW data_summary AS
        SELECT 
            'FAO' as source,
            COUNT(*) as records,
            MIN(year) as min_year,
            MAX(year) as max_year,
            NULL as regions
        FROM fao_data
        WHERE EXISTS (SELECT 1 FROM fao_data LIMIT 1)
        
        UNION ALL
        
        SELECT 
            'Weather' as source,
            COUNT(*) as records,
            EXTRACT(YEAR FROM MIN(date)) as min_year,
            EXTRACT(YEAR FROM MAX(date)) as max_year,
            COUNT(DISTINCT ville) as regions
        FROM weather_data
        WHERE EXISTS (SELECT 1 FROM weather_data LIMIT 1)
        
        UNION ALL
        
        SELECT 
            'GEE_Senegal' as source,
            COUNT(*) as records,
            MIN(year) as min_year,
            MAX(year) as max_year,
            COUNT(DISTINCT region) as regions
        FROM gee_senegal_agro_data
        WHERE EXISTS (SELECT 1 FROM gee_senegal_agro_data LIMIT 1);
        """,
        
        # Vue GEE mensuelle
        """
        CREATE OR REPLACE VIEW gee_monthly_summary AS
        SELECT 
            region,
            year,
            month,
            COUNT(*) as records,
            ROUND(CAST(AVG(temperature_era5_c) AS NUMERIC), 2) as avg_temp_c,
            ROUND(CAST(SUM(precipitation_era5_mm) AS NUMERIC), 2) as total_precip_mm,
            ROUND(CAST(AVG(ndvi_modis) AS NUMERIC), 3) as avg_ndvi,
            ROUND(CAST(AVG(data_completeness_score) AS NUMERIC), 3) as completeness
        FROM gee_senegal_agro_data
        GROUP BY region, year, month
        ORDER BY region, year, month;
        """,
        
        # Vue données modélisation
        """
        CREATE OR REPLACE VIEW modeling_data AS
        SELECT 
            region,
            date,
            temperature_era5_c,
            precipitation_era5_mm,
            precipitation_cumulative_30d,
            ndvi_modis,
            soil_moisture_smap_percent,
            growing_degree_days,
            drought_index,
            is_rainy_season,
            data_completeness_score
        FROM gee_senegal_agro_data
        WHERE data_completeness_score > 0.7
        AND temperature_era5_c IS NOT NULL
        ORDER BY region, date;
        """
    ]
    
    # Create each view in separate transactions to avoid rollback issues
    for i, view_sql in enumerate(views):
        try:
            with engine.begin() as conn:
                conn.execute(text(view_sql))
        except Exception as e:
            print(f"    ⚠️ Erreur vue {i+1}: {e}")
    
    print("✅ Vues créées")

def verify_data():
    """Vérifier les données chargées"""
    print("🔍 Vérification des données...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM data_summary ORDER BY source;"))
            
            print("📊 Résumé par source:")
            for row in result:
                source, records, min_year, max_year, regions = row
                region_info = f", {regions} régions" if regions else ""
                print(f"  {source}: {records:,} enregistrements ({min_year}-{max_year}){region_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def main():
    """Fonction principale unifiée"""
    print("🚀 Chargement Unifié dans PostgreSQL")
    print("=" * 50)
    
    success_steps = 0
    
    try:
        # Étape 1: Créer les tables
        create_tables()
        success_steps += 1
        
        # Étape 2: Vider les tables
        clear_tables()
        success_steps += 1
        
        # Étape 3: Charger FAO/Météo (optionnel)
        print("\n📊 Chargement FAO/Météo...")
        load_fao_weather_data()  # Pas critique si ça échoue
        
        # Étape 4: Charger GEE (critique)
        print("\n🌍 Chargement GEE Sénégal...")
        if load_gee_data():
            success_steps += 1
        
        # Étape 5: Créer les vues
        print("\n📋 Finalisation...")
        create_views()
        success_steps += 1
        
        # Étape 6: Vérifier
        if verify_data():
            success_steps += 1
        
        # Résumé
        print(f"\n{'='*50}")
        if success_steps >= 4:  # Au minimum: tables + clear + GEE + vues
            print("🎉 Chargement réussi!")
            print("\n💡 Vues disponibles:")
            print("  - data_summary : Vue d'ensemble")
            print("  - gee_monthly_summary : Données mensuelles")
            print("  - modeling_data : Données pour ML")
        else:
            print(f"⚠️ Chargement partiel ({success_steps}/5 étapes)")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()