"""
Modèle de prédiction des précipitations
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from models.base_model import BaseModel
import logging

logger = logging.getLogger(__name__)

class RainfallPredictionModel(BaseModel):
    """
    Modèle pour prédire les précipitations basé sur les données météorologiques et satellitaires
    """
    
    def __init__(self, algorithm: str = "random_forest"):
        super().__init__("rainfall_prediction", "regression")
        self.algorithm = algorithm
    
    def create_model(self):
        """Créer le modèle de prédiction des précipitations"""
        if self.algorithm == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.algorithm == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        else:
            return LinearRegression()
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Préparer les features pour la prédiction des précipitations"""
        data = self.load_data()
        gee_data = data['gee']
        meteo_data = data['meteo']
        
        #Combiner les données GEE et météo
        features_df = gee_data.copy()
        
        # Features météorologiques de base
        weather_features = [
            'temperature_2m', 'total_precipitation_sum', 'u_component_of_wind_10m',
            'v_component_of_wind_10m', 'surface_solar_radiation_downwards_sum'
        ]
        
        # Features satellitaires
        satellite_features = [
            'lst_day_1km', 'lst_night_1km', 'temp_day_celsius', 'temp_night_celsius',
            'evi', 'ndvi', 'ndvi_normalized', 'evi_normalized', 'ssm'
        ]
        
        # Features temporelles
        features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
        features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
        features_df['day_sin'] = np.sin(2 * np.pi * features_df['day'] / 365)
        features_df['day_cos'] = np.cos(2 * np.pi * features_df['day'] / 365)
        
        # Features dérivées
        features_df['temp_range'] = features_df['temp_day_celsius'] - features_df['temp_night_celsius']
        features_df['wind_speed'] = np.sqrt(
            features_df['u_component_of_wind_10m']**2 + 
            features_df['v_component_of_wind_10m']**2
        )
        features_df['vegetation_health'] = (features_df['ndvi'] + features_df['evi']) / 2
        
        #Features de lag (précipitations des jours précédents)
        features_df = features_df.sort_values(['region', 'date'])
        for lag in [1, 3, 7]:
            features_df[f'precipitation_lag_{lag}'] = features_df.groupby('region')['total_precipitation_sum'].shift(lag)
        
        #Moyennes mobiles
        for window in [3, 7, 15]:
            features_df[f'temp_ma_{window}'] = features_df.groupby('region')['temperature_2m'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'humidity_ma_{window}'] = features_df.groupby('region')['ssm'].rolling(window).mean().reset_index(0, drop=True)
        
        #Sélectionner les features finales
        final_features = (weather_features + satellite_features + 
                         ['month_sin', 'month_cos', 'day_sin', 'day_cos',
                          'temp_range', 'wind_speed', 'vegetation_health'] +
                         [f'precipitation_lag_{lag}' for lag in [1, 3, 7]] +
                         [f'temp_ma_{window}' for window in [3, 7, 15]] +
                         [f'humidity_ma_{window}' for window in [3, 7, 15]])
        
        #Nettoyer les données
        result_df = features_df[final_features].fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Features préparées pour la prédiction des précipitations: {len(final_features)} features")
        return result_df
    
    def get_target_variable(self) -> pd.Series:
        """Obtenir la variable cible (précipitations futures)"""
        data = self.load_data()
        gee_data = data['gee']
        
        #Prédire les précipitations du jour suivant
        gee_data = gee_data.sort_values(['region', 'date'])
        target = gee_data.groupby('region')['total_precipitation_sum'].shift(-1)
        
        return target.fillna(0)  #Remplacer les NaN par 0
    
    def train_model(self):
        """Entraîner le modèle de prédiction des précipitations"""
        logger.info("Début de l'entraînement du modèle de prédiction des précipitations")
        
        #Préparer les données
        X = self.prepare_features(None)
        y = self.get_target_variable()
        
        #Supprimer les lignes avec des valeurs manquantes
        mask = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[mask]
        y_clean = y[mask]
        
        logger.info(f"Données d'entraînement: {len(X_clean)} échantillons, {len(X_clean.columns)} features")
        
        #Entraîner le modèle
        metrics = self.train(X_clean, y_clean)
        
        #Sauvegarder le modèle
        self.save_model()
        
        return metrics
    
    def predict_rainfall(self, region: str, date: str, weather_data: dict) -> dict:
        """
        Prédire les précipitations pour une région et date données
        
        Args:
            region: Nom de la région
            date: Date au format YYYY-MM-DD
            weather_data: Dictionnaire avec les données météo actuelles
        
        Returns:
            Dictionnaire avec la prédiction et le niveau de confiance
        """
        if not self.is_trained:
            self.load_model()
        
        #Créer un DataFrame avec les données d'entrée
        input_data = pd.DataFrame([weather_data])
        
        #Faire la prédiction
        prediction = self.predict(input_data)[0]
        
        #Calculer le niveau de confiance (basé sur la variance du modèle)
        confidence = min(100, max(0, 100 - abs(prediction) * 10))
        
        #Interpréter la prédiction
        if prediction < 1:
            category = "Pas de pluie"
            risk_level = "Faible"
        elif prediction < 5:
            category = "Pluie légère"
            risk_level = "Modéré"
        elif prediction < 15:
            category = "Pluie modérée"
            risk_level = "Élevé"
        else:
            category = "Pluie forte"
            risk_level = "Très élevé"
        
        return {
            'region': region,
            'date': date,
            'predicted_rainfall_mm': round(prediction, 2),
            'category': category,
            'risk_level': risk_level,
            'confidence': round(confidence, 1),
            'recommendations': self._get_recommendations(prediction, risk_level)
        }
    
    def _get_recommendations(self, rainfall: float, risk_level: str) -> list:
        """Générer des recommandations basées sur la prédiction"""
        recommendations = []
        
        if rainfall < 1:
            recommendations.extend([
                "Prévoir l'irrigation des cultures",
                "Surveiller l'humidité du sol",
                "Protéger les jeunes plants du soleil"
            ])
        elif rainfall < 5:
            recommendations.extend([
                "Réduire l'irrigation prévue",
                "Préparer les systèmes de drainage légers"
            ])
        elif rainfall < 15:
            recommendations.extend([
                "Suspendre l'irrigation",
                "Vérifier les systèmes de drainage",
                "Protéger les cultures sensibles"
            ])
        else:
            recommendations.extend([
                "Arrêter toute irrigation",
                "Activer les systèmes de drainage",
                "Protéger les cultures contre l'excès d'eau",
                "Reporter les activités agricoles en extérieur"
            ])
        
        return recommendations

if __name__ == "__main__":
    #Test du modèle
    model = RainfallPredictionModel("random_forest")
    metrics = model.train_model()
    print(f"Métriques du modèle: {metrics}")