"""
Google Earth Engine Data Extractor for Senegal
Auteur : Alioune MBODJI
Version Airflow-compatible
"""

import ee
import pandas as pd
import os

# === Configuration globale ===
REGIONS_SENEGAL = {
    "Dakar": {"lat": 14.7167, "lon": -17.4677, "buffer": 0.2},
    "Diourbel": {"lat": 14.6558, "lon": -16.2334, "buffer": 0.3},
    "Fatick": {"lat": 14.3396, "lon": -16.4114, "buffer": 0.3},
    "Kaffrine": {"lat": 14.1050, "lon": -15.5500, "buffer": 0.3},
    "Kaolack": {"lat": 14.1469, "lon": -16.0726, "buffer": 0.3},
    "Kédougou": {"lat": 12.5556, "lon": -12.1744, "buffer": 0.4},
    "Kolda": {"lat": 12.8833, "lon": -14.9500, "buffer": 0.4},
    "Louga": {"lat": 15.6144, "lon": -16.2286, "buffer": 0.4},
    "Matam": {"lat": 15.6600, "lon": -13.2550, "buffer": 0.4},
    "Saint-Louis": {"lat": 16.0179, "lon": -16.4896, "buffer": 0.3},
    "Sédhiou": {"lat": 12.7089, "lon": -15.5561, "buffer": 0.3},
    "Tambacounda": {"lat": 13.7707, "lon": -13.6673, "buffer": 0.5},
    "Thiès": {"lat": 14.7910, "lon": -16.9250, "buffer": 0.3},
    "Ziguinchor": {"lat": 12.5833, "lon": -16.2719, "buffer": 0.3}
}

START_DATE = '2019-01-01'
END_DATE = '2024-12-31'
OUTPUT_FILE = "/opt/airflow/data/raw/gee_senegal_all_data.csv"  

# === Fonctions GEE ===
def create_region_geometry(lat, lon, buffer):
    return ee.Geometry.Rectangle([lon - buffer, lat - buffer, lon + buffer, lat + buffer])

def extract_mean(collection_id, bands, geometry, start_date, end_date, source_name, scale=5000):
    collection = ee.ImageCollection(collection_id).filterDate(start_date, end_date).filterBounds(geometry).select(bands)

    def extract_features(image):
        stats = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=geometry, scale=scale, maxPixels=1e9)
        props = {'date': image.date().format('YYYY-MM-dd')}
        for band in bands:
            props[band] = stats.get(band)
        props['data_source'] = source_name
        return ee.Feature(None, props)

    return collection.map(extract_features)

def extract_region_data(region_name, info):
    print(f"\n Extraction pour {region_name}...")
    geometry = create_region_geometry(info['lat'], info['lon'], info['buffer'])

    try:
        era5 = extract_mean('ECMWF/ERA5_LAND/DAILY_AGGR',
                            ['surface_solar_radiation_downwards_sum', 'temperature_2m',
                             'total_precipitation_sum', 'u_component_of_wind_10m', 'v_component_of_wind_10m'],
                            geometry, START_DATE, END_DATE, 'ERA5', 11132).getInfo()

        chirps = extract_mean('UCSB-CHG/CHIRPS/DAILY', ['precipitation'],
                              geometry, START_DATE, END_DATE, 'CHIRPS').getInfo()

        modis_temp = extract_mean('MODIS/006/MOD11A1', ['LST_Day_1km', 'LST_Night_1km'],
                                  geometry, START_DATE, END_DATE, 'MODIS_TEMP', 1000).getInfo()

        modis_vi = extract_mean('MODIS/006/MOD13Q1', ['NDVI', 'EVI'],
                                geometry, START_DATE, END_DATE, 'MODIS_VI', 250).getInfo()

        smap = extract_mean('NASA_USDA/HSL/SMAP10KM_soil_moisture', ['ssm'],
                            geometry, START_DATE, END_DATE, 'SMAP', 10000).getInfo()

        dfs = []
        for data in [era5, chirps, modis_temp, modis_vi, smap]:
            if data and 'features' in data:
                df = pd.DataFrame([f['properties'] for f in data['features']])
                df['region'] = region_name
                df['latitude'] = info['lat']
                df['longitude'] = info['lon']
                df['date'] = pd.to_datetime(df['date'])
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        region_df = pd.concat(dfs, ignore_index=True)

        if 'LST_Day_1km' in region_df.columns:
            region_df['temp_day_celsius'] = region_df['LST_Day_1km'] - 273.15
        if 'LST_Night_1km' in region_df.columns:
            region_df['temp_night_celsius'] = region_df['LST_Night_1km'] - 273.15
        if 'NDVI' in region_df.columns:
            region_df['ndvi_normalized'] = region_df['NDVI'] / 10000
        if 'EVI' in region_df.columns:
            region_df['evi_normalized'] = region_df['EVI'] / 10000

        return region_df

    except Exception as e:
        print(f" Erreur pour {region_name}: {e}")
        return pd.DataFrame()

# === Fonction principale appelée par Airflow ===
def extract_gee_data():
    """Extrait et consolide toutes les données GEE du Sénégal"""
    print(" Début de l'extraction et consolidation des données GEE...")

    try:
        ee.Initialize(project='dark-lexicon-433417-d8')
        print(" Connexion à Google Earth Engine réussie.")
    except Exception as e:
        print(f" Erreur d'initialisation GEE : {e}")
        return

    all_data = []
    for region, info in REGIONS_SENEGAL.items():
        df = extract_region_data(region, info)
        if not df.empty:
            all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = final_df.sort_values(by=['region', 'date'])

        ordered_cols = [
            'region', 'latitude', 'longitude', 'date',
            'surface_solar_radiation_downwards_sum', 'temperature_2m',
            'total_precipitation_sum', 'u_component_of_wind_10m', 'v_component_of_wind_10m',
            'precipitation', 'LST_Day_1km', 'LST_Night_1km',
            'temp_day_celsius', 'temp_night_celsius',
            'EVI', 'NDVI', 'ndvi_normalized', 'evi_normalized', 'ssm',
            'data_source'
        ]
        existing_cols = [c for c in ordered_cols if c in final_df.columns]
        final_df = final_df[existing_cols]

        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f" Données GEE sauvegardées dans {OUTPUT_FILE}")
        print(f" {len(final_df)} lignes enregistrées.")
    else:
        print(" Aucune donnée extraite.")
