"""
load_fao_data.py — version complète adaptée à transform_fao.py
Charge les données FAO nettoyées dans PostgreSQL avec toutes les colonnes :
[element, item, year, unit, value, source]
"""

import psycopg2
import pandas as pd
from pathlib import Path

def load_fao_data(**kwargs):
    """
    Charge les données FAO nettoyées dans la base PostgreSQL.
    Compatible avec le format produit par transform_fao.py
    """
    print("🚀 Démarrage du chargement des données FAO...")

    # 📂 Dossier des fichiers nettoyés
    processed_dir = Path("/opt/airflow/data/processed")
    fao_files = sorted(processed_dir.glob("clean_fao_*.csv"))

    if not fao_files:
        raise FileNotFoundError("❌ Aucun fichier clean_fao_*.csv trouvé dans /opt/airflow/data/processed")

    # Prendre le fichier le plus récent
    latest_file = fao_files[-1]
    print(f"📄 Fichier sélectionné : {latest_file.name}")

    # 📥 Lecture du fichier
    df = pd.read_csv(latest_file)
    df.columns = df.columns.str.lower().str.strip()
    print(f"✅ {len(df)} lignes et {len(df.columns)} colonnes prêtes à être insérées.")

    # Vérification des colonnes attendues
    expected_cols = {"element", "item", "year", "unit", "value", "source"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"❌ Colonnes manquantes dans le fichier : {missing}")

    # Nettoyage
    df["element"] = df["element"].astype(str).str.slice(0, 255)
    df["item"] = df["item"].astype(str).str.slice(0, 255)
    df["unit"] = df["unit"].astype(str).str.slice(0, 50)
    df["source"] = df["source"].astype(str).str.slice(0, 100)

    # Conversion des valeurs numériques
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # 🔌 Connexion à PostgreSQL
    try:
        conn = psycopg2.connect(
            host="db",
            port="5432",
            dbname="meteo_db",
            user="postgres",
            password="passer"
        )
        cur = conn.cursor()
        print("✅ Connexion PostgreSQL établie.")

        # 🏗️ Création de la table FAO
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fao_data (
                id SERIAL PRIMARY KEY,
                element VARCHAR(255),
                item VARCHAR(255),
                year INT,
                unit VARCHAR(50),
                value FLOAT,
                source VARCHAR(100)
            );
        """)

        # 💾 Préparation des enregistrements
        records = [
            (
                row["element"],
                row["item"],
                int(row["year"]) if not pd.isna(row["year"]) else None,
                row["unit"],
                float(row["value"]) if not pd.isna(row["value"]) else None,
                row["source"]
            )
            for _, row in df.iterrows()
        ]

        # 🚀 Insertion
        insert_query = """
            INSERT INTO fao_data (element, item, year, unit, value, source)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cur.executemany(insert_query, records)
        conn.commit()
        print(f"🎉 Données FAO insérées avec succès ({len(records)} lignes).")

    except Exception as e:
        print(f"❌ Erreur lors du chargement FAO : {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("🔒 Connexion PostgreSQL fermée.")


if __name__ == "__main__":
    load_fao_data()
