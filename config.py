import os

class Config:
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in Render
    
    # Database Configuration - Uses Render's PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Remove the Aiven SSL block - not needed for Render
    # (Delete the entire SQLALCHEMY_ENGINE_OPTIONS block)
    
    # Email Configuration (same)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # PayMongo Configuration
    PAYMONGO_SECRET_KEY = os.environ.get('PAYMONGO_SECRET_KEY')
    PAYMONGO_PUBLIC_KEY = os.environ.get('PAYMONGO_PUBLIC_KEY')
    PAYMONGO_WEBHOOK_SECRET = os.environ.get('PAYMONGO_WEBHOOK_SECRET')