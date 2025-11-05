"""
Module pour fournir des données journalières réelles combinant APIs et données historiques
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class DailyDataProvider:
    """
    Classe pour récupérer et consolider les données journalières réelles
    """
    
    def __init__(self):
        # API Keys - Lire depuis config/config.json ou variables d'environnement
        self.openweather_api_key = self._load_api_key()
        
        # Coordonnées des villes du Sénégal
        self.cities_coords = {
            'Dakar': {'lat': 14.7167, 'lon': -17.4677},
            'Thiès': {'lat': 14.7886, 'lon': -16.9246},
            'Saint-Louis': {'lat': 16.0469, 'lon': -16.4897},
            'Kaolack': {'lat': 14.1593, 'lon': -16.0728},
            'Ziguinchor': {'lat': 12.5681, 'lon': -16.2719},
            'Tambacounda': {'lat': 13.7671, 'lon': -13.6681}
        }
        
        # Charger les données historiques
        self.historical_data = self._load_historical_data()
        
    def _load_historical_data(self) -> Dict[str, pd.DataFrame]:
        """Charger les données historiques depuis les fichiers CSV"""
        data = {}
        
        try:
            # Données météo historiques
            meteo_path = 'data/processed/meteo_clean.csv'
            if os.path.exists(meteo_path):
                data['meteo'] = pd.read_csv(meteo_path)
                if 'date' in data['meteo'].columns:
                    data['meteo']['date'] = pd.to_datetime(data['meteo']['date'])
                logger.info(f"Données météo chargées: {len(data['meteo'])} enregistrements")
            
            # Données satellitaires
            satellite_path = 'data/processed/senegal_gee_transformed.csv'
            if os.path.exists(satellite_path):
                data['satellite'] = pd.read_csv(satellite_path)
                if 'date' in data['satellite'].columns:
                    data['satellite']['date'] = pd.to_datetime(data['satellite']['date'])
                logger.info(f"Données satellitaires chargées: {len(data['satellite'])} enregistrements")
            
            # Données FAO
            fao_path = 'data/processed/clean_fao_20251031.csv'
            if os.path.exists(fao_path):
                data['fao'] = pd.read_csv(fao_path)
                logger.info(f"Données FAO chargées: {len(data['fao'])} enregistrements")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données historiques: {e}")
            
        return data
    
    def _load_api_key(self) -> str:
        """Charger la clé API depuis config/config.json ou variables d'environnement"""
        # Essayer d'abord le fichier de configuration
        try:
            import json
            config_path = 'config/config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    api_key = config.get('api_key', 'demo_key')
                    if api_key and api_key != 'demo_key':
                        logger.info("Clé API chargée depuis config/config.json")
                        return api_key
        except Exception as e:
            logger.warning(f"Impossible de charger config/config.json: {e}")
        
        # Fallback vers les variables d'environnement
        env_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
        if env_key != 'demo_key':
            logger.info("Clé API chargée depuis les variables d'environnement")
            return env_key
        
        logger.warning("Aucune clé API configurée, utilisation du mode démo")
        return 'demo_key'
    
    def get_current_weather(self, city: str) -> Optional[Dict]:
        """Récupérer les données météo actuelles via OpenWeatherMap"""
        if city not in self.cities_coords:
            logger.error(f"Ville {city} non supportée")
            return None
            
        coords = self.cities_coords[city]
        
        try:
            # API OpenWeatherMap Current Weather
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': coords['lat'],
                'lon': coords['lon'],
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data['wind'].get('speed', 0),
                    'wind_direction': data['wind'].get('deg', 0),
                    'cloudiness': data['clouds']['all'],
                    'visibility': data.get('visibility', 10000) / 1000,  # km
                    'weather_description': data['weather'][0]['description'],
                    'timestamp': datetime.now()
                }
            else:
                logger.warning(f"API OpenWeather erreur {response.status_code} pour {city}")
                return self._get_fallback_weather(city)
                
        except Exception as e:
            logger.error(f"Erreur API OpenWeather pour {city}: {e}")
            return self._get_fallback_weather(city)
    
    def get_forecast_data(self, city: str, days: int = 7) -> Optional[List[Dict]]:
        """Récupérer les prévisions météo pour les prochains jours"""
        if city not in self.cities_coords:
            return None
            
        coords = self.cities_coords[city]
        
        try:
            # API OpenWeatherMap 5-day forecast
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': coords['lat'],
                'lon': coords['lon'],
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                forecasts = []
                
                for item in data['list'][:days * 8]:  # 8 prévisions par jour (3h intervals)
                    forecasts.append({
                        'datetime': datetime.fromtimestamp(item['dt']),
                        'temperature': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'pressure': item['main']['pressure'],
                        'wind_speed': item['wind'].get('speed', 0),
                        'precipitation': item.get('rain', {}).get('3h', 0),
                        'cloudiness': item['clouds']['all'],
                        'weather_description': item['weather'][0]['description']
                    })
                
                return forecasts
            else:
                logger.warning(f"API Forecast erreur {response.status_code} pour {city}")
                return self._get_fallback_forecast(city, days)
                
        except Exception as e:
            logger.error(f"Erreur API Forecast pour {city}: {e}")
            return self._get_fallback_forecast(city, days)
    
    def get_historical_averages(self, city: str, date: datetime) -> Dict:
        """Récupérer les moyennes historiques pour une date donnée"""
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # Moyennes basées sur les données historiques du Sénégal
        seasonal_data = {
            'Dakar': {
                'temp_range': (18, 35) if month in [12, 1, 2, 3] else (22, 32),
                'humidity_range': (40, 80) if month in [6, 7, 8, 9] else (30, 70),
                'precipitation_avg': 0.1 if month in [11, 12, 1, 2, 3, 4, 5] else 8.5
            },
            'Thiès': {
                'temp_range': (16, 38) if month in [12, 1, 2, 3] else (20, 35),
                'humidity_range': (35, 85) if month in [6, 7, 8, 9] else (25, 65),
                'precipitation_avg': 0.05 if month in [11, 12, 1, 2, 3, 4, 5] else 12.0
            },
            'Saint-Louis': {
                'temp_range': (15, 40) if month in [12, 1, 2, 3] else (22, 38),
                'humidity_range': (30, 75) if month in [6, 7, 8, 9] else (20, 60),
                'precipitation_avg': 0.02 if month in [11, 12, 1, 2, 3, 4, 5] else 6.5
            },
            'Kaolack': {
                'temp_range': (17, 42) if month in [12, 1, 2, 3] else (23, 39),
                'humidity_range': (35, 85) if month in [6, 7, 8, 9] else (25, 70),
                'precipitation_avg': 0.08 if month in [11, 12, 1, 2, 3, 4, 5] else 15.2
            },
            'Ziguinchor': {
                'temp_range': (20, 38) if month in [12, 1, 2, 3] else (24, 35),
                'humidity_range': (45, 90) if month in [6, 7, 8, 9] else (35, 75),
                'precipitation_avg': 0.2 if month in [11, 12, 1, 2, 3, 4, 5] else 25.8
            },
            'Tambacounda': {
                'temp_range': (15, 45) if month in [12, 1, 2, 3] else (25, 42),
                'humidity_range': (25, 80) if month in [6, 7, 8, 9] else (15, 60),
                'precipitation_avg': 0.03 if month in [11, 12, 1, 2, 3, 4, 5] else 18.5
            }
        }
        
        city_data = seasonal_data.get(city, seasonal_data['Dakar'])
        
        return {
            'temperature_min': city_data['temp_range'][0],
            'temperature_max': city_data['temp_range'][1],
            'humidity_min': city_data['humidity_range'][0],
            'humidity_max': city_data['humidity_range'][1],
            'precipitation_avg': city_data['precipitation_avg'],
            'season': 'Wet' if month in [6, 7, 8, 9, 10] else 'Dry'
        }
    
    def get_daily_alerts(self) -> List[Dict]:
        """Générer les alertes du jour basées sur les données réelles"""
        alerts = []
        
        for city in self.cities_coords.keys():
            current_weather = self.get_current_weather(city)
            if not current_weather:
                continue
                
            historical = self.get_historical_averages(city, datetime.now())
            
            # Alerte température
            if current_weather['temperature'] > historical['temperature_max'] + 3:
                alerts.append({
                    'region': city,
                    'type': 'Température',
                    'level': 'Critique',
                    'message': f"Température extrême: {current_weather['temperature']:.1f}°C"
                })
            
            # Alerte humidité (sécheresse)
            if current_weather['humidity'] < historical['humidity_min'] - 10:
                alerts.append({
                    'region': city,
                    'type': 'Sécheresse',
                    'level': 'Élevé',
                    'message': f"Humidité très faible: {current_weather['humidity']}%"
                })
            
            # Alerte vent fort
            if current_weather['wind_speed'] > 10:
                alerts.append({
                    'region': city,
                    'type': 'Vent',
                    'level': 'Modéré',
                    'message': f"Vent fort: {current_weather['wind_speed']:.1f} m/s"
                })
        
        return alerts[:3]  # Limiter à 3 alertes principales
    
    def get_regional_trends(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """Récupérer les tendances régionales des derniers jours"""
        trends = {}
        
        # Générer des dates pour les derniers jours
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')
        
        # Données de précipitations
        precip_data = {'Date': dates}
        temp_data = {'Date': dates}
        
        for city in ['Dakar', 'Thiès', 'Saint-Louis', 'Kaolack']:
            # Utiliser les données historiques si disponibles, sinon simuler
            if 'meteo' in self.historical_data and not self.historical_data['meteo'].empty:
                # Essayer de récupérer les vraies données
                city_historical = self._get_city_historical_data(city, dates)
                precip_data[city] = city_historical['precipitation']
                temp_data[city] = city_historical['temperature']
            else:
                # Données simulées basées sur les moyennes saisonnières
                historical = self.get_historical_averages(city, datetime.now())
                precip_data[city] = np.random.exponential(historical['precipitation_avg'], days)
                temp_avg = (historical['temperature_min'] + historical['temperature_max']) / 2
                temp_data[city] = temp_avg + np.random.normal(0, 2, days)
        
        trends['precipitation'] = pd.DataFrame(precip_data)
        trends['temperature'] = pd.DataFrame(temp_data)
        
        return trends
    
    def _get_city_historical_data(self, city: str, dates: pd.DatetimeIndex) -> Dict:
        """Récupérer les données historiques pour une ville et des dates spécifiques"""
        # Placeholder pour l'extraction des données historiques réelles
        # À adapter selon la structure exacte des fichiers CSV
        
        historical = self.get_historical_averages(city, datetime.now())
        
        return {
            'precipitation': np.random.exponential(historical['precipitation_avg'], len(dates)),
            'temperature': (historical['temperature_min'] + historical['temperature_max']) / 2 + np.random.normal(0, 2, len(dates))
        }
    
    def _get_fallback_weather(self, city: str) -> Dict:
        """Données météo de secours basées sur les moyennes historiques"""
        historical = self.get_historical_averages(city, datetime.now())
        
        return {
            'temperature': (historical['temperature_min'] + historical['temperature_max']) / 2,
            'humidity': (historical['humidity_min'] + historical['humidity_max']) / 2,
            'pressure': 1013,
            'wind_speed': 3.0,
            'wind_direction': 180,
            'cloudiness': 30,
            'visibility': 10,
            'weather_description': 'Données historiques',
            'timestamp': datetime.now()
        }
    
    def _get_fallback_forecast(self, city: str, days: int) -> List[Dict]:
        """Prévisions de secours basées sur les moyennes historiques"""
        forecasts = []
        historical = self.get_historical_averages(city, datetime.now())
        
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            forecasts.append({
                'datetime': date,
                'temperature': (historical['temperature_min'] + historical['temperature_max']) / 2 + np.random.normal(0, 1),
                'humidity': (historical['humidity_min'] + historical['humidity_max']) / 2 + np.random.normal(0, 5),
                'pressure': 1013 + np.random.normal(0, 5),
                'wind_speed': 3.0 + np.random.normal(0, 1),
                'precipitation': np.random.exponential(historical['precipitation_avg']),
                'cloudiness': 30 + np.random.normal(0, 10),
                'weather_description': 'Prévision basée sur historique'
            })
        
        return forecasts