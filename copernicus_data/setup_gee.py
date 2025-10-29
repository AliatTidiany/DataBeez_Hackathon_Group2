"""
Script de configuration pour Google Earth Engine
Auteur : Alioune MBODJI
Objectif : Installer et configurer Google Earth Engine pour l'extraction de données
"""

import subprocess
import sys
import os

def install_requirements():
    """Installer les packages Python nécessaires"""
    packages = [
        'earthengine-api',
        'pandas',
        'numpy',
        'geopandas',
        'folium',
        'matplotlib',
        'seaborn'
    ]
    
    print("📦 Installation des packages Python...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"  ✅ {package} installé")
        except subprocess.CalledProcessError:
            print(f"  ❌ Erreur lors de l'installation de {package}")

def authenticate_gee():
    """Authentifier Google Earth Engine"""
    print("\n🔐 Authentification Google Earth Engine...")
    print("1. Exécutez la commande suivante dans votre terminal :")
    print("   earthengine authenticate")
    print("\n2. Suivez les instructions pour vous connecter avec votre compte Google")
    print("3. Assurez-vous d'avoir accès à Google Earth Engine")
    print("\n💡 Si vous n'avez pas encore d'accès à GEE :")
    print("   - Visitez : https://earthengine.google.com/")
    print("   - Demandez l'accès avec votre compte Google")

def test_gee_connection():
    """Tester la connexion à Google Earth Engine"""
    print("\n🧪 Test de la connexion GEE...")
    
    test_script = """
import ee

try:
    ee.Initialize()
    print("✅ Google Earth Engine initialisé avec succès")
    
    # Test simple
    image = ee.Image('LANDSAT/LC08/C01/T1_TOA/LC08_044034_20140318')
    print(f"✅ Test d'accès aux données : {image.getInfo()['id']}")
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    print("💡 Exécutez 'earthengine authenticate' pour vous authentifier")
"""
    
    try:
        exec(test_script)
    except ImportError:
        print("❌ earthengine-api n'est pas installé")
        print("💡 Exécutez d'abord install_requirements()")

def create_requirements_file():
    """Créer un fichier requirements.txt"""
    requirements = """earthengine-api>=0.1.350
pandas>=1.3.0
numpy>=1.21.0
geopandas>=0.10.0
folium>=0.12.0
matplotlib>=3.5.0
seaborn>=0.11.0
xarray>=0.20.0
rasterio>=1.2.0
"""
    
    with open('requirements_gee.txt', 'w') as f:
        f.write(requirements)
    
    print("📄 Fichier requirements_gee.txt créé")
    print("💡 Installez avec : pip install -r requirements_gee.txt")

def main():
    """Fonction principale de configuration"""
    print("🚀 Configuration de Google Earth Engine pour le Sénégal")
    print("=" * 60)
    
    # Créer le fichier requirements
    create_requirements_file()
    
    # Installer les packages
    response = input("\n❓ Voulez-vous installer les packages Python ? (y/n): ")
    if response.lower() == 'y':
        install_requirements()
    
    # Instructions d'authentification
    authenticate_gee()
    
    # Test de connexion
    response = input("\n❓ Voulez-vous tester la connexion GEE ? (y/n): ")
    if response.lower() == 'y':
        test_gee_connection()
    
    print("\n🎉 Configuration terminée !")
    print("📝 Prochaines étapes :")
    print("1. Authentifiez-vous : earthengine authenticate")
    print("2. Exécutez : python google_earth_engine_senegal.py")

if __name__ == "__main__":
    main()