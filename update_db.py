"""
Update the database schema with new Document model.
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix encoding issue in config.py before importing
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'config.py')
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove emoji characters that cause encoding issues
    content = content.replace('\U0001f4c1', '')
    content = content.replace('🔑', '')
    content = content.replace('📁', '')
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

from src import create_app
from src.models import db, Document

def update_db():
    """Update the database schema with new Document model."""
    app = create_app()
    
    with app.app_context():
        # Check if Document table exists
        try:
            Document.query.first()
            print("Document table already exists.")
        except Exception as e:
            print(f"Creating Document table: {e}")
            # Create Document table
            db.create_all()
            print("Database schema updated with Document table.")

if __name__ == "__main__":
    update_db()
