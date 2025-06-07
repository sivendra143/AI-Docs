"""Test SQLite connection and database creation."""
import os
import sqlite3
from pathlib import Path

def test_sqlite_connection():
    """Test SQLite connection and database creation."""
    # Try to create a test database in the current directory
    test_db_path = os.path.abspath('test_sqlite.db')
    print(f"\n{'='*50}")
    print("🔍 TESTING SQLITE CONNECTION")
    print(f"{'='*50}")
    print(f"📁 Test database path: {test_db_path}")
    
    try:
        # Try to create a new database file
        print("\n🔄 Creating test database...")
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert a test record
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()
        
        # Query the test record
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        
        print(f"✅ Successfully created and queried test database")
        print(f"📝 Test record: {result}")
        
        # Clean up
        cursor.close()
        conn.close()
        
        # Delete the test database file
        os.remove(test_db_path)
        print("🧹 Cleaned up test database")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sqlite_connection()
