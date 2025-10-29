#!/usr/bin/env python3
"""
main_gee_pipeline.py

Pipeline principal pour l'orchestration complète des données GEE
- Extraction des données satellitaires
- Traitement et consolidation
- Analyses et visualisations
- Génération de rapports
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import time

# Configuration
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR

def run_script(script_path, description):
    """Exécute un script Python avec gestion d'erreurs"""
    print(f"🔄 {description}...")
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - Terminé en {duration:.1f}s")
            return True, result.stdout
        else:
            print(f"❌ {description} - Échec")
            print(f"Erreur: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False, str(e)

def check_prerequisites():
    """Vérifie les prérequis avant l'exécution"""
    print("🔍 Vérification des prérequis...")
    
    # Vérifier les scripts requis
    required_scripts = [
        'google_earth_engine_senegal.py',
        'analyze_gee_data.py',
        'create_dashboard.py'
    ]
    
    missing_scripts = []
    for script in required_scripts:
        script_path = SCRIPTS_DIR / script
        if not script_path.exists():
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Scripts manquants: {missing_scripts}")
        return False
    
    # Vérifier l'authentification GEE
    try:
        import ee
        ee.Initialize()
        print("✅ Google Earth Engine authentifié")
    except Exception as e:
        print(f"❌ Problème d'authentification GEE: {e}")
        print("   Exécutez: earthengine authenticate")
        return False
    
    print("✅ Tous les prérequis sont satisfaits")
    return True

def extract_gee_data():
    """Étape 1: Extraction des données GEE"""
    script_path = SCRIPTS_DIR / 'google_earth_engine_senegal.py'
    return run_script(script_path, "Extraction des données Google Earth Engine")

def organize_data():
    """Étape 2: Organisation des données (si le script existe)"""
    script_path = SCRIPTS_DIR / 'organize_data_structure.py'
    
    if script_path.exists():
        return run_script(script_path, "Organisation de la structure des données")
    else:
        print("ℹ️ Script d'organisation non trouvé - Étape ignorée")
        return True, "Skipped"

def analyze_data():
    """Étape 3: Analyse des données"""
    script_path = SCRIPTS_DIR / 'analyze_gee_data.py'
    return run_script(script_path, "Analyse avancée des données")

def create_dashboard():
    """Étape 4: Création du dashboard"""
    script_path = SCRIPTS_DIR / 'create_dashboard.py'
    return run_script(script_path, "Création du dashboard interactif")

def generate_pipeline_report(results):
    """Génère un rapport du pipeline"""
    print("📋 Génération du rapport du pipeline...")
    
    report = {
        'pipeline_execution': {
            'timestamp': datetime.now().isoformat(),
            'total_steps': len(results),
            'successful_steps': sum(1 for success, _ in results.values() if success),
            'failed_steps': sum(1 for success, _ in results.values() if not success)
        },
        'step_results': {}
    }
    
    # Détails par étape
    step_names = {
        'extract': 'Extraction GEE',
        'organize': 'Organisation des données',
        'analyze': 'Analyse des données',
        'dashboard': 'Création du dashboard'
    }
    
    for step, (success, output) in results.items():
        report['step_results'][step] = {
            'name': step_names.get(step, step),
            'success': success,
            'output_preview': output[:200] + '...' if len(output) > 200 else output
        }
    
    # Sauvegarder le rapport
    output_dir = BASE_DIR / 'data' / 'gee_senegal' / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / 'pipeline_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Rapport sauvegardé: {report_file}")
    return report

def display_summary(results, report):
    """Affiche un résumé de l'exécution"""
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ DU PIPELINE GEE")
    print(f"{'='*60}")
    
    total_steps = report['pipeline_execution']['total_steps']
    successful_steps = report['pipeline_execution']['successful_steps']
    
    print(f"⏱️ Exécuté le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    print(f"✅ Étapes réussies: {successful_steps}/{total_steps}")
    
    if successful_steps == total_steps:
        print(f"🎉 PIPELINE TERMINÉ AVEC SUCCÈS!")
        print(f"\n📁 Résultats disponibles dans:")
        print(f"   - data/gee_senegal/raw/ (données brutes)")
        print(f"   - data/gee_senegal/processed/ (données consolidées)")
        print(f"   - data/gee_senegal/analysis/ (analyses et dashboard)")
    else:
        print(f"⚠️ PIPELINE PARTIELLEMENT TERMINÉ")
        print(f"\n❌ Étapes échouées:")
        for step, (success, _) in results.items():
            if not success:
                step_name = {
                    'extract': 'Extraction GEE',
                    'organize': 'Organisation des données', 
                    'analyze': 'Analyse des données',
                    'dashboard': 'Création du dashboard'
                }.get(step, step)
                print(f"   - {step_name}")
    
    print(f"\n📋 Rapport détaillé: data/gee_senegal/analysis/pipeline_report.json")

def main():
    """Fonction principale du pipeline"""
    print("🚀 Pipeline Principal GEE Sénégal - DataBeez")
    print("=" * 60)
    print(f"Démarrage: {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Vérifier les prérequis
    if not check_prerequisites():
        print("❌ Prérequis non satisfaits - Arrêt du pipeline")
        return 1
    
    # Exécuter les étapes du pipeline
    pipeline_steps = [
        ('extract', extract_gee_data, "Extraction des données satellitaires"),
        ('organize', organize_data, "Organisation des données"),
        ('analyze', analyze_data, "Analyse avancée des données"),
        ('dashboard', create_dashboard, "Création du dashboard")
    ]
    
    results = {}
    
    print(f"\n🔄 Exécution du pipeline ({len(pipeline_steps)} étapes)...")
    
    for step_id, step_func, step_desc in pipeline_steps:
        print(f"\n{'='*20} {step_desc} {'='*20}")
        
        success, output = step_func()
        results[step_id] = (success, output)
        
        if not success and step_id in ['extract']:  # Étapes critiques
            print(f"❌ Étape critique échouée: {step_desc}")
            print("🛑 Arrêt du pipeline")
            break
    
    # Générer le rapport
    report = generate_pipeline_report(results)
    
    # Afficher le résumé
    display_summary(results, report)
    
    # Code de retour
    successful_steps = sum(1 for success, _ in results.values() if success)
    total_steps = len(results)
    
    if successful_steps == total_steps:
        return 0  # Succès complet
    elif successful_steps >= total_steps * 0.5:
        return 1  # Succès partiel
    else:
        return 2  # Échec majeur

if __name__ == "__main__":
    exit(main())