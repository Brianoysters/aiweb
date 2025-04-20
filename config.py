import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    # old mysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway
    DATABASE_URL = "mysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway"
    #DATABASE_URL = "mysql://root:RlnjaHZoFYoaoxssxFHKtLFQlvwqninP@yamanote.proxy.rlwy.net:17657/railway"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SESSION_COOKIE_SECURE = True
