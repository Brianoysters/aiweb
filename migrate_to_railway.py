from app import app, db
import os
from dotenv import load_dotenv
import time
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def wait_for_db():
    max_attempts = 5
    current_attempt = 0
    
    while current_attempt < max_attempts:
        try:
            # Hardcode the correct Railway URL for testing
            db_url = "mysql://root:hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM@gondola.proxy.rlwy.net:41520/railway"
            print(f"Using database URL: {db_url}")
            
            parts = db_url.split('://')[1].split('@')
            user_pass = parts[0].split(':')
            host_port = parts[1].split('/')
            host_parts = host_port[0].split(':')
            
            print(f"Connecting to {host_parts[0]} on port {host_parts[1]}...")
            
            connection = pymysql.connect(
                host=host_parts[0],
                port=int(host_parts[1]),
                user=user_pass[0],
                password=user_pass[1],
                database='railway',
                connect_timeout=30
            )
            print("Testing connection...")
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    print("Database connection verified!")
            connection.close()
            return True
        except Exception as e:
            current_attempt += 1
            if current_attempt < max_attempts:
                print(f"Connection attempt {current_attempt} failed. Retrying in 5 seconds... Error: {str(e)}")
                time.sleep(5)
            else:
                print(f"Failed to connect to database after {max_attempts} attempts: {str(e)}")
                return False

def migrate_db():
    print("Starting database migration...")
    if not wait_for_db():
        return False
        
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("Tables created successfully!")
            
            # If you have any initial data to migrate, you can add it here
            # For example:
            # from app import User, Module
            # new_user = User(username='admin', email='admin@example.com', password_hash='hashed_password')
            # db.session.add(new_user)
            # db.session.commit()
            
            print("Database migration completed successfully!")
            return True
        except Exception as e:
            print(f"Error during database migration: {str(e)}")
            return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    print("Environment variables loaded")
    
    success = migrate_db()
    if success:
        print("Database migration completed successfully!")
    else:
        print("Database migration failed!") 