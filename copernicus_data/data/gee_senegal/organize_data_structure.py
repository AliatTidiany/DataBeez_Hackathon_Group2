"""
Script de Réorganisation des Données GEE Sénégal
Auteur : Alioune MBODJI
Objectif : Organiser les fichiers dans une structure claire (raw, processed, analysis)
"""

import os
import shutil
import glob
from pathlib import Path

def organize_gee_data():
    """Organiser les données dans une structure claire"""
    
    data_dir = Path("data/gee_senegal")
    
    # Créer les dossiers de structure
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    analysis_dir = data_dir / "analysis"
    
    # Créer les dossiers s'ils n'existent pas
    raw_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)
    analysis_dir.mkdir(exist_ok=True)
    
    print("📁 Réorganisation de la structure des données...")
    print("=" * 60)
    
    moved_files = {"raw": 0, "processed": 0, "analysis": 0}
    
    # Parcourir tous les fichiers dans le répertoire principal
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            
            # === DONNÉES BRUTES (RAW) ===
            # Fichiers par source de données (ERA5, CHIRPS, MODIS, SMAP)
            if any(source in filename.lower() for source in ['era5', 'chirps', 'modis', 'smap']):
                destination = raw_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"📦 RAW: {filename}")
                    moved_files["raw"] += 1
            
            # === DONNÉES TRAITÉES (PROCESSED) ===
            # Fichiers consolidés par région
            elif filename.endswith('_consolidated_data.csv'):
                destination = processed_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"🔄 PROCESSED: {filename}")
                    moved_files["processed"] += 1
            
            # Statistiques descriptives
            elif filename in ['summary_statistics.csv']:
                destination = processed_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"🔄 PROCESSED: {filename}")
                    moved_files["processed"] += 1
            
            # === ANALYSES ET VISUALISATIONS (ANALYSIS) ===
            # Graphiques et visualisations
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                destination = analysis_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"📊 ANALYSIS: {filename}")
                    moved_files["analysis"] += 1
            
            # Cartes et dashboards interactifs
            elif filename.endswith(('.html', '.htm')):
                destination = analysis_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"🌐 ANALYSIS: {filename}")
                    moved_files["analysis"] += 1
            
            # Rapports et documentation
            elif filename.endswith(('.md', '.txt', '.pdf')):
                destination = analysis_dir / filename
                if not destination.exists():
                    shutil.move(str(file_path), str(destination))
                    print(f"📋 ANALYSIS: {filename}")
                    moved_files["analysis"] += 1
            
            # Fichiers système à ignorer
            elif filename.startswith('.'):
                print(f"⏩ IGNORÉ: {filename} (fichier système)")
            
            else:
                print(f"❓ NON CLASSÉ: {filename}")
    
    print("\n" + "=" * 60)
    print("📊 Résumé de la réorganisation :")
    print(f"  📦 RAW (données brutes) : {moved_files['raw']} fichiers")
    print(f"  🔄 PROCESSED (données traitées) : {moved_files['processed']} fichiers")
    print(f"  📊 ANALYSIS (analyses/visualisations) : {moved_files['analysis']} fichiers")
    print(f"  📁 Total déplacé : {sum(moved_files.values())} fichiers")

def create_data_structure_by_region():
    """Créer une sous-structure par région dans raw/"""
    
    raw_dir = Path("data/gee_senegal/raw")
    
    if not raw_dir.exists():
        print("❌ Le dossier raw/ n'existe pas encore")
        return
    
    print("\n📂 Création de la structure par région...")
    
    # Identifier toutes les régions
    regions = set()
    for file_path in raw_dir.glob("*.csv"):
        filename = file_path.name
        # Extraire le nom de la région (avant le premier underscore)
        if '_' in filename:
            region = filename.split('_')[0]
            regions.add(region)
    
    # Créer les dossiers par région
    for region in sorted(regions):
        region_dir = raw_dir / region
        region_dir.mkdir(exist_ok=True)
        
        # Déplacer les fichiers de cette région
        moved_count = 0
        for file_path in raw_dir.glob(f"{region}_*.csv"):
            destination = region_dir / file_path.name
            if not destination.exists():
                shutil.move(str(file_path), str(destination))
                moved_count += 1
        
        if moved_count > 0:
            print(f"  📁 {region.title()}: {moved_count} fichiers")

def create_data_structure_by_source():
    """Créer une sous-structure par source de données dans raw/"""
    
    raw_dir = Path("data/gee_senegal/raw")
    
    if not raw_dir.exists():
        print("❌ Le dossier raw/ n'existe pas encore")
        return
    
    print("\n🛰️ Création de la structure par source de données...")
    
    # Définir les sources de données
    sources = {
        'era5': 'ERA5_Land',
        'chirps': 'CHIRPS',
        'modis_temp': 'MODIS_Temperature',
        'modis_vi': 'MODIS_Vegetation',
        'smap': 'SMAP_SoilMoisture'
    }
    
    # Créer les dossiers par source
    for source_key, source_name in sources.items():
        source_dir = raw_dir / source_name
        source_dir.mkdir(exist_ok=True)
        
        # Déplacer les fichiers de cette source
        moved_count = 0
        pattern = f"*_{source_key}_*.csv"
        
        for file_path in raw_dir.glob(pattern):
            destination = source_dir / file_path.name
            if not destination.exists():
                shutil.move(str(file_path), str(destination))
                moved_count += 1
        
        if moved_count > 0:
            print(f"  🛰️ {source_name}: {moved_count} fichiers")

