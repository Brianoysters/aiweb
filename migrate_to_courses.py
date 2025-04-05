from app import app, db, Course, Module

def migrate_to_courses():
    with app.app_context():
        try:
            # Create AI course
            ai_course = Course(
                title="Introduction to Artificial Intelligence",
                description="Master the fundamentals of AI through our comprehensive course covering key concepts, applications, and hands-on projects.",
                is_active=True
            )
            db.session.add(ai_course)
            db.session.commit()
            
            # Update existing modules to belong to AI course
            modules = Module.query.all()
            for module in modules:
                module.course_id = ai_course.id
            
            db.session.commit()
            print("Successfully migrated modules to AI course")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_to_courses() 