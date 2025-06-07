import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_database():
    from src import create_app, db
    from src.models import User
    from werkzeug.security import generate_password_hash
    
    # Create app with development config
    app = create_app('development')
    
    with app.app_context():
        # Print database path for debugging
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'chatbot.db'))
        print(f"\n🔍 Database path: {db_path}")
        print(f"   Directory exists: {os.path.exists(os.path.dirname(db_path))}")
        print(f"   Database file exists: {os.path.exists(db_path)}\n")
        
        # Try to create tables
        try:
            print("🔄 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("\n👤 Creating admin user...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('admin123'),
                    is_admin=True,
                    preferred_language='en'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created successfully!")
                print(f"   Username: admin")
                print(f"   Password: admin123")
            else:
                print("\nℹ️ Admin user already exists")
                print(f"   Username: {admin.username}")
                print(f"   Email: {admin.email}")
            
            # List all users
            print("\n👥 All users in database:")
            users = User.query.all()
            if users:
                for user in users:
                    print(f"   - {user.username} (ID: {user.id}, Email: {user.email}, Admin: {user.is_admin}")
            else:
                print("   No users found in the database")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Make sure the 'instance' directory exists and is writable")
            print("2. Check if another process is using the database file")
            print("3. Try deleting the database file and running this script again")
            print(f"   Path to delete: {db_path}")

if __name__ == '__main__':
    # Ensure instance directory exists
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    print(f"📁 Instance directory: {os.path.abspath(instance_dir)}")
    
    verify_database()
