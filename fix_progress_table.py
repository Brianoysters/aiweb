"""
This script focuses on fixing the progress table by adding the completion_date column.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import time
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Use hardcoded value temporarily for Railway MySQL deployment
DATABASE_URL = "mysql://root:RlnjaHZoFYoaoxssxFHKtLFQlvwqninP@yamanote.proxy.rlwy.net:17657/railway"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def wait_for_db():
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the database
            db.session.execute(text("SELECT 1"))
            print("Successfully connected to the database")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to the database.")
                return False

def fix_progress_table():
    if not wait_for_db():
        return

    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"Existing tables: {existing_tables}")
        
        # Check and add missing columns to progress table
        if 'progress' in existing_tables:
            progress_columns = db.session.execute(text("SHOW COLUMNS FROM progress")).fetchall()
            progress_column_names = [col[0] for col in progress_columns]
            print(f"Existing progress columns: {progress_column_names}")
            
            if 'completion_date' not in progress_column_names:
                print("Adding completion_date column to progress table...")
                db.session.execute(text("""
                    ALTER TABLE progress
                    ADD COLUMN completion_date DATETIME NULL
                """))
                db.session.commit()
                print("Added completion_date to progress table")
                
    except Exception as e:
        print(f"Error fixing progress table: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        fix_progress_table() 