"""
transform_fao.py

Nettoyage et préparation enrichie des données FAO
-------------------------------------------------
- Nettoie et fusionne les fichiers FAO :
    1. Crops & Livestock Products
    2. Value of Agricultural Production
- Conserve les colonnes pertinentes : produit, domaine, type d'élément, unité, valeur, année
- Supprime les doublons et les valeurs estimées
- Permet une analyse détaillée par produit agricole

Entrées :
  - data/FAOSTAT_data_Crops_and_livestock_products_Senegal.csv
  - data/FAOSTAT_data_en_Value_of_Agricultural_Production_Senegal.csv
Sortie :
  - data/clean_fao.csv
"""

import pandas as pd
import os

# --- Fichiers d'entrée/sortie ---
FAO_CROPS_CSV = "/Users/alii_ibn_hassan/Documents/DataBeez_Hackaton/Base/data/FAOSTAT_data_Crops_and_livestock_products_Senegal.csv"
FAO_VALUE_CSV = "/Users/alii_ibn_hassan/Documents/DataBeez_Hackaton/Base/data/FAOSTAT_data_en_Value_of_Agricultural_Production_Senegal.csv"
OUTPUT_CSV = "/Users/alii_ibn_hassan/Documents/DataBeez_Hackaton/Base/data/clean_fao.csv"


def clean_fao_file(path, source_name):
    """Nettoyage individuel d’un fichier FAO."""
    if not os.path.exists(path):
        raise FileNotFoundError(f" Fichier introuvable : {path}")

    print(f"🔍 Lecture du fichier {os.path.basename(path)} ...")

    # Lecture robuste avec détection des erreurs
    try:
        df = pd.read_csv(path, sep=",", quotechar='"', engine="python", on_bad_lines="skip")
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du fichier {path}: {e}")

    # Nettoyage des colonnes
    df.columns = [c.strip() for c in df.columns]

    # Vérification de la présence des colonnes clés
    required_cols = ["Domain", "Element", "Item", "Year", "Unit", "Value"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Colonnes manquantes dans {source_name}: {missing}")

    # Filtrer uniquement le Sénégal si la colonne existe
    if "Area" in df.columns:
        df = df[df["Area"].astype(str).str.strip().str.lower() == "senegal"]

    # Supprimer les valeurs estimées
    if "Flag Description" in df.columns:
        df = df[~df["Flag Description"].astype(str).str.contains("Estimated", case=False, na=False)]

    # Conserver les colonnes d’intérêt existantes
    keep_cols = [c for c in required_cols if c in df.columns]
    df = df[keep_cols].copy()

    # Conversion de la colonne Value
    if "Value" in df.columns:
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Ajout d’une colonne “Source” pour la traçabilité
    df["Source"] = source_name

    # Suppression des doublons
    df = df.drop_duplicates(subset=["Item", "Year", "Element"], keep="first")

    return df


def clean_fao():
    """Lecture, nettoyage et fusion des fichiers FAO."""
    print("🌾 Lecture et nettoyage des fichiers FAO...")

    fao_crops = clean_fao_file(FAO_CROPS_CSV, "Crops_and_Livestock")
    fao_value = clean_fao_file(FAO_VALUE_CSV, "Value_of_Agricultural_Production")

    # Fusion
    df_all = pd.concat([fao_crops, fao_value], ignore_index=True)

    # Nettoyage final
    df_all = df_all.dropna(subset=["Value"])
    df_all["Value"] = df_all["Value"].astype(float)

    # Tri logique
    df_all = df_all.sort_values(by=["Year", "Domain", "Item"]).reset_index(drop=True)

    print(f"✅ Données nettoyées : {len(df_all)} lignes")
    return df_all


def main():
    print("🚜 Transformation enrichie des données FAO...")
    df = clean_fao()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Fichier enrichi sauvegardé -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
