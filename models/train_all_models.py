#!/usr/bin/env python3
"""
Script pour entraîner tous les modèles prédictifs
"""

import logging
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.rainfall_prediction import RainfallPredictionModel
from models.drought_prediction import DroughtPredictionModel
from models.irrigation_optimization import IrrigationOptimizationModel
from models.disease_prediction import DiseasePredictionModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('models/logs/training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def train_all_models():
    """Entraîner tous les modèles prédictifs"""
    logger.info("=== Début de l'entraînement de tous les modèles ===")
    start_time = datetime.now()
    
    results = {}
    
    # Liste des modèles à entraîner
    models_to_train = [
        ("Prédiction des précipitations", RainfallPredictionModel, "random_forest"),
        ("Prédiction de sécheresse", DroughtPredictionModel, "random_forest"),
        ("Optimisation de l'irrigation", IrrigationOptimizationModel, "random_forest"),
        ("Prédiction des maladies", DiseasePredictionModel, "random_forest")
    ]
    
    for model_name, model_class, algorithm in models_to_train:
        logger.info(f"\n--- Entraînement: {model_name} ---")
        
        try:
            # Créer et entraîner le modèle
            model = model_class(algorithm)
            metrics = model.train_model()
            
            results[model_name] = {
                'status': 'success',
                'metrics': metrics,
                'algorithm': algorithm
            }
            
            logger.info(f"✅ {model_name} entraîné avec succès")
            logger.info(f"Métriques: {metrics}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'entraînement de {model_name}: {e}")
            results[model_name] = {
                'status': 'error',
                'error': str(e),
                'algorithm': algorithm
            }
    
    # Résumé final
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"\n=== Résumé de l'entraînement ===")
    logger.info(f"Durée totale: {duration}")
    
    successful_models = [name for name, result in results.items() if result['status'] == 'success']
    failed_models = [name for name, result in results.items() if result['status'] == 'error']
    
    logger.info(f"Modèles entraînés avec succès: {len(successful_models)}")
    for model in successful_models:
        logger.info(f"  ✅ {model}")
    
    if failed_models:
        logger.info(f"Modèles en échec: {len(failed_models)}")
        for model in failed_models:
            logger.info(f"  ❌ {model}")
    
    return results

def validate_data_availability():
    """Vérifier que les données nécessaires sont disponibles"""
    logger.info("Vérification de la disponibilité des données...")
    
    required_files = [
        "data/processed/senegal_gee_transformed.csv",
        "data/processed/meteo_clean.csv",
        "data/processed/clean_fao_20251031.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("Fichiers de données manquants:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        return False
    
    logger.info("✅ Tous les fichiers de données sont disponibles")
    return True

def create_directories():
    """Créer les répertoires nécessaires"""
    directories = [
        "models/saved",
        "models/logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Répertoire créé/vérifié: {directory}")

if __name__ == "__main__":
    # Créer les répertoires nécessaires
    create_directories()
    
    # Vérifier la disponibilité des données
    if not validate_data_availability():
        logger.error("Impossible de continuer sans les données nécessaires")
        sys.exit(1)
    
    # Entraîner tous les modèles
    results = train_all_models()
    
    # Code de sortie basé sur les résultats
    failed_count = sum(1 for result in results.values() if result['status'] == 'error')
    if failed_count > 0:
        logger.warning(f"Entraînement terminé avec {failed_count} échec(s)")
        sys.exit(1)
    else:
        logger.info("🎉 Tous les modèles ont été entraînés avec succès!")
        sys.exit(0)