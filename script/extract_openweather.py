"""
extract_openweather.py

Script d'extraction des données météorologiques en temps réel 
pour les 14 régions du Sénégal via l'API OpenWeatherMap.

Utilise l'API One Call 3.0 pour récupérer les conditions météo actuelles
et sauvegarde les données dans un fichier CSV.
"""

import requests
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv non installé. Installez avec: pip install python-dotenv")
    print("   Ou définissez manuellement les variables d'environnement")

# Configuration API
API_KEY = os.getenv("OPENWEATHER_API_KEY")  

# Configuration des chemins
BASE_DATA_DIR = Path("/Users/alii_ibn_hassan/Documents/DataBeez_Hackaton/Base/data")
RAW_DATA_DIR = BASE_DATA_DIR / "raw"
CLEAN_DATA_DIR = BASE_DATA_DIR / "clean"

# Régions du Sénégal avec coordonnées géographiques
REGIONS_SENEGAL = {
    "Dakar": {"lat": 14.7167, "lon": -17.4677},
    "Thiès": {"lat": 14.7910, "lon": -16.9250},
    "Saint-Louis": {"lat": 16.0179, "lon": -16.4896},
    "Kaolack": {"lat": 14.1469, "lon": -16.0726},
    "Ziguinchor": {"lat": 12.5833, "lon": -16.2719},
    "Tambacounda": {"lat": 13.7707, "lon": -13.6673},
    "Fatick": {"lat": 14.3396, "lon": -16.4114},
    "Diourbel": {"lat": 14.6558, "lon": -16.2334},
    "Louga": {"lat": 15.6144, "lon": -16.2286},
    "Matam": {"lat": 15.6600, "lon": -13.2550},
    "Kolda": {"lat": 12.8833, "lon": -14.9500},
    "Kaffrine": {"lat": 14.1050, "lon": -15.5500},
    "Sédhiou": {"lat": 12.7089, "lon": -15.5561},
    "Kédougou": {"lat": 12.5556, "lon": -12.1744}
}

def extract_weather_data(region_name, coordinates):
    """
    Appelle l'API OpenWeather One Call pour une région donnée
    
    Args:
        region_name (str): Nom de la région
        coordinates (dict): Dictionnaire avec 'lat' et 'lon'
    
    Returns:
        dict: Données météo formatées ou None en cas d'erreur
    """
    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": coordinates["lat"],
        "lon": coordinates["lon"],
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr",
        "exclude": "minutely,hourly,daily,alerts"  # garder seulement current
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "current" not in data:
            print(f"❌ Erreur {region_name}: {data}")
            return None
        
        current = data["current"]
        
        # Formatage des données
        weather_record = {
            "ville": region_name,
            "type": "current",
            "date": datetime.utcfromtimestamp(current.get("dt")).strftime("%Y-%m-%d %H:%M:%S"),
            "temperature_c": current.get("temp"),
            "humidity_percent": current.get("humidity"),
            "pressure_hpa": current.get("pressure"),
            "wind_m_s": current.get("wind_speed"),
            "precipitation_mm": current.get("rain", {}).get("1h", 0),  # mm dernière heure
            "weather_description": current["weather"][0]["description"] if "weather" in current else None
        }
        
        print(f"✅ {region_name}: {weather_record['temperature_c']}°C, {weather_record['weather_description']}")
        return weather_record
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau {region_name}: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur {region_name}: {e}")
        return None

def create_data_structure():
    """
    Crée la structure de dossiers pour les données
    """
    try:
        # Créer les dossiers s'ils n'existent pas
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Structure créée:")
        print(f"  - Données brutes: {RAW_DATA_DIR}")
        print(f"  - Données nettoyées: {CLEAN_DATA_DIR}")
        
    except Exception as e:
        print(f"❌ Erreur création dossiers: {e}")

