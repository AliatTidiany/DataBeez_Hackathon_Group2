"""
Module pour récupérer les données en temps réel et faire des prédictions automatiques
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RealTimeDataProvider:
    """
    Classe pour récupérer les données météorologiques en temps réel
    """
    
    def __init__(self):
        # API Keys (à configurer dans les variables d'environnement)
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
        
        # Coordonnées des principales villes du Sénégal
        self.cities_coords = {
            'Dakar': {'lat': 14.7167, 'lon': -17.4677},
            'Thiès': {'lat': 14.7886, 'lon': -16.9246},
            'Saint-Louis': {'lat': 16.0469, 'lon': -16.4897},
            'Kaolack': {'lat': 14.1593, 'lon': -16.0728},
            'Ziguinchor': {'lat': 12.5681, 'lon': -16.2719},
            'Tambacounda': {'lat': 13.7671, 'lon': -13.6681}
        }
        
        # Données empiriques basées sur les moyennes historiques
        self.empirical_data = {
            'ndvi_seasonal': {
                'Dry': {'mean': 0.3, 'std': 0.1},
                'Wet': {'mean': 0.7, 'std': 0.15}
            },
            'soil_moisture_seasonal': {
                'Dry': {'mean': 0.25, 'std': 0.08},
                'Wet': {'mean': 0.65, 'std': 0.12}
            },
            'crop_stages': {
                'mil': {'planting_month': 6, 'harvest_month': 10},
                'sorgho': {'planting_month': 6, 'harvest_month': 11},
                'mais': {'planting_month': 5, 'harvest_month': 9},
                'riz': {'planting_month': 7, 'harvest_month': 12},
                'arachide': {'planting_month': 6, 'harvest_month': 11},
                'coton': {'planting_month': 5, 'harvest_month': 12}
            }
        }
    
    def get_current_weather(self, city: str) -> Dict:
        """Récupérer les données météo actuelles"""
        try:
            if city not in self.cities_coords:
                raise ValueError(f"Ville {city} non supportée")
            
            coords = self.cities_coords[city]
            
            # URL de l'API OpenWeatherMap
            url = f"http://api.openweathermap.org/data/3.0/weather"
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
                    'wind_speed': data['wind'].get('speed', 2.0),
                    'description': data['weather'][0]['description'],
                    'timestamp': datetime.now()
                }
            else:
                logger.warning(f"API météo indisponible, utilisation de données par défaut")
                return self._get_default_weather(city)
                
        except Exception as e:
            logger.error(f"Erreur récupération météo pour {city}: {e}")
            return self._get_default_weather(city)
    
    def _get_default_weather(self, city: str) -> Dict:
        """Données météo par défaut basées sur les moyennes saisonnières"""
        current_month = datetime.now().month
        
        # Déterminer la saison
        if 11 <= current_month <= 4:  # Saison sèche
            season = 'Dry'
            temp_base = 28
            humidity_base = 45
        else:  # Saison des pluies
            season = 'Wet'
            temp_base = 26
            humidity_base = 75
        
        # Ajustements par ville (latitude)
        city_adjustments = {
            'Saint-Louis': {'temp': +3, 'humidity': -10},
            'Tambacounda': {'temp': +4, 'humidity': -15},
            'Ziguinchor': {'temp': -1, 'humidity': +5},
            'Dakar': {'temp': 0, 'humidity': 0},
            'Thiès': {'temp': +1, 'humidity': -5},
            'Kaolack': {'temp': +2, 'humidity': -8}
        }
        
        adj = city_adjustments.get(city, {'temp': 0, 'humidity': 0})
        
        return {
            'temperature': temp_base + adj['temp'] + np.random.normal(0, 2),
            'humidity': max(20, min(100, humidity_base + adj['humidity'] + np.random.normal(0, 10))),
            'pressure': 1012 + np.random.normal(0, 5),
            'wind_speed': 2.5 + np.random.exponential(1),
            'description': 'données simulées',
            'timestamp': datetime.now(),
            'season': season
        }
    
    def get_empirical_data(self, city: str, crop_type: str = 'mil') -> Dict:
        """Récupérer les données empiriques pour une région et culture"""
        current_month = datetime.now().month
        current_date = datetime.now()
        
        # Déterminer la saison
        season = 'Wet' if 5 <= current_month <= 10 else 'Dry'
        
        # NDVI basé sur la saison
        ndvi_params = self.empirical_data['ndvi_seasonal'][season]
        ndvi = max(0.1, min(1.0, np.random.normal(ndvi_params['mean'], ndvi_params['std'])))
        
        # Humidité du sol basée sur la saison
        ssm_params = self.empirical_data['soil_moisture_seasonal'][season]
        soil_moisture = max(0.1, min(1.0, np.random.normal(ssm_params['mean'], ssm_params['std'])))
        
        # Stade de croissance de la culture
        crop_info = self.empirical_data['crop_stages'].get(crop_type, self.empirical_data['crop_stages']['mil'])
        planting_month = crop_info['planting_month']
        
        # Calculer les jours depuis la plantation
        if current_month >= planting_month:
            months_since_planting = current_month - planting_month
        else:
            months_since_planting = (12 - planting_month) + current_month
        
        growth_stage = min(180, max(1, months_since_planting * 30 + current_date.day))
        
        # Données satellitaires simulées
        solar_radiation = 20 + 5 * np.sin(2 * np.pi * current_month / 12) + np.random.normal(0, 2)
        
        return {
            'ndvi': ndvi,
            'evi': ndvi * 0.8,
            'soil_moisture': soil_moisture,
            'season': season,
            'growth_stage': growth_stage,
            'solar_radiation': max(10, solar_radiation),
            'precipitation_7d': 0 if season == 'Dry' else np.random.exponential(10),
            'leaf_wetness': 2 if season == 'Dry' else 8 + np.random.exponential(4),
            'crop_type': crop_type
        }
    
    def get_complete_data(self, city: str, crop_type: str = 'mil') -> Dict:
        """Récupérer toutes les données nécessaires pour les prédictions"""
        weather_data = self.get_current_weather(city)
        empirical_data = self.get_empirical_data(city, crop_type)
        
        # Combiner toutes les données
        complete_data = {
            **weather_data,
            **empirical_data,
            'city': city,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'temp_max': weather_data['temperature'] + np.random.uniform(2, 6),
            'temp_min': weather_data['temperature'] - np.random.uniform(3, 7)
        }
        
        return complete_data

class AutomaticPredictor:
    """
    Classe pour faire des prédictions automatiques avec les données en temps réel
    """
    
    def __init__(self, models_dict):
        self.models = models_dict
        self.data_provider = RealTimeDataProvider()
    
    def predict_all_for_city(self, city: str, crop_type: str = 'mil') -> Dict:
        """Faire toutes les prédictions pour une ville donnée"""
        try:
            # Récupérer les données en temps réel
            data = self.data_provider.get_complete_data(city, crop_type)
            
            results = {
                'city': city,
                'crop_type': crop_type,
                'timestamp': data['timestamp'],
                'weather_conditions': {
                    'temperature': data['temperature'],
                    'humidity': data['humidity'],
                    'season': data['season'],
                    'description': data['description']
                }
            }
            
            # Prédiction des précipitations
            if self.models.get('rainfall'):
                try:
                    from models.streamlit_app import prepare_features_for_model
                    features_df = prepare_features_for_model(self.models['rainfall'], data, data['date'])
                    if features_df is not None:
                        prediction = self.models['rainfall'].predict(features_df)[0]
                        results['rainfall'] = {
                            'predicted_mm': round(prediction, 2),
                            'category': self._categorize_rainfall(prediction),
                            'confidence': 85
                        }
                    else:
                        # Valeur par défaut basée sur la saison
                        default_rain = 0.5 if data['season'] == 'Dry' else 3.0
                        results['rainfall'] = {
                            'predicted_mm': default_rain,
                            'category': self._categorize_rainfall(default_rain),
                            'confidence': 60
                        }
                except Exception as e:
                    # Valeur par défaut en cas d'erreur
                    default_rain = 0.5 if data.get('season', 'Dry') == 'Dry' else 3.0
                    results['rainfall'] = {
                        'predicted_mm': default_rain,
                        'category': self._categorize_rainfall(default_rain),
                        'confidence': 50
                    }
            
            # Prédiction de sécheresse
            if self.models.get('drought'):
                try:
                    from models.streamlit_app import prepare_features_for_model
                    features_df = prepare_features_for_model(self.models['drought'], data, data['date'])
                    if features_df is not None:
                        prediction = self.models['drought'].predict(features_df)[0]
                        results['drought'] = {
                            'risk_level': self._categorize_drought(prediction),
                            'severity': int(prediction),
                            'confidence': 85
                        }
                    else:
                        # Valeur par défaut basée sur les conditions
                        default_severity = 2 if data['season'] == 'Dry' and data['ssm'] < 0.3 else 1
                        results['drought'] = {
                            'risk_level': self._categorize_drought(default_severity),
                            'severity': default_severity,
                            'confidence': 60
                        }
                except Exception as e:
                    # Valeur par défaut en cas d'erreur
                    default_severity = 1 if data.get('season', 'Wet') == 'Wet' else 2
                    results['drought'] = {
                        'risk_level': self._categorize_drought(default_severity),
                        'severity': default_severity,
                        'confidence': 50
                    }
            
            # Optimisation irrigation
            if self.models.get('irrigation'):
                try:
                    from models.streamlit_app import prepare_features_for_model
                    features_df = prepare_features_for_model(self.models['irrigation'], data, data['date'])
                    if features_df is not None:
                        prediction = self.models['irrigation'].predict(features_df)[0]
                        results['irrigation'] = {
                            'need_mm_per_day': round(prediction, 2),
                            'frequency': self._get_irrigation_frequency(prediction),
                            'efficiency': 85
                        }
                    else:
                        # Calcul par défaut basé sur les conditions
                        base_need = 5.0 if data['season'] == 'Dry' else 3.0
                        temp_factor = (data['temperature'] - 25) * 0.2
                        humidity_factor = (70 - data['humidity']) * 0.05
                        default_need = max(1.0, base_need + temp_factor + humidity_factor)
                        
                        results['irrigation'] = {
                            'need_mm_per_day': round(default_need, 2),
                            'frequency': self._get_irrigation_frequency(default_need),
                            'efficiency': 75
                        }
                except Exception as e:
                    # Valeur par défaut en cas d'erreur
                    default_need = 4.0 if data.get('season', 'Wet') == 'Dry' else 2.5
                    results['irrigation'] = {
                        'need_mm_per_day': default_need,
                        'frequency': self._get_irrigation_frequency(default_need),
                        'efficiency': 70
                    }
            
            # Prédiction maladies supprimée pour simplifier l'interface
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur prédiction automatique pour {city}: {e}")
            return {'error': str(e)}
    
    def _categorize_rainfall(self, value: float) -> str:
        """Catégoriser les précipitations"""
        if value < 1:
            return "Pas de pluie"
        elif value < 5:
            return "Pluie légère"
        elif value < 15:
            return "Pluie modérée"
        else:
            return "Pluie forte"
    
    def _categorize_drought(self, value: int) -> str:
        """Catégoriser le risque de sécheresse"""
        levels = {0: "Aucun", 1: "Léger", 2: "Modéré", 3: "Sévère"}
        return levels.get(value, "Inconnu")
    
    def _get_irrigation_frequency(self, value: float) -> str:
        """Déterminer la fréquence d'irrigation"""
        if value < 2:
            return "Tous les 3-4 jours"
        elif value < 5:
            return "Tous les 2 jours"
        elif value < 8:
            return "Quotidienne"
        else:
            return "2 fois par jour"
    
    def _categorize_disease_risk(self, value: int) -> str:
        """Catégoriser le risque de maladie"""
        levels = {0: "Faible", 1: "Modéré", 2: "Élevé", 3: "Critique"}
        return levels.get(value, "Inconnu")
    
    def get_daily_predictions_all_cities(self, crop_type: str = 'mil') -> Dict:
        """Obtenir les prédictions pour toutes les villes"""
        all_predictions = {}
        
        for city in self.data_provider.cities_coords.keys():
            all_predictions[city] = self.predict_all_for_city(city, crop_type)
        
        return {
            'timestamp': datetime.now(),
            'predictions': all_predictions,
            'summary': self._generate_summary(all_predictions)
        }
    
    def _generate_summary(self, predictions: Dict) -> Dict:
        """Générer un résumé des prédictions"""
        summary = {
            'total_cities': len(predictions),
            'high_rainfall_cities': [],
            'drought_risk_cities': [],
            'high_irrigation_need_cities': []
        }
        
        for city, pred in predictions.items():
            if 'error' not in pred:
                # Analyser les risques
                if pred.get('rainfall', {}).get('predicted_mm', 0) > 10:
                    summary['high_rainfall_cities'].append(city)
                
                if pred.get('drought', {}).get('severity', 0) >= 2:
                    summary['drought_risk_cities'].append(city)
                
                if pred.get('irrigation', {}).get('need_mm_per_day', 0) > 6:
                    summary['high_irrigation_need_cities'].append(city)
        
        return summary