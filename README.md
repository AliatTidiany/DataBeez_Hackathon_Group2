
---

# Plateforme d’Intelligent Météo & Agricole – DataBeez Hackathon

## Contexte

L’agriculture en Afrique est fortement dépendante de la météo, mais les agriculteurs font face à :

* Imprévisibilité des pluies → irrigation mal planifiée
* Sécheresses et chaleurs extrêmes → pertes de récoltes
* Manque d’informations fiables en temps réel

Les solutions existantes sont souvent trop générales ou difficiles d’accès.

## Objectif

Créer une **plateforme intelligente d’aide à la décision agricole** pour :

1. Fournir des prévisions météo locales adaptées aux champs.
2. Développer des modèles prédictifs pour la pluie, la sécheresse, l’irrigation et les maladies.
3. Proposer une interface simple et accessible via Streamlit.

**But final** : aider les agriculteurs à mieux planifier les semis, l’arrosage et la récolte afin d’améliorer le rendement et réduire les pertes.

## Technologies utilisées

* Python 3.9
* Docker & Docker Compose
* PostgreSQL 15
* Apache Airflow 2.7
* Streamlit
* Pandas, Scikit-learn

## Installation et démarrage

### 1. Cloner le projet

```bash
git clone <lien_du_repo>
cd Project
```

### 2. Lancer Docker Compose

```bash
docker-compose up --build
```

### 3. Accéder aux services

* Streamlit : [http://localhost:8501](http://localhost:8501)
* Airflow : [http://localhost:8080](http://localhost:8080)

  * Username : admin
  * Password : admin
* PgAdmin : [http://localhost:5050](http://localhost:5050)

  * Email : [admin@admin.com](mailto:admin@admin.com)
  * Password : admin

## Structure du projet

```
Project/
│
├─ config/             # Fichiers de configuration (paramètres, clés, etc.)
├─ dags/               # DAGs Apache Airflow pour orchestrer les workflows
├─ data/               # Données brutes et transformées
├─ etl/                # Scripts ETL : extraction, transformation et chargement
├─ logs/               # Fichiers de logs (Airflow, modèles, etc.)
├─ models/             # Modèles de machine learning et scripts associés
│
├─ .env                # Variables d'environnement
├─ .gitignore          # Fichiers à exclure du suivi Git
├─ docker-compose.yml  # Configuration des services Docker
├─ README.md           # Documentation du projet
└─ requirements.txt    # Dépendances Python
```

## Fonctionnalités

* Extraction automatique des données météo et agricoles
* Prédictions intelligentes via des modèles de machine learning
* Entraînement automatique des modèles si aucun n’est disponible
* Application Streamlit pour visualiser les prévisions et recommandations
* Orchestration complète des pipelines via Apache Airflow


