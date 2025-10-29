"""
test_postgres_connection.py

Script de test pour vérifier la connexion PostgreSQL et les données
"""

from sqlalchemy import create_engine, text
import pandas as pd

# Paramètres de connexion
DB_NAME = "projet_DataBeez"
USER = os.getenv("DB_USER", "your_db_username")
PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
HOST = "localhost"
PORT = "5432"

def test_connection():
    """Tester la connexion à PostgreSQL"""
    
    print("🔌 Test de connexion PostgreSQL...")
    
    try:
        engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}")
        
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connexion réussie!")
            print(f"📊 Version PostgreSQL: {version}")
        
        return engine
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def check_tables(engine):
    """Vérifier les tables existantes"""
    
    print("\n📋 Vérification des tables...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                print("✅ Tables trouvées:")
                for table in tables:
                    print(f"  📄 {table}")
            else:
                print("⚠️ Aucune table trouvée")
            
            return tables
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des tables: {e}")
        return []

def check_data_summary(engine):
    """Vérifier le résumé des données si la vue existe"""
    
    print("\n📊 Vérification des données...")
    
    try:
        with engine.begin() as conn:
            # Vérifier si la vue data_summary existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views 
                    WHERE table_name = 'data_summary'
                );
            """))
            
            view_exists = result.scalar()
            
            if view_exists:
                result = conn.execute(text("SELECT * FROM data_summary ORDER BY source;"))
                
                print("✅ Résumé des données:")
                for row in result:
                    source, records, min_year, max_year, regions = row
                    region_info = f", {regions} régions" if regions else ""
                    print(f"  📈 {source}: {records:,} enregistrements ({min_year}-{max_year}){region_info}")
            else:
                print("⚠️ Vue data_summary non trouvée - vérification manuelle...")
                
                # Vérifier chaque table individuellement
                tables_to_check = ['fao_data', 'weather_data', 'gee_senegal_agro_data']
                
                for table in tables_to_check:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                        count = result.scalar()
                        print(f"  📄 {table}: {count:,} enregistrements")
                    except:
                        print(f"  ❌ {table}: table non trouvée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des données: {e}")

def check_gee_regions(engine):
    """Vérifier les régions GEE si la table existe"""
    
    print("\n🌍 Vérification des régions GEE...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT region, COUNT(*) as count 
                FROM gee_senegal_agro_data 
                GROUP BY region 
                ORDER BY region;
            """))
            
            print("✅ Régions GEE:")
            for row in result:
                print(f"  📍 {row[0]}: {row[1]:,} enregistrements")
                
    except Exception as e:
        print(f"⚠️ Table GEE non disponible: {e}")

def main():
    """Fonction principale de test"""
    
    print("🧪 Test de Connexion et Vérification des Données PostgreSQL")
    print("=" * 65)
    
    # Test de connexion
    engine = test_connection()
    
    if engine is None:
        print("\n❌ Impossible de continuer sans connexion")
        return
    
    # Vérifier les tables
    tables = check_tables(engine)
    
    # Vérifier les données
    check_data_summary(engine)
    
    # Vérifier les régions GEE
    if 'gee_senegal_agro_data' in tables:
        check_gee_regions(engine)
    
    print(f"\n{'='*65}")
    print("🎉 Test terminé!")
    
    if len(tables) > 0:
        print("💡 Connexion PostgreSQL opérationnelle")
        print("💡 Vous pouvez maintenant exécuter load_to_postgres.py")
    else:
        print("💡 Exécutez load_to_postgres.py pour créer les tables")

if __name__ == "__main__":
    main()