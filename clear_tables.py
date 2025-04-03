from app import app, db
from app import User, Module, Progress, QuizResult

def clear_tables():
    try:
        with app.app_context():
            # Clear tables in order to respect foreign key constraints
            print("Clearing QuizResult table...")
            QuizResult.query.delete()
            
            print("Clearing Progress table...")
            Progress.query.delete()
            
            print("Clearing Module table...")
            Module.query.delete()
            
            print("Clearing User table...")
            User.query.delete()
            
            # Commit the changes
            db.session.commit()
            print("\nAll tables have been cleared successfully!")
            
    except Exception as e:
        print(f"\nError clearing tables: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    print("Starting database cleanup...")
    clear_tables()
