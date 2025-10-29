#!/usr/bin/env python3
"""
analyze_gee_data.py

Analyse avancée des données Google Earth Engine pour le Sénégal
- Analyses statistiques détaillées
- Détection de tendances
- Corrélations entre variables
- Génération de rapports
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "gee_senegal"
OUTPUT_DIR = BASE_DIR / "data" / "gee_senegal" / "analysis"

# Configuration des graphiques
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_all_data():
    """Charge toutes les données consolidées"""
    print("📊 Chargement des données pour analyse...")
    
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
            all_data.append(df)
            
        except Exception as e:
            print(f"  ❌ Erreur {file_path.name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"✅ Données chargées: {len(combined_df):,} enregistrements, {len(all_data)} régions")
        return combined_df
    
    return None

def analyze_data_availability(df):
    """Analyse la disponibilité des données"""
    print("🔍 Analyse de la disponibilité des données...")
    
    # Créer le dossier de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculer les statistiques de disponibilité
    availability_stats = {}
    
    for col in df.select_dtypes(include=[np.number]).columns:
        total_count = len(df)
        available_count = df[col].notna().sum()
        availability_pct = (available_count / total_count) * 100
        
        availability_stats[col] = {
            'total': total_count,
            'available': available_count,
            'missing': total_count - available_count,
            'availability_pct': availability_pct
        }
    
    # Créer un graphique de disponibilité
    fig, ax = plt.subplots(figsize=(12, 8))
    
    variables = list(availability_stats.keys())
    percentages = [availability_stats[var]['availability_pct'] for var in variables]
    
    bars = ax.barh(variables, percentages)
    
    # Colorer les barres selon le pourcentage
    for i, (bar, pct) in enumerate(zip(bars, percentages)):
        if pct >= 80:
            bar.set_color('green')
        elif pct >= 50:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    ax.set_xlabel('Pourcentage de Disponibilité (%)')
    ax.set_title('Disponibilité des Données par Variable')
    ax.set_xlim(0, 100)
    
    # Ajouter les pourcentages sur les barres
    for i, pct in enumerate(percentages):
        ax.text(pct + 1, i, f'{pct:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'data_availability.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  📊 Graphique sauvegardé: data_availability.png")
    
    return availability_stats

def analyze_temporal_trends(df):
    """Analyse les tendances temporelles"""
    print("📈 Analyse des tendances temporelles...")
    
    # Variables clés à analyser
    key_variables = []
    
    # Identifier les variables disponibles
    for pattern in ['temperature', 'precipitation', 'ndvi', 'evi']:
        matching_cols = [col for col in df.columns if pattern in col.lower() and df[col].notna().sum() > 100]
        if matching_cols:
            key_variables.append(matching_cols[0])
    
    if not key_variables:
        print("⚠️ Aucune variable clé trouvée pour l'analyse temporelle")
        return None
    
    # Créer des moyennes mensuelles
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_data = df.groupby('year_month')[key_variables].mean().reset_index()
    monthly_data['date'] = monthly_data['year_month'].dt.to_timestamp()
    
    # Créer le graphique
    fig, axes = plt.subplots(len(key_variables), 1, figsize=(15, 4*len(key_variables)))
    if len(key_variables) == 1:
        axes = [axes]
    
    for i, var in enumerate(key_variables):
        axes[i].plot(monthly_data['date'], monthly_data[var], linewidth=2)
        axes[i].set_title(f'Tendance Temporelle - {var}')
        axes[i].set_ylabel(var)
        axes[i].grid(True, alpha=0.3)
        
        # Ajouter une ligne de tendance
        x_numeric = np.arange(len(monthly_data))
        z = np.polyfit(x_numeric, monthly_data[var].dropna(), 1)
        p = np.poly1d(z)
        axes[i].plot(monthly_data['date'], p(x_numeric), "r--", alpha=0.8, label='Tendance')
        axes[i].legend()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'temporal_trends.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Graphique sauvegardé: temporal_trends.png")
    
    return monthly_data

def analyze_regional_differences(df):
    """Analyse les différences régionales"""
    print("🗺️ Analyse des différences régionales...")
    
    # Variables numériques disponibles
    numeric_vars = [col for col in df.select_dtypes(include=[np.number]).columns 
                   if df[col].notna().sum() > 100]
    
    if not numeric_vars:
        print("⚠️ Aucune variable numérique trouvée")
        return None
    
    # Prendre les 4 premières variables les plus complètes
    top_vars = sorted(numeric_vars, key=lambda x: df[x].notna().sum(), reverse=True)[:4]
    
    # Créer des moyennes par région
    regional_stats = df.groupby('region')[top_vars].mean()
    
    # Créer le graphique
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, var in enumerate(top_vars):
        regional_stats[var].plot(kind='bar', ax=axes[i])
        axes[i].set_title(f'Moyennes Régionales - {var}')
        axes[i].set_ylabel(var)
        axes[i].tick_params(axis='x', rotation=45)
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regional_differences.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  🗺️ Graphique sauvegardé: regional_differences.png")
    
    return regional_stats

def analyze_correlations(df):
    """Analyse les corrélations entre variables"""
    print("🔗 Analyse des corrélations...")
    
    # Sélectionner les variables numériques avec suffisamment de données
    numeric_vars = [col for col in df.select_dtypes(include=[np.number]).columns 
                   if df[col].notna().sum() > 500]
    
    if len(numeric_vars) < 2:
        print("⚠️ Pas assez de variables pour l'analyse de corrélation")
        return None
    
    # Calculer la matrice de corrélation
    corr_matrix = df[numeric_vars].corr()
    
    # Créer le heatmap
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    
    sns.heatmap(
        corr_matrix, 
        mask=mask,
        annot=True, 
        cmap='RdBu_r', 
        center=0,
        square=True,
        fmt='.2f',
        cbar_kws={"shrink": .8}
    )
    
    plt.title('Matrice de Corrélation des Variables')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  🔗 Graphique sauvegardé: correlation_matrix.png")
    
    # Identifier les corrélations fortes
    strong_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:
                strong_correlations.append({
                    'var1': corr_matrix.columns[i],
                    'var2': corr_matrix.columns[j],
                    'correlation': corr_val
                })
    
    return corr_matrix, strong_correlations

def analyze_seasonal_patterns(df):
    """Analyse les patterns saisonniers"""
    print("🌱 Analyse des patterns saisonniers...")
    
    # Ajouter des variables temporelles
    df['month'] = df['date'].dt.month
    df['season'] = df['month'].map(lambda x: 'Saison sèche' if x in [11, 12, 1, 2, 3, 4, 5] else 'Saison des pluies')
    
    # Variables à analyser
    seasonal_vars = []
    for pattern in ['temperature', 'precipitation', 'ndvi']:
        matching_cols = [col for col in df.columns if pattern in col.lower() and df[col].notna().sum() > 200]
        if matching_cols:
            seasonal_vars.append(matching_cols[0])
    
    if not seasonal_vars:
        print("⚠️ Aucune variable trouvée pour l'analyse saisonnière")
        return None
    
    # Créer le graphique
    fig, axes = plt.subplots(len(seasonal_vars), 1, figsize=(12, 4*len(seasonal_vars)))
    if len(seasonal_vars) == 1:
        axes = [axes]
    
    for i, var in enumerate(seasonal_vars):
        seasonal_data = df.groupby(['month', 'season'])[var].mean().reset_index()
        
        for season in seasonal_data['season'].unique():
            season_data = seasonal_data[seasonal_data['season'] == season]
            axes[i].plot(season_data['month'], season_data[var], 
                        marker='o', linewidth=2, label=season)
        
        axes[i].set_title(f'Pattern Saisonnier - {var}')
        axes[i].set_xlabel('Mois')
        axes[i].set_ylabel(var)
        axes[i].set_xticks(range(1, 13))
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'seasonal_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  🌱 Graphique sauvegardé: seasonal_patterns.png")
    
    return seasonal_data

def generate_analysis_report(df, availability_stats, strong_correlations):
    """Génère un rapport d'analyse détaillé"""
    print("📋 Génération du rapport d'analyse...")
    
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_records': len(df),
            'regions': df['region'].nunique(),
            'date_range': {
                'start': df['date'].min().isoformat(),
                'end': df['date'].max().isoformat()
            }
        },
        'data_availability': availability_stats,
        'strong_correlations': strong_correlations,
        'regional_summary': {},
        'key_findings': []
    }
    
    # Statistiques par région
    for region in df['region'].unique():
        region_data = df[df['region'] == region]
        report['regional_summary'][region] = {
            'records': len(region_data),
            'date_range': {
                'start': region_data['date'].min().isoformat(),
                'end': region_data['date'].max().isoformat()
            }
        }
    
    # Findings clés
    if availability_stats:
        best_var = max(availability_stats.keys(), key=lambda x: availability_stats[x]['availability_pct'])
        worst_var = min(availability_stats.keys(), key=lambda x: availability_stats[x]['availability_pct'])
        
        report['key_findings'].extend([
            f"Variable la plus complète: {best_var} ({availability_stats[best_var]['availability_pct']:.1f}%)",
            f"Variable la moins complète: {worst_var} ({availability_stats[worst_var]['availability_pct']:.1f}%)"
        ])
    
    if strong_correlations:
        report['key_findings'].append(f"{len(strong_correlations)} corrélations fortes détectées (|r| > 0.7)")
    
    # Sauvegarder le rapport
    report_file = OUTPUT_DIR / 'analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Créer aussi un rapport markdown
    md_content = f"""# Rapport d'Analyse GEE Sénégal

**Généré le:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}

## 📊 Résumé des Données

- **Enregistrements totaux:** {len(df):,}
- **Régions:** {df['region'].nunique()}
- **Période:** {df['date'].min().strftime('%Y-%m-%d')} à {df['date'].max().strftime('%Y-%m-%d')}

## 🔍 Disponibilité des Données

| Variable | Disponibilité | Enregistrements |
|----------|---------------|-----------------|
"""
    
    if availability_stats:
        for var, stats in sorted(availability_stats.items(), 
                                key=lambda x: x[1]['availability_pct'], reverse=True):
            md_content += f"| {var} | {stats['availability_pct']:.1f}% | {stats['available']:,} |\n"
    
    md_content += f"""
## 🔗 Corrélations Fortes

"""
    
    if strong_correlations:
        for corr in strong_correlations:
            md_content += f"- **{corr['var1']}** ↔ **{corr['var2']}**: r = {corr['correlation']:.3f}\n"
    else:
        md_content += "Aucune corrélation forte détectée (|r| > 0.7)\n"
    
    md_content += f"""
## 📈 Graphiques Générés

- `data_availability.png` - Disponibilité des données par variable
- `temporal_trends.png` - Tendances temporelles des variables clés
- `regional_differences.png` - Différences entre régions
- `correlation_matrix.png` - Matrice de corrélation
- `seasonal_patterns.png` - Patterns saisonniers

## 🗺️ Régions Analysées

"""
    
    for region in sorted(df['region'].unique()):
        region_data = df[df['region'] == region]
        md_content += f"- **{region}**: {len(region_data):,} enregistrements\n"
    
    # Sauvegarder le rapport markdown
    md_file = OUTPUT_DIR / 'analysis_report.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"  📋 Rapport JSON: {report_file}")
    print(f"  📋 Rapport Markdown: {md_file}")
    
    return report

def main():
    """Fonction principale"""
    print("🔬 Analyse Avancée des Données GEE Sénégal")
    print("=" * 50)
    
    try:
        # Charger les données
        df = load_all_data()
        if df is None:
            return 1
        
        # Analyses
        availability_stats = analyze_data_availability(df)
        temporal_data = analyze_temporal_trends(df)
        regional_stats = analyze_regional_differences(df)
        corr_matrix, strong_correlations = analyze_correlations(df)
        seasonal_data = analyze_seasonal_patterns(df)
        
        # Générer le rapport
        report = generate_analysis_report(df, availability_stats, strong_correlations)
        
        print(f"\n🎉 Analyse terminée avec succès!")
        print(f"📁 Dossier de sortie: {OUTPUT_DIR}")
        print(f"📊 Graphiques générés: 5")
        print(f"📋 Rapports générés: 2")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return 1

if __name__ == "__main__":
    exit(main())