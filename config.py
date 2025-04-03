import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DATABASE_URL = "mysql+pymysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
