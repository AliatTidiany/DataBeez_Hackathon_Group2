

````markdown
# 🌾 Plateforme d’Intelligent Météo & Agricole – DataBeez Hackathon

## 🔹 Contexte
L’agriculture en Afrique est fortement dépendante de la météo, mais les agriculteurs font face à :  
- Imprévisibilité des pluies → irrigation mal planifiée  
- Sécheresses et chaleurs extrêmes → pertes de récoltes  
- Manque d’informations fiables en temps réel  

Les solutions existantes sont souvent trop générales ou difficiles d’accès.  

## 🎯 Objectif
Créer une **plateforme intelligente d’aide à la décision agricole** pour :  
1. Prévisions météo locales adaptées aux champs.  
2. Modèles prédictifs : pluie, sécheresse, irrigation, maladies.  
3. Interface simple et accessible via **Streamlit**.  

💡 **But** : aider les agriculteurs à mieux planifier semis, arrosage et récoltes pour améliorer le rendement et réduire les pertes.  

## 🛠️ Technologies utilisées
- Python 3.9  
- Docker & Docker Compose  
- PostgreSQL 15  
- Apache Airflow 2.7  
- Streamlit  
- Pandas, Scikit-learn  

## ⚙️ Installation et démarrage
1. **Cloner le projet**  
```bash
git clone <lien_du_repo>
cd Project
````


2. **Lancer Docker Compose**

```bash
docker-compose up --build
```

3. **Accéder aux services**

* **Streamlit** : [http://localhost:8501](http://localhost:8501)
* **Airflow** : [http://localhost:8080](http://localhost:8080)

  * Username : `admin`
  * Password : `admin`
* **PgAdmin** : [http://localhost:5050](http://localhost:5050)

  * Email : `admin@admin.com`
  * Password : `admin`

## 🗂️ Structure du projet

```
Project/
│
├─ .env
├─ docker-compose.yml
├─ requirements.txt
│
├─ config/             # Configurations (ex : coordonnées, paramètres)
├─ dags/               # DAGs Airflow pour orchestrer les pipelines
├─ data/               # Données brutes et traitées
│   ├─ raw/
│   └─ processed/
├─ etl/                # Scripts ETL : extraction, transformation, chargement
├─ logs/               # Logs Airflow et modèles
├─ models/             # Modèles ML et application Streamlit
│   ├─ saved/          # Modèles entraînés
│   ├─ logs/           # Logs d’entraînement
│   ├─ Dockerfile
│   ├─ start.sh
│   └─ streamlit_app.py
└─ plugins/            # Plugins Airflow personnalisés
```

## 🚀 Fonctionnalités

* Extraction automatique des données météo et agricoles
* Prédictions intelligentes avec les modèles ML
* Entraînement automatique si aucun modèle existant
* **Application Streamlit** pour visualiser les prévisions et recommandations
* Orchestration automatique via **Airflow**


