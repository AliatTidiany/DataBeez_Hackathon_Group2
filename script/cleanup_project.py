#!/usr/bin/env python3
"""
cleanup_project.py

Script de nettoyage automatique du projet DataBeez.
Supprime les fichiers temporaires, cache et redondants.
"""

import os
import shutil
from pathlib import Path

def cleanup_system_files():
    """Supprime les fichiers système (.DS_Store, etc.)"""
    print("🧹 Nettoyage des fichiers système...")
    
    system_files = ['.DS_Store', 'Thumbs.db', '._.DS_Store']
    count = 0
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file in system_files:
                file_path = Path(root) / file
                try:
                    file_path.unlink()
                    print(f"  ✅ Supprimé: {file_path}")
                    count += 1
                except Exception as e:
                    print(f"  ❌ Erreur: {file_path} - {e}")
    
    print(f"  📊 {count} fichier(s) système supprimé(s)")

def cleanup_python_cache():
    """Supprime les fichiers de cache Python"""
    print("\n🐍 Nettoyage du cache Python...")
    
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(Path(root) / '__pycache__')
    
    count = 0
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✅ Supprimé: {cache_dir}")
            count += 1
        except Exception as e:
            print(f"  ❌ Erreur: {cache_dir} - {e}")
    
    print(f"  📊 {count} dossier(s) de cache supprimé(s)")

def cleanup_temp_files():
    """Supprime les fichiers temporaires"""
    print("\n🗑️ Nettoyage des fichiers temporaires...")
    
    temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak', '*.old']
    count = 0
    
    for pattern in temp_patterns:
        for file_path in Path('.').rglob(pattern):
            try:
                file_path.unlink()
                print(f"  ✅ Supprimé: {file_path}")
                count += 1
            except Exception as e:
                print(f"  ❌ Erreur: {file_path} - {e}")
    
    print(f"  📊 {count} fichier(s) temporaire(s) supprimé(s)")

def cleanup_logs():
    """Supprime les anciens fichiers de log"""
    print("\n📋 Nettoyage des logs...")
    
    log_files = list(Path('.').rglob('*.log'))
    count = 0
    
    for log_file in log_files:
        try:
            log_file.unlink()
            print(f"  ✅ Supprimé: {log_file}")
            count += 1
        except Exception as e:
            print(f"  ❌ Erreur: {log_file} - {e}")
    
    print(f"  📊 {count} fichier(s) de log supprimé(s)")

def show_project_size():
    """Affiche la taille du projet"""
    print("\n📊 Taille du projet:")
    
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk('.'):
        # Exclure certains dossiers
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv_DataBeez', 'node_modules']]
        
        for file in files:
            file_path = Path(root) / file
            try:
                size = file_path.stat().st_size
                total_size += size
                file_count += 1
            except:
                continue
    
    # Conversion en unités lisibles
    if total_size < 1024:
        size_str = f"{total_size} B"
    elif total_size < 1024**2:
        size_str = f"{total_size/1024:.1f} KB"
    elif total_size < 1024**3:
        size_str = f"{total_size/(1024**2):.1f} MB"
    else:
        size_str = f"{total_size/(1024**3):.1f} GB"
    
    print(f"  📁 Fichiers: {file_count}")
    print(f"  💾 Taille totale: {size_str}")

def main():
    """Fonction principale de nettoyage"""
    print("🧹 Nettoyage Automatique du Projet DataBeez")
    print("=" * 50)
    
    # Vérifier qu'on est dans le bon répertoire
    if not Path('README.md').exists() or not Path('script').exists():
        print("❌ Erreur: Ce script doit être exécuté depuis la racine du projet DataBeez")
        return 1
    
    try:
        cleanup_system_files()
        cleanup_python_cache()
        cleanup_temp_files()
        cleanup_logs()
        show_project_size()
        
        print(f"\n🎉 Nettoyage terminé avec succès!")
        print("✨ Projet DataBeez nettoyé et optimisé")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erreur lors du nettoyage: {e}")
        return 1

if __name__ == "__main__":
    exit(main())