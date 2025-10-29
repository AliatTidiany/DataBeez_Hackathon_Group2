#!/usr/bin/env python3
"""
check_config.py

Script de validation de la configuration du projet DataBeez.
Vérifie que toutes les variables d'environnement nécessaires sont définies.
"""

import os
import sys
from pathlib import Path

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Fichier .env chargé")
except ImportError:
    print("⚠️ python-dotenv non installé")
    print("   Installez avec: pip install python-dotenv")
except FileNotFoundError:
    print("⚠️ Fichier .env non trouvé")
    print("   Copiez .env.example vers .env et configurez vos valeurs")

def check_required_vars():
    """Vérifie les variables d'environnement requises"""
    required_vars = {
        'DB_NAME': 'Nom de la base de données PostgreSQL',
        'DB_USER': 'Nom d\'utilisateur PostgreSQL',
        'DB_PASSWORD': 'Mot de passe PostgreSQL',
        'DB_HOST': 'Hôte PostgreSQL (généralement localhost)',
        'DB_PORT': 'Port PostgreSQL (généralement 5432)',
        'OPENWEATHER_API_KEY': 'Clé API OpenWeatherMap'
    }
    
    missing_vars = []
    placeholder_vars = []
    
    print("\n🔍 Vérification des variables d'environnement:")
    print("-" * 50)
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: MANQUANT - {description}")
        elif value in ['your_db_username', 'your_db_password', 'your_api_key_here', 'votre_cle_api']:
            placeholder_vars.append(var)
            print(f"⚠️ {var}: PLACEHOLDER - {description}")
        else:
            # Masquer les valeurs sensibles
            if 'password' in var.lower() or 'key' in var.lower():
                masked_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
    
    return missing_vars, placeholder_vars

def test_database_connection():
    """Teste la connexion à la base de données"""
    print("\n🔌 Test de connexion PostgreSQL:")
    print("-" * 50)
    
    try:
        from sqlalchemy import create_engine, text
        
        db_name = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        
        if not all([db_name, user, password, host, port]):
            print("❌ Variables de base de données manquantes")
            return False
        
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}")
        
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connexion réussie: {version.split(',')[0]}")
            return True
            
    except ImportError as e:
        print(f"❌ Dépendances manquantes: {e}")
        print("   Installez avec: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_api_key():
    """Teste la clé API OpenWeather"""
    print("\n🌤️ Test de la clé API OpenWeather:")
    print("-" * 50)
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        print("❌ Clé API manquante")
        return False
    
    if api_key in ['your_api_key_here', 'votre_cle_api']:
        print("❌ Clé API non configurée (placeholder détecté)")
        return False
    
    try:
        import requests
        
        # Test simple avec les coordonnées de Dakar
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": 14.7167,
            "lon": -17.4677,
            "appid": api_key,
            "exclude": "minutely,hourly,daily,alerts"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'current' in data:
                temp = data['current'].get('temp', 'N/A')
                print(f"✅ API fonctionnelle - Température Dakar: {temp}K")
                return True
            else:
                print("❌ Réponse API invalide")
                return False
        elif response.status_code == 401:
            print("❌ Clé API invalide (401 Unauthorized)")
            return False
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ Module requests manquant")
        return False
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return False

def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("\n📁 Vérification de la structure des fichiers:")
    print("-" * 50)
    
    required_files = [
        '.env.example',
        '.gitignore',
        'requirements.txt',
        'script/load_to_postgres.py',
        'script/extract_openweather.py'
    ]
    
    required_dirs = [
        'data/raw',
        'data/clean',
        'script'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MANQUANT")
            all_good = False
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"⚠️ {dir_path}/ - MANQUANT (sera créé automatiquement)")
    
    return all_good

def main():
    """Fonction principale"""
    print("🔧 Validation de la configuration DataBeez")
    print("=" * 50)
    
    # Vérification des variables
    missing_vars, placeholder_vars = check_required_vars()
    
    # Vérification de la structure
    structure_ok = check_file_structure()
    
    # Tests de connexion
    db_ok = test_database_connection()
    api_ok = test_api_key()
    
    # Résumé
    print("\n📊 Résumé:")
    print("=" * 50)
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
    
    if placeholder_vars:
        print(f"⚠️ Variables à configurer: {', '.join(placeholder_vars)}")
    
    if not missing_vars and not placeholder_vars:
        print("✅ Toutes les variables sont configurées")
    
    print(f"📁 Structure des fichiers: {'✅ OK' if structure_ok else '❌ Problèmes'}")
    print(f"🔌 Base de données: {'✅ OK' if db_ok else '❌ Problème'}")
    print(f"🌤️ API météo: {'✅ OK' if api_ok else '❌ Problème'}")
    
    if all([not missing_vars, not placeholder_vars, structure_ok, db_ok, api_ok]):
        print("\n🎉 Configuration complète et fonctionnelle!")
        return 0
    else:
        print("\n⚠️ Configuration incomplète ou problématique")
        print("   Consultez CONFIGURATION.md pour plus d'informations")
        return 1

if __name__ == "__main__":
    sys.exit(main())