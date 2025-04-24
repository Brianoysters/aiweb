"""
This script can be run separately to perform database migrations.
Useful for troubleshooting database issues during deployment.
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

def fix_database_schema():
    if not wait_for_db():
        return

    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            # Create all tables if they don't exist
            print("No tables found. Creating all tables...")
            db.create_all()
            print("Created all tables with new schema")
        else:
            print(f"Existing tables: {existing_tables}")
            
            # Check and add missing columns to user table
            if 'user' in existing_tables:
                user_columns = db.session.execute(text("SHOW COLUMNS FROM user")).fetchall()
                user_column_names = [col[0] for col in user_columns]
                print(f"Existing user columns: {user_column_names}")
                
                if 'is_admin' not in user_column_names:
                    print("Adding is_admin column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
                    """))
                
                if 'is_paid' not in user_column_names:
                    print("Adding is_paid column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN is_paid BOOLEAN DEFAULT FALSE
                    """))
                
                if 'date_created' not in user_column_names:
                    print("Adding date_created column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user
                        ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                    """))
                
                db.session.commit()
                print("Added missing columns to user table")
            
            # Check and add missing columns to course table
            if 'course' in existing_tables:
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
                
                if 'is_active' not in course_column_names:
                    missing_columns.append("ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                
                if missing_columns:
                    alter_query = f"ALTER TABLE course {', '.join(missing_columns)}"
                    print(f"Executing: {alter_query}")
                    db.session.execute(text(alter_query))
                    db.session.commit()
                    print("Added missing columns to course table")
            
            # Check and add missing columns to module table
            if 'module' in existing_tables:
                module_columns = db.session.execute(text("SHOW COLUMNS FROM module")).fetchall()
                module_column_names = [col[0] for col in module_columns]
                print(f"Existing module columns: {module_column_names}")
                
                missing_module_columns = []
                
                if 'date_created' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP")
                
                if 'doc_link' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN doc_link VARCHAR(500) NULL")
                
                if 'order' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN `order` INT NOT NULL DEFAULT 1")
                
                if missing_module_columns:
                    alter_module_query = f"ALTER TABLE module {', '.join(missing_module_columns)}"
                    print(f"Executing: {alter_module_query}")
                    db.session.execute(text(alter_module_query))
                    db.session.commit()
                    print("Added missing columns to module table")
            
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
            
            # Make the first user an admin
            first_user = db.session.execute(text("SELECT id FROM user LIMIT 1")).fetchone()
            if first_user:
                db.session.execute(text("""
                    UPDATE user 
                    SET is_admin = TRUE, is_paid = TRUE
                    WHERE id = :user_id
                """), {"user_id": first_user[0]})
                db.session.commit()
                print("Made first user an admin and paid user")
                
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        fix_database_schema() 