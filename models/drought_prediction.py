"""
Modèle de prédiction de sécheresse
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.ensemble import GradientBoostingClassifier
from models.base_model import BaseModel
import logging

logger = logging.getLogger(__name__)

class DroughtPredictionModel(BaseModel):
    """
    Modèle pour prédire les risques de sécheresse basé sur les indices de végétation,
    les données météorologiques et l'humidité du sol
    """
    
    def __init__(self, algorithm: str = "random_forest"):
        super().__init__("drought_prediction", "classification")
        self.algorithm = algorithm
    
    def create_model(self):
        """Créer le modèle de prédiction de sécheresse"""
        if self.algorithm == "random_forest":
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
        elif self.algorithm == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        else:
            return SVC(
                kernel='rbf',
                random_state=42,
                class_weight='balanced'
            )
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Préparer les features pour la prédiction de sécheresse"""
        data = self.load_data()
        gee_data = data['gee']
        
        features_df = gee_data.copy()
        
        # Features de base pour la sécheresse
        base_features = [
            'temperature_2m', 'total_precipitation_sum', 'surface_solar_radiation_downwards_sum',
            'lst_day_1km', 'lst_night_1km', 'temp_day_celsius', 'temp_night_celsius',
            'evi', 'ndvi', 'ndvi_normalized', 'evi_normalized', 'ssm'
        ]
        
        # Features temporelles
        features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
        features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
        features_df['is_dry_season'] = features_df['season'].apply(lambda x: 1 if x == 'Dry' else 0)
        
        # Indices de sécheresse calculés
        # 1. Indice de stress hydrique basé sur NDVI et température
        features_df['water_stress_index'] = (
            (features_df['temp_day_celsius'] - features_df['temp_day_celsius'].mean()) / 
            features_df['temp_day_celsius'].std() - 
            (features_df['ndvi'] - features_df['ndvi'].mean()) / features_df['ndvi'].std()
        )
        
        # 2. Indice de sécheresse météorologique
        features_df['meteorological_drought_index'] = (
            (features_df['temperature_2m'] - features_df['temperature_2m'].mean()) / 
            features_df['temperature_2m'].std() - 
            (features_df['total_precipitation_sum'] - features_df['total_precipitation_sum'].mean()) / 
            features_df['total_precipitation_sum'].std()
        )
        
        # 3. Indice de sécheresse agricole
        features_df['agricultural_drought_index'] = (
            1 - features_df['ssm'] / features_df['ssm'].max()
        ) * (1 - features_df['ndvi_normalized'])
        
        # Features de tendance (moyennes mobiles et écarts)
        features_df = features_df.sort_values(['region', 'date'])
        
        for window in [7, 15, 30]:
            # Moyennes mobiles
            features_df[f'temp_ma_{window}'] = features_df.groupby('region')['temperature_2m'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'precip_ma_{window}'] = features_df.groupby('region')['total_precipitation_sum'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'ndvi_ma_{window}'] = features_df.groupby('region')['ndvi'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'ssm_ma_{window}'] = features_df.groupby('region')['ssm'].rolling(window).mean().reset_index(0, drop=True)
            
            # Écarts par rapport à la moyenne
            features_df[f'temp_deviation_{window}'] = features_df['temperature_2m'] - features_df[f'temp_ma_{window}']
            features_df[f'precip_deviation_{window}'] = features_df['total_precipitation_sum'] - features_df[f'precip_ma_{window}']
            features_df[f'ndvi_deviation_{window}'] = features_df['ndvi'] - features_df[f'ndvi_ma_{window}']
        
        # Cumuls de précipitations
        for period in [7, 15, 30, 60]:
            features_df[f'precip_cumul_{period}'] = features_df.groupby('region')['total_precipitation_sum'].rolling(period).sum().reset_index(0, drop=True)
        
        # Jours consécutifs sans pluie
        features_df['no_rain'] = (features_df['total_precipitation_sum'] < 0.1).astype(int)
        features_df['consecutive_dry_days'] = features_df.groupby('region')['no_rain'].apply(
            lambda x: x.groupby((x != x.shift()).cumsum()).cumsum()
        ).reset_index(0, drop=True)
        
        # Sélectionner les features finales
        final_features = (base_features + 
                         ['month_sin', 'month_cos', 'is_dry_season',
                          'water_stress_index', 'meteorological_drought_index', 'agricultural_drought_index',
                          'consecutive_dry_days'] +
                         [f'temp_ma_{w}' for w in [7, 15, 30]] +
                         [f'precip_ma_{w}' for w in [7, 15, 30]] +
                         [f'ndvi_ma_{w}' for w in [7, 15, 30]] +
                         [f'ssm_ma_{w}' for w in [7, 15, 30]] +
                         [f'temp_deviation_{w}' for w in [7, 15, 30]] +
                         [f'precip_deviation_{w}' for w in [7, 15, 30]] +
                         [f'ndvi_deviation_{w}' for w in [7, 15, 30]] +
                         [f'precip_cumul_{p}' for p in [7, 15, 30, 60]])
        
        # Nettoyer les données
        result_df = features_df[final_features].fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Features préparées pour la prédiction de sécheresse: {len(final_features)} features")
        return result_df
    
    def get_target_variable(self) -> pd.Series:
        """Créer la variable cible pour la classification de sécheresse"""
        data = self.load_data()
        gee_data = data['gee']
        
        # Calculer l'indice de sécheresse composite
        drought_index = (
            # Faible précipitation (30 derniers jours)
            (gee_data.groupby('region')['total_precipitation_sum'].rolling(30).sum().reset_index(0, drop=True) < 
             gee_data.groupby('region')['total_precipitation_sum'].rolling(30).sum().quantile(0.2)) * 0.3 +
            
            # Haute température
            (gee_data['temperature_2m'] > gee_data['temperature_2m'].quantile(0.8)) * 0.2 +
            
            # Faible humidité du sol
            (gee_data['ssm'] < gee_data['ssm'].quantile(0.2)) * 0.3 +
            
            # Faible NDVI (stress végétatif)
            (gee_data['ndvi'] < gee_data['ndvi'].quantile(0.2)) * 0.2
        )
        
        # Classification en 4 niveaux
        # 0: Pas de sécheresse, 1: Sécheresse légère, 2: Sécheresse modérée, 3: Sécheresse sévère
        target = pd.cut(drought_index, 
                       bins=[-np.inf, 0.2, 0.4, 0.6, np.inf], 
                       labels=[0, 1, 2, 3]).astype(int)
        
        return target
    
    def train_model(self):
        """Entraîner le modèle de prédiction de sécheresse"""
        logger.info("Début de l'entraînement du modèle de prédiction de sécheresse")
        
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
    
    def predict_drought(self, region: str, date: str, environmental_data: dict) -> dict:
        """
        Prédire le risque de sécheresse pour une région et date données
        
        Args:
            region: Nom de la région
            date: Date au format YYYY-MM-DD
            environmental_data: Dictionnaire avec les données environnementales
        
        Returns:
            Dictionnaire avec la prédiction et les recommandations
        """
        if not self.is_trained:
            self.load_model()
        
        # Créer un DataFrame avec les données d'entrée
        input_data = pd.DataFrame([environmental_data])
        
        # Faire la prédiction
        prediction = self.predict(input_data)[0]
        
        # Obtenir les probabilités si disponible
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(self.scaler.transform(input_data.fillna(input_data.mean())))[0]
            confidence = max(probabilities) * 100
        else:
            confidence = 75  # Valeur par défaut
        
        # Interpréter la prédiction
        drought_levels = {
            0: {"level": "Pas de sécheresse", "risk": "Faible", "color": "green"},
            1: {"level": "Sécheresse légère", "risk": "Modéré", "color": "yellow"},
            2: {"level": "Sécheresse modérée", "risk": "Élevé", "color": "orange"},
            3: {"level": "Sécheresse sévère", "risk": "Critique", "color": "red"}
        }
        
        result = drought_levels[prediction]
        
        return {
            'region': region,
            'date': date,
            'drought_level': result["level"],
            'risk_category': result["risk"],
            'severity_score': int(prediction),
            'confidence': round(confidence, 1),
            'alert_color': result["color"],
            'recommendations': self._get_drought_recommendations(prediction),
            'monitoring_actions': self._get_monitoring_actions(prediction)
        }
    
    def _get_drought_recommendations(self, severity: int) -> list:
        """Générer des recommandations basées sur le niveau de sécheresse"""
        recommendations = []
        
        if severity == 0:  # Pas de sécheresse
            recommendations.extend([
                "Maintenir les pratiques d'irrigation normales",
                "Surveiller les indicateurs météorologiques",
                "Préparer les plans de gestion de l'eau"
            ])
        elif severity == 1:  # Sécheresse légère
            recommendations.extend([
                "Optimiser l'efficacité de l'irrigation",
                "Surveiller l'humidité du sol quotidiennement",
                "Considérer des cultures résistantes à la sécheresse",
                "Réduire les pertes d'eau par évaporation"
            ])
        elif severity == 2:  # Sécheresse modérée
            recommendations.extend([
                "Implémenter des mesures d'économie d'eau strictes",
                "Prioriser l'irrigation des cultures les plus sensibles",
                "Utiliser du paillis pour conserver l'humidité",
                "Considérer l'irrigation goutte-à-goutte",
                "Reporter les nouvelles plantations"
            ])
        else:  # Sécheresse sévère
            recommendations.extend([
                "Activer les protocoles d'urgence pour la sécheresse",
                "Rationner l'eau d'irrigation",
                "Récolter prématurément si nécessaire",
                "Protéger les cultures permanentes prioritaires",
                "Chercher des sources d'eau alternatives",
                "Considérer l'assurance récolte"
            ])
        
        return recommendations
    
    def _get_monitoring_actions(self, severity: int) -> list:
        """Actions de monitoring recommandées"""
        actions = [
            "Surveiller les prévisions météorologiques à 7 jours",
            "Mesurer l'humidité du sol quotidiennement"
        ]
        
        if severity >= 1:
            actions.extend([
                "Surveiller l'état de la végétation via satellite",
                "Mesurer les niveaux des réservoirs d'eau"
            ])
        
        if severity >= 2:
            actions.extend([
                "Surveillance quotidienne des cultures sensibles",
                "Coordination avec les autorités locales"
            ])
        
        if severity == 3:
            actions.extend([
                "Surveillance continue 24h/24",
                "Activation du comité de crise sécheresse"
            ])
        
        return actions

if __name__ == "__main__":
    # Test du modèle
    model = DroughtPredictionModel("random_forest")
    metrics = model.train_model()
    print(f"Métriques du modèle: {metrics}")