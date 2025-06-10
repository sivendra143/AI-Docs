"""Configuration settings for the application."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # Database settings - Using a file in the project directory
    DB_DIR = os.path.abspath(os.path.join(BASE_DIR, 'data'))
    DB_FILENAME = 'chatbot.db'
    
    # Ensure the data directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Create the full database path
    DB_PATH = os.path.join(DB_DIR, DB_FILENAME)
    
    # Format SQLite URI with forward slashes for Windows compatibility
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH.replace(os.sep, "/")}'
    
    print(f"\nDatabase path: {DB_PATH}")
    print(f"Database URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'csv', 'xlsx'}
    
    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000,file://*').split(',')
    
    # Chat settings
    CHAT_HISTORY_LIMIT = 20
    DEFAULT_LANGUAGE = 'en'
    
    # Model settings
    MODEL_NAME = os.environ.get('MODEL_NAME', 'all-MiniLM-L6-v2')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    
    @staticmethod
    def init_app(app):
        """Initialize configuration."""
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        # Create instance folder if it doesn't exist
        os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
