import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    # Database Configuration
    # old mysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway
    # old DATABASE_URL = "mysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway"
    DATABASE_URL = "mysql://root:RlnjaHZoFYoaoxssxFHKtLFQlvwqninP@yamanote.proxy.rlwy.net:17657/railway"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Logging config
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'true').lower() == 'true'
