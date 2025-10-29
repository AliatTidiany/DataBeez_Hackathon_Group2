#!/usr/bin/env python3
"""
create_dashboard.py

Création d'un dashboard interactif pour les données GEE du Sénégal
- Visualisations des données satellitaires
- Cartes interactives
- Analyses temporelles
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from pathlib import Path
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration des chemins
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "gee_senegal"
OUTPUT_DIR = BASE_DIR / "data" / "gee_senegal" / "analysis"

# Coordonnées des régions du Sénégal
SENEGAL_REGIONS = {
    "Dakar": {"lat": 14.7167, "lon": -17.4677},
    "Thiès": {"lat": 14.7910, "lon": -16.9250},
    "Saint-Louis": {"lat": 16.0179, "lon": -16.4896},
    "Kaolack": {"lat": 14.1469, "lon": -16.0726},
    "Ziguinchor": {"lat": 12.5833, "lon": -16.2719},
    "Tambacounda": {"lat": 13.7707, "lon": -13.6673},
    "Fatick": {"lat": 14.3396, "lon": -16.4114},
    "Diourbel": {"lat": 14.6558, "lon": -16.2334},
    "Louga": {"lat": 15.6144, "lon": -16.2286},
    "Matam": {"lat": 15.6600, "lon": -13.2550},
    "Kolda": {"lat": 12.8833, "lon": -14.9500},
    "Kaffrine": {"lat": 14.1050, "lon": -15.5500},
    "Sédhiou": {"lat": 12.7089, "lon": -15.5561},
    "Kédougou": {"lat": 12.5556, "lon": -12.1744}
}

def load_consolidated_data():
    """Charge toutes les données consolidées"""
    print("📊 Chargement des données consolidées...")
    
    processed_dir = DATA_DIR / "processed"
    if not processed_dir.exists():
        processed_dir = DATA_DIR
    
    consolidated_files = list(processed_dir.glob("*_consolidated_data.csv"))
    
    if not consolidated_files:
        print("❌ Aucun fichier consolidé trouvé")
        return None
    
    all_data = []
    
    for file_path in consolidated_files:
        region_name = file_path.stem.replace('_consolidated_data', '').title()
        
        try:
            df = pd.read_csv(file_path)
            df['region'] = region_name
            df['date'] = pd.to_datetime(df['date'])
            
            # Ajouter les coordonnées
            if region_name in SENEGAL_REGIONS:
                df['latitude'] = SENEGAL_REGIONS[region_name]['lat']
                df['longitude'] = SENEGAL_REGIONS[region_name]['lon']
            
            all_data.append(df)
            print(f"  ✅ {region_name}: {len(df)} enregistrements")
            
        except Exception as e:
            print(f"  ❌ Erreur {file_path.name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"📊 Total: {len(combined_df):,} enregistrements pour {len(all_data)} régions")
        return combined_df
    
    return None

def create_temperature_analysis(df):
    """Crée l'analyse des températures"""
    print("🌡️ Création de l'analyse des températures...")
    
    # Graphique des températures moyennes par région
    temp_cols = [col for col in df.columns if 'temperature' in col.lower() and df[col].notna().sum() > 0]
    
    if not temp_cols:
        print("⚠️ Aucune donnée de température disponible")
        return None
    
    # Utiliser la première colonne de température disponible
    temp_col = temp_cols[0]
    
    # Moyennes mensuelles par région
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_temp = df.groupby(['region', 'year_month'])[temp_col].mean().reset_index()
    monthly_temp['date'] = monthly_temp['year_month'].dt.to_timestamp()
    
    fig = px.line(
        monthly_temp, 
        x='date', 
        y=temp_col, 
        color='region',
        title='Évolution des Températures par Région',
        labels={temp_col: 'Température (°C)', 'date': 'Date'}
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def create_precipitation_analysis(df):
    """Crée l'analyse des précipitations"""
    print("🌧️ Création de l'analyse des précipitations...")
    
    precip_cols = [col for col in df.columns if 'precipitation' in col.lower() and df[col].notna().sum() > 0]
    
    if not precip_cols:
        print("⚠️ Aucune donnée de précipitation disponible")
        return None
    
    precip_col = precip_cols[0]
    
    # Précipitations cumulées mensuelles
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_precip = df.groupby(['region', 'year_month'])[precip_col].sum().reset_index()
    monthly_precip['date'] = monthly_precip['year_month'].dt.to_timestamp()
    
    fig = px.bar(
        monthly_precip.tail(168),  # Derniers 12 mois pour 14 régions
        x='date',
        y=precip_col,
        color='region',
        title='Précipitations Mensuelles par Région',
        labels={precip_col: 'Précipitations (mm)', 'date': 'Date'}
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        barmode='group'
    )
    
    return fig

def create_vegetation_analysis(df):
    """Crée l'analyse de la végétation"""
    print("🌱 Création de l'analyse de la végétation...")
    
    ndvi_cols = [col for col in df.columns if 'ndvi' in col.lower() and df[col].notna().sum() > 0]
    
    if not ndvi_cols:
        print("⚠️ Aucune donnée NDVI disponible")
        return None
    
    ndvi_col = ndvi_cols[0]
    
    # NDVI moyen par région et par saison
    df['season'] = df['date'].dt.month.map(lambda x: 'Saison sèche' if x in [11, 12, 1, 2, 3, 4, 5] else 'Saison des pluies')
    
    seasonal_ndvi = df.groupby(['region', 'season'])[ndvi_col].mean().reset_index()
    
    fig = px.bar(
        seasonal_ndvi,
        x='region',
        y=ndvi_col,
        color='season',
        title='NDVI Moyen par Région et Saison',
        labels={ndvi_col: 'NDVI', 'region': 'Région'}
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        xaxis_tickangle=-45
    )
    
    return fig

def create_correlation_matrix(df):
    """Crée une matrice de corrélation"""
    print("🔗 Création de la matrice de corrélation...")
    
    # Sélectionner les colonnes numériques
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # Exclure les colonnes d'identifiants
    exclude_cols = ['latitude', 'longitude']
    numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(numeric_cols) < 2:
        print("⚠️ Pas assez de variables numériques pour la corrélation")
        return None
    
    # Calculer la matrice de corrélation
    corr_matrix = df[numeric_cols].corr()
    
    fig = px.imshow(
        corr_matrix,
        title='Matrice de Corrélation des Variables',
        color_continuous_scale='RdBu',
        aspect='auto'
    )
    
    fig.update_layout(height=600)
    
    return fig

def create_interactive_map(df):
    """Crée une carte interactive"""
    print("🗺️ Création de la carte interactive...")
    
    # Données moyennes par région
    region_stats = df.groupby('region').agg({
        'latitude': 'first',
        'longitude': 'first',
        **{col: 'mean' for col in df.select_dtypes(include=[np.number]).columns 
           if col not in ['latitude', 'longitude']}
    }).reset_index()
    
    # Créer la carte centrée sur le Sénégal
    m = folium.Map(
        location=[14.5, -14.5],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Ajouter les marqueurs pour chaque région
    for _, row in region_stats.iterrows():
        # Créer le popup avec les informations
        popup_text = f"<b>{row['region']}</b><br>"
        
        # Ajouter les statistiques disponibles
        for col in region_stats.columns:
            if col not in ['region', 'latitude', 'longitude'] and pd.notna(row[col]):
                popup_text += f"{col}: {row[col]:.2f}<br>"
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=row['region'],
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(m)
    
    return m

def create_time_series_dashboard(df):
    """Crée un dashboard de séries temporelles"""
    print("📈 Création du dashboard de séries temporelles...")
    
    # Créer des sous-graphiques
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Température', 'Précipitations', 'NDVI', 'Données Disponibles'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Données mensuelles
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_data = df.groupby('year_month').agg({
        col: 'mean' for col in df.select_dtypes(include=[np.number]).columns
    }).reset_index()
    monthly_data['date'] = monthly_data['year_month'].dt.to_timestamp()
    
    # Graphique 1: Température
    temp_cols = [col for col in monthly_data.columns if 'temperature' in col.lower()]
    if temp_cols:
        fig.add_trace(
            go.Scatter(x=monthly_data['date'], y=monthly_data[temp_cols[0]], 
                      name='Température', line=dict(color='red')),
            row=1, col=1
        )
    
    # Graphique 2: Précipitations
    precip_cols = [col for col in monthly_data.columns if 'precipitation' in col.lower()]
    if precip_cols:
        fig.add_trace(
            go.Scatter(x=monthly_data['date'], y=monthly_data[precip_cols[0]], 
                      name='Précipitations', line=dict(color='blue')),
            row=1, col=2
        )
    
    # Graphique 3: NDVI
    ndvi_cols = [col for col in monthly_data.columns if 'ndvi' in col.lower()]
    if ndvi_cols:
        fig.add_trace(
            go.Scatter(x=monthly_data['date'], y=monthly_data[ndvi_cols[0]], 
                      name='NDVI', line=dict(color='green')),
            row=2, col=1
        )
    
    # Graphique 4: Disponibilité des données
    data_counts = df.groupby('year_month').size().reset_index(name='count')
    data_counts['date'] = data_counts['year_month'].dt.to_timestamp()
    
    fig.add_trace(
        go.Scatter(x=data_counts['date'], y=data_counts['count'], 
                  name='Nb Enregistrements', line=dict(color='purple')),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        title_text="Dashboard des Séries Temporelles - Sénégal",
        showlegend=False
    )
    
    return fig

def save_dashboard_files(figures, interactive_map):
    """Sauvegarde tous les fichiers du dashboard"""
    print("💾 Sauvegarde des fichiers du dashboard...")
    
    # Créer le dossier de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    # Sauvegarder les graphiques
    for name, fig in figures.items():
        if fig is not None:
            html_file = OUTPUT_DIR / f"{name}.html"
            fig.write_html(str(html_file))
            saved_files.append(html_file)
            print(f"  ✅ {html_file.name}")
    
    # Sauvegarder la carte
    if interactive_map is not None:
        map_file = OUTPUT_DIR / "senegal_regions_map.html"
        interactive_map.save(str(map_file))
        saved_files.append(map_file)
        print(f"  ✅ {map_file.name}")
    
    return saved_files

def generate_dashboard_index(saved_files):
    """Génère une page d'index pour le dashboard"""
    print("📋 Génération de la page d'index...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard GEE Sénégal - DataBeez</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .dashboard-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .dashboard-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .dashboard-card h3 {{ color: #2c3e50; margin-top: 0; }}
            .dashboard-card a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
            .dashboard-card a:hover {{ text-decoration: underline; }}
            .stats {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌾 Dashboard GEE Sénégal - DataBeez</h1>
            <p>Visualisations interactives des données satellitaires</p>
            <div class="stats">
                <strong>Généré le:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
            </div>
        </div>
        
        <div class="dashboard-grid">
    """
    
    # Descriptions des visualisations
    descriptions = {
        "temperature_analysis.html": {
            "title": "🌡️ Analyse des Températures",
            "description": "Évolution temporelle des températures par région"
        },
        "precipitation_analysis.html": {
            "title": "🌧️ Analyse des Précipitations", 
            "description": "Précipitations mensuelles et saisonnières"
        },
        "vegetation_analysis.html": {
            "title": "🌱 Analyse de la Végétation",
            "description": "Indices NDVI et santé de la végétation"
        },
        "correlation_matrix.html": {
            "title": "🔗 Matrice de Corrélation",
            "description": "Corrélations entre variables climatiques"
        },
        "time_series_dashboard.html": {
            "title": "📈 Séries Temporelles",
            "description": "Dashboard complet des tendances temporelles"
        },
        "senegal_regions_map.html": {
            "title": "🗺️ Carte Interactive",
            "description": "Carte du Sénégal avec données par région"
        }
    }
    
    # Ajouter les cartes pour chaque fichier
    for file_path in saved_files:
        file_name = file_path.name
        if file_name in descriptions:
            desc = descriptions[file_name]
            html_content += f"""
            <div class="dashboard-card">
                <h3>{desc['title']}</h3>
                <p>{desc['description']}</p>
                <a href="{file_name}" target="_blank">Ouvrir la visualisation →</a>
            </div>
            """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Sauvegarder la page d'index
    index_file = OUTPUT_DIR / "dashboard_senegal_gee.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Page d'index créée: {index_file}")
    return index_file

def main():
    """Fonction principale"""
    print("📊 Création du Dashboard GEE Sénégal")
    print("=" * 50)
    
    try:
        # Charger les données
        df = load_consolidated_data()
        if df is None:
            return 1
        
        # Créer les visualisations
        figures = {
            'temperature_analysis': create_temperature_analysis(df),
            'precipitation_analysis': create_precipitation_analysis(df),
            'vegetation_analysis': create_vegetation_analysis(df),
            'correlation_matrix': create_correlation_matrix(df),
            'time_series_dashboard': create_time_series_dashboard(df)
        }
        
        # Créer la carte interactive
        interactive_map = create_interactive_map(df)
        
        # Sauvegarder tous les fichiers
        saved_files = save_dashboard_files(figures, interactive_map)
        
        # Générer la page d'index
        index_file = generate_dashboard_index(saved_files)
        
        print(f"\n🎉 Dashboard créé avec succès!")
        print(f"📁 Dossier de sortie: {OUTPUT_DIR}")
        print(f"🌐 Page principale: {index_file}")
        print(f"📊 {len(saved_files)} visualisations créées")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du dashboard: {e}")
        return 1

if __name__ == "__main__":
    exit(main())