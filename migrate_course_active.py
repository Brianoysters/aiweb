from app import app, db, Course

def migrate_course_active():
    with app.app_context():
        try:
            # Add is_active column to all existing courses
            courses = Course.query.all()
            for course in courses:
                course.is_active = True
            
            db.session.commit()
            print("Successfully updated all courses with is_active=True")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_course_active() 