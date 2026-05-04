import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Aiven MySQL Connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SSL Configuration para sa Aiven (kailangan ito!)
    if SQLALCHEMY_DATABASE_URI and 'aivencloud.com' in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'ssl': {'ca': 'ca.pem'}
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