"""
Initialize the database with required tables and default admin user.
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import create_app
from src.models import db, User

def init_db():
    """Initialize the database with required tables and default admin user."""
    app = create_app('development')
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            
            # Create test user
            test_user = User(
                username='test',
                email='test@example.com',
                password=generate_password_hash('test123'),
                is_admin=False
            )
            db.session.add(test_user)
            
            db.session.commit()
            print("Database initialized with admin and test users.")
        else:
            print("Database already initialized.")

if __name__ == "__main__":
    init_db()
