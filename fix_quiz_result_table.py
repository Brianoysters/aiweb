"""
This script focuses on fixing the quiz_result table by adding missing columns.
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

def fix_quiz_result_table():
    if not wait_for_db():
        return

    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"Existing tables: {existing_tables}")
        
        # Check and add missing columns to quiz_result table
        if 'quiz_result' in existing_tables:
            quiz_result_columns = db.session.execute(text("SHOW COLUMNS FROM quiz_result")).fetchall()
            quiz_result_column_names = [col[0] for col in quiz_result_columns]
            print(f"Existing quiz_result columns: {quiz_result_column_names}")
            
            missing_quiz_result_columns = []
            
            if 'completion_date' not in quiz_result_column_names:
                missing_quiz_result_columns.append("ADD COLUMN completion_date DATETIME NULL")
            
            if 'next_attempt_available' not in quiz_result_column_names:
                missing_quiz_result_columns.append("ADD COLUMN next_attempt_available DATETIME NULL")
            
            if 'attempt_number' not in quiz_result_column_names:
                missing_quiz_result_columns.append("ADD COLUMN attempt_number INT NOT NULL DEFAULT 1")
            
            if missing_quiz_result_columns:
                alter_quiz_result_query = f"ALTER TABLE quiz_result {', '.join(missing_quiz_result_columns)}"
                print(f"Executing: {alter_quiz_result_query}")
                db.session.execute(text(alter_quiz_result_query))
                db.session.commit()
                print("Added missing columns to quiz_result table")
            else:
                print("No missing columns found in quiz_result table")
        else:
            print("quiz_result table not found in database")
                
    except Exception as e:
        print(f"Error fixing quiz_result table: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        fix_quiz_result_table() 