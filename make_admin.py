from app import app, db
from app import User

def make_first_user_admin():
    with app.app_context():
        first_user = User.query.first()
        if first_user:
            first_user.is_admin = True
            db.session.commit()
            print(f"User {first_user.username} has been made an admin")
        else:
            print("No users found in the database")

if __name__ == '__main__':
    make_first_user_admin() 