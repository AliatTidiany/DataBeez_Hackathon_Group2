#!/usr/bin/env python3
"""
transform_fao.py

Script de transformation et nettoyage des données FAO
- Nettoyage des données brutes FAOSTAT
- Standardisation des formats
- Validation des données
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration des chemins
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
CLEAN_DATA_DIR = BASE_DIR / "data" / "clean"

def load_fao_data():
    """Charge les données FAO brutes"""
    print("📥 Chargement des données FAO brutes...")
    
    # Chercher les fichiers FAOSTAT
    fao_files = list(RAW_DATA_DIR.glob("FAOSTAT_data_*.csv"))
    
    if not fao_files:
        print("❌ Aucun fichier FAOSTAT trouvé dans data/raw/")
        return None
    
    all_data = []
    
    for file_path in fao_files:
        print(f"  📄 Lecture: {file_path.name}")
        try:
            df = pd.read_csv(file_path)
            df['source'] = file_path.stem.replace('FAOSTAT_data_', '').replace('_Senegal', '')
            all_data.append(df)
        except Exception as e:
            print(f"  ❌ Erreur lecture {file_path.name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"✅ Données chargées: {len(combined_df):,} enregistrements")
        return combined_df
    
    return None

def clean_fao_data(df):
    """Nettoie et standardise les données FAO"""
    print("🧹 Nettoyage des données FAO...")
    
    # Standardiser les noms de colonnes
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Colonnes essentielles
    essential_columns = ['element', 'item', 'year', 'unit', 'value', 'source']
    
    # Vérifier les colonnes disponibles
    available_columns = [col for col in essential_columns if col in df.columns]
    missing_columns = [col for col in essential_columns if col not in df.columns]
    
    if missing_columns:
        print(f"⚠️ Colonnes manquantes: {missing_columns}")
    
    # Garder seulement les colonnes essentielles
    df_clean = df[available_columns].copy()
    
    # Nettoyer les valeurs
    if 'value' in df_clean.columns:
        # Supprimer les valeurs non numériques
        df_clean['value'] = pd.to_numeric(df_clean['value'], errors='coerce')
        
        # Supprimer les lignes avec valeurs manquantes
        initial_count = len(df_clean)
        df_clean = df_clean.dropna(subset=['value'])
        removed_count = initial_count - len(df_clean)
        
        if removed_count > 0:
            print(f"  🗑️ Supprimé {removed_count:,} lignes avec valeurs manquantes")
    
    # Nettoyer les années
    if 'year' in df_clean.columns:
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')
        df_clean = df_clean.dropna(subset=['year'])
        df_clean['year'] = df_clean['year'].astype(int)
    
    # Nettoyer les chaînes de caractères
    string_columns = ['element', 'item', 'unit', 'source']
    for col in string_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    print(f"✅ Données nettoyées: {len(df_clean):,} enregistrements")
    return df_clean

def validate_fao_data(df):
    """Valide la qualité des données FAO"""
    print("🔍 Validation des données FAO...")
    
    validation_results = {
        'total_records': len(df),
        'unique_elements': df['element'].nunique() if 'element' in df.columns else 0,
        'unique_items': df['item'].nunique() if 'item' in df.columns else 0,
        'year_range': (df['year'].min(), df['year'].max()) if 'year' in df.columns else (None, None),
        'value_stats': df['value'].describe() if 'value' in df.columns else None
    }
    
    print(f"  📊 Enregistrements totaux: {validation_results['total_records']:,}")
    print(f"  📈 Éléments uniques: {validation_results['unique_elements']}")
    print(f"  🌾 Items uniques: {validation_results['unique_items']}")
    
    if validation_results['year_range'][0]:
        print(f"  📅 Période: {validation_results['year_range'][0]}-{validation_results['year_range'][1]}")
    
    if validation_results['value_stats'] is not None:
        stats = validation_results['value_stats']
        print(f"  💰 Valeurs - Min: {stats['min']:,.0f}, Max: {stats['max']:,.0f}, Moyenne: {stats['mean']:,.0f}")
    
    return validation_results

def save_clean_data(df):
    """Sauvegarde les données nettoyées"""
    print("💾 Sauvegarde des données nettoyées...")
    
    # Créer le dossier clean s'il n'existe pas
    CLEAN_DATA_DIR.mkdir(exist_ok=True)
    
    # Sauvegarder
    output_file = CLEAN_DATA_DIR / "clean_fao.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ Données sauvegardées: {output_file}")
    print(f"  📊 {len(df):,} enregistrements")
    
    return output_file

def generate_summary_report(df, validation_results):
    """Génère un rapport de résumé"""
    print("📋 Génération du rapport de résumé...")
    
    # Top 10 des éléments
    if 'element' in df.columns:
        top_elements = df['element'].value_counts().head(10)
        print(f"\n🔝 Top 10 des éléments:")
        for element, count in top_elements.items():
            print(f"  - {element}: {count:,} enregistrements")
    
    # Top 10 des items
    if 'item' in df.columns:
        top_items = df['item'].value_counts().head(10)
        print(f"\n🌾 Top 10 des items:")
        for item, count in top_items.items():
            print(f"  - {item}: {count:,} enregistrements")
    
    # Répartition par année
    if 'year' in df.columns:
        yearly_counts = df['year'].value_counts().sort_index()
        print(f"\n📅 Répartition par année:")
        for year, count in yearly_counts.tail(5).items():
            print(f"  - {year}: {count:,} enregistrements")

def main():
    """Fonction principale"""
    print("🌾 Transformation des Données FAO")
    print("=" * 40)
    
    try:
        # Charger les données brutes
        df_raw = load_fao_data()
        if df_raw is None:
            return 1
        
        # Nettoyer les données
        df_clean = clean_fao_data(df_raw)
        
        # Valider les données
        validation_results = validate_fao_data(df_clean)
        
        # Sauvegarder
        output_file = save_clean_data(df_clean)
        
        # Générer le rapport
        generate_summary_report(df_clean, validation_results)
        
        print(f"\n🎉 Transformation terminée avec succès!")
        print(f"📄 Fichier de sortie: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la transformation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())