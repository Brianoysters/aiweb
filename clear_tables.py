from app import app, db, User, Progress, QuizResult
from werkzeug.security import generate_password_hash

def clear_tables():
    with app.app_context():
        try:
            # Clear progress table
            Progress.query.delete()
            
            # Clear quiz results table
            QuizResult.query.delete()
            
            # Clear user table
            User.query.delete()
            
            # Create admin user with pbkdf2:sha256 hashing method
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True,
                is_paid=True
            )
            db.session.add(admin_user)
            
            db.session.commit()
            print("Successfully cleared all tables and created admin user")
            print("Admin credentials:")
            print("Username: admin")
            print("Password: admin123")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    clear_tables()
