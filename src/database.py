import os
import sqlite3
from pathlib import Path
from flask import current_app
from . import db
from .config import Config

def create_sqlite_db(db_path):
    """Create an empty SQLite database file if it doesn't exist."""
    try:
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        print(f"🔍 Ensuring database directory exists: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
        
        # Test if we can write to the directory
        test_file = os.path.join(db_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✅ Directory is writable: {db_dir}")
            
            # Create the database file
            conn = sqlite3.connect(db_path)
            conn.close()
            print(f"✅ Created SQLite database at {db_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating SQLite database: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error in create_sqlite_db: {str(e)}")
        return False

def init_database():
    """Initialize the database and create tables."""
    from .extensions import db
    from .models import User
    from werkzeug.security import generate_password_hash
    
    with current_app.app_context():
        try:
            # Get database configuration
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            db_path = current_app.config.get('DB_PATH', '')
            
            print("\n" + "="*50)
            print("🔧 DATABASE INITIALIZATION")
            print("="*50)
            print(f"📄 Database URI: {db_uri}")
            print(f"📁 Database path: {db_path}")
            
            # Check if we can write to the database directory
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                print(f"🔨 Creating database directory: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            # Create the database file if it doesn't exist
            if not os.path.exists(db_path):
                print(f"🔨 Creating database file: {db_path}")
                if not create_sqlite_db(db_path):
                    print("❌ Failed to create database file")
                    return False
            else:
                print(f"✅ Database file exists: {db_path}")
            
            # Create all database tables
            print("🔄 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Database tables: {tables}")
            
            # Create admin user if it doesn't exist
            print("👤 Checking admin user...")
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('admin123'),
                    is_admin=True,
                    preferred_language='en'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Created admin user (admin/admin123)")
            else:
                print("✅ Admin user already exists")
                
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def create_admin_user():
    """Create a default admin user if it doesn't exist."""
    from .models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            is_admin=True,
            preferred_language='en'
        )
        db.session.add(admin)
        db.session.commit()
        return True
    return False
