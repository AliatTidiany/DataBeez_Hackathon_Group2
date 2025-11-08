"""
Classe de base pour tous les modèles prédictifs
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, classification_report
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """
    Classe de base abstraite pour tous les modèles prédictifs
    """
    
    def __init__(self, model_name: str, model_type: str = "regression"):
        self.model_name = model_name
        self.model_type = model_type  # "regression" ou "classification"
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = None
        self.model_path = Path(f"models/saved/{model_name}")
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def create_model(self) -> Any:
        """Créer le modèle spécifique"""
        pass
    
    @abstractmethod
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Préparer les features spécifiques au modèle"""
        pass
    
    def load_data(self) -> pd.DataFrame:
        """Charger et combiner toutes les données disponibles"""
        try:
            # Charger les données GEE
            gee_data = pd.read_csv("data/processed/senegal_gee_transformed.csv")
            gee_data['date'] = pd.to_datetime(gee_data['date'])
            
            # Charger les données météo
            meteo_data = pd.read_csv("data/processed/meteo_clean.csv")
            meteo_data['date'] = pd.to_datetime(meteo_data['date'])
            
            # Charger les données FAO
            fao_data = pd.read_csv("data/processed/clean_fao_20251031.csv")
            
            logger.info(f"Données chargées: GEE={len(gee_data)}, Météo={len(meteo_data)}, FAO={len(fao_data)}")
            
            return {
                'gee': gee_data,
                'meteo': meteo_data,
                'fao': fao_data
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            raise
    
    def preprocess_data(self, X: pd.DataFrame, y: pd.Series = None, fit_scaler: bool = True) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Préprocesser les données"""
        #Gérer les valeurs manquantes
        X_clean = X.fillna(X.mean())
        
        #Normaliser les features
        if fit_scaler:
            X_scaled = self.scaler.fit_transform(X_clean)
        else:
            X_scaled = self.scaler.transform(X_clean)
        
        y_processed = y.values if y is not None else None
        
        return X_scaled, y_processed
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> Dict[str, float]:
        """Entraîner le modèle"""
        logger.info(f"Début de l'entraînement du modèle {self.model_name}")
        
        #Créer le modèle
        self.model = self.create_model()
        
        #Sauvegarder les noms des features
        self.feature_names = X.columns.tolist()
        
        #Préprocesser les données
        X_processed, y_processed = self.preprocess_data(X, y, fit_scaler=True)
        
        #Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y_processed, test_size=test_size, random_state=random_state
        )
        
        #Entraîner le modèle
        self.model.fit(X_train, y_train)
        
        #Évaluer le modèle
        y_pred = self.model.predict(X_test)
        
        if self.model_type == "regression":
            metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred)
            }
        else:  #classification
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1': f1_score(y_test, y_pred, average='weighted')
            }
        
        self.is_trained = True
        logger.info(f"Modèle {self.model_name} entraîné avec succès. Métriques: {metrics}")
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Faire des prédictions"""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")
        
        X_processed, _ = self.preprocess_data(X, fit_scaler=False)
        predictions = self.model.predict(X_processed)
        
        return predictions
    
    def save_model(self) -> None:
        """Sauvegarder le modèle"""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant d'être sauvegardé")
        
        model_file = self.model_path / f"{self.model_name}.joblib"
        scaler_file = self.model_path / f"{self.model_name}_scaler.joblib"
        features_file = self.model_path / f"{self.model_name}_features.joblib"
        
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        joblib.dump(self.feature_names, features_file)
        
        logger.info(f"Modèle sauvegardé dans {self.model_path}")
    
    def load_model(self) -> None:
        """Charger un modèle sauvegardé"""
        model_file = self.model_path / f"{self.model_name}.joblib"
        scaler_file = self.model_path / f"{self.model_name}_scaler.joblib"
        features_file = self.model_path / f"{self.model_name}_features.joblib"
        
        if not all([f.exists() for f in [model_file, scaler_file, features_file]]):
            raise FileNotFoundError(f"Fichiers du modèle non trouvés dans {self.model_path}")
        
        self.model = joblib.load(model_file)
        self.scaler = joblib.load(scaler_file)
        self.feature_names = joblib.load(features_file)
        self.is_trained = True
        
        logger.info(f"Modèle {self.model_name} chargé avec succès")