def collect_all_weather_data():
    """
    Collecte les données météo pour toutes les régions du Sénégal
    
    Returns:
        pd.DataFrame: DataFrame avec toutes les données météo
    """
    print("🌤️ Extraction des données météo OpenWeather")
    print("=" * 50)
    
    weather_records = []
    
    for region, coordinates in REGIONS_SENEGAL.items():
        record = extract_weather_data(region, coordinates)
        if record:
            weather_records.append(record)
    
    if not weather_records:
        print("❌ Aucune donnée météo récupérée")
        return pd.DataFrame()
    
    df_weather = pd.DataFrame(weather_records)
    
    print(f"\n📊 Résumé:")
    print(f"  - Régions collectées: {len(df_weather)}/{len(REGIONS_SENEGAL)}")
    print(f"  - Température moyenne: {df_weather['temperature_c'].mean():.1f}°C")
    print(f"  - Humidité moyenne: {df_weather['humidity_percent'].mean():.0f}%")
    
    return df_weather

def save_weather_data(df_weather):
    """
    Sauvegarde les données météo dans les dossiers appropriés
    
    Args:
        df_weather (pd.DataFrame): DataFrame avec les données météo
    """
    if df_weather.empty:
        print("⚠️ Aucune donnée à sauvegarder")
        return
    
    try:
        # Sauvegarder les données brutes
        raw_file = RAW_DATA_DIR / "weather_senegal_raw.csv"
        df_weather.to_csv(raw_file, index=False, encoding="utf-8-sig")
        print(f"💾 Données brutes: {raw_file}")
        
        # Créer une version nettoyée (renommer les colonnes pour correspondre au schéma DB)
        df_clean = df_weather.copy()
        df_clean = df_clean.rename(columns={
            'temperature_c': 'temperature_c',
            'humidity_percent': 'humidity_percent', 
            'pressure_hpa': 'pressure_hpa',
            'wind_m_s': 'wind_m_s',
            'precipitation_mm': 'precipitation_mm',
            'weather_description': 'weather_description'
        })
        
        # Sauvegarder la version nettoyée
        clean_file = CLEAN_DATA_DIR / "clean_weather.csv"
        df_clean.to_csv(clean_file, index=False, encoding="utf-8-sig")
        print(f"💾 Données nettoyées: {clean_file}")
        
        # Écraser aussi l'ancien fichier dans le répertoire principal
        main_file = BASE_DATA_DIR / "weather_senegal.csv"
        df_clean.to_csv(main_file, index=False, encoding="utf-8-sig")
        print(f"💾 Fichier principal écrasé: {main_file}")
        
        # Affichage d'un aperçu
        print(f"\n📋 Aperçu des données:")
        print(df_clean[['ville', 'temperature_c', 'humidity_percent', 'weather_description']].head())
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def display_weather_info(df_weather):
    """
    Affiche des informations détaillées sur les données météo
    
    Args:
        df_weather (pd.DataFrame): DataFrame avec les données météo
    """
    if df_weather.empty:
        return
    
    print(f"\n📈 Informations détaillées:")
    print(f"  - Nombre d'enregistrements: {len(df_weather)}")
    print(f"  - Colonnes: {list(df_weather.columns)}")
    print(f"  - Types de données:")
    
    for col in df_weather.columns:
        dtype = df_weather[col].dtype
        non_null = df_weather[col].count()
        print(f"    {col}: {dtype} ({non_null} non-null)")

def main():
    """Fonction principale"""
    try:
        # Vérification de la clé API
        if not API_KEY:
            print("⚠️ Clé API OpenWeather manquante!")
            print("   Définissez la variable d'environnement OPENWEATHER_API_KEY")
            print("   Exemple: export OPENWEATHER_API_KEY=your_api_key_here")
            return
        
        # Créer la structure de dossiers
        create_data_structure()
        
        # Collecte des données
        df_weather = collect_all_weather_data()
        
        if not df_weather.empty:
            # Sauvegarde
            save_weather_data(df_weather)
            
            # Informations détaillées
            display_weather_info(df_weather)
            
            print(f"\n🎉 Extraction terminée avec succès!")
        else:
            print("❌ Échec de l'extraction")
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()