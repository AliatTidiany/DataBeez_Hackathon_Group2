import os
import pandas as pd

def clean_weather_data(df):
    """
    Nettoyage et préparation du DataFrame exporté par extract_weather_data().
    Étapes :
      1. Suppression des doublons et lignes incomplètes
      2. Conversion des colonnes numériques
      3. Filtrage des valeurs incohérentes
    """

    print("Début du nettoyage des données météo...")

    # Supprimer les doublons
    df = df.drop_duplicates()

    # Supprimer les lignes avec valeurs essentielles manquantes
    df = df.dropna(subset=["date", "temperature", "humidite"], how="any")

    # Conversion des colonnes numériques
    numeric_cols = ["temperature", "humidite", "pression", "vent", "pluie"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Nettoyage final : valeurs cohérentes
    df = df[
        (df["humidite"].between(0, 100)) &
        (df["temperature"].between(-80, 60))
    ]

    print(f"Nettoyage terminé : {len(df)} lignes conservées après filtrage.")
    return df


def transform_weather():
    """
    Fonction principale appelée par Airflow.
    Nettoie les données brutes issues de l’extraction météo
    et sauvegarde le résultat dans data/processed/meteo_clean.csv.
    Compatible avec Docker + Airflow.
    """

    raw_path = "/opt/airflow/data/raw/meteo_raw.csv"
    output_path = "/opt/airflow/data/processed/meteo_clean.csv"

    print("Chargement des données brutes...")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f" Fichier introuvable : {raw_path}")

    # Charger les données
    df_raw = pd.read_csv(raw_path, parse_dates=["date"])

    # Nettoyer
    df_clean = clean_weather_data(df_raw)

    # Créer le dossier processed si besoin
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Sauvegarder
    df_clean.to_csv(output_path, index=False)
    print(f"Transformation terminée, fichier enregistré dans : {output_path}")


if __name__ == "__main__":
    transform_weather()
