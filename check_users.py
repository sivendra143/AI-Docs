from src import create_app
from src.models import User, db

def check_users():
    app = create_app('development')
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"✅ Admin user found! ID: {admin.id}, Email: {admin.email}")
            print(f"Password hash: {admin.password}")
        else:
            print("❌ Admin user not found!")
        
        # List all users
        print("\nAll users in database:")
        users = User.query.all()
        for user in users:
            print(f"- {user.username} (ID: {user.id}, Email: {user.email}, Admin: {user.is_admin})")

if __name__ == '__main__':
    check_users()
