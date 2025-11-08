"""
Modèle de prédiction des maladies des cultures
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from models.base_model import BaseModel
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DiseasePredictionModel(BaseModel):
    """
    Modèle pour prédire les risques de maladies des cultures basé sur les conditions
    météorologiques, l'humidité, la température et les indices de végétation
    """
    
    def __init__(self, algorithm: str = "random_forest"):
        super().__init__("disease_prediction", "classification")
        self.algorithm = algorithm
        
        # Base de connaissances des maladies par culture
        self.disease_database = {
            'mil': {
                'mildiou': {'temp_range': (20, 30), 'humidity_min': 80, 'risk_season': 'Wet'},
                'charbon': {'temp_range': (25, 35), 'humidity_min': 60, 'risk_season': 'Wet'},
                'rouille': {'temp_range': (15, 25), 'humidity_min': 70, 'risk_season': 'Wet'}
            },
            'sorgho': {
                'anthracnose': {'temp_range': (22, 32), 'humidity_min': 75, 'risk_season': 'Wet'},
                'charbon_grain': {'temp_range': (20, 30), 'humidity_min': 65, 'risk_season': 'Wet'},
                'helminthosporiose': {'temp_range': (25, 35), 'humidity_min': 80, 'risk_season': 'Wet'}
            },
            'mais': {
                'helminthosporiose': {'temp_range': (20, 30), 'humidity_min': 85, 'risk_season': 'Wet'},
                'rouille': {'temp_range': (16, 25), 'humidity_min': 75, 'risk_season': 'Wet'},
                'charbon': {'temp_range': (25, 32), 'humidity_min': 70, 'risk_season': 'Wet'}
            },
            'riz': {
                'pyriculariose': {'temp_range': (25, 30), 'humidity_min': 90, 'risk_season': 'Wet'},
                'helminthosporiose': {'temp_range': (28, 35), 'humidity_min': 85, 'risk_season': 'Wet'},
                'bacteriose': {'temp_range': (25, 35), 'humidity_min': 80, 'risk_season': 'Wet'}
            },
            'arachide': {
                'cercosporiose': {'temp_range': (25, 30), 'humidity_min': 80, 'risk_season': 'Wet'},
                'rouille': {'temp_range': (22, 28), 'humidity_min': 75, 'risk_season': 'Wet'},
                'rosette': {'temp_range': (20, 30), 'humidity_min': 60, 'risk_season': 'Dry'}
            },
            'coton': {
                'fusariose': {'temp_range': (25, 35), 'humidity_min': 70, 'risk_season': 'Wet'},
                'bacteriose': {'temp_range': (28, 35), 'humidity_min': 80, 'risk_season': 'Wet'},
                'alternariose': {'temp_range': (20, 30), 'humidity_min': 75, 'risk_season': 'Wet'}
            }
        }
    
    def create_model(self):
        """Créer le modèle de prédiction des maladies"""
        if self.algorithm == "random_forest":
            return RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
        elif self.algorithm == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=10,
                random_state=42
            )
        else:
            return SVC(
                kernel='rbf',
                random_state=42,
                class_weight='balanced',
                probability=True
            )
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Préparer les features pour la prédiction des maladies"""
        data = self.load_data()
        gee_data = data['gee']
        
        features_df = gee_data.copy()
        
        # Features météorologiques de base
        weather_features = [
            'temperature_2m', 'total_precipitation_sum', 'surface_solar_radiation_downwards_sum',
            'u_component_of_wind_10m', 'v_component_of_wind_10m', 'ssm'
        ]
        
        # Features satellitaires
        satellite_features = [
            'lst_day_1km', 'lst_night_1km', 'temp_day_celsius', 'temp_night_celsius',
            'evi', 'ndvi', 'ndvi_normalized', 'evi_normalized'
        ]
        
        # Features temporelles
        features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
        features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
        features_df['is_wet_season'] = features_df['season'].apply(lambda x: 1 if x == 'Wet' else 0)
        features_df['day_of_year'] = features_df['date'].dt.dayofyear
        
        # Simuler différents types de cultures
        np.random.seed(42)
        features_df['crop_type'] = np.random.choice(list(self.disease_database.keys()), len(features_df))
        
        # Encoder les types de cultures
        for crop in self.disease_database.keys():
            features_df[f'crop_{crop}'] = (features_df['crop_type'] == crop).astype(int)
        
        # Sélectionner les features finales
        final_features = (weather_features + satellite_features +
                         ['month_sin', 'month_cos', 'is_wet_season', 'day_of_year'] +
                         [f'crop_{crop}' for crop in self.disease_database.keys()])
        
        # Nettoyer les données
        result_df = features_df[final_features].fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Features préparées pour la prédiction des maladies: {len(final_features)} features")
        return result_df
    
    def get_target_variable(self) -> pd.Series:
        """Créer la variable cible pour la classification des risques de maladie"""
        data = self.load_data()
        gee_data = data['gee']
        
        # Calculer un indice de risque composite basé sur les conditions météorologiques
        risk_score = (
            # Humidité élevée (40%)
            (gee_data['ssm'] > gee_data['ssm'].quantile(0.7)) * 0.4 +
            
            # Température dans la plage critique (30%)
            (gee_data['temperature_2m'].between(20, 32)) * 0.3 +
            
            # Précipitations récentes (20%)
            (gee_data['total_precipitation_sum'] > gee_data['total_precipitation_sum'].quantile(0.6)) * 0.2 +
            
            # Faible radiation solaire (10%)
            (gee_data['surface_solar_radiation_downwards_sum'] < 
             gee_data['surface_solar_radiation_downwards_sum'].quantile(0.4)) * 0.1
        )
        
        # Classification en 4 niveaux de risque
        # 0: Faible, 1: Modéré, 2: Élevé, 3: Critique
        target = pd.cut(risk_score, 
                       bins=[-np.inf, 0.3, 0.6, 0.8, np.inf], 
                       labels=[0, 1, 2, 3]).astype(int)
        
        return target
    
    def train_model(self):
        """Entraîner le modèle de prédiction des maladies"""
        logger.info("Début de l'entraînement du modèle de prédiction des maladies")
        
        # Préparer les données
        X = self.prepare_features(None)
        y = self.get_target_variable()
        
        # Supprimer les lignes avec des valeurs manquantes
        mask = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[mask]
        y_clean = y[mask]
        
        logger.info(f"Données d'entraînement: {len(X_clean)} échantillons, {len(X_clean.columns)} features")
        logger.info(f"Distribution des classes: {y_clean.value_counts().to_dict()}")
        
        # Entraîner le modèle
        metrics = self.train(X_clean, y_clean)
        
        # Sauvegarder le modèle
        self.save_model()
        
        return metrics

if __name__ == "__main__":
    # Test du modèle
    model = DiseasePredictionModel("random_forest")
    metrics = model.train_model()
    print(f"Métriques du modèle: {metrics}")