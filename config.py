import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Local MySQL Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db').replace('mysql://', 'mysql+pymysql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
