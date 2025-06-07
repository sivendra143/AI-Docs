import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_db_uri():
    from src import create_app
    
    # Create app with development config
    app = create_app('development')
    
    print("\n🔍 Database Configuration:")
    print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Instance path: {app.instance_path}")
    
    # Try to access the database
    try:
        from src import db
        with app.app_context():
            print("\n🔍 Testing database connection...")
            db.engine.connect()
            print("✅ Successfully connected to the database")
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == '__main__':
    check_db_uri()
