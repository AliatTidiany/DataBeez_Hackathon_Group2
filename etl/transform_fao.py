"""
transform_fao.py — version adaptée pour Airflow/Docker
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ---------------------------
# 📁 Configuration des chemins
# ---------------------------
RAW_PATH = Path("/opt/airflow/data/raw")
CLEAN_DATA_DIR = Path("/opt/airflow/data/processed")

def load_fao_data():
    """Charge les fichiers FAO bruts"""
    print("📥 Chargement des fichiers FAO bruts depuis /opt/airflow/data/raw ...")
    
    fao_files = list(RAW_PATH.glob("FAOSTAT_data_*.csv"))
    if not fao_files:
        print("❌ Aucun fichier FAOSTAT trouvé dans /opt/airflow/data/raw/")
        return None

    all_data = []
    for file_path in fao_files:
        print(f"  📄 Lecture : {file_path.name}")
        try:
            df = pd.read_csv(file_path)
            df["source"] = file_path.stem.replace("FAOSTAT_data_", "").replace("_Senegal", "")
            all_data.append(df)
        except Exception as e:
            print(f"  ❌ Erreur de lecture {file_path.name}: {e}")

    if not all_data:
        print("❌ Aucun fichier lisible.")
        return None

    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Données chargées : {len(combined_df):,} enregistrements")
    return combined_df

def clean_fao_data(df):
    """Nettoie et standardise les données FAO"""
    print("🧹 Nettoyage et standardisation...")
    
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    essential_columns = ["element", "item", "year", "unit", "value", "source"]
    available_cols = [c for c in essential_columns if c in df.columns]

    df_clean = df[available_cols].copy()
    if "value" in df_clean.columns:
        df_clean["value"] = pd.to_numeric(df_clean["value"], errors="coerce")
        before = len(df_clean)
        df_clean.dropna(subset=["value"], inplace=True)
        print(f"  🗑️ Supprimé {before - len(df_clean):,} lignes sans valeur numérique")

    if "year" in df_clean.columns:
        df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce").astype("Int64")
        df_clean.dropna(subset=["year"], inplace=True)

    for col in ["element", "item", "unit", "source"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

    print(f"✅ Données prêtes : {len(df_clean):,} lignes, {len(df_clean.columns)} colonnes")
    return df_clean

def validate_fao_data(df):
    """Valide la qualité du jeu de données"""
    print("🔍 Validation des données FAO...")
    summary = {
        "total_records": len(df),
        "unique_elements": df["element"].nunique() if "element" in df else 0,
        "unique_items": df["item"].nunique() if "item" in df else 0,
        "year_range": (
            df["year"].min(),
            df["year"].max()
        ) if "year" in df else (None, None),
        "value_stats": df["value"].describe() if "value" in df else None
    }

    print(f"  📊 Enregistrements : {summary['total_records']:,}")
    if summary["year_range"][0] is not None:
        print(f"  📅 Années : {summary['year_range'][0]} à {summary['year_range'][1]}")
    if summary["value_stats"] is not None:
        print(f"  💰 Valeur moyenne : {summary['value_stats']['mean']:.0f}")
    return summary

def save_clean_data(df):
    """Sauvegarde les données nettoyées"""
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = CLEAN_DATA_DIR / f"clean_fao_{timestamp}.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"💾 Données sauvegardées : {output_file}")
    return output_file

def generate_summary_report(df):
    """Rapport rapide"""
    if "item" in df.columns:
        print(f"\n🌾 Top 5 Items :")
        print(df["item"].value_counts().head(5))
    if "year" in df.columns:
        print(f"\n📅 Période : {df['year'].min()} → {df['year'].max()}")

def main():
    print("🌾 Début de la transformation FAO")
    print("=" * 40)
    try:
        df_raw = load_fao_data()
        if df_raw is None:
            print("⚠️ Aucune donnée FAO trouvée. Fin du script.")
            return 1

        df_clean = clean_fao_data(df_raw)
        validate_fao_data(df_clean)
        output = save_clean_data(df_clean)
        generate_summary_report(df_clean)

        print(f"\n🎉 Transformation FAO terminée avec succès.")
        print(f"📄 Fichier : {output}")
        return 0

    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return 1

# 👉 Interface pour Airflow
def transform_fao(**kwargs):
    """Fonction appelée par le DAG Airflow"""
    return main()

if __name__ == "__main__":
    exit(main())
