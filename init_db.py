from app import app, db
from flask_migrate import upgrade, stamp
import time
import pymysql

def wait_for_db():
    max_attempts = 5
    current_attempt = 0
    
    while current_attempt < max_attempts:
        try:
            connection = pymysql.connect(
                host="sql8.freesqldatabase.com",
                user="sql8769838",
                password="WHUW9lqTPD",
                database="sql8769838",
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

def init_db():
    print("Starting database initialization...")
    if not wait_for_db():
        return False
        
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("Tables created successfully!")
            
            print("Initializing migrations...")
            stamp()
            print("Database stamped with current migration!")
            
            return True
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_db()
    if success:
        print("Database initialization completed successfully!")
    else:
        print("Database initialization failed!")
