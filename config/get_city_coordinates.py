import requests
import json
import os
import time


def generate_city_coordinates(
    api_key_path="/opt/airflow/config/config.json",
    output_path="/opt/airflow/config/coords.json"
):
    """
    Récupère les coordonnées (latitude, longitude) des principales villes agricoles du Sénégal
    et les sauvegarde dans config/coords.json.
    Compatible avec Airflow + Docker.
    """

    # Charger la clé API depuis config.json
    with open(api_key_path, "r") as f:
        api_data = json.load(f)
    API_KEY = api_data.get("api_key")

    if not API_KEY:
        raise ValueError("Clé API manquante dans config/config.json")

    # Liste des principales villes agricoles du Sénégal
    villes = [
        "Dakar", "Thiès", "Kaolack", "Saint-Louis", "Ziguinchor",
        "Tambacounda", "Louga", "Fatick", "Kolda", "Kaffrine",
        "Matam", "Diourbel", "Podor", "Richard-Toll", "Bakel"
    ]

    coords = []
    print("Début de la récupération des coordonnées...\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    for ville in villes:
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={ville},SN&limit=1&appid={API_KEY}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Erreur {response.status_code} pour {ville}")
                continue

            data = response.json()
            if not data:
                print(f" Aucune donnée trouvée pour {ville}")
                continue

            lat, lon = data[0]["lat"], data[0]["lon"]
            coords.append({
                "ville": ville,
                "lat": round(lat, 4),
                "lon": round(lon, 4)
            })
            print(f"{ville}: lat={round(lat, 4)}, lon={round(lon, 4)}")

            time.sleep(0.5)  # pour éviter le rate-limit API

        except Exception as e:
            print(f" Erreur avec {ville}: {e}")

    # Sauvegarde dans config/coords.json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=4, ensure_ascii=False)

    print(f"\n Coordonnées enregistrées dans {output_path}")
    return coords


if __name__ == "__main__":
    generate_city_coordinates()
