import os
import sys
from pathlib import Path
import sqlite3

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_db():
    # Get the database path from the config
    from src.config import Config
    
    # Print the database path
    db_path = Config.DB_PATH
    print(f"Database path from config: {db_path}")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Try to connect directly with SQLite
    try:
        print("\n🔍 Testing direct SQLite connection...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute('''CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)''')
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()
        
        # Query the test table
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        print(f"✅ Successfully queried test table: {rows}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error with direct SQLite connection: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_direct_db()
    if success:
        print("\n✅ Direct SQLite test successful!")
    else:
        print("\n❌ Direct SQLite test failed.")
