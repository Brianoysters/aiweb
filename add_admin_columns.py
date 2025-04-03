from app import app, db
from sqlalchemy import text
import time

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

def add_admin_columns():
    if not wait_for_db():
        return
        
    with app.app_context():
        try:
            # Check if columns already exist
            columns = db.session.execute(text("""
                SHOW COLUMNS FROM user
            """)).fetchall()
            
            column_names = [col[0] for col in columns]
            
            if 'is_admin' not in column_names:
                print("Adding is_admin column...")
                db.session.execute(text("""
                    ALTER TABLE user 
                    ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
                """))
            
            if 'is_paid' not in column_names:
                print("Adding is_paid column...")
                db.session.execute(text("""
                    ALTER TABLE user 
                    ADD COLUMN is_paid BOOLEAN DEFAULT FALSE
                """))
            
            db.session.commit()
            print("Successfully added admin and payment columns")
            
            # Make the first user an admin
            first_user = db.session.execute(text("SELECT id FROM user LIMIT 1")).fetchone()
            if first_user:
                db.session.execute(text("""
                    UPDATE user 
                    SET is_admin = TRUE 
                    WHERE id = :user_id
                """), {"user_id": first_user[0]})
                db.session.commit()
                print("Made first user an admin")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_admin_columns() 