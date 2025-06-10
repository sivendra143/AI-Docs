"""
Simple script to update the database schema with the Document model.
"""
import os
import sys
import sqlite3

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')

# SQL to create the documents table
create_documents_table = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    user_id INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT 0,
    is_public BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if documents table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
    if cursor.fetchone():
        print("Documents table already exists.")
    else:
        # Create the documents table
        cursor.execute(create_documents_table)
        conn.commit()
        print("Documents table created successfully.")
    
    # Close the connection
    conn.close()
    print("Database schema updated successfully.")
except Exception as e:
    print(f"Error updating database schema: {e}")
