from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os

# --- Configuration des chemins ---
sys.path.append('/opt/airflow/etl')

# --- Import des fonctions ETL ---
from etl.extract_weather import extract_weather_data
from etl.transform_weather import transform_weather
from etl.load_weather import load_weather_data

from etl.transform_fao import transform_fao
from etl.load_fao import load_fao_data

from etl.extract_gee_data import extract_gee_data
from etl.transform_gee_data import transform_gee_data
from etl.load_gee_data import load_gee_data

# --- Paramètres du DAG ---
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'start_date': datetime(2025, 10, 22),
}

# --- Définition du DAG ---
with DAG(
    dag_id='etl_pipeline_meteo_fao_gee',
    default_args=default_args,
    description='Pipeline ETL complet pour OpenWeather, FAO et Google Earth Engine',
    schedule_interval='@daily',  # Exécution quotidienne
    catchup=False,
    tags=['ETL', 'Meteo', 'FAO', 'GEE', 'Agriculture']
) as dag:

    # =============== ETL MÉTÉO ===============
    extract_weather_task = PythonOperator(
        task_id='extract_weather',
        python_callable=extract_weather_data
    )

    transform_weather_task = PythonOperator(
        task_id='transform_weather',
        python_callable=transform_weather
    )

    load_weather_task = PythonOperator(
        task_id='load_weather',
        python_callable=load_weather_data
    )

    # =============== ETL FAO ===============
    transform_fao_task = PythonOperator(
        task_id='transform_fao',
        python_callable=transform_fao
    )

    load_fao_task = PythonOperator(
        task_id='load_fao',
        python_callable=load_fao_data
    )

    # =============== ETL GEE (Google Earth Engine) ===============
    extract_gee_task = PythonOperator(
        task_id='extract_gee',
        python_callable=extract_gee_data
    )

    transform_gee_task = PythonOperator(
        task_id='transform_gee',
        python_callable=transform_gee_data
    )

    load_gee_task = PythonOperator(
        task_id='load_gee',
        python_callable=load_gee_data
    )

    # --- Dépendances du pipeline ---

    # Pipeline météo
    extract_weather_task >> transform_weather_task >> load_weather_task

    # Pipeline FAO
    transform_fao_task >> load_fao_task

    # Pipeline GEE
    extract_gee_task >> transform_gee_task >> load_gee_task

    
