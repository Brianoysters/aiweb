from app import app, db
from sqlalchemy import text

def add_admin_columns():
    with app.app_context():
        try:
            # Add is_admin column
            db.session.execute(text("""
                ALTER TABLE user 
                ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
            """))
            
            # Add is_paid column
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