import os
from src import create_app, db
from src.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    # Create app with development config
    app = create_app('development')
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Create admin user
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
            print(f"Username: admin")
            print(f"Password: admin123")
        else:
            print("ℹ️ Admin user already exists!")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")

if __name__ == '__main__':
    # Ensure instance folder exists
    os.makedirs('instance', exist_ok=True)
    create_admin_user()
