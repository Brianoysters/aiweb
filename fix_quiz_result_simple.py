"""
A simplified script to fix the quiz_result table.
This script is compatible with both Python 2 and Python 3.
"""

import os
import sys
import time

# Check Python version
PY3 = sys.version_info[0] >= 3

# Import the right modules based on Python version
if PY3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

try:
    # Try to import Flask and SQLAlchemy
    from flask import Flask
    from sqlalchemy import text, create_engine
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    print("Error: Flask or SQLAlchemy not installed.")
    print("Please install them with: pip install flask sqlalchemy")
    sys.exit(1)

# Get database URL from environment or use the hardcoded value
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    "mysql://root:RlnjaHZoFYoaoxssxFHKtLFQlvwqninP@yamanote.proxy.rlwy.net:17657/railway"
)

def print_log(message):
    """Print log message with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print("[{}] {}".format(timestamp, message))

def wait_for_db(engine, max_retries=5, retry_delay=5):
    """Wait for database to be available"""
    print_log("Trying to connect to the database...")
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the database
            conn = engine.connect()
            conn.execute(text("SELECT 1"))
            conn.close()
            print_log("Successfully connected to the database")
            return True
        except Exception as e:
            print_log("Attempt {} failed: {}".format(attempt + 1, str(e)))
            if attempt < max_retries - 1:
                print_log("Waiting {} seconds before retrying...".format(retry_delay))
                time.sleep(retry_delay)
            else:
                print_log("Max retries reached. Could not connect to the database.")
                return False

def fix_quiz_result_table(engine):
    """Add missing columns to quiz_result table"""
    try:
        conn = engine.connect()
        
        # Check if table exists
        print_log("Checking if quiz_result table exists...")
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'railway'
            AND table_name = 'quiz_result'
        """))
        table_exists = result.scalar() > 0
        
        if not table_exists:
            print_log("Error: quiz_result table does not exist.")
            conn.close()
            return False
        
        # Get existing columns
        print_log("Getting existing columns...")
        result = conn.execute(text("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'railway'
            AND TABLE_NAME = 'quiz_result'
        """))
        columns = [row[0] for row in result]
        print_log("Existing columns: {}".format(", ".join(columns)))
        
        # Add missing columns
        missing_columns = []
        if 'completion_date' not in columns:
            missing_columns.append("ADD COLUMN completion_date DATETIME NULL")
        
        if 'next_attempt_available' not in columns:
            missing_columns.append("ADD COLUMN next_attempt_available DATETIME NULL")
        
        if 'attempt_number' not in columns:
            missing_columns.append("ADD COLUMN attempt_number INT NOT NULL DEFAULT 1")
        
        if missing_columns:
            print_log("Adding missing columns: {}".format(", ".join(missing_columns)))
            alter_query = "ALTER TABLE quiz_result {}".format(", ".join(missing_columns))
            conn.execute(text(alter_query))
            print_log("Added missing columns successfully")
        else:
            print_log("No missing columns found")
        
        # Verify columns were added
        print_log("Verifying columns...")
        result = conn.execute(text("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'railway'
            AND TABLE_NAME = 'quiz_result'
        """))
        new_columns = [row[0] for row in result]
        print_log("Current columns: {}".format(", ".join(new_columns)))
        
        conn.close()
        return True
    except Exception as e:
        print_log("Error fixing quiz_result table: {}".format(str(e)))
        return False

def main():
    """Main function"""
    print_log("Starting fix_quiz_result_simple.py")
    
    try:
        # Create engine
        print_log("Creating database engine...")
        engine = create_engine(DATABASE_URL)
        
        # Wait for database
        if not wait_for_db(engine):
            print_log("Failed to connect to database. Exiting.")
            return
        
        # Fix quiz_result table
        if fix_quiz_result_table(engine):
            print_log("Successfully fixed quiz_result table")
        else:
            print_log("Failed to fix quiz_result table")
    except Exception as e:
        print_log("Unexpected error: {}".format(str(e)))

if __name__ == "__main__":
    main() 