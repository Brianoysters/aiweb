from app import app, db, Course, User, Module
from sqlalchemy import text

def update_database():
    with app.app_context():
        try:
            # Add is_active column to courses table if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE course
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
                """))
                conn.commit()
                print("Added is_active column to courses table")

            # Update existing courses to be active
            courses = Course.query.all()
            for course in courses:
                course.is_active = True
            db.session.commit()
            print("Updated existing courses to be active")

            # Add last_quiz_attempt column to users table if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE user
                    ADD COLUMN IF NOT EXISTS last_quiz_attempt DATETIME NULL
                """))
                conn.commit()
                print("Added last_quiz_attempt column to users table")

            print("Database schema update completed successfully")

        except Exception as e:
            print(f"Error during database update: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    update_database() 