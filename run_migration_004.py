"""
Run migration 004: Japanese Training Tables
"""
import sys
from sqlalchemy import text
from config.database import SessionLocal

def run_migration():
    try:
        # Get database session
        db = SessionLocal()
        
        # Read migration file
        with open('db_migrations/004_add_japanese_training.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute migration
        db.execute(text(sql))
        db.commit()
        db.close()
        
        print("✓ Migration 004 executed successfully")
        print("✓ Created 20 Japanese training tables")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
