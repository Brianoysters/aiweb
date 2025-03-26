from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

def setup_database():
    try:
        # Replace these with your actual database credentials for production
        DB_USER = os.getenv('DB_USER', 'your_username')
        DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_NAME = os.getenv('DB_NAME', 'certificate_db')

        # Create database URL
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # SQL queries for creating tables
        create_certificates_table = text("""
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course VARCHAR(100) NOT NULL,
                date_issued TIMESTAMP NOT NULL,
                certificate_id VARCHAR(50) UNIQUE NOT NULL
            );
        """)
        
        # Execute the queries
        with engine.connect() as conn:
            conn.execute(create_certificates_table)
            conn.commit()
            
        print("Database and tables created successfully!")
        return True
        
    except SQLAlchemyError as e:
        print(f"An error occurred while setting up the database: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database()
