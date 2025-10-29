#!/usr/bin/env python3
"""
transform_weather.py

Script de transformation et nettoyage des données météorologiques
- Nettoyage des données météo brutes
- Standardisation des formats
- Validation et enrichissement
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration des chemins
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
CLEAN_DATA_DIR = BASE_DIR / "data" / "clean"

def load_weather_data():
    """Charge les données météo brutes"""
    print("📥 Chargement des données météo brutes...")
    
    # Chercher les fichiers météo
    weather_files = list(RAW_DATA_DIR.glob("weather_*.csv"))
    
    if not weather_files:
        print("❌ Aucun fichier météo trouvé dans data/raw/")
        return None
    
    all_data = []
    
    for file_path in weather_files:
        print(f"  📄 Lecture: {file_path.name}")
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except Exception as e:
            print(f"  ❌ Erreur lecture {file_path.name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"✅ Données chargées: {len(combined_df):,} enregistrements")
        return combined_df
    
    return None

def clean_weather_data(df):
    """Nettoie et standardise les données météo"""
    print("🧹 Nettoyage des données météo...")
    
    # Standardiser les noms de colonnes
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Mapping des colonnes pour standardisation
    column_mapping = {
        'ville': 'ville',
        'city': 'ville',
        'region': 'ville',
        'temperature': 'temperature_c',
        'temp': 'temperature_c',
        'humidite': 'humidity_percent',
        'humidity': 'humidity_percent',
        'pression': 'pressure_hpa',
        'pressure': 'pressure_hpa',
        'vent': 'wind_m_s',
        'wind': 'wind_m_s',
        'wind_speed': 'wind_m_s',
        'pluie': 'precipitation_mm',
        'rain': 'precipitation_mm',
        'precipitation': 'precipitation_mm',
        'description': 'weather_description'
    }
    
    # Renommer les colonnes
    df = df.rename(columns=column_mapping)
    
    # Colonnes essentielles
    essential_columns = [
        'ville', 'date', 'temperature_c', 'humidity_percent', 
        'pressure_hpa', 'wind_m_s', 'precipitation_mm', 'weather_description'
    ]
    
    # Garder les colonnes disponibles
    available_columns = [col for col in essential_columns if col in df.columns]
    df_clean = df[available_columns].copy()
    
    # Nettoyer la date
    if 'date' in df_clean.columns:
        df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
        df_clean = df_clean.dropna(subset=['date'])
    
    # Nettoyer les valeurs numériques
    numeric_columns = ['temperature_c', 'humidity_percent', 'pressure_hpa', 'wind_m_s', 'precipitation_mm']
    
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Ajouter une colonne type si elle n'existe pas
    if 'type' not in df_clean.columns:
        df_clean['type'] = 'current'
    
    # Supprimer les doublons
    initial_count = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    removed_duplicates = initial_count - len(df_clean)
    
    if removed_duplicates > 0:
        print(f"  🗑️ Supprimé {removed_duplicates:,} doublons")
    
    print(f"✅ Données nettoyées: {len(df_clean):,} enregistrements")
    return df_clean

def validate_weather_data(df):
    """Valide la qualité des données météo"""
    print("🔍 Validation des données météo...")
    
    validation_results = {
        'total_records': len(df),
        'unique_cities': df['ville'].nunique() if 'ville' in df.columns else 0,
        'date_range': None,
        'temperature_range': None,
        'missing_values': {}
    }
    
    # Analyse des dates
    if 'date' in df.columns:
        date_range = (df['date'].min(), df['date'].max())
        validation_results['date_range'] = date_range
        print(f"  📅 Période: {date_range[0].strftime('%Y-%m-%d')} à {date_range[1].strftime('%Y-%m-%d')}")
    
    # Analyse des températures
    if 'temperature_c' in df.columns:
        temp_stats = df['temperature_c'].describe()
        validation_results['temperature_range'] = (temp_stats['min'], temp_stats['max'])
        print(f"  🌡️ Température: {temp_stats['min']:.1f}°C à {temp_stats['max']:.1f}°C")
    
    # Analyse des valeurs manquantes
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            missing_pct = (missing_count / len(df)) * 100
            validation_results['missing_values'][col] = missing_pct
            print(f"  ⚠️ {col}: {missing_pct:.1f}% de valeurs manquantes")
    
    print(f"  📊 Enregistrements totaux: {validation_results['total_records']:,}")
    print(f"  🏙️ Villes uniques: {validation_results['unique_cities']}")
    
    return validation_results

def enrich_weather_data(df):
    """Enrichit les données météo avec des variables dérivées"""
    print("🔧 Enrichissement des données météo...")
    
    # Ajouter des variables temporelles
    if 'date' in df.columns:
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_year'] = df['date'].dt.dayofyear
        df['weekday'] = df['date'].dt.weekday
    
    # Calculer l'indice de chaleur (si température et humidité disponibles)
    if 'temperature_c' in df.columns and 'humidity_percent' in df.columns:
        # Formule simplifiée de l'indice de chaleur
        df['heat_index'] = df['temperature_c'] + (0.5 * df['humidity_percent'] / 100 * df['temperature_c'])
    
    # Calculer la vitesse du vent en km/h
    if 'wind_m_s' in df.columns:
        df['wind_km_h'] = df['wind_m_s'] * 3.6
    
    # Catégoriser les conditions météo
    if 'weather_description' in df.columns:
        def categorize_weather(description):
            if pd.isna(description):
                return 'unknown'
            desc_lower = str(description).lower()
            if any(word in desc_lower for word in ['pluie', 'rain', 'orage', 'storm']):
                return 'rainy'
            elif any(word in desc_lower for word in ['nuage', 'cloud', 'couvert']):
                return 'cloudy'
            elif any(word in desc_lower for word in ['clair', 'clear', 'dégagé']):
                return 'clear'
            else:
                return 'other'
        
        df['weather_category'] = df['weather_description'].apply(categorize_weather)
    
    print(f"✅ Données enrichies avec {len([col for col in df.columns if col not in ['ville', 'date', 'temperature_c', 'humidity_percent', 'pressure_hpa', 'wind_m_s', 'precipitation_mm', 'weather_description']])} nouvelles variables")
    
    return df

def save_clean_data(df):
    """Sauvegarde les données nettoyées"""
    print("💾 Sauvegarde des données nettoyées...")
    
    # Créer le dossier clean s'il n'existe pas
    CLEAN_DATA_DIR.mkdir(exist_ok=True)
    
    # Sauvegarder
    output_file = CLEAN_DATA_DIR / "clean_weather.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ Données sauvegardées: {output_file}")
    print(f"  📊 {len(df):,} enregistrements")
    print(f"  📋 {len(df.columns)} colonnes")
    
    return output_file

def generate_summary_report(df):
    """Génère un rapport de résumé"""
    print("📋 Génération du rapport de résumé...")
    
    # Statistiques par ville
    if 'ville' in df.columns:
        city_stats = df['ville'].value_counts()
        print(f"\n🏙️ Répartition par ville:")
        for city, count in city_stats.items():
            print(f"  - {city}: {count:,} enregistrements")
    
    # Statistiques météo moyennes
    if 'temperature_c' in df.columns:
        temp_by_city = df.groupby('ville')['temperature_c'].mean().sort_values(ascending=False)
        print(f"\n🌡️ Température moyenne par ville:")
        for city, temp in temp_by_city.head().items():
            print(f"  - {city}: {temp:.1f}°C")
    
    # Conditions météo les plus fréquentes
    if 'weather_category' in df.columns:
        weather_counts = df['weather_category'].value_counts()
        print(f"\n☁️ Conditions météo:")
        for condition, count in weather_counts.items():
            pct = (count / len(df)) * 100
            print(f"  - {condition}: {count:,} ({pct:.1f}%)")

def main():
    """Fonction principale"""
    print("🌤️ Transformation des Données Météo")
    print("=" * 40)
    
    try:
        # Charger les données brutes
        df_raw = load_weather_data()
        if df_raw is None:
            return 1
        
        # Nettoyer les données
        df_clean = clean_weather_data(df_raw)
        
        # Valider les données
        validation_results = validate_weather_data(df_clean)
        
        # Enrichir les données
        df_enriched = enrich_weather_data(df_clean)
        
        # Sauvegarder
        output_file = save_clean_data(df_enriched)
        
        # Générer le rapport
        generate_summary_report(df_enriched)
        
        print(f"\n🎉 Transformation terminée avec succès!")
        print(f"📄 Fichier de sortie: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la transformation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())