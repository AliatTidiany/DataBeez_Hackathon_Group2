import psycopg2
import pandas as pd
import os

def load_weather_data():
    """
    Charge les données météo nettoyées dans PostgreSQL avec psycopg2.
    """
    print(" Démarrage du chargement des données météo...")

    file_path = "/opt/airflow/data/processed/meteo_clean.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    df = pd.read_csv(file_path)
    print(f" {len(df)} lignes prêtes à être insérées dans meteo_data.")

    try:
        # Connexion à la base PostgreSQL (service db dans docker-compose)
        conn = psycopg2.connect(
            host="db",
            port="5432",
            dbname="meteo_db",
            user="postgres",
            password="passer"
        )
        cur = conn.cursor()

        # Créer la table si elle n’existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meteo_data (
                id SERIAL PRIMARY KEY,
                ville VARCHAR(100),
                type VARCHAR(20),
                date TIMESTAMP,
                temperature FLOAT,
                humidite FLOAT,
                pression FLOAT,
                vent FLOAT,
                pluie FLOAT,
                description TEXT
            );
        """)

        # Préparer l’insertion
        insert_query = """
            INSERT INTO meteo_data (ville, type, date, temperature, humidite, pression, vent, pluie, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        # Conversion en liste de tuples
        records = [
            (
                row["ville"], row["type"], row["date"], row["temperature"],
                row["humidite"], row.get("pression"), row.get("vent"),
                row.get("pluie"), row.get("description")
            )
            for _, row in df.iterrows()
        ]

        # Insertion en masse
        cur.executemany(insert_query, records)
        conn.commit()

        print("Données météo chargées avec succès dans PostgreSQL.")

    except Exception as e:
        print(f" Erreur lors du chargement des données météo : {e}")
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()
