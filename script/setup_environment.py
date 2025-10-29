#!/usr/bin/env python3
"""
setup_environment.py

Script d'aide à la configuration initiale de l'environnement DataBeez
"""

import os
from pathlib import Path
import subprocess
import sys

def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Vérification de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Installe les dépendances de base"""
    print("📦 Installation des dépendances de base...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], check=True)
        print("✅ python-dotenv installé")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur installation python-dotenv")
        return False

def setup_env_file():
    """Configure le fichier .env"""
    print("🔧 Configuration du fichier .env...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ Fichier .env.example manquant")
        return False
    
    if env_file.exists():
        response = input("📄 Le fichier .env existe déjà. Le remplacer ? (y/N): ")
        if response.lower() != 'y':
            print("✅ Fichier .env conservé")
            return True
    
    # Copier .env.example vers .env
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Fichier .env créé depuis .env.example")
    print("⚠️ N'oubliez pas de modifier .env avec vos vraies valeurs !")
    
    return True

def run_config_check():
    """Lance la vérification de configuration"""
    print("🔍 Vérification de la configuration...")
    
    try:
        result = subprocess.run([sys.executable, "script/check_config.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("🎉 Configuration validée avec succès !")
            return True
        else:
            print("⚠️ Problèmes de configuration détectés")
            print("📝 Modifiez le fichier .env avec vos vraies valeurs")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def show_next_steps():
    """Affiche les prochaines étapes"""
    print("\n📋 Prochaines étapes:")
    print("1. Modifiez le fichier .env avec vos vraies valeurs")
    print("2. Installez toutes les dépendances: pip install -r requirements.txt")
    print("3. Configurez PostgreSQL et Google Earth Engine")
    print("4. Lancez: python script/check_config.py")
    print("\n📚 Consultez le README.md pour plus de détails")

def main():
    """Fonction principale"""
    print("🚀 Configuration Initiale DataBeez")
    print("=" * 40)
    
    steps = [
        ("Vérification Python", check_python_version),
        ("Installation dépendances", install_dependencies),
        ("Configuration .env", setup_env_file),
        ("Vérification config", run_config_check)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if step_func():
            success_count += 1
        else:
            print(f"❌ Échec: {step_name}")
            break
    
    print(f"\n{'='*40}")
    if success_count == len(steps):
        print("🎉 Configuration initiale terminée !")
    else:
        print(f"⚠️ Configuration partielle ({success_count}/{len(steps)})")
        show_next_steps()

if __name__ == "__main__":
    main()