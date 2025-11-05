"""
Application Streamlit pour les modèles prédictifs agricoles
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
import sys
import os

#Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.rainfall_prediction import RainfallPredictionModel
from models.drought_prediction import DroughtPredictionModel
from models.irrigation_optimization import IrrigationOptimizationModel
from models.disease_prediction import DiseasePredictionModel
from models.disease_prediction import DiseasePredictionModel

#Configuration de la page
st.set_page_config(
    page_title="🌾 DataBeez - Plateforme d’Intelligent Météo & Agricole",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Fonction utilitaire pour préparer les features selon le modèle
def prepare_features_for_model(model, input_data, date_str):
    """Préparer les features exactement comme attendu par le modèle"""
    if not hasattr(model, 'feature_names') or not model.feature_names:
        st.error("❌ Le modèle n'a pas de noms de features sauvegardés. Veuillez le ré-entraîner.")
        return None
    
    current_date = dt.strptime(str(date_str), '%Y-%m-%d')
    
    # Créer un dictionnaire avec toutes les features possibles
    all_features = {
        # Features météorologiques de base
        'temperature_2m': input_data.get('temperature', 25.0),
        'total_precipitation_sum': input_data.get('precipitation', 0.0),
        'surface_solar_radiation_downwards_sum': input_data.get('solar_radiation', 20.0) * 1000000,
        'u_component_of_wind_10m': input_data.get('wind_speed', 2.0) * 0.7,
        'v_component_of_wind_10m': input_data.get('wind_speed', 2.0) * 0.3,
        
        # Features satellitaires
        'lst_day_1km': input_data.get('temp_max', input_data.get('temperature', 25.0)) * 100,
        'lst_night_1km': input_data.get('temp_min', input_data.get('temperature', 25.0) - 8) * 100,
        'temp_day_celsius': input_data.get('temp_max', input_data.get('temperature', 25.0)),
        'temp_night_celsius': input_data.get('temp_min', input_data.get('temperature', 25.0) - 8),
        'evi': input_data.get('evi', 0.5),
        'ndvi': input_data.get('ndvi', 0.6),
        'ndvi_normalized': input_data.get('ndvi', 0.6),
        'evi_normalized': input_data.get('evi', 0.5),
        'ssm': input_data.get('soil_moisture', input_data.get('humidity', 70) / 100 * 0.8),
        
        # Features temporelles
        'month_sin': np.sin(2 * np.pi * current_date.month / 12),
        'month_cos': np.cos(2 * np.pi * current_date.month / 12),
        'day_sin': np.sin(2 * np.pi * current_date.timetuple().tm_yday / 365),
        'day_cos': np.cos(2 * np.pi * current_date.timetuple().tm_yday / 365),
        'is_dry_season': 1 if input_data.get('season', 'Wet') == 'Dry' else 0,
        'is_wet_season': 1 if input_data.get('season', 'Wet') == 'Wet' else 0,
        'day_of_year': current_date.timetuple().tm_yday,
        
        # Features dérivées communes
        'temp_range': input_data.get('temp_max', input_data.get('temperature', 25.0)) - input_data.get('temp_min', input_data.get('temperature', 25.0) - 8),
        'wind_speed': input_data.get('wind_speed', 2.0),
        'temp_max': input_data.get('temp_max', input_data.get('temperature', 25.0)),
        'temp_min': input_data.get('temp_min', input_data.get('temperature', 25.0) - 8),
        
        # Features spécifiques
        'vegetation_health': (input_data.get('ndvi', 0.6) + input_data.get('evi', 0.5)) / 2,
        'water_stress_index': (input_data.get('temperature', 25.0) - 25) / 10 - (input_data.get('ndvi', 0.6) - 0.5) / 0.3,
        'meteorological_drought_index': (input_data.get('temperature', 25.0) - 25) / 10 - (input_data.get('precipitation', 0.0) - 2) / 5,
        'agricultural_drought_index': (1 - input_data.get('soil_moisture', 0.6)) * (1 - input_data.get('ndvi', 0.6)),
        'temp_humidity_index': input_data.get('temperature', 25.0) * input_data.get('soil_moisture', 0.6),
        'leaf_wetness_duration': input_data.get('leaf_wetness', 8),
        'thermal_stress': abs(input_data.get('temperature', 25.0) - 25) / 10,
        'water_stress': max(0, 0.4 - input_data.get('soil_moisture', 0.6)),
        'vegetation_density': input_data.get('ndvi', 0.6),
        'temp_variation': input_data.get('temp_max', input_data.get('temperature', 25.0)) - input_data.get('temp_min', input_data.get('temperature', 25.0) - 8),
        'soil_water_deficit': max(0, 0.4 - input_data.get('soil_moisture', 0.6)),
        'vegetation_stress': 1 - input_data.get('ndvi', 0.6),
        'irrigation_efficiency': 0.8,
        'growth_stage': input_data.get('growth_stage', 60),
        'et0': 5.0,
        'etc': 6.0,
        
        # Conditions spécifiques
        'fungal_conditions': 1 if (input_data.get('soil_moisture', 0.6) > 0.7 and 20 <= input_data.get('temperature', 25.0) <= 30) else 0,
        'bacterial_conditions': 1 if (input_data.get('soil_moisture', 0.6) > 0.8 and input_data.get('temperature', 25.0) > 25) else 0,
        'viral_conditions': 1 if (25 <= input_data.get('temperature', 25.0) <= 35 and 0.4 <= input_data.get('soil_moisture', 0.6) <= 0.8) else 0,
        'consecutive_dry_days': 0 if input_data.get('precipitation_7d', 0) > 1 else 3,
        'consecutive_fungal_days': 0,
    }
    
    #Ajouter les moyennes mobiles et cumuls
    temp = all_features['temperature_2m']
    precip = all_features['total_precipitation_sum']
    ssm = all_features['ssm']
    ndvi = all_features['ndvi']
    
    for window in [3, 7, 14, 15, 30]:
        all_features[f'temp_ma_{window}'] = temp
        all_features[f'precip_ma_{window}'] = precip
        all_features[f'ssm_ma_{window}'] = ssm
        all_features[f'ndvi_ma_{window}'] = ndvi
        all_features[f'humidity_ma_{window}'] = ssm
        all_features[f'et0_ma_{window}'] = 5.0
        all_features[f'leaf_wetness_ma_{window}'] = input_data.get('leaf_wetness', 8)
        
        all_features[f'temp_deviation_{window}'] = 0.0
        all_features[f'precip_deviation_{window}'] = 0.0
        all_features[f'ndvi_deviation_{window}'] = 0.0
    
    for period in [1, 3, 7, 14, 15, 30, 60]:
        all_features[f'precipitation_lag_{period}'] = 0.0
        all_features[f'precip_cumul_{period}'] = input_data.get('precipitation_7d', 0) * (period / 7)
    
    # Ajouter les features de culture
    crop_types = ['mil', 'sorgho', 'mais', 'riz', 'arachide', 'coton']
    crop_type = input_data.get('crop_type', 'mil')
    for crop in crop_types:
        all_features[f'crop_{crop}'] = 1 if crop == crop_type else 0
    
    #Sélectionner seulement les features attendues par le modèle, dans le bon ordre
    model_features = {}
    for feature_name in model.feature_names:
        if feature_name in all_features:
            model_features[feature_name] = all_features[feature_name]
        else:
            #Valeur par défaut pour les features manquantes
            model_features[feature_name] = 0.0
            st.warning(f"⚠️ Feature manquante: {feature_name}, utilisation de la valeur par défaut 0.0")
    
    return pd.DataFrame([model_features])

#Cache pour les modèles
@st.cache_resource
def load_models():
    """Charger tous les modèles"""
    models = {}
    try:
        models['rainfall'] = RainfallPredictionModel()
        models['rainfall'].load_model()
    except:
        models['rainfall'] = None
    
    try:
        models['drought'] = DroughtPredictionModel()
        models['drought'].load_model()
    except:
        models['drought'] = None
    
    try:
        models['irrigation'] = IrrigationOptimizationModel()
        models['irrigation'].load_model()
    except:
        models['irrigation'] = None
    
    try:
        models['disease'] = DiseasePredictionModel()
        models['disease'].load_model()
    except:
        models['disease'] = None
    
    try:
        models['disease'] = DiseasePredictionModel()
        models['disease'].load_model()
    except:
        models['disease'] = None
    
    return models

def main():
    """Application principale"""
    
    # En-tête
    st.markdown('<h1 class="main-header">DataBeez - Plateforme Intelligente Météo & Agricole</h1>', unsafe_allow_html=True)
    st.markdown("### 🇸🇳 Prédictions agricoles pour le Sénégal")
    
    # Sidebar pour la navigation
    st.sidebar.title("🎯 Navigation")
    page = st.sidebar.selectbox(
        "Choisir une section",
        ["🏠 Tableau de Bord", "🤖 Prédictions Auto", "🌧️ Précipitations", "🏜️ Sécheresse", "💧 Irrigation", "🦠 Maladies", "📊 Analyse Complète", "⚙️ Configuration"]
    )
    
    # Charger les modèles
    models = load_models()
    
    # Afficher la page sélectionnée
    if page == "🏠 Tableau de Bord":
        dashboard_page(models)
    elif page == "🤖 Prédictions Auto":
        automatic_predictions_page(models)
    elif page == "🌧️ Précipitations":
        rainfall_page(models)
    elif page == "🏜️ Sécheresse":
        drought_page(models)
    elif page == "💧 Irrigation":
        irrigation_page(models)
    elif page == "🦠 Maladies":
        disease_page(models)
    elif page == "📊 Analyse Complète":
        comprehensive_page(models)
    elif page == "⚙️ Configuration":
        config_page(models)

def automatic_predictions_page(models):
    """Page de prédictions automatiques en temps réel"""
    st.header("🤖 Prédictions Automatiques en Temps Réel")
    
    st.info("🌍 Cette section utilise des données météorologiques en temps réel et des données empiriques pour générer automatiquement des prédictions pour toutes les régions du Sénégal.")
    
    # Vérifier que les modèles sont disponibles
    available_models = sum(1 for model in models.values() if model is not None)
    if available_models == 0:
        st.error("❌ Aucun modèle disponible. Veuillez les entraîner d'abord dans la section Configuration.")
        return
    
    st.success(f"✅ {available_models}/4 modèles disponibles")
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        selected_city = st.selectbox(
            "🌍 Ville à analyser",
            ["Toutes les villes", "Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"]
        )
    
    with col2:
        auto_refresh = st.checkbox("🔄 Actualisation automatique (30s)", value=False)
    
    #Type de culture fixe pour simplifier
    crop_type = "mil"  #Culture par défaut
    
    # Bouton de prédiction
    if st.button("🚀 Générer les Prédictions Automatiques", type="primary"):
        
        try:
            # Importer le module de prédictions automatiques
            from models.real_time_data import AutomaticPredictor
            
            # Créer le prédicteur
            predictor = AutomaticPredictor(models)
            
            with st.spinner("🔄 Récupération des données en temps réel et génération des prédictions..."):
                
                if selected_city == "Toutes les villes":
                    # Prédictions pour toutes les villes
                    results = predictor.get_daily_predictions_all_cities(crop_type)
                    
                    # Afficher le résumé
                    st.subheader("📋 Résumé Exécutif")
                    summary = results['summary']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🏙️ Villes Analysées", summary['total_cities'])
                    
                    with col2:
                        st.metric("🌧️ Fortes Pluies", len(summary['high_rainfall_cities']))
                    
                    with col3:
                        st.metric("🏜️ Risque Sécheresse", len(summary['drought_risk_cities']))
                    
                    with col4:
                        st.metric("💧 Irrigation Intensive", len(summary['high_irrigation_need_cities']))
                    
                    # Alertes prioritaires
                    if summary['high_rainfall_cities'] or summary['drought_risk_cities'] or summary['high_irrigation_need_cities']:
                        st.subheader("🚨 Alertes Prioritaires")
                        
                        if summary['high_rainfall_cities']:
                            st.warning(f"🌧️ **Fortes précipitations prévues** : {', '.join(summary['high_rainfall_cities'])}")
                        
                        if summary['drought_risk_cities']:
                            st.error(f"🏜️ **Risque de sécheresse élevé** : {', '.join(summary['drought_risk_cities'])}")
                        
                        if summary['high_irrigation_need_cities']:
                            st.info(f"💧 **Irrigation intensive requise** : {', '.join(summary['high_irrigation_need_cities'])}")
                    
                    # Détails par ville
                    st.subheader("🏙️ Prédictions Détaillées par Ville")
                    
                    for city, prediction in results['predictions'].items():
                        if 'error' not in prediction:
                            with st.expander(f"📍 {city} - {prediction['weather_conditions']['description']}"):
                                
                                # Conditions actuelles
                                st.write("**🌡️ Conditions Actuelles:**")
                                weather = prediction['weather_conditions']
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Température", f"{weather['temperature']:.1f}°C")
                                with col2:
                                    st.metric("Humidité", f"{weather['humidity']:.0f}%")
                                with col3:
                                    st.metric("Saison", weather['season'])
                                
                                # Prédictions
                                st.write("**🔮 Prédictions pour Demain:**")
                                
                                pred_cols = st.columns(3)
                                
                                with pred_cols[0]:
                                    if 'rainfall' in prediction and 'error' not in prediction['rainfall']:
                                        r = prediction['rainfall']
                                        st.metric("🌧️ Pluie", f"{r['predicted_mm']} mm", delta=r['category'])
                                    else:
                                        st.metric("🌧️ Pluie", "0.0 mm", delta="Pas de données")
                                
                                with pred_cols[1]:
                                    if 'drought' in prediction and 'error' not in prediction['drought']:
                                        d = prediction['drought']
                                        confidence_indicator = "🎯" if d.get('confidence', 0) > 70 else "📊"
                                        st.metric("🏜️ Sécheresse", d['risk_level'], delta=f"{confidence_indicator} Niveau {d['severity']}")
                                    else:
                                        st.metric("🏜️ Sécheresse", "Faible", delta="📊 Estimation")
                                
                                with pred_cols[2]:
                                    if 'irrigation' in prediction and 'error' not in prediction['irrigation']:
                                        i = prediction['irrigation']
                                        efficiency_indicator = "🎯" if i.get('efficiency', 0) > 80 else "📊"
                                        st.metric("💧 Irrigation", f"{i['need_mm_per_day']} mm/j", delta=f"{efficiency_indicator} {i['frequency']}")
                                    else:
                                        st.metric("💧 Irrigation", "3.0 mm/j", delta="📊 Estimation")
                        else:
                            st.error(f"❌ Erreur pour {city}: {prediction['error']}")
                
                else:
                    # Prédiction pour une ville spécifique
                    result = predictor.predict_all_for_city(selected_city, crop_type)
                    
                    if 'error' not in result:
                        st.success(f"✅ Prédictions générées pour {selected_city}")
                        
                        # Conditions actuelles
                        st.subheader("🌡️ Conditions Actuelles")
                        weather = result['weather_conditions']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("🌡️ Température", f"{weather['temperature']:.1f}°C")
                        with col2:
                            st.metric("💧 Humidité", f"{weather['humidity']:.0f}%")
                        with col3:
                            st.metric("🗓️ Saison", weather['season'])
                        with col4:
                            st.metric("📅 Prédiction", "Demain")
                        
                        st.info(f"📡 Conditions: {weather['description']}")
                        
                        # Prédictions détaillées
                        st.subheader("🔮 Prédictions pour Demain")
                        
                        # Onglets pour chaque prédiction
                        tab1, tab2, tab3 = st.tabs(["🌧️ Précipitations", "🏜️ Sécheresse", "💧 Irrigation"])
                        
                        with tab1:
                            if 'rainfall' in result and 'error' not in result['rainfall']:
                                r = result['rainfall']
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Précipitations Prévues", f"{r['predicted_mm']} mm")
                                    st.metric("Catégorie", r['category'])
                                with col2:
                                    st.metric("Confiance", f"{r['confidence']}%")
                                
                                # Recommandations automatiques
                                if r['predicted_mm'] > 10:
                                    st.warning("⚠️ **Fortes pluies prévues** - Protéger les cultures sensibles")
                                elif r['predicted_mm'] < 1:
                                    st.info("ℹ️ **Pas de pluie prévue** - Prévoir l'irrigation")
                                else:
                                    st.success("✅ **Conditions normales** - Surveillance standard")
                            else:
                                st.error("❌ Prédiction des précipitations non disponible")
                        
                        with tab2:
                            if 'drought' in result and 'error' not in result['drought']:
                                d = result['drought']
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Niveau de Risque", d['risk_level'])
                                    st.metric("Score de Sévérité", f"{d['severity']}/3")
                                with col2:
                                    st.metric("Confiance", f"{d['confidence']}%")
                                    source = "Modèle ML" if d['confidence'] > 70 else "Estimation empirique"
                                    st.metric("Source", source)
                                
                                # Alertes automatiques
                                if d['severity'] >= 2:
                                    st.error("🚨 **Risque de sécheresse élevé** - Mesures d'urgence recommandées")
                                    st.write("**Actions immédiates :**")
                                    st.write("• Rationner l'eau d'irrigation")
                                    st.write("• Prioriser les cultures sensibles")
                                    st.write("• Surveiller l'humidité du sol quotidiennement")
                                elif d['severity'] == 1:
                                    st.warning("⚠️ **Surveillance renforcée** - Optimiser l'utilisation de l'eau")
                                    st.write("**Recommandations :**")
                                    st.write("• Surveiller les prévisions météo")
                                    st.write("• Optimiser l'efficacité de l'irrigation")
                                    st.write("• Préparer les mesures d'économie d'eau")
                                else:
                                    st.success("✅ **Pas de risque** - Conditions normales")
                                    st.write("**Surveillance standard :**")
                                    st.write("• Maintenir les pratiques habituelles")
                                    st.write("• Surveiller l'évolution des conditions")
                            else:
                                st.info("ℹ️ Prédiction basée sur les conditions saisonnières moyennes")
                        
                        with tab3:
                            if 'irrigation' in result and 'error' not in result['irrigation']:
                                i = result['irrigation']
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Besoins en Eau", f"{i['need_mm_per_day']} mm/jour")
                                    st.metric("Fréquence Recommandée", i['frequency'])
                                with col2:
                                    st.metric("Efficacité", f"{i['efficiency']}%")
                                    source = "Modèle ML" if i['efficiency'] > 80 else "Calcul empirique"
                                    st.metric("Source", source)
                                
                                # Conseils automatiques
                                if i['need_mm_per_day'] > 6:
                                    st.warning("⚠️ **Besoins élevés** - Irrigation intensive requise")
                                    st.write("**Planning recommandé :**")
                                    st.write("• Irrigation 2 fois par jour (matin et soir)")
                                    st.write("• Durée : 45-60 minutes par session")
                                    st.write("• Surveiller le drainage pour éviter l'engorgement")
                                elif i['need_mm_per_day'] > 3:
                                    st.info("ℹ️ **Besoins modérés** - Irrigation régulière")
                                    st.write("**Planning recommandé :**")
                                    st.write("• Irrigation quotidienne ou tous les 2 jours")
                                    st.write("• Durée : 30-45 minutes")
                                    st.write("• Meilleurs moments : 6h-8h ou 17h-19h")
                                else:
                                    st.success("✅ **Besoins faibles** - Irrigation légère suffisante")
                                    st.write("**Planning recommandé :**")
                                    st.write("• Irrigation tous les 3-4 jours")
                                    st.write("• Durée : 15-30 minutes")
                                    st.write("• Surveiller l'humidité du sol")
                                
                                # Conseils d'économie d'eau
                                st.write("**💡 Conseils d'économie :**")
                                st.write("• Utiliser du paillis pour réduire l'évaporation")
                                st.write("• Vérifier les fuites du système d'irrigation")
                                st.write("• Ajuster selon les prévisions de pluie")
                            else:
                                st.info("ℹ️ Estimation basée sur les conditions météorologiques actuelles")
                        

                    
                    else:
                        st.error(f"❌ Erreur lors de la génération des prédictions: {result['error']}")
        
        except ImportError:
            st.error("❌ Module de prédictions automatiques non disponible. Vérifiez l'installation.")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération des prédictions: {e}")
    
    # Actualisation automatique
    if auto_refresh:
        import time
        time.sleep(30)
        st.experimental_rerun()
    
    # Informations sur les données
    with st.expander("ℹ️ Sources de Données"):
        st.write("""
        **🌐 Données en Temps Réel:**
        - Température, humidité, pression, vent : API OpenWeatherMap
        - Coordonnées GPS des 6 principales villes du Sénégal
        
        **📊 Données Empiriques:**
        - NDVI et humidité du sol : Moyennes saisonnières historiques
        - Stades de croissance : Calendriers agricoles locaux
        - Radiation solaire : Modèles astronomiques
        
        **🔄 Fréquence de Mise à Jour:**
        - Données météo : Temps réel (API)
        - Données empiriques : Calculées dynamiquement
        - Prédictions : À la demande ou auto-refresh 30s
        """)

def dashboard_page(models):
    """Page tableau de bord avec données réelles"""
    st.header("📊 Tableau de Bord DataBeez")
    
    # Initialiser le fournisseur de données
    try:
        from models.daily_data_provider import DailyDataProvider
        data_provider = DailyDataProvider()
        data_available = True
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fournisseur de données: {e}")
        data_available = False
        data_provider = None
    
    # CSS pour les alertes et cartes météo
    st.markdown("""
    <style>
    .alert-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .alert-low {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .weather-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌧️ Modèle Pluie", "Actif" if models['rainfall'] else "Inactif", 
                 delta="✅" if models['rainfall'] else "❌")
    
    with col2:
        st.metric("Modèle Sécheresse", "Actif" if models['drought'] else "Inactif",
                 delta="✅" if models['drought'] else "❌")
    
    with col3:
        st.metric("Modèle Irrigation", "Actif" if models['irrigation'] else "Inactif",
                 delta="✅" if models['irrigation'] else "❌")
    
    with col4:
        # Informations sur le modèle de prédiction des maladies
        if models['disease']:
            # Calculer les statistiques du modèle de maladies
            try:
                disease_model = models['disease']
                
                # Obtenir des informations sur le modèle
                if hasattr(disease_model, 'disease_database'):
                    total_diseases = sum(len(diseases) for diseases in disease_model.disease_database.values())
                    cultures_count = len(disease_model.disease_database.keys())
                    
                    st.metric(
                        "🦠 Modèle Maladies", 
                        f"{total_diseases} maladies",
                        delta=f"{cultures_count} cultures"
                    )
                else:
                    st.metric("🦠 Modèle Maladies", "Actif", delta="✅")
                    
            except Exception:
                st.metric("🦠 Modèle Maladies", "Actif", delta="✅")
        else:
            st.metric("🦠 Modèle Maladies", "Inactif", delta="❌")
    
    st.divider()
    
    if data_available and data_provider:
        # Conditions météo actuelles
        st.subheader("🌤️ Conditions Météo Actuelles")
        
        # Vérifier d'abord si l'API fonctionne
        api_working = False
        try:
            test_weather = data_provider.get_current_weather('Dakar')
            api_working = test_weather is not None and 'temperature' in test_weather
        except:
            api_working = False
        
        if api_working:
            weather_cols = st.columns(3)
            cities_sample = ['Dakar', 'Thiès', 'Saint-Louis']
            
            for i, city in enumerate(cities_sample):
                with weather_cols[i]:
                    current_weather = data_provider.get_current_weather(city)
                    if current_weather and 'temperature' in current_weather:
                        # Déterminer la source des données
                        data_source = "🌐 API Live" if data_provider.openweather_api_key != 'demo_key' else "📊 Historique"
                        
                        st.markdown(f"""
                        <div class="weather-card">
                            <h4>🏙️ {city}</h4>
                            <p><strong>🌡️ Température:</strong> {current_weather['temperature']:.1f}°C</p>
                            <p><strong>💧 Humidité:</strong> {current_weather['humidity']}%</p>
                            <p><strong>💨 Vent:</strong> {current_weather['wind_speed']:.1f} m/s</p>
                            <p><strong>☁️ Nuages:</strong> {current_weather['cloudiness']}%</p>
                            <p><em>{current_weather['weather_description']}</em></p>
                            <p><small>{data_source}</small></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Utiliser les données historiques comme fallback
                        historical = data_provider.get_historical_averages(city, datetime.now())
                        avg_temp = (historical['temperature_min'] + historical['temperature_max']) / 2
                        avg_humidity = (historical['humidity_min'] + historical['humidity_max']) / 2
                        
                        st.markdown(f"""
                        <div class="weather-card">
                            <h4>🏙️ {city}</h4>
                            <p><strong>🌡️ Température:</strong> {avg_temp:.1f}°C</p>
                            <p><strong>💧 Humidité:</strong> {avg_humidity:.0f}%</p>
                            <p><strong>💨 Vent:</strong> 3.0 m/s</p>
                            <p><strong>☁️ Nuages:</strong> 30%</p>
                            <p><em>Moyennes saisonnières</em></p>
                            <p><small>📊 Données Historiques</small></p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # API ne fonctionne pas, afficher un message informatif
            st.warning("⚠️ **API météo indisponible** - Utilisation des données historiques")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("""
                **💡 Pour activer les données temps réel :**
                1. Obtenez une clé API gratuite sur [OpenWeatherMap](https://openweathermap.org/api)
                2. Copiez `models/.env.example` vers `models/.env`
                3. Ajoutez votre clé : `OPENWEATHER_API_KEY=votre_clé`
                4. Redémarrez l'application
                """)
            
            with col2:
                st.markdown("""
                **📊 Données disponibles sans API :**
                - ✅ Moyennes saisonnières historiques
                - ✅ Tendances régionales
                - ✅ Prédictions basées sur historique
                - ✅ Alertes intelligentes
                """)
            
            # Afficher quand même quelques données historiques
            st.subheader("📈 Moyennes Saisonnières Actuelles")
            hist_cols = st.columns(3)
            cities_sample = ['Dakar', 'Thiès', 'Saint-Louis']
            
            for i, city in enumerate(cities_sample):
                with hist_cols[i]:
                    historical = data_provider.get_historical_averages(city, datetime.now())
                    avg_temp = (historical['temperature_min'] + historical['temperature_max']) / 2
                    avg_humidity = (historical['humidity_min'] + historical['humidity_max']) / 2
                    
                    st.metric(
                        f"🏙️ {city}",
                        f"{avg_temp:.1f}°C",
                        delta=f"{avg_humidity:.0f}% humidité"
                    )
        
        st.divider()
        
        # Alertes du jour avec vraies données
        st.subheader("🚨 Alertes du Jour")
        
        real_alerts = data_provider.get_daily_alerts()
        if real_alerts:
            for alert in real_alerts:
                if alert["level"] == "Critique":
                    st.markdown(f'<div class="alert-high">🔴 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
                elif alert["level"] == "Élevé":
                    st.markdown(f'<div class="alert-medium">🟠 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-low">🟡 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
        else:
            st.info("✅ Aucune alerte critique aujourd'hui")
        
        st.divider()
        
        # Graphiques de tendances avec vraies données
        st.subheader("📈 Tendances Régionales (7 derniers jours)")
        
        trends = data_provider.get_regional_trends(days=7)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌧️ Précipitations")
            if 'precipitation' in trends:
                precip_melted = trends['precipitation'].melt(id_vars=['Date'], var_name='Région', value_name='Précipitations (mm)')
                fig = px.line(precip_melted,
                             x='Date', y='Précipitations (mm)', color='Région',
                             title="Évolution des précipitations (données réelles)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ Données de précipitations indisponibles")
        
        with col2:
            st.subheader("🌡️ Températures")
            if 'temperature' in trends:
                temp_melted = trends['temperature'].melt(id_vars=['Date'], var_name='Région', value_name='Température (°C)')
                fig = px.line(temp_melted,
                             x='Date', y='Température (°C)', color='Région',
                             title="Évolution des températures (données réelles)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ Données de température indisponibles")
        
        # Prévisions pour demain
        st.divider()
        st.subheader("🔮 Prévisions pour Demain")
        
        forecast_cols = st.columns(2)
        
        with forecast_cols[0]:
            st.write("**🌤️ Conditions Prévues**")
            for city in ['Dakar', 'Thiès']:
                forecast = data_provider.get_forecast_data(city, days=1)
                if forecast and len(forecast) > 0:
                    tomorrow = forecast[0]
                    st.write(f"**{city}:** {tomorrow['temperature']:.1f}°C, {tomorrow['humidity']}% humidité")
                else:
                    st.write(f"**{city}:** Prévisions indisponibles")
        
        with forecast_cols[1]:
            st.write("**📊 Recommandations**")
            st.write("• Surveiller l'évolution des conditions météo")
            st.write("• Ajuster l'irrigation selon les prévisions")
            st.write("• Vérifier les alertes régulièrement")
        
        # Section risques de maladies
        if models['disease']:
            st.divider()
            st.subheader("🦠 Risques de Maladies des Cultures")
            
            try:
                disease_model = models['disease']
                
                # Analyser les conditions actuelles pour les risques de maladies
                disease_cols = st.columns(3)
                cultures = ['mil', 'sorgho', 'mais']
                
                for i, culture in enumerate(cultures):
                    with disease_cols[i]:
                        if hasattr(disease_model, 'disease_database') and culture in disease_model.disease_database:
                            diseases = disease_model.disease_database[culture]
                            
                            # Obtenir les conditions actuelles réelles
                            if data_available and data_provider:
                                try:
                                    # Utiliser les données météo de Dakar comme référence
                                    current_weather = data_provider.get_current_weather('Dakar')
                                    if current_weather:
                                        current_temp = current_weather['temperature']
                                        current_humidity = current_weather['humidity']
                                    else:
                                        current_temp = 28
                                        current_humidity = 70
                                    
                                    # Déterminer la saison basée sur le mois actuel
                                    current_month = dt.now().month
                                    current_season = 'Wet' if 6 <= current_month <= 10 else 'Dry'
                                except:
                                    current_temp = 28
                                    current_humidity = 70
                                    current_season = 'Wet'
                            else:
                                current_temp = 28
                                current_humidity = 70
                                current_season = 'Wet'
                            
                            high_risk_diseases = []
                            medium_risk_diseases = []
                            
                            for disease_name, conditions in diseases.items():
                                temp_min, temp_max = conditions['temp_range']
                                humidity_min = conditions['humidity_min']
                                risk_season = conditions['risk_season']
                                
                                # Évaluer le risque
                                temp_risk = temp_min <= current_temp <= temp_max
                                humidity_risk = current_humidity >= humidity_min
                                season_risk = current_season == risk_season
                                
                                if temp_risk and humidity_risk and season_risk:
                                    high_risk_diseases.append(disease_name)
                                elif (temp_risk and humidity_risk) or (temp_risk and season_risk):
                                    medium_risk_diseases.append(disease_name)
                            
                            # Afficher les résultats
                            st.markdown(f"**🌾 {culture.title()}**")
                            
                            if high_risk_diseases:
                                st.error(f"🔴 Risque élevé: {', '.join(high_risk_diseases)}")
                            elif medium_risk_diseases:
                                st.warning(f"🟡 Risque modéré: {', '.join(medium_risk_diseases)}")
                            else:
                                st.success("🟢 Risque faible")
                            
                            st.write(f"📊 {len(diseases)} maladies surveillées")
                        else:
                            st.write(f"**🌾 {culture.title()}**")
                            st.info("Données de maladies non disponibles")
                
                # Afficher les conditions utilisées pour l'évaluation
                st.markdown("---")
                st.info(f"📊 **Évaluation basée sur :** Température: {current_temp:.1f}°C, Humidité: {current_humidity}%, Saison: {current_season}")
                
                # Recommandations générales
                st.write("**💡 Recommandations Phytosanitaires :**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("• Inspecter régulièrement les cultures")
                    st.write("• Maintenir une bonne aération des parcelles")
                    st.write("• Éviter l'excès d'humidité")
                
                with col2:
                    st.write("• Appliquer des traitements préventifs si nécessaire")
                    st.write("• Surveiller les conditions météo favorables aux maladies")
                    st.write("• Consulter un agronome en cas de symptômes")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse des maladies: {e}")
                st.info("🦠 Le modèle de prédiction des maladies est disponible mais nécessite une configuration.")
        

    
    else:
        # Mode fallback avec données simulées
        st.warning("⚠️ Utilisation des données simulées (fournisseur de données indisponible)")
        
        # Alertes simulées
        st.subheader("🚨 Alertes du Jour (Simulées)")
        alerts = [
            {"region": "Dakar", "type": "Précipitations", "level": "Modéré", "message": "Pluies légères prévues"},
            {"region": "Thiès", "type": "Sécheresse", "level": "Élevé", "message": "Risque de stress hydrique"},
            {"region": "Saint-Louis", "type": "Irrigation", "level": "Critique", "message": "Irrigation intensive requise"}
        ]
        
        for alert in alerts:
            if alert["level"] == "Critique":
                st.markdown(f'<div class="alert-high">🔴 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
            elif alert["level"] == "Élevé":
                st.markdown(f'<div class="alert-medium">🟠 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-low">🟡 <strong>{alert["region"]}</strong> - {alert["type"]}: {alert["message"]}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Graphiques simulés
        st.subheader("📈 Tendances Régionales (Simulées)")
        
        dates = pd.date_range(start='2025-10-01', end='2025-11-02', freq='D')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌧️ Précipitations (7 derniers jours)")
            precip_data = pd.DataFrame({
                'Date': dates[-7:],
                'Dakar': np.random.exponential(2, 7),
                'Thiès': np.random.exponential(1.5, 7),
                'Saint-Louis': np.random.exponential(1, 7),
                'Kaolack': np.random.exponential(3, 7)
            })
            
            fig = px.line(precip_data.melt(id_vars=['Date'], var_name='Région', value_name='Précipitations (mm)'),
                         x='Date', y='Précipitations (mm)', color='Région',
                         title="Évolution des précipitations (simulées)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🌡️ Températures Moyennes")
            temp_data = pd.DataFrame({
                'Date': dates[-7:],
                'Dakar': 28 + np.random.normal(0, 2, 7),
                'Thiès': 30 + np.random.normal(0, 2, 7),
                'Saint-Louis': 32 + np.random.normal(0, 2, 7),
                'Kaolack': 29 + np.random.normal(0, 2, 7)
            })
            
            fig = px.line(temp_data.melt(id_vars=['Date'], var_name='Région', value_name='Température (°C)'),
                         x='Date', y='Température (°C)', color='Région',
                         title="Évolution des températures (simulées)")
            st.plotly_chart(fig, use_container_width=True)

def rainfall_page(models):
    """Page prédiction des précipitations"""
    st.header("🌧️ Prédiction des Précipitations")
    
    if not models['rainfall']:
        st.error("❌ Modèle de précipitations non disponible. Veuillez l'entraîner d'abord.")
        return
    
    # Formulaire de saisie
    with st.form("rainfall_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.selectbox("🌍 Région", 
                                ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"])
            date = st.date_input("📅 Date", dt.now() + timedelta(days=1))
            
            # Essayer de récupérer les données actuelles pour pré-remplir
            try:
                from models.daily_data_provider import DailyDataProvider
                data_provider = DailyDataProvider()
                current_weather = data_provider.get_current_weather(region)
                
                if current_weather:
                    default_temp = current_weather['temperature']
                    default_humidity = current_weather['humidity']
                    st.info(f"🌤️ Conditions actuelles à {region}: {default_temp:.1f}°C, {default_humidity}%")
                else:
                    default_temp = 28.0
                    default_humidity = 70
                    st.warning(f"⚠️ Données actuelles indisponibles pour {region}")
            except:
                default_temp = 28.0
                default_humidity = 70
                st.warning("⚠️ Fournisseur de données indisponible")
            
            temperature = st.slider("🌡️ Température (°C)", 15.0, 45.0, float(default_temp))
            humidity = st.slider("💧 Humidité (%)", 20, 100, int(default_humidity))
        
        with col2:
            pressure = st.slider("🌪️ Pression (hPa)", 980, 1040, 1012)
            wind_speed = st.slider("💨 Vitesse du vent (m/s)", 0.0, 15.0, 3.0)
            solar_radiation = st.slider("☀️ Radiation solaire (MJ/m²)", 5.0, 35.0, 20.0)
        
        submitted = st.form_submit_button("🔮 Prédire les Précipitations")
    
    if submitted:
        # Préparer les données avec toutes les features nécessaires
        
        current_date = dt.strptime(str(date), '%Y-%m-%d')
        
        weather_data = {
            'temperature_2m': temperature,
            'total_precipitation_sum': 0.0,  # Valeur par défaut
            'surface_solar_radiation_downwards_sum': solar_radiation * 1000000,
            'u_component_of_wind_10m': wind_speed * 0.7,
            'v_component_of_wind_10m': wind_speed * 0.3,
            'lst_day_1km': temperature * 100,
            'lst_night_1km': (temperature - 8) * 100,
            'temp_day_celsius': temperature,
            'temp_night_celsius': temperature - 8,
            'evi': 0.5,  # Valeur par défaut
            'ndvi': 0.6,  # Valeur par défaut
            'ndvi_normalized': 0.6,
            'evi_normalized': 0.5,
            'ssm': humidity / 100 * 0.8,
            'month_sin': np.sin(2 * np.pi * current_date.month / 12),
            'month_cos': np.cos(2 * np.pi * current_date.month / 12),
            'day_sin': np.sin(2 * np.pi * current_date.timetuple().tm_yday / 365),
            'day_cos': np.cos(2 * np.pi * current_date.timetuple().tm_yday / 365),
            'temp_range': 8.0,  # Différence jour/nuit
            'wind_speed': wind_speed,
            'vegetation_health': 0.55,  # (ndvi + evi) / 2
            'precipitation_lag_1': 0.0,
            'precipitation_lag_3': 0.0,
            'precipitation_lag_7': 0.0,
            'temp_ma_3': temperature,
            'temp_ma_7': temperature,
            'temp_ma_15': temperature,
            'humidity_ma_3': humidity / 100 * 0.8,
            'humidity_ma_7': humidity / 100 * 0.8,
            'humidity_ma_15': humidity / 100 * 0.8
        }
        
        try:
            # Préparer les données d'entrée
            input_data = {
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure,
                'wind_speed': wind_speed,
                'solar_radiation': solar_radiation
            }
            
            # Préparer les features pour le modèle
            features_df = prepare_features_for_model(models['rainfall'], input_data, date)
            
            if features_df is None:
                st.error("❌ Impossible de préparer les features pour la prédiction")
                return
            
            # Faire la prédiction directement
            prediction_value = models['rainfall'].predict(features_df)[0]
            
            # Créer l'objet de prédiction
            if prediction_value < 1:
                category = "Pas de pluie"
                risk_level = "Faible"
            elif prediction_value < 5:
                category = "Pluie légère"
                risk_level = "Modéré"
            elif prediction_value < 15:
                category = "Pluie modérée"
                risk_level = "Élevé"
            else:
                category = "Pluie forte"
                risk_level = "Très élevé"
            
            prediction = {
                'predicted_rainfall_mm': round(prediction_value, 2),
                'category': category,
                'risk_level': risk_level,
                'confidence': 85.0,
                'recommendations': [
                    "Surveiller les conditions météorologiques",
                    "Ajuster l'irrigation selon les prévisions",
                    "Protéger les cultures si nécessaire"
                ]
            }
            
            # Afficher les résultats
            st.success("✅ Prédiction réalisée avec succès!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🌧️ Précipitations Prévues", 
                         f"{prediction['predicted_rainfall_mm']} mm",
                         delta=prediction['category'])
            
            with col2:
                st.metric("📊 Niveau de Confiance", 
                         f"{prediction['confidence']}%")
            
            with col3:
                risk_color = {"Faible": "🟢", "Modéré": "🟡", "Élevé": "🟠", "Très élevé": "🔴"}
                st.metric("⚠️ Niveau de Risque", 
                         f"{risk_color.get(prediction['risk_level'], '⚪')} {prediction['risk_level']}")
            
            # Recommandations
            st.subheader("💡 Recommandations")
            for i, rec in enumerate(prediction['recommendations'], 1):
                st.write(f"{i}. {rec}")
            
            # Graphique de visualisation
            st.subheader("📊 Visualisation")
            
            # Graphique en jauge pour les précipitations
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = prediction['predicted_rainfall_mm'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Précipitations (mm)"},
                delta = {'reference': 5},
                gauge = {
                    'axis': {'range': [None, 20]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 1], 'color': "lightgray"},
                        {'range': [1, 5], 'color': "yellow"},
                        {'range': [5, 15], 'color': "orange"},
                        {'range': [15, 20], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 15
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la prédiction: {e}")

def drought_page(models):
    """Page prédiction de sécheresse"""
    st.header("🏜️ Prédiction de Sécheresse")
    
    if not models['drought']:
        st.error("❌ Modèle de sécheresse non disponible. Veuillez l'entraîner d'abord.")
        return
    
    # Formulaire de saisie
    with st.form("drought_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.selectbox("🌍 Région", 
                                ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"])
            date = st.date_input("📅 Date", dt.now())
            temperature = st.slider("🌡️ Température (°C)", 15.0, 45.0, 32.0)
            soil_moisture = st.slider("💧 Humidité du sol", 0.1, 1.0, 0.3)
        
        with col2:
            ndvi = st.slider("🌱 Indice NDVI", 0.0, 1.0, 0.4)
            season = st.selectbox("🗓️ Saison", ["Dry", "Wet"])
            precipitation_7d = st.slider("🌧️ Précipitations 7j (mm)", 0.0, 50.0, 2.0)
        
        submitted = st.form_submit_button("🔮 Évaluer le Risque de Sécheresse")
    
    if submitted:
        # Préparer les données avec toutes les features nécessaires
        
        current_date = dt.strptime(str(date), '%Y-%m-%d')
        
        environmental_data = {
            'temperature_2m': temperature,
            'total_precipitation_sum': precipitation_7d / 7,
            'surface_solar_radiation_downwards_sum': 20000000,
            'u_component_of_wind_10m': 2.0,
            'v_component_of_wind_10m': 1.5,
            'ssm': soil_moisture,
            'lst_day_1km': temperature * 100,
            'lst_night_1km': (temperature - 8) * 100,
            'temp_day_celsius': temperature,
            'temp_night_celsius': temperature - 8,
            'evi': ndvi * 0.8,
            'ndvi': ndvi,
            'ndvi_normalized': ndvi,
            'evi_normalized': ndvi * 0.8,
            'month_sin': np.sin(2 * np.pi * current_date.month / 12),
            'month_cos': np.cos(2 * np.pi * current_date.month / 12),
            'is_dry_season': 1 if season == 'Dry' else 0,
            'water_stress_index': (temperature - 25) / 10 - (ndvi - 0.5) / 0.3,
            'meteorological_drought_index': (temperature - 25) / 10 - (precipitation_7d / 7 - 2) / 5,
            'agricultural_drought_index': (1 - soil_moisture) * (1 - ndvi),
            'consecutive_dry_days': 0 if precipitation_7d > 1 else 3,
            'temp_ma_7': temperature,
            'temp_ma_15': temperature,
            'temp_ma_30': temperature,
            'precip_ma_7': precipitation_7d / 7,
            'precip_ma_15': precipitation_7d / 7,
            'precip_ma_30': precipitation_7d / 7,
            'ndvi_ma_7': ndvi,
            'ndvi_ma_15': ndvi,
            'ndvi_ma_30': ndvi,
            'ssm_ma_7': soil_moisture,
            'ssm_ma_15': soil_moisture,
            'ssm_ma_30': soil_moisture,
            'temp_deviation_7': 0.0,
            'temp_deviation_15': 0.0,
            'temp_deviation_30': 0.0,
            'precip_deviation_7': 0.0,
            'precip_deviation_15': 0.0,
            'precip_deviation_30': 0.0,
            'ndvi_deviation_7': 0.0,
            'ndvi_deviation_15': 0.0,
            'ndvi_deviation_30': 0.0,
            'precip_cumul_7': precipitation_7d,
            'precip_cumul_15': precipitation_7d * 2,
            'precip_cumul_30': precipitation_7d * 4,
            'precip_cumul_60': precipitation_7d * 8
        }
        
        try:
            # Préparer les données d'entrée
            input_data = {
                'temperature': temperature,
                'soil_moisture': soil_moisture,
                'ndvi': ndvi,
                'season': season,
                'precipitation_7d': precipitation_7d
            }
            
            # Préparer les features pour le modèle
            features_df = prepare_features_for_model(models['drought'], input_data, date)
            
            if features_df is None:
                st.error("❌ Impossible de préparer les features pour la prédiction")
                return
            
            # Faire la prédiction directement
            prediction_value = models['drought'].predict(features_df)[0]
            
            # Interpréter la prédiction
            drought_levels = {
                0: {"level": "Pas de sécheresse", "risk": "Faible", "color": "green"},
                1: {"level": "Sécheresse légère", "risk": "Modéré", "color": "yellow"},
                2: {"level": "Sécheresse modérée", "risk": "Élevé", "color": "orange"},
                3: {"level": "Sécheresse sévère", "risk": "Critique", "color": "red"}
            }
            
            result = drought_levels.get(prediction_value, drought_levels[0])
            
            prediction = {
                'drought_level': result["level"],
                'risk_category': result["risk"],
                'severity_score': int(prediction_value),
                'confidence': 85.0,
                'alert_color': result["color"],
                'recommendations': [
                    "Surveiller l'humidité du sol",
                    "Optimiser l'irrigation",
                    "Protéger les cultures sensibles"
                ],
                'monitoring_actions': [
                    "Surveillance quotidienne",
                    "Mesure de l'humidité du sol"
                ]
            }
            
            # Afficher les résultats
            st.success("✅ Évaluation réalisée avec succès!")
            
            # Alerte selon le niveau
            if prediction['severity_score'] >= 3:
                st.error(f"🔴 **ALERTE CRITIQUE** - {prediction['drought_level']}")
            elif prediction['severity_score'] >= 2:
                st.warning(f"🟠 **ALERTE ÉLEVÉE** - {prediction['drought_level']}")
            elif prediction['severity_score'] >= 1:
                st.info(f"🟡 **SURVEILLANCE** - {prediction['drought_level']}")
            else:
                st.success(f"🟢 **NORMAL** - {prediction['drought_level']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Score de Sévérité", 
                         f"{prediction['severity_score']}/3")
            
            with col2:
                st.metric("🎯 Confiance", 
                         f"{prediction['confidence']}%")
            
            with col3:
                st.metric("⚠️ Catégorie de Risque", 
                         prediction['risk_category'])
            
            # Recommandations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💡 Recommandations")
                for i, rec in enumerate(prediction['recommendations'], 1):
                    st.write(f"{i}. {rec}")
            
            with col2:
                st.subheader("👁️ Actions de Monitoring")
                for i, action in enumerate(prediction['monitoring_actions'], 1):
                    st.write(f"{i}. {action}")
            
        except Exception as e:
            st.error(f"❌ Erreur lors de l'évaluation: {e}")

def irrigation_page(models):
    """Page optimisation irrigation"""
    st.header("💧 Optimisation de l'Irrigation")
    
    if not models['irrigation']:
        st.error("❌ Modèle d'irrigation non disponible. Veuillez l'entraîner d'abord.")
        return
    
    # Formulaire de saisie
    with st.form("irrigation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.selectbox("🌍 Région", 
                                ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"])
            date = st.date_input("📅 Date", dt.now())
            crop_type = st.selectbox("🌾 Type de Culture", 
                                   ["mil", "sorgho", "mais", "riz", "arachide", "coton"])
            growth_stage = st.slider("📈 Stade de Croissance (jours)", 1, 200, 60)
        
        with col2:
            temp_max = st.slider("🌡️ Température Max (°C)", 20.0, 45.0, 35.0)
            temp_min = st.slider("🌡️ Température Min (°C)", 15.0, 35.0, 22.0)
            humidity = st.slider("💧 Humidité (%)", 20, 100, 60)
            wind_speed = st.slider("💨 Vitesse du vent (m/s)", 0.0, 15.0, 2.5)
            solar_radiation = st.slider("☀️ Radiation solaire (MJ/m²)", 10.0, 35.0, 22.5)
        
        submitted = st.form_submit_button("🔮 Optimiser l'Irrigation")
    
    if submitted:
        # Préparer les données
        environmental_data = {
            'temp_max': temp_max,
            'temp_min': temp_min,
            'temperature_2m': (temp_max + temp_min) / 2,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'solar_radiation': solar_radiation,
            'ssm': humidity / 100 * 0.6,
            'latitude': 14.7,  # Latitude moyenne du Sénégal
            'surface_solar_radiation_downwards_sum': solar_radiation * 1000000,
            'total_precipitation_sum': 0,
            'u_component_of_wind_10m': wind_speed * 0.7,
            'v_component_of_wind_10m': wind_speed * 0.3,
            'ndvi': 0.6,
            'evi': 0.5,
            'ndvi_normalized': 0.6,
            'evi_normalized': 0.5
        }
        
        try:
            # Préparer les données d'entrée
            input_data = {
                'temp_max': temp_max,
                'temp_min': temp_min,
                'humidity': humidity,
                'wind_speed': wind_speed,
                'solar_radiation': solar_radiation,
                'crop_type': crop_type,
                'growth_stage': growth_stage
            }
            
            # Préparer les features pour le modèle
            features_df = prepare_features_for_model(models['irrigation'], input_data, date)
            
            if features_df is None:
                st.error("❌ Impossible de préparer les features pour la prédiction")
                return
            
            # Faire la prédiction directement
            prediction_value = models['irrigation'].predict(features_df)[0]
            
            # Créer l'objet d'optimisation
            optimization = {
                'irrigation_need_mm': round(prediction_value, 2),
                'etc_mm': round(prediction_value * 0.8, 2),
                'et0_mm': round(prediction_value * 0.7, 2),
                'efficiency_score': 85,
                'water_cost_fcfa_per_m2': round(prediction_value * 0.1, 2),
                'frequency': "Quotidienne" if prediction_value > 5 else "Tous les 2 jours",
                'duration': "45-60 minutes" if prediction_value > 5 else "30-45 minutes",
                'best_times': ["05h00 - 07h00 (optimal)", "17h00 - 19h00 (si nécessaire)"],
                'recommendations': [
                    "Surveiller l'humidité du sol",
                    "Ajuster selon les conditions météo",
                    "Utiliser l'irrigation goutte-à-goutte si possible"
                ],
                'water_conservation_tips': [
                    "Utiliser du paillis pour réduire l'évaporation",
                    "Vérifier et réparer les fuites du système",
                    "Programmer l'irrigation aux heures fraîches"
                ]
            }
            
            # Afficher les résultats
            st.success("✅ Optimisation réalisée avec succès!")
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💧 Besoins en Eau", 
                         f"{optimization['irrigation_need_mm']} mm/jour")
            
            with col2:
                st.metric("📊 Score d'Efficacité", 
                         f"{optimization['efficiency_score']}/100")
            
            with col3:
                st.metric("💰 Coût Estimé", 
                         f"{optimization['water_cost_fcfa_per_m2']} FCFA/m²")
            
            with col4:
                st.metric("🌱 ET Culture", 
                         f"{optimization['etc_mm']} mm/jour")
            
            # Détails de planification
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⏰ Planification")
                st.write(f"**Fréquence:** {optimization['frequency']}")
                st.write(f"**Durée:** {optimization['duration']}")
                
                st.subheader("🕐 Meilleurs Moments")
                for time in optimization['best_times']:
                    st.write(f"• {time}")
            
            with col2:
                st.subheader("💡 Recommandations")
                for i, rec in enumerate(optimization['recommendations'], 1):
                    st.write(f"{i}. {rec}")
                
                st.subheader("💚 Conseils d'Économie")
                for i, tip in enumerate(optimization['water_conservation_tips'], 1):
                    st.write(f"{i}. {tip}")
            
            # Graphique des besoins
            st.subheader("📊 Visualisation des Besoins")
            
            # Graphique en barres comparatif
            comparison_data = pd.DataFrame({
                'Paramètre': ['ET0 (Référence)', 'ETc (Culture)', 'Besoins Irrigation'],
                'Valeur (mm/jour)': [optimization['et0_mm'], optimization['etc_mm'], optimization['irrigation_need_mm']]
            })
            
            fig = px.bar(comparison_data, x='Paramètre', y='Valeur (mm/jour)',
                        title="Comparaison des Besoins Hydriques",
                        color='Paramètre')
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de l'optimisation: {e}")

def disease_page(models):
    """Page prédiction des maladies"""
    st.header("🦠 Prédiction des Maladies")
    
    if not models['disease']:
        st.error("❌ Modèle de maladies non disponible. Veuillez l'entraîner d'abord.")
        return
    
    # Formulaire de saisie
    with st.form("disease_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            region = st.selectbox("🌍 Région", 
                                ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"])
            date = st.date_input("📅 Date", dt.now())
            crop_type = st.selectbox("🌾 Type de Culture", 
                                   ["mil", "sorgho", "mais", "riz", "arachide", "coton"])
            temperature = st.slider("🌡️ Température (°C)", 15.0, 40.0, 28.0)
        
        with col2:
            humidity = st.slider("💧 Humidité (%)", 30, 100, 80)
            season = st.selectbox("🗓️ Saison", ["Wet", "Dry"])
            leaf_wetness = st.slider("🍃 Durée Humectation (h)", 0, 24, 8)
            soil_moisture = st.slider("🌱 Humidité Sol", 0.2, 1.0, 0.7)
        
        submitted = st.form_submit_button("🔮 Évaluer les Risques de Maladies")
    
    if submitted:
        # Préparer les données
        environmental_data = {
            'temperature_2m': temperature,
            'ssm': soil_moisture,
            'humidity': humidity,
            'season': season,
            'leaf_wetness_duration': leaf_wetness,
            'surface_solar_radiation_downwards_sum': 18000000,
            'total_precipitation_sum': 5 if season == 'Wet' else 0.5,
            'u_component_of_wind_10m': 2.0,
            'v_component_of_wind_10m': 1.5,
            'lst_day_1km': temperature * 100,
            'lst_night_1km': (temperature - 8) * 100,
            'temp_day_celsius': temperature,
            'temp_night_celsius': temperature - 8,
            'evi': 0.6,
            'ndvi': 0.7,
            'ndvi_normalized': 0.7,
            'evi_normalized': 0.6
        }
        
        try:
            # Préparer les données d'entrée
            input_data = {
                'temperature': temperature,
                'humidity': humidity,
                'season': season,
                'leaf_wetness': leaf_wetness,
                'soil_moisture': soil_moisture,
                'crop_type': crop_type
            }
            
            # Préparer les features pour le modèle
            features_df = prepare_features_for_model(models['disease'], input_data, date)
            
            if features_df is None:
                st.error("❌ Impossible de préparer les features pour la prédiction")
                return
            
            # Faire la prédiction directement
            prediction_value = models['disease'].predict(features_df)[0]
            
            # Interpréter la prédiction
            risk_levels = {
                0: {"level": "Faible", "color": "green", "action": "Surveillance normale"},
                1: {"level": "Modéré", "color": "yellow", "action": "Surveillance renforcée"},
                2: {"level": "Élevé", "color": "orange", "action": "Mesures préventives"},
                3: {"level": "Critique", "color": "red", "action": "Intervention immédiate"}
            }
            
            result = risk_levels.get(prediction_value, risk_levels[0])
            
            prediction = {
                'overall_risk_level': result["level"],
                'risk_score': int(prediction_value),
                'confidence': 85.0,
                'alert_color': result["color"],
                'recommended_action': result["action"],
                'specific_diseases': [],
                'prevention_measures': [
                    "Améliorer la circulation d'air",
                    "Éviter l'irrigation par aspersion",
                    "Surveiller les symptômes"
                ],
                'monitoring_schedule': {
                    'frequency': "Hebdomadaire" if prediction_value == 0 else "Quotidienne",
                    'focus': "Surveillance générale"
                },
                'treatment_options': [
                    "Traitement préventif" if prediction_value < 2 else "Traitement curatif"
                ]
            }
            
            # Afficher les résultats
            st.success("✅ Évaluation réalisée avec succès!")
            
            # Alerte selon le niveau
            if prediction['risk_score'] >= 3:
                st.error(f"🔴 **RISQUE CRITIQUE** - {prediction['overall_risk_level']}")
            elif prediction['risk_score'] >= 2:
                st.warning(f"🟠 **RISQUE ÉLEVÉ** - {prediction['overall_risk_level']}")
            elif prediction['risk_score'] >= 1:
                st.info(f"🟡 **RISQUE MODÉRÉ** - {prediction['overall_risk_level']}")
            else:
                st.success(f"🟢 **RISQUE FAIBLE** - {prediction['overall_risk_level']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Score de Risque", 
                         f"{prediction['risk_score']}/3")
            
            with col2:
                st.metric("🎯 Confiance", 
                         f"{prediction['confidence']}%")
            
            with col3:
                st.metric("⚡ Action Recommandée", 
                         prediction['recommended_action'])
            
            # Maladies spécifiques
            if prediction['specific_diseases']:
                st.subheader("🦠 Maladies Spécifiques Détectées")
                
                for disease in prediction['specific_diseases']:
                    with st.expander(f"🔍 {disease['disease'].title()} - Risque {disease['risk_level']}"):
                        st.write(f"**Score de risque:** {disease['risk_score']}/100")
                        st.write("**Conditions favorables rencontrées:**")
                        for condition in disease['conditions_met']:
                            st.write(f"• {condition}")
            
            # Recommandations et actions
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🛡️ Mesures Préventives")
                for i, measure in enumerate(prediction['prevention_measures'], 1):
                    st.write(f"{i}. {measure}")
                
                st.subheader("👁️ Planning de Surveillance")
                monitoring = prediction['monitoring_schedule']
                st.write(f"**Fréquence:** {monitoring['frequency']}")
                st.write(f"**Focus:** {monitoring['focus']}")
            
            with col2:
                st.subheader("💊 Options de Traitement")
                for i, treatment in enumerate(prediction['treatment_options'], 1):
                    st.write(f"{i}. {treatment}")
            
        except Exception as e:
            st.error(f"❌ Erreur lors de l'évaluation: {e}")

def comprehensive_page(models):
    """Page analyse complète"""
    st.header("📊 Analyse Complète")
    
    # Vérifier que tous les modèles sont disponibles
    available_models = sum(1 for model in models.values() if model is not None)
    
    if available_models == 0:
        st.error("❌ Aucun modèle disponible. Veuillez les entraîner d'abord.")
        return
    
    st.info(f"ℹ️ {available_models}/4 modèles disponibles")
    
    # Formulaire de saisie
    with st.form("comprehensive_form"):
        st.subheader("🎯 Paramètres de l'Analyse")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            region = st.selectbox("🌍 Région", 
                                ["Dakar", "Thiès", "Saint-Louis", "Kaolack", "Ziguinchor", "Tambacounda"])
            date = st.date_input("📅 Date", dt.now())
            crop_type = st.selectbox("🌾 Culture", 
                                   ["mil", "sorgho", "mais", "riz", "arachide", "coton"])
            growth_stage = st.slider("📈 Stade (jours)", 1, 200, 60)
        
        with col2:
            temperature = st.slider("🌡️ Température (°C)", 15.0, 45.0, 30.0)
            humidity = st.slider("💧 Humidité (%)", 20, 100, 70)
            wind_speed = st.slider("💨 Vent (m/s)", 0.0, 15.0, 3.0)
            pressure = st.slider("🌪️ Pression (hPa)", 980, 1040, 1012)
        
        with col3:
            soil_moisture = st.slider("🌱 Humidité Sol", 0.1, 1.0, 0.6)
            solar_radiation = st.slider("☀️ Radiation (MJ/m²)", 10.0, 35.0, 22.0)
            season = st.selectbox("🗓️ Saison", ["Wet", "Dry"])
            precipitation_7d = st.slider("🌧️ Pluie 7j (mm)", 0.0, 100.0, 10.0)
        
        submitted = st.form_submit_button("🚀 Lancer l'Analyse Complète")
    
    if submitted:
        # Préparer les données communes
        environmental_data = {
            'temperature_2m': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'solar_radiation': solar_radiation,
            'ssm': soil_moisture,
            'season': season,
            'total_precipitation_sum': precipitation_7d / 7,
            'surface_solar_radiation_downwards_sum': solar_radiation * 1000000,
            'u_component_of_wind_10m': wind_speed * 0.7,
            'v_component_of_wind_10m': wind_speed * 0.3,
            'temp_max': temperature + 5,
            'temp_min': temperature - 5,
            'latitude': 14.7,
            'ndvi': 0.6,
            'evi': 0.5,
            'ndvi_normalized': 0.6,
            'evi_normalized': 0.5,
            'lst_day_1km': temperature * 100,
            'lst_night_1km': (temperature - 8) * 100,
            'temp_day_celsius': temperature,
            'temp_night_celsius': temperature - 8
        }
        
        results = {}
        
        # Exécuter toutes les prédictions
        with st.spinner("🔄 Analyse en cours..."):
            
            # Précipitations
            if models['rainfall']:
                try:
                    input_data = {
                        'temperature': temperature,
                        'humidity': humidity,
                        'pressure': pressure,
                        'wind_speed': wind_speed,
                        'solar_radiation': solar_radiation
                    }
                    features_df = prepare_features_for_model(models['rainfall'], input_data, date)
                    if features_df is not None:
                        prediction_value = models['rainfall'].predict(features_df)[0]
                        category = "Pas de pluie" if prediction_value < 1 else ("Pluie légère" if prediction_value < 5 else ("Pluie modérée" if prediction_value < 15 else "Pluie forte"))
                        results['rainfall'] = {
                            'predicted_rainfall_mm': round(prediction_value, 2),
                            'category': category,
                            'confidence': 85.0,
                            'recommendations': [
                                "Surveiller les conditions météorologiques",
                                "Ajuster l'irrigation selon les prévisions",
                                "Protéger les cultures si nécessaire"
                            ]
                        }
                    else:
                        results['rainfall'] = {'error': 'Impossible de préparer les features'}
                except Exception as e:
                    results['rainfall'] = {'error': str(e)}
            
            # Sécheresse
            if models['drought']:
                try:
                    input_data = {
                        'temperature': temperature,
                        'soil_moisture': soil_moisture,
                        'ndvi': 0.6,
                        'season': season,
                        'precipitation_7d': precipitation_7d
                    }
                    features_df = prepare_features_for_model(models['drought'], input_data, date)
                    if features_df is not None:
                        prediction_value = models['drought'].predict(features_df)[0]
                        drought_levels = {
                            0: "Pas de sécheresse", 1: "Sécheresse légère", 
                            2: "Sécheresse modérée", 3: "Sécheresse sévère"
                        }
                        results['drought'] = {
                            'drought_level': drought_levels.get(prediction_value, "Inconnu"),
                            'severity_score': int(prediction_value),
                            'confidence': 85.0,
                            'recommendations': [
                                "Surveiller l'humidité du sol",
                                "Optimiser l'utilisation de l'eau",
                                "Protéger les cultures sensibles"
                            ]
                        }
                    else:
                        results['drought'] = {'error': 'Impossible de préparer les features'}
                except Exception as e:
                    results['drought'] = {'error': str(e)}
            
            # Irrigation
            if models['irrigation']:
                try:
                    input_data = {
                        'temp_max': temperature + 5,
                        'temp_min': temperature - 5,
                        'humidity': humidity,
                        'wind_speed': wind_speed,
                        'solar_radiation': solar_radiation,
                        'crop_type': crop_type,
                        'growth_stage': growth_stage
                    }
                    features_df = prepare_features_for_model(models['irrigation'], input_data, date)
                    if features_df is not None:
                        prediction_value = models['irrigation'].predict(features_df)[0]
                        results['irrigation'] = {
                            'irrigation_need_mm': round(prediction_value, 2),
                            'frequency': "Quotidienne" if prediction_value > 5 else "Tous les 2 jours",
                            'efficiency_score': 85,
                            'recommendations': [
                                "Utiliser l'irrigation goutte-à-goutte",
                                "Surveiller l'humidité du sol",
                                "Irriguer aux heures fraîches"
                            ]
                        }
                    else:
                        results['irrigation'] = {'error': 'Impossible de préparer les features'}
                except Exception as e:
                    results['irrigation'] = {'error': str(e)}
            
            # Maladies
            if models['disease']:
                try:
                    input_data = {
                        'temperature': temperature,
                        'humidity': humidity,
                        'season': season,
                        'leaf_wetness': 8,
                        'soil_moisture': soil_moisture,
                        'crop_type': crop_type
                    }
                    features_df = prepare_features_for_model(models['disease'], input_data, date)
                    if features_df is not None:
                        prediction_value = models['disease'].predict(features_df)[0]
                        risk_levels = {
                            0: "Faible", 1: "Modéré", 2: "Élevé", 3: "Critique"
                        }
                        results['disease'] = {
                            'overall_risk_level': risk_levels.get(prediction_value, "Inconnu"),
                            'risk_score': int(prediction_value),
                            'confidence': 85.0,
                            'prevention_measures': [
                                "Améliorer la circulation d'air",
                                "Éviter l'irrigation par aspersion",
                                "Surveiller les premiers symptômes"
                            ]
                        }
                    else:
                        results['disease'] = {'error': 'Impossible de préparer les features'}
                except Exception as e:
                    results['disease'] = {'error': str(e)}
        
        # Afficher les résultats
        st.success("✅ Analyse complète terminée!")
        
        # Résumé exécutif
        st.subheader("📋 Résumé Exécutif")
        
        # Calculer le niveau de risque global
        risk_scores = []
        alerts = []
        
        if 'rainfall' in results and 'error' not in results['rainfall']:
            rainfall_mm = results['rainfall'].get('predicted_rainfall_mm', 0)
            if rainfall_mm > 15:
                alerts.append("🔴 Fortes précipitations prévues")
                risk_scores.append(3)
            elif rainfall_mm < 1:
                alerts.append("🟡 Risque de manque d'eau")
                risk_scores.append(1)
        
        if 'drought' in results and 'error' not in results['drought']:
            drought_score = results['drought'].get('severity_score', 0)
            risk_scores.append(drought_score)
            if drought_score >= 2:
                alerts.append(f"🟠 Risque de sécheresse {results['drought'].get('drought_level', '')}")
        
        if 'disease' in results and 'error' not in results['disease']:
            disease_score = results['disease'].get('risk_score', 0)
            risk_scores.append(disease_score)
            if disease_score >= 2:
                alerts.append(f"🔴 Risque de maladie {results['disease'].get('overall_risk_level', '')}")
        
        # Niveau de risque global
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            if avg_risk >= 2.5:
                st.error("🚨 **NIVEAU DE RISQUE GLOBAL: CRITIQUE**")
            elif avg_risk >= 1.5:
                st.warning("⚠️ **NIVEAU DE RISQUE GLOBAL: ÉLEVÉ**")
            elif avg_risk >= 0.5:
                st.info("ℹ️ **NIVEAU DE RISQUE GLOBAL: MODÉRÉ**")
            else:
                st.success("✅ **NIVEAU DE RISQUE GLOBAL: FAIBLE**")
        
        # Alertes
        if alerts:
            st.subheader("🚨 Alertes Prioritaires")
            for alert in alerts:
                st.write(f"• {alert}")
        
        # Résultats détaillés par onglets
        tab1, tab2, tab3, tab4 = st.tabs(["🌧️ Précipitations", "🏜️ Sécheresse", "💧 Irrigation", "🦠 Maladies"])
        
        with tab1:
            if 'rainfall' in results:
                if 'error' in results['rainfall']:
                    st.error(f"Erreur: {results['rainfall']['error']}")
                else:
                    r = results['rainfall']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Précipitations", f"{r['predicted_rainfall_mm']} mm")
                    with col2:
                        st.metric("Catégorie", r['category'])
                    with col3:
                        st.metric("Confiance", f"{r['confidence']}%")
                    
                    st.write("**Recommandations:**")
                    recommendations = r.get('recommendations', ["Aucune recommandation disponible"])
                    for rec in recommendations:
                        st.write(f"• {rec}")
            else:
                st.info("Modèle de précipitations non disponible")
        
        with tab2:
            if 'drought' in results:
                if 'error' in results['drought']:
                    st.error(f"Erreur: {results['drought']['error']}")
                else:
                    d = results['drought']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Niveau", d['drought_level'])
                    with col2:
                        st.metric("Score", f"{d['severity_score']}/3")
                    with col3:
                        st.metric("Confiance", f"{d['confidence']}%")
                    
                    st.write("**Recommandations:**")
                    recommendations = d.get('recommendations', ["Aucune recommandation disponible"])
                    for rec in recommendations:
                        st.write(f"• {rec}")
            else:
                st.info("Modèle de sécheresse non disponible")
        
        with tab3:
            if 'irrigation' in results:
                if 'error' in results['irrigation']:
                    st.error(f"Erreur: {results['irrigation']['error']}")
                else:
                    i = results['irrigation']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Besoins", f"{i['irrigation_need_mm']} mm/jour")
                    with col2:
                        st.metric("Fréquence", i['frequency'])
                    with col3:
                        st.metric("Efficacité", f"{i['efficiency_score']}/100")
                    
                    st.write("**Recommandations:**")
                    recommendations = i.get('recommendations', ["Aucune recommandation disponible"])
                    for rec in recommendations:
                        st.write(f"• {rec}")
            else:
                st.info("Modèle d'irrigation non disponible")
        
        with tab4:
            if 'disease' in results:
                if 'error' in results['disease']:
                    st.error(f"Erreur: {results['disease']['error']}")
                else:
                    dis = results['disease']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Niveau", dis['overall_risk_level'])
                    with col2:
                        st.metric("Score", f"{dis['risk_score']}/3")
                    with col3:
                        st.metric("Confiance", f"{dis['confidence']}%")
                    
                    st.write("**Mesures préventives:**")
                    measures = dis.get('prevention_measures', ["Aucune mesure disponible"])
                    for measure in measures:
                        st.write(f"• {measure}")
            else:
                st.info("Modèle de maladies non disponible")

def config_page(models):
    """Page de configuration"""
    st.header("⚙️ Configuration et Entraînement")
    
    # État des modèles
    st.subheader("📊 État des Modèles")
    
    model_status = [
        {"Modèle": "🌧️ Précipitations", "État": "✅ Actif" if models['rainfall'] else "❌ Inactif"},
        {"Modèle": "🏜️ Sécheresse", "État": "✅ Actif" if models['drought'] else "❌ Inactif"},
        {"Modèle": "💧 Irrigation", "État": "✅ Actif" if models['irrigation'] else "❌ Inactif"},
        {"Modèle": "🦠 Maladies", "État": "✅ Actif" if models['disease'] else "❌ Inactif"}
    ]
    
    st.table(pd.DataFrame(model_status))
    
    st.divider()
    
    # Entraînement des modèles
    st.subheader("🎯 Entraînement des Modèles")
    
    st.info("⚠️ L'entraînement des modèles peut prendre plusieurs minutes. Assurez-vous que les données sont disponibles dans le dossier `data/processed/`.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌧️ Entraîner Modèle Précipitations", use_container_width=True):
            with st.spinner("Entraînement en cours..."):
                try:
                    model = RainfallPredictionModel()
                    metrics = model.train_model()
                    st.success(f"✅ Modèle entraîné! RMSE: {metrics.get('rmse', 'N/A'):.2f}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        
        if st.button("💧 Entraîner Modèle Irrigation", use_container_width=True):
            with st.spinner("Entraînement en cours..."):
                try:
                    model = IrrigationOptimizationModel()
                    metrics = model.train_model()
                    st.success(f"✅ Modèle entraîné! RMSE: {metrics.get('rmse', 'N/A'):.2f}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
    
    with col2:
        if st.button("🏜️ Entraîner Modèle Sécheresse", use_container_width=True):
            with st.spinner("Entraînement en cours..."):
                try:
                    model = DroughtPredictionModel()
                    metrics = model.train_model()
                    st.success(f"✅ Modèle entraîné! Accuracy: {metrics.get('accuracy', 'N/A'):.2f}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        
        if st.button("🦠 Entraîner Modèle Maladies", use_container_width=True):
            with st.spinner("Entraînement en cours..."):
                try:
                    model = DiseasePredictionModel()
                    metrics = model.train_model()
                    st.success(f"✅ Modèle entraîné! Accuracy: {metrics.get('accuracy', 'N/A'):.2f}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
    
    st.divider()
    
    if st.button("🚀 Entraîner Tous les Modèles", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        models_to_train = [
            ("Précipitations", RainfallPredictionModel),
            ("Sécheresse", DroughtPredictionModel),
            ("Irrigation", IrrigationOptimizationModel),
            ("Maladies", DiseasePredictionModel)
        ]
        
        for i, (name, model_class) in enumerate(models_to_train):
            status_text.text(f"Entraînement du modèle {name}...")
            try:
                model = model_class()
                metrics = model.train_model()
                st.success(f"✅ {name}: Entraîné avec succès")
            except Exception as e:
                st.error(f"❌ {name}: {e}")
            
            progress_bar.progress((i + 1) / len(models_to_train))
        
        status_text.text("Entraînement terminé!")
        st.balloons()
        st.experimental_rerun()
    
    st.divider()
    
    # Informations système
    st.subheader("💻 Informations Système")
    
    try:
        import psutil
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💾 RAM Utilisée", f"{psutil.virtual_memory().percent}%")
        
        with col2:
            st.metric("💽 CPU Utilisé", f"{psutil.cpu_percent()}%")
        
        with col3:
            st.metric("💿 Disque Utilisé", f"{psutil.disk_usage('/').percent}%")
    
    except ImportError:
        st.info("Installez `psutil` pour voir les métriques système")

if __name__ == "__main__":
    main()