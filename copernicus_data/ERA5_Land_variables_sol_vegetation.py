"""
Copernicus Agro-Meteorological Data Downloader
Auteur : Alioune MBODJI
Objectif :
Télécharger les données agro-météorologiques du Sénégal depuis le CDS (Copernicus)
et sauvegarder un fichier CSV par année et par mois, sans granularité horaire/journalière.

Variables : précipitation, température, rayonnement, humidité, couverture nuageuse.
"""

import os
import zipfile
import pandas as pd
import xarray as xr
import cdsapi
from datetime import datetime

# === Initialisation du client Copernicus ===
client = cdsapi.Client()

# === Paramètres généraux ===
DATASET = "sis-agrometeorological-indicators"

VARIABLES = [
    "precipitation_flux",
    "2m_temperature",
    "solar_radiation_flux",
    "2m_relative_humidity",
    "cloud_cover"
]

REGIONS = {
    "Dakar": {"lat": 14.7167, "lon": -17.4677},
    "Diourbel": {"lat": 14.6558, "lon": -16.2334},
    "Fatick": {"lat": 14.3396, "lon": -16.4114},
    "Kaffrine": {"lat": 14.1050, "lon": -15.5500},
    "Kaolack": {"lat": 14.1469, "lon": -16.0726},
    "Kédougou": {"lat": 12.5556, "lon": -12.1744},
    "Kolda": {"lat": 12.8833, "lon": -14.9500},
    "Louga": {"lat": 15.6144, "lon": -16.2286},
    "Matam": {"lat": 15.6600, "lon": -13.2550},
    "Saint-Louis": {"lat": 16.0179, "lon": -16.4896},
    "Sédhiou": {"lat": 12.7089, "lon": -15.5561},
    "Tambacounda": {"lat": 13.7707, "lon": -13.6673},
    "Thiès": {"lat": 14.7910, "lon": -16.9250},
    "Ziguinchor": {"lat": 12.5833, "lon": -16.2719}
}

# === Répertoires de sortie ===
OUTPUT_DIR = "data/copernicus"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Période d’étude ===
YEARS = [str(y) for y in range(2019, 2025)]
MONTHS = [f"{m:02d}" for m in range(1, 13)]

# === Boucle principale ===
for year in YEARS:
    for month in MONTHS:
        print(f"📅 Téléchargement {year}-{month}...")

        request = {
            "variable": VARIABLES,
            "year": year,
            "month": [month],
            "day": ["01"],  # requis par CDS mais ignoré ensuite
            "version": "1_1",
            "area": [17.0, -18.0, 12.0, -12.0],  # Sénégal (N, W, S, E)
            "format": "zip"
        }

        zip_path = os.path.join(OUTPUT_DIR, f"copernicus_{year}_{month}.zip")

        # --- Téléchargement du fichier ZIP ---
        try:
            if not os.path.exists(zip_path):
                client.retrieve(DATASET, request).download(zip_path)
            else:
                print(f"⏩ Fichier déjà présent : {zip_path}")
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement {year}-{month} : {e}")
            continue

        # --- Décompression ---
        extract_dir = os.path.join(OUTPUT_DIR, f"{year}_{month}")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # --- Conversion NetCDF → CSV ---
        all_dfs = []

        for file in os.listdir(extract_dir):
            if file.endswith(".nc"):
                nc_path = os.path.join(extract_dir, file)
                try:
                    ds = xr.open_dataset(nc_path)
                    df = ds.to_dataframe().reset_index()

                    # Gestion des coordonnées
                    if "latitude" in df.columns and "longitude" in df.columns:
                        lat_col, lon_col = "latitude", "longitude"
                    elif "lat" in df.columns and "lon" in df.columns:
                        lat_col, lon_col = "lat", "lon"
                    else:
                        df["latitude"], df["longitude"] = None, None
                        lat_col, lon_col = "latitude", "longitude"

                    # Colonnes temporelles
                    if "time" in df.columns:
                        df["year"] = pd.to_datetime(df["time"]).dt.year
                        df["month"] = pd.to_datetime(df["time"]).dt.month
                    else:
                        df["year"], df["month"] = int(year), int(month)

                    # Extraction des variables existantes
                    cols = ["year", "month", lat_col, lon_col]
                    for v in VARIABLES:
                        if v in df.columns:
                            cols.append(v)

                    df = df[cols]
                    all_dfs.append(df)

                except Exception as e:
                    print(f"⚠️ Erreur sur {file}: {e}")
                    continue

        # --- Fusion et sauvegarde ---
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            csv_path = os.path.join(OUTPUT_DIR, f"copernicus_{year}_{month}.csv")
            final_df.to_csv(csv_path, index=False)
            print(f"✅ Données sauvegardées : {csv_path}")
        else:
            print(f"⚠️ Aucune donnée valide pour {year}-{month}")


































































































































































































































































































