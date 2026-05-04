import os

class Config:
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    
    # Database Configuration - Aiven MySQL
    # Get the full connection string from Aiven dashboard
    # Format: mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://avnadmin:AVNS_ZWOExSxvktrGoscBW4M@mysql-2f4eacb9-salvadorearl8-09a8.l.aivencloud.com:10310/defaultdb?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SSL Configuration for Aiven MySQL
    # Using the absolute path to ca.pem file (download from Aiven dashboard)
    ca_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ca.pem')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'ssl': {'ca': ca_path}
        }
    }
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'salvadorearl8@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # PayMongo Configuration
    PAYMONGO_SECRET_KEY = os.environ.get('PAYMONGO_SECRET_KEY', '')
    PAYMONGO_PUBLIC_KEY = os.environ.get('PAYMONGO_PUBLIC_KEY', '')
    PAYMONGO_WEBHOOK_SECRET = os.environ.get('PAYMONGO_WEBHOOK_SECRET', '')