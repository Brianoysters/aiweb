import json
from datetime import datetime
from app import db, User, Course, Module, QuizQuestion, QuizResult, Progress, Certificate, enrollment

def restore_database(backup_file):
    try:
        # Read backup file
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Clear existing data
        db.session.query(enrollment).delete()
        Certificate.query.delete()
        Progress.query.delete()
        QuizResult.query.delete()
        QuizQuestion.query.delete()
        Module.query.delete()
        Course.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Restore Users
        for user_data in backup_data['tables']['users']:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data['is_admin'],
                is_paid=user_data['is_paid'],
                created_at=datetime.fromisoformat(user_data['created_at']) if user_data['created_at'] else None
            )
            db.session.add(user)
        db.session.commit()
        
        # Restore Courses
        for course_data in backup_data['tables']['courses']:
            course = Course(
                id=course_data['id'],
                title=course_data['title'],
                description=course_data['description'],
                duration=course_data['duration'],
                mode=course_data['mode'],
                fee=course_data['fee'],
                is_active=course_data['is_active']
            )
            db.session.add(course)
        db.session.commit()
        
        # Restore Modules
        for module_data in backup_data['tables']['modules']:
            module = Module(
                id=module_data['id'],
                title=module_data['title'],
                content=module_data['content'],
                order=module_data['order'],
                course_id=module_data['course_id']
            )
            db.session.add(module)
        db.session.commit()
        
        # Restore Quiz Questions
        for question_data in backup_data['tables']['quiz_questions']:
            question = QuizQuestion(
                id=question_data['id'],
                question_text=question_data['question_text'],
                option_a=question_data['option_a'],
                option_b=question_data['option_b'],
                option_c=question_data['option_c'],
                option_d=question_data['option_d'],
                correct_answer=question_data['correct_answer'],
                module_id=question_data['module_id']
            )
            db.session.add(question)
        db.session.commit()
        
        # Restore Quiz Results
        for result_data in backup_data['tables']['quiz_results']:
            result = QuizResult(
                id=result_data['id'],
                user_id=result_data['user_id'],
                score=result_data['score'],
                passed=result_data['passed'],
                attempt_number=result_data['attempt_number'],
                completed_at=datetime.fromisoformat(result_data['completed_at']) if result_data['completed_at'] else None
            )
            db.session.add(result)
        db.session.commit()
        
        # Restore Progress
        for progress_data in backup_data['tables']['progress']:
            progress = Progress(
                id=progress_data['id'],
                user_id=progress_data['user_id'],
                module_id=progress_data['module_id'],
                completed=progress_data['completed'],
                completed_at=datetime.fromisoformat(progress_data['completed_at']) if progress_data['completed_at'] else None
            )
            db.session.add(progress)
        db.session.commit()
        
        # Restore Certificates
        for cert_data in backup_data['tables']['certificates']:
            certificate = Certificate(
                id=cert_data['id'],
                user_id=cert_data['user_id'],
                course_id=cert_data['course_id'],
                issue_date=datetime.fromisoformat(cert_data['issue_date']) if cert_data['issue_date'] else None,
                score=cert_data['score']
            )
            db.session.add(certificate)
        db.session.commit()
        
        # Restore Enrollments
        for enroll_data in backup_data['tables']['enrollments']:
            stmt = enrollment.insert().values(
                user_id=enroll_data['user_id'],
                course_id=enroll_data['course_id'],
                enrolled_at=datetime.fromisoformat(enroll_data['enrolled_at']) if enroll_data['enrolled_at'] else None
            )
            db.session.execute(stmt)
        db.session.commit()
        
        print("Database restored successfully!")
        return True
        
    except Exception as e:
        print(f"Error during restoration: {str(e)}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    # Replace with your backup file path
    backup_file = 'database_backup/db_backup_20240321_120000.json'  # Example path
    restore_database(backup_file) 