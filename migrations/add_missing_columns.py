"""
This script adds missing columns to the existing database tables
to match the SQLAlchemy model definitions.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
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

def add_missing_columns():
    if not wait_for_db():
        return
        
    try:
        # Check if the table exists first
        tables = db.session.execute(text("SHOW TABLES")).fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"Existing tables: {table_names}")
        
        # Add missing columns to user table
        if 'user' in table_names:
            # Check if columns exist in user table
            user_columns = db.session.execute(text("SHOW COLUMNS FROM user")).fetchall()
            user_column_names = [col[0] for col in user_columns]
            print(f"Existing user columns: {user_column_names}")
            
            if 'date_created' not in user_column_names:
                print("Adding date_created column to user table...")
                db.session.execute(text("""
                    ALTER TABLE user
                    ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                db.session.commit()
                print("Added date_created to user table")
        
        # Add missing columns to course table
        if 'course' in table_names:
            # Check if columns exist in course table
            course_columns = db.session.execute(text("SHOW COLUMNS FROM course")).fetchall()
            course_column_names = [col[0] for col in course_columns]
            print(f"Existing course columns: {course_column_names}")
            
            missing_columns = []
            if 'duration' not in course_column_names:
                missing_columns.append("ADD COLUMN duration VARCHAR(50) NOT NULL DEFAULT '8 weeks'")
            
            if 'mode' not in course_column_names:
                missing_columns.append("ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'Online'")
            
            if 'fee' not in course_column_names:
                missing_columns.append("ADD COLUMN fee VARCHAR(50) NOT NULL DEFAULT 'KES 15,000'")
            
            if 'date_created' not in course_column_names:
                missing_columns.append("ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP")
            
            if missing_columns:
                alter_query = f"ALTER TABLE course {', '.join(missing_columns)}"
                print(f"Executing: {alter_query}")
                db.session.execute(text(alter_query))
                db.session.commit()
                print("Added missing columns to course table")
        
        # Add missing columns to module table
        if 'module' in table_names:
            # Check if columns exist in module table
            module_columns = db.session.execute(text("SHOW COLUMNS FROM module")).fetchall()
            module_column_names = [col[0] for col in module_columns]
            print(f"Existing module columns: {module_column_names}")
            
            if 'date_created' not in module_column_names:
                print("Adding date_created column to module table...")
                db.session.execute(text("""
                    ALTER TABLE module
                    ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                db.session.commit()
                print("Added date_created to module table")
        
        print("Migration completed successfully")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_missing_columns() 