import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Database Configuration
    MYSQL_HOST = '127.0.0.1'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '1234'
    MYSQL_DB = 'dog_cat_classifier'
    MYSQL_PORT = 3306
    
    # FastAPI Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production-12345'
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_UPLOAD_FILES = 20
    
    # Model Configuration
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'cat_dog_dl_model.h5')
    
    # Server Configuration
    HOST = '127.0.0.1'
    PORT = 8000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}