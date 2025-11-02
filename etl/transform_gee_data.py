"""
Nettoyage et Transformation des Données GEE - Sénégal (Version améliorée Airflow)
Auteur : Alioune MBODJI
Objectif :
Préparer les données extraites de Google Earth Engine (GEE) pour l'analyse et le Machine Learning.
Optimisations :
- Fusion cohérente des données par région/date
- Interpolation robuste
- Réduction des NaN
- Réorganisation claire pour PostgreSQL
"""

import pandas as pd
import numpy as np
import os

# === Chemins Docker ===
INPUT_FILE = "/opt/airflow/data/raw/gee_senegal_all_data.csv"
OUTPUT_FILE = "/opt/airflow/data/processed/senegal_gee_transformed.csv"


def transform_gee_data():
    """Nettoie et transforme les données GEE pour intégration ou analyse."""
    print(" Début du nettoyage et de la transformation des données GEE...")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f" Fichier introuvable : {INPUT_FILE}")

    # ===  Chargement des données ===
    df = pd.read_csv(INPUT_FILE)
    print(f" Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    # === Standardisation des noms de colonnes ===
    df.columns = df.columns.str.strip().str.lower()

    # ===  Conversion des types ===
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_cols = [
        "surface_solar_radiation_downwards_sum", "temperature_2m",
        "total_precipitation_sum", "u_component_of_wind_10m", "v_component_of_wind_10m",
        "precipitation", "lst_day_1km", "lst_night_1km",
        "temp_day_celsius", "temp_night_celsius",
        "evi", "ndvi", "ndvi_normalized", "evi_normalized",
        "ssm", "latitude", "longitude"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ===  Regroupement pour fusion cohérente ===
    df = df.groupby(["region", "date", "latitude", "longitude"], as_index=False).first()
    print(f" Fusion par région/date terminée : {df.shape[0]} lignes uniques")

    # === 5️ Suppression des doublons & tri ===
    before = len(df)
    df = df.drop_duplicates(subset=["region", "date"])
    print(f" {before - len(df)} doublons supprimés")

    df = df.dropna(subset=["region", "date"])
    df = df.sort_values(by=["region", "date"]).reset_index(drop=True)

    # === 6️ Interpolation robuste par région ===
    print(" Interpolation des valeurs manquantes...")
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df.groupby("region")[col].transform(lambda g: g.interpolate(method="linear", limit_direction="both"))

    # ===  Fallback : remplissage avant/après si encore des NaN ===
    df[numeric_cols] = df.groupby("region")[numeric_cols].ffill().bfill()

    # === Conversion des températures (Kelvin → °C) ===
    if "temperature_2m" in df.columns:
        df.loc[df["temperature_2m"] > 200, "temperature_2m"] -= 273.15
    if "lst_day_1km" in df.columns:
        df.loc[df["lst_day_1km"] > 200, "lst_day_1km"] -= 273.15
    if "lst_night_1km" in df.columns:
        df.loc[df["lst_night_1km"] > 200, "lst_night_1km"] -= 273.15

    # ===  Variables temporelles ===
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["season"] = df["month"].map({
        12: "Dry", 1: "Dry", 2: "Dry",
        3: "Transition", 4: "Transition", 5: "Transition",
        6: "Rainy", 7: "Rainy", 8: "Rainy", 9: "Rainy",
        10: "Post-Rainy", 11: "Post-Rainy"
    })

    # === Nettoyage final (humidité du sol) ===
    if "ssm" in df.columns:
        df.loc[df["ssm"] < 0, "ssm"] = np.nan
        df.loc[df["ssm"] > 1, "ssm"] = df["ssm"] / 100

    # ===  Réorganisation des colonnes ===
    ordered_cols = [
        "region", "latitude", "longitude", "date",
        "year", "month", "day", "season",
        "surface_solar_radiation_downwards_sum", "temperature_2m",
        "total_precipitation_sum", "u_component_of_wind_10m", "v_component_of_wind_10m",
        "precipitation", "lst_day_1km", "lst_night_1km",
        "temp_day_celsius", "temp_night_celsius",
        "evi", "ndvi", "ndvi_normalized", "evi_normalized",
        "ssm", "data_source"
    ]
    df = df[[col for col in ordered_cols if col in df.columns]]

    # ===  Export final ===
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f" Données GEE nettoyées sauvegardées : {OUTPUT_FILE}")
    print(f" Lignes finales : {len(df)} | Colonnes : {len(df.columns)}")


if __name__ == "__main__":
    transform_gee_data()
