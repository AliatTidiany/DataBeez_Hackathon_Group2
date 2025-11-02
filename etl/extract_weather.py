import requests
import pandas as pd
import json
from datetime import datetime, timezone
import time
import os


def extract_weather_data(
    config_path="/opt/airflow/config/coords.json",
    api_key_path="/opt/airflow/config/config.json",
    output_path="/opt/airflow/data/raw/meteo_raw.csv"
):
    """
    Extraction des données météo depuis OpenWeather One Call 3.0
    pour les villes définies dans coords.json.

    Compatible avec Airflow (Docker).
    """

    # Vérification des chemins
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Charger la clé API
    with open(api_key_path) as f:
        api_data = json.load(f)
    API_KEY = api_data.get("api_key")
    if not API_KEY:
        raise ValueError("Clé API OpenWeather manquante dans config/config.json")

    # Charger les coordonnées
    with open(config_path) as f:
        locations = json.load(f)

    all_data = []
    print(" Début de l'extraction des données météo...\n")

    for loc in locations:
        ville = loc.get("ville")
        lat = loc.get("lat")
        lon = loc.get("lon")

        if not (lat and lon):
            print(f"Coordonnées manquantes pour {ville}, passage...")
            continue

        try:
            url = (
                f"https://api.openweathermap.org/data/3.0/onecall?"
                f"lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fr"
            )
            response = requests.get(url)

            if response.status_code != 200:
                print(f" Erreur {response.status_code} pour {ville}")
                continue

            data = response.json()

            # --- Données actuelles ---
            current = data.get("current", {})
            if current:
                description = current.get("weather", [{}])[0].get("description")
                all_data.append({
                    "ville": ville,
                    "type": "current",
                    "date": datetime.fromtimestamp(current["dt"], tz=timezone.utc),
                    "temperature": current.get("temp"),
                    "humidite": current.get("humidity"),
                    "pression": current.get("pressure"),
                    "vent": current.get("wind_speed"),
                    "pluie": current.get("rain", {}).get("1h", 0),
                    "description": description
                })

            # --- Données horaires (48h) ---
            for h in data.get("hourly", []):
                description = h.get("weather", [{}])[0].get("description")
                all_data.append({
                    "ville": ville,
                    "type": "hourly",
                    "date": datetime.fromtimestamp(h["dt"], tz=timezone.utc),
                    "temperature": h.get("temp"),
                    "humidite": h.get("humidity"),
                    "pression": h.get("pressure"),
                    "vent": h.get("wind_speed"),
                    "pluie": h.get("rain", {}).get("1h", 0),
                    "description": description
                })

            # --- Données journalières (8 jours) ---
            for d in data.get("daily", []):
                description = d.get("weather", [{}])[0].get("description")
                all_data.append({
                    "ville": ville,
                    "type": "daily",
                    "date": datetime.fromtimestamp(d["dt"], tz=timezone.utc),
                    "temperature": d.get("temp", {}).get("day"),
                    "humidite": d.get("humidity"),
                    "pression": d.get("pressure"),
                    "vent": d.get("wind_speed"),
                    "pluie": d.get("rain", 0),
                    "description": description
                })

            print(f" Données extraites pour {ville}")
            time.sleep(1)  # éviter le rate limit API

        except Exception as e:
            print(f" Erreur pour {ville}: {e}")

    # Convertir en DataFrame
    df = pd.DataFrame(all_data)

    # Sauvegarder
    df.to_csv(output_path, index=False)
    print(f"\n Extraction terminée : {len(df)} lignes enregistrées dans {output_path}")
    return df


if __name__ == "__main__":
    extract_weather_data()