def create_readme_files():
    """Créer des fichiers README pour chaque dossier"""
    
    data_dir = Path("data/gee_senegal")
    
    # README pour le dossier raw/
    raw_readme = """# Données Brutes (Raw Data)

Ce dossier contient les données brutes extraites directement de Google Earth Engine.

## Structure
- **ERA5_Land/** : Données météorologiques ERA5-Land
- **CHIRPS/** : Données de précipitations CHIRPS
- **MODIS_Temperature/** : Données de température MODIS
- **MODIS_Vegetation/** : Indices de végétation MODIS (NDVI, EVI)
- **SMAP_SoilMoisture/** : Données d'humidité du sol SMAP

## Format
- Fichiers CSV avec colonnes : date, région, latitude, longitude, variables
- Un fichier par région et par source de données
- Données non traitées, telles qu'extraites de GEE
"""
    
    # README pour le dossier processed/
    processed_readme = """# Données Traitées (Processed Data)

Ce dossier contient les données consolidées et traitées.

## Contenu
- **{region}_consolidated_data.csv** : Données fusionnées par région
- **summary_statistics.csv** : Statistiques descriptives par région

## Format
- Données nettoyées et harmonisées
- Toutes les sources fusionnées par région
- Métadonnées ajoutées (région, coordonnées)
"""
    
    # README pour le dossier analysis/
    analysis_readme = """# Analyses et Visualisations

Ce dossier contient tous les résultats d'analyse et visualisations.

## Graphiques
- **temperature_analysis.png** : Analyse des tendances de température
- **precipitation_analysis.png** : Analyse des précipitations
- **vegetation_analysis.png** : Analyse de la végétation (NDVI/EVI)
- **data_availability_heatmap.png** : Disponibilité des données
- **regions_temperature_comparison.png** : Comparaison inter-régionale

## Cartes Interactives
- **senegal_regions_map.html** : Carte interactive des régions
- **dashboard_senegal_gee.html** : Tableau de bord complet

## Rapports
- **analysis_report.md** : Rapport d'analyse détaillé
"""
    
    # Écrire les fichiers README
    readme_files = [
        (data_dir / "raw" / "README.md", raw_readme),
        (data_dir / "processed" / "README.md", processed_readme),
        (data_dir / "analysis" / "README.md", analysis_readme)
    ]
    
    for readme_path, content in readme_files:
        if readme_path.parent.exists():
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 README créé : {readme_path}")

def show_final_structure():
    """Afficher la structure finale des dossiers"""
    
    data_dir = Path("data/gee_senegal")
    
    print("\n🌳 Structure finale des données :")
    print("=" * 50)
    
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        
        if not directory.exists():
            return
        
        items = sorted(directory.iterdir())
        dirs = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]
        
        # Afficher les dossiers
        for i, item in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and len(files) == 0
            current_prefix = "└── " if is_last_dir else "├── "
            print(f"{prefix}{current_prefix}📁 {item.name}/")
            
            next_prefix = prefix + ("    " if is_last_dir else "│   ")
            print_tree(item, next_prefix, max_depth, current_depth + 1)
        
        # Afficher quelques fichiers (limité pour la lisibilité)
        if files and current_depth < 2:
            file_count = len(files)
            show_count = min(3, file_count)
            
            for i, item in enumerate(files[:show_count]):
                is_last = (i == show_count - 1) and (show_count == file_count)
                current_prefix = "└── " if is_last else "├── "
                
                # Icône selon le type de fichier
                if item.suffix == '.csv':
                    icon = "📊"
                elif item.suffix in ['.png', '.jpg']:
                    icon = "🖼️"
                elif item.suffix in ['.html', '.htm']:
                    icon = "🌐"
                elif item.suffix == '.md':
                    icon = "📝"
                else:
                    icon = "📄"
                
                print(f"{prefix}{current_prefix}{icon} {item.name}")
            
            if file_count > show_count:
                print(f"{prefix}└── ... et {file_count - show_count} autres fichiers")
    
    print_tree(data_dir)

def main():
    """Fonction principale de réorganisation"""
    
    print("🗂️ Réorganisation de la Structure des Données GEE Sénégal")
    print("=" * 70)
    
    # Étape 1: Organisation de base
    organize_gee_data()
    
    # Étape 2: Structure par source de données
    create_data_structure_by_source()
    
    # Étape 3: Créer les fichiers README
    create_readme_files()
    
    # Étape 4: Afficher la structure finale
    show_final_structure()
    
    print("\n🎉 Réorganisation terminée !")
    print("💡 Utilisez 'ls -la data/gee_senegal/' pour voir la nouvelle structure")

if __name__ == "__main__":
    main()