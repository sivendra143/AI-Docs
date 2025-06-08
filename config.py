class Config:
    SECRET_KEY = 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Development(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    FLASK_APP = 'src:app'
