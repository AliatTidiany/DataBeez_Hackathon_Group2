import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
import os

def load_gee_data():
    """Charge toutes les données GEE transformées dans PostgreSQL."""
    print("🚀 Démarrage du chargement des données GEE...")

    # === Fichier d'entrée ===
    file_path = "/opt/airflow/data/processed/senegal_gee_transformed.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ Fichier introuvable : {file_path}")

    # === Lecture du CSV ===
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("⚠️ Le fichier GEE est vide — aucune donnée à charger.")
        print(f"📄 {len(df)} lignes et {len(df.columns)} colonnes prêtes à être insérées.")
        print(f"🧩 Colonnes : {list(df.columns)}")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV : {e}")
        raise

    # === Connexion PostgreSQL ===
    try:
        conn = psycopg2.connect(
            host="db",
            port="5432",
            dbname="meteo_db",
            user="postgres",
            password="passer"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        print("✅ Connexion PostgreSQL réussie.")

        # === Création de la table ===
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gee_data (
                id SERIAL PRIMARY KEY,
                region VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                date TIMESTAMP,
                year INT,
                month INT,
                day INT,
                season VARCHAR(20),
                surface_solar_radiation_downwards_sum FLOAT,
                temperature_2m FLOAT,
                total_precipitation_sum FLOAT,
                u_component_of_wind_10m FLOAT,
                v_component_of_wind_10m FLOAT,
                precipitation FLOAT,
                lst_day_1km FLOAT,
                lst_night_1km FLOAT,
                temp_day_celsius FLOAT,
                temp_night_celsius FLOAT,
                evi FLOAT,
                ndvi FLOAT,
                ndvi_normalized FLOAT,
                evi_normalized FLOAT,
                ssm FLOAT,
                data_source VARCHAR(50)
            );
        """)

        # === Requête d’insertion ===
        insert_query = """
            INSERT INTO gee_data (
                region, latitude, longitude, date,
                year, month, day, season,
                surface_solar_radiation_downwards_sum,
                temperature_2m, total_precipitation_sum,
                u_component_of_wind_10m, v_component_of_wind_10m,
                precipitation, lst_day_1km, lst_night_1km,
                temp_day_celsius, temp_night_celsius,
                evi, ndvi, ndvi_normalized, evi_normalized,
                ssm, data_source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        # === Préparation des enregistrements ===
        records = [
            (
                row.get("region"),
                row.get("latitude"),
                row.get("longitude"),
                row.get("date"),
                row.get("year"),
                row.get("month"),
                row.get("day"),
                row.get("season"),
                row.get("surface_solar_radiation_downwards_sum"),
                row.get("temperature_2m"),
                row.get("total_precipitation_sum"),
                row.get("u_component_of_wind_10m"),
                row.get("v_component_of_wind_10m"),
                row.get("precipitation"),
                row.get("lst_day_1km"),
                row.get("lst_night_1km"),
                row.get("temp_day_celsius"),
                row.get("temp_night_celsius"),
                row.get("evi"),
                row.get("ndvi"),
                row.get("ndvi_normalized"),
                row.get("evi_normalized"),
                row.get("ssm"),
                row.get("data_source")
            )
            for _, row in df.iterrows()
        ]

        # === Insertion batchée ===
        execute_batch(cur, insert_query, records, page_size=1000)
        conn.commit()
        print(f"✅ Données GEE chargées avec succès dans la table gee_data ({len(df)} lignes).")

    except Exception as e:
        print(f"❌ Erreur lors du chargement des données GEE : {e}")
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()
        print("🔒 Connexion PostgreSQL fermée.")

# === Exécution directe ===
if __name__ == "__main__":
    load_gee_data()
