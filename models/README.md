# Modèles Prédictifs Agricoles - DataBeez

Modèles d'intelligence artificielle pour l'agriculture de précision au Sénégal.

## Modèles Disponibles

### 1. Prédiction des Précipitations
- Objectif : Prédire les précipitations pour les 24h
- Algorithmes : Random Forest, Gradient Boosting, Régression Linéaire
- Features : Données météo, indices satellitaires, patterns temporels
- Sortie : Quantité de pluie (mm), catégorie, recommandations

### 2. Prédiction de Sécheresse
- Objectif : Évaluer les risques de sécheresse à court/moyen terme
- Algorithmes : Random Forest, Gradient Boosting, SVM
- Features : Indices de végétation, humidité du sol, températures
- Sortie : Niveau de risque (0-3), alertes, actions recommandées

### 3. Optimisation de l'Irrigation
- Objectif : Calculer les besoins optimaux en irrigation
- Algorithmes : Random Forest, Gradient Boosting, Ridge Regression
- Features : Évapotranspiration, type de culture, stade de croissance
- Sortie : Besoins en eau (mm), fréquence, moments optimaux

## Architecture

```
models/
├── base_model.py              # Classe de base abstraite
├── rainfall_prediction.py     # Modèle précipitations
├── drought_prediction.py      # Modèle sécheresse
├── irrigation_optimization.py # Modèle irrigation
├── streamlit_app.py          # Interface utilisateur Streamlit
├── real_time_data.py         # Données temps réel et prédictions auto
├── train_all_models.py       # Script d'entraînement
├── saved/                    # Modèles sauvegardés
├── logs/                     # Logs d'entraînement
├── Dockerfile               # Container Docker
└── requirements.txt         # Dépendances Python
```

## Utilisation

### Entraînement des Modèles

```bash
# Entraîner tous les modèles
python models/train_all_models.py

# Entraîner un modèle spécifique
python -c "from models.rainfall_prediction import RainfallPredictionModel; model = RainfallPredictionModel(); model.train_model()"
```

### Interface Streamlit

```bash
# Démarrer l'application Streamlit
streamlit run models/streamlit_app.py

# Ou avec Docker (Recommandé)
docker-compose up ml-models
```

**Accès :** http://localhost:8501

### Interface Web

L'application Streamlit offre :

- Tableau de Bord : Vue d'ensemble des alertes et tendances
- Prédictions Auto : Prédictions automatiques en temps réel avec données météo live
- Prédictions Précipitations : Interface interactive pour prédire la pluie
- Évaluation Sécheresse : Analyse des risques de sécheresse
- Optimisation Irrigation : Calcul des besoins en eau optimaux
- Analyse Complète : Vue consolidée de tous les modèles
- Configuration : Entraînement et gestion des modèles

Accès : http://localhost:8501

### Prédictions Automatiques en Temps Réel

Fonctionnalité qui combine données en temps réel et données empiriques :

#### Données en Temps Réel
- API OpenWeatherMap : Température, humidité, pression, vent actuels
- 6 villes du Sénégal : Dakar, Thiès, Saint-Louis, Kaolack, Ziguinchor, Tambacounda
- Mise à jour continue : Données fraîches à chaque prédiction

#### Données Empiriques
- NDVI saisonnier : Indices de végétation basés sur les moyennes historiques
- Humidité du sol : Estimations selon la saison et la région
- Stades de croissance : Calendriers agricoles automatiques par culture
- Radiation solaire : Calculs astronomiques précis

#### Configuration API
```bash
# 1. Obtenir une clé API gratuite sur openweathermap.org
# 2. Créer un fichier .env
cp models/.env.example models/.env

# 3. Configurer la clé API
OPENWEATHER_API_KEY= #Au niveau du fichier config
```

## Métriques de Performance

| Modèle | Métrique | Valeur |
|--------|----------|--------|
| Précipitations | RMSE | ~2.5 mm |
| Précipitations | R² | ~0.75 |
| Sécheresse | Accuracy | ~85% |
| Sécheresse | F1-Score | ~0.82 |
| Irrigation | RMSE | ~1.8 mm |
| Irrigation | R² | ~0.78 |

## Configuration Docker

```yaml
ml-models:
  build:
    context: .
    dockerfile: models/Dockerfile
  ports:
    - "8501:8501"
  volumes:
    - ./models:/app/models
    - ./data:/app/data
  env_file:
    - .env
```

## Test avec Docker

### Application Desktop
```bash
# Test complet automatisé
./test_docker.sh

# Test manuel
docker-compose build ml-models
docker-compose up ml-models
# Accès : http://localhost:8501
```
# Pas encore déployé
### Application Mobile
```bash
# Lancement interactif
./docker-mobile.sh

# Lancement direct mobile
docker-compose up ml-models-mobile
# Accès : http://localhost:8502

# Lancement complet (Desktop + Mobile)
docker-compose up
# Desktop : http://localhost:8501
# Mobile : http://localhost:8502
```

### Test des modules
```bash
docker-compose exec ml-models python models/test_realtime.py
docker-compose exec ml-models-mobile python models/test_realtime.py
```

## Cultures Supportées

| Culture | Coefficient Kc | Durée (jours) |
|---------|----------------|---------------|
| Mil | 0.3 → 1.0 → 0.4 | 120 |
| Sorgho | 0.3 → 1.15 → 0.4 | 130 |
| Maïs | 0.3 → 1.2 → 0.6 | 125 |
| Riz | 1.05 → 1.2 → 0.9 | 150 |
| Arachide | 0.4 → 1.15 → 0.6 | 130 |
| Coton | 0.35 → 1.15 → 0.7 | 180 |

## Validation Scientifique

- Penman-Monteith pour l'évapotranspiration
- Indices NDVI/EVI pour le stress végétatif
- Validation croisée temporelle et spatiale
- Sources : Google Earth Engine, ERA5, FAO

## Mise à Jour des Modèles

Les modèles peuvent être re-entraînés depuis l'interface Streamlit :
1. Aller dans Configuration
2. Cliquer sur le bouton d'entraînement souhaité
3. Ou utiliser "Entraîner Tous les Modèles"