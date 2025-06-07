import sqlite3
import os

def test_sqlite():
    db_path = os.path.abspath('instance/test.db')
    print(f"Testing SQLite at: {db_path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Try to create and write to a test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute('''CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)''')
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()
        
        # Query the test table
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        print("✅ Successfully created and queried test database")
        print(f"Rows in test table: {rows}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_sqlite()
    if success:
        print("\nSQLite test successful! The issue might be with the application's database configuration.")
    else:
        print("\nSQLite test failed. There might be permission issues with the instance directory.")
