"""
Modèle d'optimisation de l'irrigation
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from models.base_model import BaseModel
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IrrigationOptimizationModel(BaseModel):
    """
    Modèle pour optimiser les besoins en irrigation basé sur l'évapotranspiration,
    l'humidité du sol, les conditions météorologiques et les caractéristiques des cultures
    """
    
    def __init__(self, algorithm: str = "random_forest"):
        super().__init__("irrigation_optimization", "regression")
        self.algorithm = algorithm
        self.crop_coefficients = {
            'mil': {'kc_initial': 0.3, 'kc_mid': 1.0, 'kc_end': 0.4, 'growing_days': 120},
            'sorgho': {'kc_initial': 0.3, 'kc_mid': 1.15, 'kc_end': 0.4, 'growing_days': 130},
            'mais': {'kc_initial': 0.3, 'kc_mid': 1.2, 'kc_end': 0.6, 'growing_days': 125},
            'riz': {'kc_initial': 1.05, 'kc_mid': 1.2, 'kc_end': 0.9, 'growing_days': 150},
            'arachide': {'kc_initial': 0.4, 'kc_mid': 1.15, 'kc_end': 0.6, 'growing_days': 130},
            'coton': {'kc_initial': 0.35, 'kc_mid': 1.15, 'kc_end': 0.7, 'growing_days': 180}
        }
    
    def create_model(self):
        """Créer le modèle d'optimisation de l'irrigation"""
        if self.algorithm == "random_forest":
            return RandomForestRegressor(
                n_estimators=150,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif self.algorithm == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            )
        else:
            return Ridge(alpha=1.0)
    
    def calculate_et0(self, temp_max: float, temp_min: float, humidity: float, 
                      wind_speed: float, solar_radiation: float, latitude: float, 
                      day_of_year: int) -> float:
        """
        Calculer l'évapotranspiration de référence (ET0) selon Penman-Monteith
        """
        # Constantes
        STEFAN_BOLTZMANN = 4.903e-9  # MJ K-4 m-2 day-1
        
        # Température moyenne
        temp_mean = (temp_max + temp_min) / 2
        
        # Pente de la courbe de pression de vapeur saturante
        delta = 4098 * (0.6108 * np.exp(17.27 * temp_mean / (temp_mean + 237.3))) / ((temp_mean + 237.3) ** 2)
        
        # Pression atmosphérique (approximation au niveau de la mer)
        pressure = 101.3
        
        # Constante psychrométrique
        gamma = 0.665 * pressure
        
        # Pression de vapeur saturante
        es_max = 0.6108 * np.exp(17.27 * temp_max / (temp_max + 237.3))
        es_min = 0.6108 * np.exp(17.27 * temp_min / (temp_min + 237.3))
        es = (es_max + es_min) / 2
        
        # Pression de vapeur actuelle
        ea = es * humidity / 100
        
        # Rayonnement net (approximation)
        rn = solar_radiation * 0.77 - STEFAN_BOLTZMANN * ((temp_max + 273.16)**4 + (temp_min + 273.16)**4) / 2 * (0.34 - 0.14 * np.sqrt(ea))
        
        # Flux de chaleur du sol (approximation)
        g = 0
        
        # ET0 selon Penman-Monteith
        et0 = (0.408 * delta * (rn - g) + gamma * 900 / (temp_mean + 273) * wind_speed * (es - ea)) / (delta + gamma * (1 + 0.34 * wind_speed))
        
        return max(0, et0)
    
    def calculate_crop_et(self, et0: float, crop_type: str, growth_stage: int) -> float:
        """
        Calculer l'évapotranspiration de la culture (ETc)
        """
        if crop_type not in self.crop_coefficients:
            crop_type = 'mil'  # Valeur par défaut
        
        crop_data = self.crop_coefficients[crop_type]
        total_days = crop_data['growing_days']
        
        # Déterminer le coefficient cultural selon le stade de croissance
        if growth_stage <= total_days * 0.25:  # Stade initial
            kc = crop_data['kc_initial']
        elif growth_stage <= total_days * 0.75:  # Stade de développement/mi-saison
            # Interpolation linéaire
            progress = (growth_stage - total_days * 0.25) / (total_days * 0.5)
            kc = crop_data['kc_initial'] + progress * (crop_data['kc_mid'] - crop_data['kc_initial'])
        else:  # Stade final
            # Interpolation linéaire
            progress = (growth_stage - total_days * 0.75) / (total_days * 0.25)
            kc = crop_data['kc_mid'] + progress * (crop_data['kc_end'] - crop_data['kc_mid'])
        
        return et0 * kc
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Préparer les features pour l'optimisation de l'irrigation"""
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
        
        # Calculer les features dérivées
        features_df['temp_max'] = features_df['temp_day_celsius']
        features_df['temp_min'] = features_df['temp_night_celsius']
        features_df['temp_range'] = features_df['temp_max'] - features_df['temp_min']
        features_df['wind_speed'] = np.sqrt(
            features_df['u_component_of_wind_10m']**2 + 
            features_df['v_component_of_wind_10m']**2
        )
        
        # Calculer l'évapotranspiration de référence (ET0)
        features_df['day_of_year'] = features_df['date'].dt.dayofyear
        features_df['et0'] = features_df.apply(
            lambda row: self.calculate_et0(
                row['temp_max'], row['temp_min'], row['ssm'] * 100,
                row['wind_speed'], row['surface_solar_radiation_downwards_sum'] / 1000000,
                row['latitude'], row['day_of_year']
            ), axis=1
        )
        
        # Simuler différents types de cultures et stades de croissance
        np.random.seed(42)
        features_df['crop_type'] = np.random.choice(list(self.crop_coefficients.keys()), len(features_df))
        features_df['growth_stage'] = np.random.randint(1, 180, len(features_df))
        
        # Calculer l'évapotranspiration de la culture (ETc)
        features_df['etc'] = features_df.apply(
            lambda row: self.calculate_crop_et(row['et0'], row['crop_type'], row['growth_stage']),
            axis=1
        )
        
        # Features temporelles
        features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
        features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
        features_df['is_dry_season'] = features_df['season'].apply(lambda x: 1 if x == 'Dry' else 0)
        
        # Déficit hydrique du sol (approximation)
        features_df['soil_water_deficit'] = np.maximum(0, 0.4 - features_df['ssm'])  # 0.4 = capacité au champ approximative
        
        # Stress hydrique de la végétation
        features_df['vegetation_stress'] = 1 - features_df['ndvi_normalized']
        
        # Efficacité de l'irrigation (basée sur les conditions météo)
        features_df['irrigation_efficiency'] = 1 - (features_df['wind_speed'] / 10 + features_df['temp_range'] / 20) / 2
        features_df['irrigation_efficiency'] = np.clip(features_df['irrigation_efficiency'], 0.3, 1.0)
        
        # Moyennes mobiles pour les tendances
        features_df = features_df.sort_values(['region', 'date'])
        for window in [3, 7, 15]:
            features_df[f'temp_ma_{window}'] = features_df.groupby('region')['temperature_2m'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'precip_ma_{window}'] = features_df.groupby('region')['total_precipitation_sum'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'ssm_ma_{window}'] = features_df.groupby('region')['ssm'].rolling(window).mean().reset_index(0, drop=True)
            features_df[f'et0_ma_{window}'] = features_df.groupby('region')['et0'].rolling(window).mean().reset_index(0, drop=True)
        
        # Cumuls de précipitations
        for period in [3, 7, 15]:
            features_df[f'precip_cumul_{period}'] = features_df.groupby('region')['total_precipitation_sum'].rolling(period).sum().reset_index(0, drop=True)
        
        # Encoder les types de cultures
        for crop in self.crop_coefficients.keys():
            features_df[f'crop_{crop}'] = (features_df['crop_type'] == crop).astype(int)
        
        # Sélectionner les features finales
        final_features = (weather_features + satellite_features + 
                         ['temp_max', 'temp_min', 'temp_range', 'wind_speed', 'et0', 'etc',
                          'month_sin', 'month_cos', 'is_dry_season', 'day_of_year',
                          'soil_water_deficit', 'vegetation_stress', 'irrigation_efficiency',
                          'growth_stage'] +
                         [f'temp_ma_{w}' for w in [3, 7, 15]] +
                         [f'precip_ma_{w}' for w in [3, 7, 15]] +
                         [f'ssm_ma_{w}' for w in [3, 7, 15]] +
                         [f'et0_ma_{w}' for w in [3, 7, 15]] +
                         [f'precip_cumul_{p}' for p in [3, 7, 15]] +
                         [f'crop_{crop}' for crop in self.crop_coefficients.keys()])
        
        # Nettoyer les données
        result_df = features_df[final_features].fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"Features préparées pour l'optimisation de l'irrigation: {len(final_features)} features")
        return result_df
    
    def get_target_variable(self) -> pd.Series:
        """Calculer les besoins en irrigation optimaux (mm/jour)"""
        data = self.load_data()
        gee_data = data['gee']
        
        # Préparer les features pour obtenir ETc
        features_df = self.prepare_features(None)
        
        # Calculer les besoins en irrigation
        # Besoins = ETc - Précipitations effectives + Déficit du sol
        effective_rainfall = gee_data['total_precipitation_sum'] * 0.8  # 80% d'efficacité
        
        irrigation_needs = np.maximum(0, 
            features_df['etc'] - effective_rainfall + features_df['soil_water_deficit'] * 10
        )
        
        # Ajuster selon l'efficacité du système d'irrigation
        irrigation_needs = irrigation_needs / features_df['irrigation_efficiency']
        
        # Limiter les valeurs extrêmes
        irrigation_needs = np.clip(irrigation_needs, 0, 15)  # Max 15mm/jour
        
        return pd.Series(irrigation_needs, index=gee_data.index)
    
    def train_model(self):
        """Entraîner le modèle d'optimisation de l'irrigation"""
        logger.info("Début de l'entraînement du modèle d'optimisation de l'irrigation")
        
        # Préparer les données
        X = self.prepare_features(None)
        y = self.get_target_variable()
        
        # Supprimer les lignes avec des valeurs manquantes
        mask = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[mask]
        y_clean = y[mask]
        
        logger.info(f"Données d'entraînement: {len(X_clean)} échantillons, {len(X_clean.columns)} features")
        logger.info(f"Besoins en irrigation - Min: {y_clean.min():.2f}, Max: {y_clean.max():.2f}, Moyenne: {y_clean.mean():.2f} mm/jour")
        
        # Entraîner le modèle
        metrics = self.train(X_clean, y_clean)
        
        # Sauvegarder le modèle
        self.save_model()
        
        return metrics
    
    def optimize_irrigation(self, region: str, date: str, crop_type: str, 
                          growth_stage: int, environmental_data: dict) -> dict:
        """
        Optimiser l'irrigation pour des conditions données
        
        Args:
            region: Nom de la région
            date: Date au format YYYY-MM-DD
            crop_type: Type de culture
            growth_stage: Stade de croissance (jours depuis plantation)
            environmental_data: Données environnementales
        
        Returns:
            Dictionnaire avec les recommandations d'irrigation
        """
        if not self.is_trained:
            self.load_model()
        
        # Préparer les données d'entrée
        input_data = environmental_data.copy()
        input_data['crop_type'] = crop_type
        input_data['growth_stage'] = growth_stage
        
        # Ajouter les features encodées pour les cultures
        for crop in self.crop_coefficients.keys():
            input_data[f'crop_{crop}'] = 1 if crop == crop_type else 0
        
        input_df = pd.DataFrame([input_data])
        
        # Faire la prédiction
        irrigation_need = self.predict(input_df)[0]
        
        # Calculer des métriques supplémentaires
        et0 = self.calculate_et0(
            input_data.get('temp_max', 30), input_data.get('temp_min', 20),
            input_data.get('humidity', 60), input_data.get('wind_speed', 2),
            input_data.get('solar_radiation', 20), input_data.get('latitude', 14),
            pd.to_datetime(date).dayofyear
        )
        
        etc = self.calculate_crop_et(et0, crop_type, growth_stage)
        
        # Déterminer la fréquence d'irrigation optimale
        if irrigation_need < 2:
            frequency = "Tous les 3-4 jours"
            duration = "15-30 minutes"
        elif irrigation_need < 5:
            frequency = "Tous les 2 jours"
            duration = "30-45 minutes"
        elif irrigation_need < 8:
            frequency = "Quotidienne"
            duration = "45-60 minutes"
        else:
            frequency = "2 fois par jour"
            duration = "30-45 minutes par session"
        
        # Déterminer le meilleur moment d'irrigation
        best_times = self._get_optimal_irrigation_times(environmental_data)
        
        # Calculer l'efficacité économique
        water_cost = irrigation_need * 0.1  # Coût approximatif en FCFA/m²
        
        return {
            'region': region,
            'date': date,
            'crop_type': crop_type,
            'growth_stage': growth_stage,
            'irrigation_need_mm': round(irrigation_need, 2),
            'et0_mm': round(et0, 2),
            'etc_mm': round(etc, 2),
            'frequency': frequency,
            'duration': duration,
            'best_times': best_times,
            'water_cost_fcfa_per_m2': round(water_cost, 2),
            'efficiency_score': self._calculate_efficiency_score(irrigation_need, etc),
            'recommendations': self._get_irrigation_recommendations(irrigation_need, crop_type, growth_stage),
            'water_conservation_tips': self._get_conservation_tips(irrigation_need)
        }
    
    def _get_optimal_irrigation_times(self, environmental_data: dict) -> list:
        """Déterminer les meilleurs moments pour irriguer"""
        temp_max = environmental_data.get('temp_max', 35)
        wind_speed = environmental_data.get('wind_speed', 2)
        
        times = []
        
        # Tôt le matin (moins d'évaporation)
        if temp_max > 30:
            times.append("05h00 - 07h00 (optimal)")
        else:
            times.append("06h00 - 08h00")
        
        # Fin d'après-midi si nécessaire
        if temp_max > 35 or wind_speed > 5:
            times.append("17h00 - 19h00 (si nécessaire)")
        
        return times
    
    def _calculate_efficiency_score(self, irrigation_need: float, etc: float) -> int:
        """Calculer un score d'efficacité (0-100)"""
        if etc == 0:
            return 100
        
        efficiency = min(100, max(0, 100 - abs(irrigation_need - etc) / etc * 50))
        return int(efficiency)
    
    def _get_irrigation_recommendations(self, irrigation_need: float, crop_type: str, growth_stage: int) -> list:
        """Générer des recommandations spécifiques"""
        recommendations = []
        
        if irrigation_need < 2:
            recommendations.extend([
                "Irrigation légère suffisante",
                "Surveiller l'humidité du sol",
                "Profiter des conditions favorables pour économiser l'eau"
            ])
        elif irrigation_need < 5:
            recommendations.extend([
                "Irrigation modérée recommandée",
                "Utiliser l'irrigation goutte-à-goutte si possible",
                "Vérifier l'uniformité de distribution"
            ])
        elif irrigation_need < 8:
            recommendations.extend([
                "Irrigation intensive nécessaire",
                "Fractionner en plusieurs applications",
                "Surveiller le drainage pour éviter l'engorgement"
            ])
        else:
            recommendations.extend([
                "Besoins en eau très élevés",
                "Irrigation fractionnée obligatoire",
                "Considérer l'ombrage temporaire",
                "Vérifier l'état du système d'irrigation"
            ])
        
        # Recommandations spécifiques à la culture
        if crop_type == 'riz':
            recommendations.append("Maintenir une lame d'eau de 2-5 cm")
        elif crop_type in ['mil', 'sorgho']:
            recommendations.append("Éviter l'excès d'eau, ces cultures tolèrent la sécheresse")
        elif crop_type == 'coton':
            recommendations.append("Irrigation critique pendant la floraison")
        
        return recommendations
    
    def _get_conservation_tips(self, irrigation_need: float) -> list:
        """Conseils pour économiser l'eau"""
        tips = [
            "Utiliser du paillis pour réduire l'évaporation",
            "Vérifier et réparer les fuites du système",
            "Ajuster les asperseurs pour éviter le gaspillage"
        ]
        
        if irrigation_need > 5:
            tips.extend([
                "Considérer l'irrigation goutte-à-goutte",
                "Installer des capteurs d'humidité du sol",
                "Programmer l'irrigation aux heures fraîches"
            ])
        
        return tips

if __name__ == "__main__":
    # Test du modèle
    model = IrrigationOptimizationModel("random_forest")
    metrics = model.train_model()
    print(f"Métriques du modèle: {metrics}")