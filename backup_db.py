import os
import json
from datetime import datetime
from app import db, User, Course, Module, QuizQuestion, QuizResult, Progress, Certificate, enrollment

def backup_database():
    try:
        # Create backup directory if it doesn't exist
        backup_dir = 'database_backup'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Get current timestamp for backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
        
        # Initialize backup data structure
        backup_data = {
            'timestamp': timestamp,
            'tables': {}
        }
        
        # Backup Users
        users = User.query.all()
        backup_data['tables']['users'] = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'is_admin': user.is_admin,
            'is_paid': user.is_paid,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]
        
        # Backup Courses
        courses = Course.query.all()
        backup_data['tables']['courses'] = [{
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'duration': course.duration,
            'mode': course.mode,
            'fee': course.fee,
            'is_active': course.is_active
        } for course in courses]
        
        # Backup Modules
        modules = Module.query.all()
        backup_data['tables']['modules'] = [{
            'id': module.id,
            'title': module.title,
            'content': module.content,
            'order': module.order,
            'course_id': module.course_id
        } for module in modules]
        
        # Backup Quiz Questions
        questions = QuizQuestion.query.all()
        backup_data['tables']['quiz_questions'] = [{
            'id': question.id,
            'question_text': question.question_text,
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d,
            'correct_answer': question.correct_answer,
            'module_id': question.module_id
        } for question in questions]
        
        # Backup Quiz Results
        results = QuizResult.query.all()
        backup_data['tables']['quiz_results'] = [{
            'id': result.id,
            'user_id': result.user_id,
            'score': result.score,
            'passed': result.passed,
            'attempt_number': result.attempt_number,
            'completed_at': result.completed_at.isoformat() if result.completed_at else None
        } for result in results]
        
        # Backup Progress
        progress = Progress.query.all()
        backup_data['tables']['progress'] = [{
            'id': p.id,
            'user_id': p.user_id,
            'module_id': p.module_id,
            'completed': p.completed,
            'completed_at': p.completed_at.isoformat() if p.completed_at else None
        } for p in progress]
        
        # Backup Certificates
        certificates = Certificate.query.all()
        backup_data['tables']['certificates'] = [{
            'id': cert.id,
            'user_id': cert.user_id,
            'course_id': cert.course_id,
            'issue_date': cert.issue_date.isoformat() if cert.issue_date else None,
            'score': cert.score
        } for cert in certificates]
        
        # Backup Enrollments
        enrollments = db.session.query(enrollment).all()
        backup_data['tables']['enrollments'] = [{
            'user_id': e.user_id,
            'course_id': e.course_id,
            'enrolled_at': e.enrolled_at.isoformat() if e.enrolled_at else None
        } for e in enrollments]
        
        # Write backup to file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=4)
        
        print(f"Backup completed successfully. File saved as: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"Error during backup: {str(e)}")
        return None

if __name__ == '__main__':
    backup_database() 