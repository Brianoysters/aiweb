from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from flask_migrate import Migrate
from config import Config
from functools import wraps
from sqlalchemy import text
import time
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Add debug logging for static files
@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('URL: %s', request.url)

# Use hardcoded value temporarily for Railway MySQL deployment
DATABASE_URL = "mysql://root:RlnjaHZoFYoaoxssxFHKtLFQlvwqninP@yamanote.proxy.rlwy.net:17657/railway"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

def fix_database_schema():
    if not wait_for_db():
        return

    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            # Create all tables if they don't exist
            print("No tables found. Creating all tables...")
            db.create_all()
            print("Created all tables with new schema")
        else:
            print(f"Existing tables: {existing_tables}")
            
            # Check and add missing columns to user table
            if 'user' in existing_tables:
                user_columns = db.session.execute(text("SHOW COLUMNS FROM user")).fetchall()
                user_column_names = [col[0] for col in user_columns]
                print(f"Existing user columns: {user_column_names}")
                
                if 'is_admin' not in user_column_names:
                    print("Adding is_admin column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
                    """))
                
                if 'is_paid' not in user_column_names:
                    print("Adding is_paid column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user 
                        ADD COLUMN is_paid BOOLEAN DEFAULT FALSE
                    """))
                
                if 'date_created' not in user_column_names:
                    print("Adding date_created column to user table...")
                    db.session.execute(text("""
                        ALTER TABLE user
                        ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                    """))
                
                db.session.commit()
                print("Added missing columns to user table")
            
            # Check and add missing columns to course table
            if 'course' in existing_tables:
                course_columns = db.session.execute(text("SHOW COLUMNS FROM course")).fetchall()
                course_column_names = [col[0] for col in course_columns]
                print(f"Existing course columns: {course_column_names}")
                
                missing_columns = []
                if 'duration' not in course_column_names:
                    missing_columns.append("ADD COLUMN duration VARCHAR(50) NOT NULL DEFAULT '8 weeks'")
                
                if 'mode' not in course_column_names:
                    missing_columns.append("ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'Online'")
                
                if 'fee' not in course_column_names:
                    missing_columns.append("ADD COLUMN fee VARCHAR(50) NOT NULL DEFAULT 'KES 15,000'")
                
                if 'date_created' not in course_column_names:
                    missing_columns.append("ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP")
                
                if 'is_active' not in course_column_names:
                    missing_columns.append("ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                
                if missing_columns:
                    alter_query = f"ALTER TABLE course {', '.join(missing_columns)}"
                    print(f"Executing: {alter_query}")
                    db.session.execute(text(alter_query))
                    db.session.commit()
                    print("Added missing columns to course table")
            
            # Check and add missing columns to module table
            if 'module' in existing_tables:
                module_columns = db.session.execute(text("SHOW COLUMNS FROM module")).fetchall()
                module_column_names = [col[0] for col in module_columns]
                print(f"Existing module columns: {module_column_names}")
                
                missing_module_columns = []
                
                if 'date_created' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP")
                
                if 'doc_link' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN doc_link VARCHAR(500) NULL")
                
                if 'order' not in module_column_names:
                    missing_module_columns.append("ADD COLUMN `order` INT NOT NULL DEFAULT 1")
                
                if missing_module_columns:
                    alter_module_query = f"ALTER TABLE module {', '.join(missing_module_columns)}"
                    print(f"Executing: {alter_module_query}")
                    db.session.execute(text(alter_module_query))
                    db.session.commit()
                    print("Added missing columns to module table")
            
            # Check and add missing columns to progress table
            if 'progress' in existing_tables:
                progress_columns = db.session.execute(text("SHOW COLUMNS FROM progress")).fetchall()
                progress_column_names = [col[0] for col in progress_columns]
                print(f"Existing progress columns: {progress_column_names}")
                
                if 'completion_date' not in progress_column_names:
                    print("Adding completion_date column to progress table...")
                    db.session.execute(text("""
                        ALTER TABLE progress
                        ADD COLUMN completion_date DATETIME NULL
                    """))
                    db.session.commit()
                    print("Added completion_date to progress table")
            
            # Check and add missing columns to quiz_result table
            if 'quiz_result' in existing_tables:
                quiz_result_columns = db.session.execute(text("SHOW COLUMNS FROM quiz_result")).fetchall()
                quiz_result_column_names = [col[0] for col in quiz_result_columns]
                print(f"Existing quiz_result columns: {quiz_result_column_names}")
                
                missing_quiz_result_columns = []
                
                if 'completion_date' not in quiz_result_column_names:
                    missing_quiz_result_columns.append("ADD COLUMN completion_date DATETIME NULL")
                
                if 'next_attempt_available' not in quiz_result_column_names:
                    missing_quiz_result_columns.append("ADD COLUMN next_attempt_available DATETIME NULL")
                
                if 'attempt_number' not in quiz_result_column_names:
                    missing_quiz_result_columns.append("ADD COLUMN attempt_number INT NOT NULL DEFAULT 1")
                
                if missing_quiz_result_columns:
                    alter_quiz_result_query = f"ALTER TABLE quiz_result {', '.join(missing_quiz_result_columns)}"
                    print(f"Executing: {alter_quiz_result_query}")
                    db.session.execute(text(alter_quiz_result_query))
                    db.session.commit()
                    print("Added missing columns to quiz_result table")
            
            # Make the first user an admin
            first_user = db.session.execute(text("SELECT id FROM user LIMIT 1")).fetchone()
            if first_user:
                db.session.execute(text("""
                    UPDATE user 
                    SET is_admin = TRUE, is_paid = TRUE
                    WHERE id = :user_id
                """), {"user_id": first_user[0]})
                db.session.commit()
                print("Made first user an admin and paid user")
                
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        db.session.rollback()

# Run schema fixing when the app starts
with app.app_context():
    fix_database_schema()

# Define the enrollment table
enrollment = db.Table('enrollment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.relationship('Progress', backref='user', lazy=True)
    enrolled_courses = db.relationship('Course', secondary='enrollment', lazy='joined',
        backref=db.backref('enrolled_users', lazy='joined'))

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    fee = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    modules = db.relationship('Module', backref='course', lazy=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    doc_link = db.Column(db.String(500), nullable=True)
    progress = db.relationship('Progress', backref='module', lazy=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, user_id, module_id, completed=False, completion_date=None):
        self.user_id = user_id
        self.module_id = module_id
        self.completed = completed
        self.completion_date = completion_date

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    completion_date = db.Column(db.DateTime, nullable=True)
    next_attempt_available = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, user_id, score, passed=False, attempt_number=1, completion_date=None, next_attempt_available=None):
        self.user_id = user_id
        self.score = score
        self.passed = passed
        self.attempt_number = attempt_number
        self.completion_date = completion_date
        self.next_attempt_available = next_attempt_available

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'a', 'b', or 'c'
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for user completed modules
user_completed_modules = db.Table('user_completed_modules',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('module_id', db.Integer, db.ForeignKey('module.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Updated to use session.get()

@app.route('/')
def index():
    courses = Course.query.filter_by(is_active=True).all()
    # Get the two specific courses for flyers
    web_dev_course = Course.query.filter_by(title="Web Development Crash Course").first()
    civil3d_course = Course.query.filter_by(title="AutoCAD Civil 3D Crash Course").first()
    
    return render_template('index.html', 
                         courses=courses,
                         web_dev_course=web_dev_course,
                         civil3d_course=civil3d_course)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get all available courses
        courses = Course.query.filter_by(is_active=True).all()
        
        # Get all admin users for the admin section
        admins = User.query.filter_by(is_admin=True).all()
        
        # Get user's enrolled courses
        enrolled_courses = [c.id for c in current_user.enrolled_courses]
        
        return render_template('dashboard.html', 
                            courses=courses,
                            admins=admins,
                            enrolled_courses=enrolled_courses)
    except Exception as e:
        # Log the error
        app.logger.error(f"Dashboard error: {str(e)}")
        
        # Redirect to the simple dashboard as a fallback
        return redirect(url_for('dashboard_simple'))

@app.route('/course/<int:course_id>')
@login_required
def course(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.is_paid:
        flash('Please complete your payment to access this course.', 'warning')
        return redirect(url_for('dashboard'))
    modules = Module.query.filter_by(course_id=course_id).order_by(Module.order).all()
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()
    completed_modules = [p.module_id for p in user_progress if p.completed]
    return render_template('course.html', 
                         course=course,
                         modules=modules,
                         completed_modules=completed_modules)

@app.route('/module/<int:module_id>')
@login_required
def module(module_id):
    if not current_user.is_paid:
        flash('Please complete your payment to access the modules.', 'warning')
        return redirect(url_for('dashboard'))
    
    module = Module.query.get_or_404(module_id)
    course = module.course
    
    # Get completed modules from Progress model
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()
    completed_modules = [p.module_id for p in user_progress if p.completed]
    
    # Only check previous module completion for non-quiz modules
    if module.order < 5 and module.order > 1:
        prev_module = Module.query.filter_by(order=module.order-1).first()
        prev_progress = Progress.query.filter_by(
            user_id=current_user.id, 
            module_id=prev_module.id
        ).first()
        
        if not prev_progress or not prev_progress.completed:
            flash('Please complete the previous module first')
            return redirect(url_for('dashboard'))
    
    # If this is module 5 (quiz module), check quiz status
    if module.order == 5:
        passed_result = QuizResult.query.filter_by(
            user_id=current_user.id,
            passed=True
        ).first()
        
        if passed_result:
            return render_template('module.html', 
                                module=module,
                                course=course,
                                completed_modules=completed_modules,
                                already_passed=True,
                                score=passed_result.score,
                                completion_date=passed_result.completion_date)
        
        # Get user's last quiz attempt
        last_attempt = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.attempt_number.desc()).first()
        
        if last_attempt:
            # Check if user has attempts remaining for today
            if last_attempt.attempt_number >= 2:
                # Check if 24 hours have passed since the first attempt of the day
                first_attempt_today = QuizResult.query.filter(
                    QuizResult.user_id == current_user.id,
                    QuizResult.completion_date >= datetime.utcnow().date()
                ).order_by(QuizResult.attempt_number).first()
                
                if first_attempt_today:
                    time_since_first_attempt = datetime.utcnow() - first_attempt_today.completion_date
                    if time_since_first_attempt.total_seconds() < 86400:  # 24 hours in seconds
                        next_attempt_time = first_attempt_today.completion_date + timedelta(days=1)
                        return render_template('module.html', 
                                            module=module,
                                            course=course,
                                            completed_modules=completed_modules,
                                            next_attempt_available=next_attempt_time)
            
            # Check if cooldown period has passed
            if last_attempt.next_attempt_available and datetime.utcnow() < last_attempt.next_attempt_available:
                return render_template('module.html', 
                                    module=module,
                                    course=course,
                                    completed_modules=completed_modules,
                                    next_attempt_available=last_attempt.next_attempt_available)
    
    return render_template('module.html', module=module, course=course, completed_modules=completed_modules)

@app.route('/complete_module/<int:module_id>')
@login_required
def complete_module(module_id):
    if not current_user.is_paid:
        flash('Please complete your payment to access the modules.', 'warning')
        return redirect(url_for('dashboard'))
    
    progress = Progress.query.filter_by(
        user_id=current_user.id,
        module_id=module_id
    ).first()
    
    if not progress:
        progress = Progress(user_id=current_user.id, module_id=module_id)
        db.session.add(progress)
    
    progress.completed = True
    progress.completion_date = datetime.utcnow()
    db.session.commit()
    
    # Get the module to find its course_id
    module = Module.query.get_or_404(module_id)
    return redirect(url_for('course', course_id=module.course_id))

@app.route('/quiz')
@login_required
def quiz():
    if not current_user.is_paid:
        flash('Please complete your payment to access the quiz.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get the quiz module (module 5)
    quiz_module = Module.query.filter_by(order=5).first()
    if not quiz_module:
        flash('Quiz module not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user has already passed the quiz
    passed_result = QuizResult.query.filter_by(
        user_id=current_user.id,
        passed=True
    ).first()
    
    if passed_result:
        return render_template('quiz.html', 
                             already_passed=True,
                             score=passed_result.score,
                             completion_date=passed_result.completion_date)
    
    # Get user's last quiz attempt
    last_attempt = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.attempt_number.desc()).first()
    
    if last_attempt:
        # Check if user has attempts remaining for today
        if last_attempt.attempt_number >= 2:
            # Check if 24 hours have passed since the first attempt of the day
            first_attempt_today = QuizResult.query.filter(
                QuizResult.user_id == current_user.id,
                QuizResult.completion_date >= datetime.utcnow().date()
            ).order_by(QuizResult.attempt_number).first()
            
            if first_attempt_today:
                time_since_first_attempt = datetime.utcnow() - first_attempt_today.completion_date
                if time_since_first_attempt.total_seconds() < 86400:  # 24 hours in seconds
                    next_attempt_time = first_attempt_today.completion_date + timedelta(days=1)
                    return render_template('quiz.html', 
                                        next_attempt_available=next_attempt_time)
        
        # Check if cooldown period has passed
        if last_attempt.next_attempt_available and datetime.utcnow() < last_attempt.next_attempt_available:
            return render_template('quiz.html', 
                                next_attempt_available=last_attempt.next_attempt_available)
    
    # Get quiz questions from database and randomize them
    questions = QuizQuestion.query.filter_by(module_id=quiz_module.id).order_by(db.func.random()).all()
    
    return render_template('quiz.html', questions=questions)

@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    if not current_user.is_paid:
        flash('Please complete your payment to submit the quiz.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get the quiz module
    quiz_module = Module.query.filter_by(order=5).first()
    if not quiz_module:
        flash('Quiz module not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all questions for this module
    questions = QuizQuestion.query.filter_by(module_id=quiz_module.id).all()
    
    # Calculate score
    correct_count = 0
    for question in questions:
        user_answer = request.form.get(f'q{question.id}')
        if user_answer == question.correct_answer:
            correct_count += 1
    
    score = (correct_count / len(questions)) * 100
    passed = score >= 80
    current_time = datetime.utcnow()
    
    # Get attempt number
    attempt_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    
    # Store quiz result
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        passed=passed,
        attempt_number=attempt_count + 1,
        completion_date=current_time,
        next_attempt_available=current_time + timedelta(days=1) if not passed else None
    )
    db.session.add(quiz_result)
    db.session.commit()
    
    # Prepare feedback message
    if passed:
        flash(f'Congratulations! You scored {score:.1f}% and passed the quiz!', 'success')
        return redirect(url_for('certificate'))
    else:
        flash(f'You scored {score:.1f}%. You need 80% to pass. Try again after the cooldown period.', 'warning')
        return redirect(url_for('dashboard'))

@app.route('/certificate')
@login_required
def certificate():
    try:
        if not current_user.is_paid:
            flash('Please complete your payment to access the certificate.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Get the latest quiz result
        latest_result = QuizResult.query.filter_by(
            user_id=current_user.id,
            passed=True
        ).order_by(QuizResult.completion_date.desc()).first()
        
        if not latest_result:
            flash('You need to pass the quiz to get a certificate.', 'warning')
            return redirect(url_for('dashboard'))
            
        # First show the score and certificate preview
        return render_template('certificate.html', 
                            score=latest_result.score,
                            completion_date=latest_result.completion_date)
    except Exception as e:
        # Log the error
        app.logger.error(f"Certificate error: {str(e)}")
        
        # Show error page with helpful message
        return render_template('error.html', 
                            message="Certificate Error",
                            error="There was an error generating your certificate. This may be due to missing database columns.",
                            user=current_user), 500

@app.route('/download_certificate')
@login_required
def download_certificate():
    try:
        if not current_user.is_paid:
            flash('Please complete your payment to download the certificate.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Get the latest quiz result
        latest_result = QuizResult.query.filter_by(
            user_id=current_user.id,
            passed=True
        ).order_by(QuizResult.completion_date.desc()).first()
        
        if not latest_result:
            flash('You need to pass the quiz to get a certificate.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Create certificate
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add decorative border with gradient
        c.setStrokeColorRGB(0.0, 0.2, 0.4)  # Royal blue color
        c.setLineWidth(2)
        c.rect(30, 30, width-60, height-60)
        
        # Add corner decorations
        corner_size = 20
        c.setLineWidth(1)
        c.setStrokeColorRGB(0.8, 0.6, 0.0)  # Maroon color
        # Top-left corner
        c.line(30, height-30, 30+corner_size, height-30)
        c.line(30, height-30, 30, height-30-corner_size)
        # Top-right corner
        c.line(width-30, height-30, width-30-corner_size, height-30)
        c.line(width-30, height-30, width-30, height-30-corner_size)
        # Bottom-left corner
        c.line(30, 30, 30+corner_size, 30)
        c.line(30, 30, 30, 30+corner_size)
        # Bottom-right corner
        c.line(width-30, 30, width-30-corner_size, 30)
        c.line(width-30, 30, width-30, 30+corner_size)
        
        # Add watermark first (behind all text)
        c.saveState()
        c.setFillColorRGB(0.9, 0.9, 0.9)  # Light gray
        c.setFont("Helvetica-Bold", 40)
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "SUBOMAP AFRICA ACADEMY")
        c.restoreState()
        
        # Add company name with decorative underline
        c.setFont("Helvetica-Bold", 28)
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue color
        c.drawCentredString(width/2, height - 150, "SUBOMAP AFRICA ACADEMY")
        c.setStrokeColorRGB(0.8, 0.6, 0.0)  # Maroon color
        c.setLineWidth(2)
        c.line(width/2 - 150, height - 160, width/2 + 150, height - 160)
        
        # Add certificate title with decorative elements
        c.setFont("Helvetica-Bold", 36)
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue color
        c.drawCentredString(width/2, height - 250, "Certificate of Completion")
        
        # Add decorative line under title
        c.setStrokeColorRGB(0.8, 0.6, 0.0)  # Maroon color
        c.setLineWidth(1)
        c.line(width/2 - 200, height - 260, width/2 + 200, height - 260)
        
        # Add certificate text with improved spacing
        c.setFont("Helvetica", 18)
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue color
        c.drawCentredString(width/2, height - 300, "This is to certify that")
        
        # Add user name with decorative underline
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height - 350, current_user.username)
        c.setStrokeColorRGB(0.8, 0.6, 0.0)  # Maroon color
        c.setLineWidth(1)
        c.line(width/2 - 150, height - 360, width/2 + 150, height - 360)
        
        # Add completion text
        c.setFont("Helvetica", 18)
        c.drawCentredString(width/2, height - 400, "has successfully completed the")
        c.drawCentredString(width/2, height - 430, "AI in Web GIS Course")
        c.drawCentredString(width/2, height - 460, "at SUBOMAP AFRICA ACADEMY")
        
        # Add enrollment and completion dates with decorative background
        c.setFillColorRGB(1.0, 0.8, 0.0)  # Yellow background
        c.rect(width/2 - 150, height - 520, 300, 60, fill=1)
        c.setFont("Helvetica", 14)
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue text
        
        # Get completion date from quiz result
        completion_date = latest_result.completion_date.strftime("%B %d, %Y")
        
        # For enrollment date, we'll use the completion date minus 8 weeks (course duration)
        enrollment_date = (latest_result.completion_date - timedelta(weeks=8)).strftime("%B %d, %Y")
        
        c.drawCentredString(width/2, height - 500, f"Enrolled: {enrollment_date}")
        c.drawCentredString(width/2, height - 480, f"Completed: {completion_date}")
        
        # Add score with decorative background
        c.setFillColorRGB(1.0, 0.8, 0.0)  # Yellow background
        c.rect(width/2 - 100, height - 580, 200, 40, fill=1)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue text
        c.drawCentredString(width/2, height - 560, f"Score: {latest_result.score:.1f}%")
        
        # Add signature section with decorative background
        c.setFillColorRGB(0.0, 0.2, 0.4)  # Royal blue background
        c.rect(50, 100, width-100, 100, fill=1)
        
        # Add signature lines
        y_position = 150  # Position from bottom
        line_width = 200  # Width of signature line
        
        # Course Director signature
        c.setLineWidth(1)
        c.setStrokeColorRGB(1.0, 0.8, 0.0)  # Yellow color
        c.line(width/4 - line_width/2, y_position, width/4 + line_width/2, y_position)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(1.0, 1.0, 1.0)  # White text
        c.drawCentredString(width/4, y_position - 20, "Course Director")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/4, y_position - 35, "Eng. Brian Otieno")
        
        # CEO signature
        c.line(3*width/4 - line_width/2, y_position, 3*width/4 + line_width/2, y_position)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(3*width/4, y_position - 20, "Chief Executive Officer")
        c.setFont("Helvetica", 10)
        c.drawCentredString(3*width/4, y_position - 35, "Boaz Odhiambo Nyakongo")
        
        # Add certificate number with decorative background
        c.setFillColorRGB(0.8, 0.6, 0.0)  # Maroon background
        c.rect(50, 50, width-100, 30, fill=1)
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(1.0, 1.0, 1.0)  # White text
        cert_number = f"CERT-{current_user.id:04d}-{latest_result.id:04d}"
        c.drawCentredString(width/2, 65, f"Certificate Number: {cert_number}")
        
        c.save()
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=SUBOMAP_AFRICA_ACADEMY_AI_WebGIS_Certificate_{current_user.username}.pdf'
        
        return response
        
    except Exception as e:
        # Log the error
        app.logger.error(f"Download certificate error: {str(e)}")
        
        # Show error page with helpful message
        return render_template('error.html', 
                            message="Certificate Download Error",
                            error="There was an error generating your certificate PDF. This may be due to database issues or PDF generation errors.",
                            user=current_user), 500

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
            
        if not current_user.is_admin:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    try:
        # Check if user is authenticated and is admin
        if not current_user.is_authenticated:
            flash('Please login to access the admin dashboard', 'error')
            return redirect(url_for('login'))
            
        if not current_user.is_admin:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))
            
        # Get all users and courses
        users = User.query.all()
        courses = Course.query.all()
        
        # Log the number of users and courses
        print(f"Admin dashboard accessed by {current_user.username}")
        print(f"Total users: {len(users)}")
        print(f"Total courses: {len(courses)}")
        
        return render_template('admin/admin_dashboard.html', 
                            users=users, 
                            courses=courses)
                            
    except Exception as e:
        print(f"Error in admin dashboard: {str(e)}")
        flash('An error occurred while accessing the admin dashboard', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin/user/<int:user_id>/toggle_payment', methods=['POST'])
@login_required
@admin_required
def toggle_payment_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_paid = not user.is_paid
    db.session.commit()
    flash(f'Payment status for {user.username} has been updated')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/make_admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'{user.username} has been made an admin')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-details')
def admin_details():
    return render_template('admin_details.html')

@app.route('/courses')
@login_required
def courses():
    all_courses = Course.query.all()
    enrolled_courses = [c.id for c in current_user.enrolled_courses]
    return render_template('courses.html', courses=all_courses, enrolled_courses=enrolled_courses)

@app.route('/enroll_course/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user is already enrolled
    if course in current_user.enrolled_courses:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('course', course_id=course_id))
    
    try:
        # Add enrollment
        current_user.enrolled_courses.append(course)
        db.session.commit()
        flash('Successfully enrolled in the course!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error enrolling in the course. Please try again.', 'error')
        app.logger.error(f"Error enrolling user {current_user.id} in course {course_id}: {str(e)}")

    return redirect(url_for('course', course_id=course_id))

def init_db():
    with app.app_context():
        try:
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Only create tables if they don't exist
            if not existing_tables:
                db.create_all()
                print("Created all tables with new schema")
            else:
                print("Tables already exist, skipping creation")
            
            # Check if admin user exists, if not create one
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                    is_admin=True,
                    is_paid=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Created admin user")
            else:
                print("Admin user already exists")
            
            # Check if courses exist, if not create sample course
            if not Course.query.first():
                course = Course(
                    title="Introduction to Artificial Intelligence",
                    description="Master the fundamentals of AI through our comprehensive course covering key concepts, applications, and hands-on projects.",
                    duration="8 weeks",
                    mode="Online & Physical (Hybrid)",
                    fee="KES 15,000",
                    is_active=True
                )
                db.session.add(course)
                db.session.commit()
                print("Created sample course")
                
                # Create modules for the course
                modules = [
                    Module(
                        order=1,
                        title="Introduction to AI and ML",
                        content="""<h2>What is Artificial Intelligence?</h2>
                        <p>Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.</p>

                        <h2>Key Concepts in AI</h2>
                        <ul>
                            <li>Machine Learning: A subset of AI that enables systems to learn and improve from experience</li>
                            <li>Deep Learning: A type of machine learning that uses neural networks with many layers</li>
                            <li>Natural Language Processing: The ability of computers to understand and process human language</li>
                            <li>Computer Vision: The ability of computers to interpret and understand visual information</li>
                        </ul>""",
                        course_id=course.id
                    ),
                    Module(
                        order=2,
                        title="Machine Learning Fundamentals",
                        content="""<h2>Understanding Machine Learning</h2>
                        <p>Machine Learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.</p>

                        <h2>Types of Machine Learning</h2>
                        <ul>
                            <li>Supervised Learning: Learning from labeled data</li>
                            <li>Unsupervised Learning: Finding patterns in unlabeled data</li>
                            <li>Reinforcement Learning: Learning through trial and error</li>
                        </ul>""",
                        course_id=course.id
                    ),
                    Module(
                        order=3,
                        title="AI in Spatial Analysis",
                        content="""<h2>Spatial Analysis with AI</h2>
                        <p>AI enhances spatial analysis by providing more sophisticated tools for pattern recognition, prediction, and decision-making in geographic contexts.</p>

                        <h2>Key Applications</h2>
                        <ul>
                            <li>Land Use Classification</li>
                            <li>Population Density Prediction</li>
                            <li>Environmental Change Detection</li>
                            <li>Infrastructure Planning</li>
                        </ul>""",
                        course_id=course.id
                    ),
                    Module(
                        order=4,
                        title="Practical Applications",
                        content="""<h2>Real-World Applications</h2>
                        <p>This module explores practical applications of AI and ML in GIS through case studies and examples.</p>

                        <h2>Case Studies</h2>
                        <ul>
                            <li>Urban Planning and Smart Cities</li>
                            <li>Environmental Monitoring</li>
                            <li>Disaster Management</li>
                            <li>Transportation Planning</li>
                        </ul>""",
                        course_id=course.id
                    ),
                    Module(
                        order=5,
                        title="Final Quiz",
                        content="""<h2>Course Quiz</h2>
                        <p>Test your knowledge of AI and ML in GIS with this comprehensive quiz. Each question has multiple choice answers. Select the best answer for each question.</p>""",
                        course_id=course.id
                    )
                ]
                
                for module in modules:
                    db.session.add(module)
                db.session.commit()
                print("Created all modules")
                
                # Create quiz questions for the final module
                quiz_module = Module.query.filter_by(order=5).first()
                quiz_questions = [
                    QuizQuestion(
                        question_text="What is the primary goal of Artificial Intelligence?",
                        option_a="To create machines that can think and learn like humans",
                        option_b="To replace human workers with machines",
                        option_c="To make computers faster than humans",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which of these is NOT a type of Machine Learning?",
                        option_a="Supervised Learning",
                        option_b="Unsupervised Learning",
                        option_c="Manual Learning",
                        correct_answer="c",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is the main advantage of using AI in GIS?",
                        option_a="Automated analysis of large spatial datasets",
                        option_b="Making maps more colorful",
                        option_c="Reducing the need for GPS devices",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which algorithm is commonly used for image classification in GIS?",
                        option_a="Convolutional Neural Networks",
                        option_b="Linear Regression",
                        option_c="K-means Clustering",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is the purpose of validation in machine learning?",
                        option_a="To ensure the model performs well on unseen data",
                        option_b="To make the model run faster",
                        option_c="To reduce the size of the dataset",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which of these is an example of supervised learning?",
                        option_a="Predicting house prices based on features",
                        option_b="Grouping similar customers together",
                        option_c="Finding patterns in unlabeled data",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is the role of neural networks in GIS?",
                        option_a="To process complex spatial patterns and relationships",
                        option_b="To store geographic data",
                        option_c="To create 3D models of buildings",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which of these is a common application of AI in urban planning?",
                        option_a="Predicting traffic patterns and congestion",
                        option_b="Designing building facades",
                        option_c="Calculating property taxes",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is the main challenge in implementing AI in GIS?",
                        option_a="Data quality and availability",
                        option_b="Computer processing speed",
                        option_c="Internet connection speed",
                        correct_answer="a",
                        module_id=quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="How does AI contribute to environmental monitoring?",
                        option_a="By analyzing satellite imagery for changes",
                        option_b="By replacing environmental sensors",
                        option_c="By controlling weather patterns",
                        correct_answer="a",
                        module_id=quiz_module.id
                    )
                ]
                
                for question in quiz_questions:
                    db.session.add(question)
                db.session.commit()
                print("Created quiz questions")
            else:
                print("Courses already exist, skipping creation")
                
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            db.session.rollback()

# Initialize database
init_db()

def verify_admin_user():
    with app.app_context():
        try:
            # Get the admin user
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                # Verify admin permissions
                if not admin.is_admin:
                    print("Fixing admin permissions...")
                    admin.is_admin = True
                    admin.is_paid = True
                    db.session.commit()
                    print("Admin permissions fixed")
                else:
                    print("Admin permissions are correct")
            else:
                print("Admin user not found, creating one...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                    is_admin=True,
                    is_paid=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created")
                
        except Exception as e:
            print(f"Error verifying admin user: {str(e)}")
            db.session.rollback()

# Verify admin user on startup
verify_admin_user()

def add_gis_course():
    with app.app_context():
        try:
            # Check if course already exists
            existing_course = Course.query.filter_by(title="GIS Fundamentals").first()
            if existing_course:
                print("GIS Fundamentals course already exists")
                return

            # Create the course
            gis_course = Course(
                title="GIS Fundamentals",
                description="Master the fundamentals of Geographic Information Systems (GIS) through our comprehensive course covering key concepts, applications, and hands-on projects.",
                duration="4 weeks",
                mode="Online & Physical (Hybrid)",
                fee="KES 12,000",
                is_active=True
            )
            db.session.add(gis_course)
            db.session.commit()
            print("Created GIS Fundamentals course")

            # Create modules for the course
            modules = [
                Module(
                    order=1,
                    title="Introduction to GIS",
                    content="""<h2>Introduction to GIS</h2>
                    <p><strong>Objective:</strong> Understand the foundational concepts of Geographic Information Systems (GIS), including spatial thinking and the role of GIS in modern applications</p>
                    
                    <h3>Topics:</h3>
                    <ul>
                        <li>Spatial Thinking</li>
                        <li>Geographic Concept</li>
                        <li>GIS for Today and Beyond</li>
                    </ul>
                    
                    <h3>Reading:</h3>
                    <p><a href="https://2012books.lardbucket.org/books/geographic-information-system-basics/s05-introduction.html" target="_blank">Chapter 1: Introduction</a></p>""",
                    course_id=gis_course.id
                ),
                Module(
                    order=2,
                    title="Map Anatomy and Coordinate Systems",
                    content="""<h2>Map Anatomy and Coordinate Systems</h2>
                    <p><strong>Objective:</strong> Explore the components of maps, different map types, and the coordinate systems used in GIS.</p>
                    
                    <h3>Topics:</h3>
                    <ul>
                        <li>Maps and Map Types</li>
                        <li>Map Scale, Coordinate Systems, and Map Projections</li>
                        <li>Map Abstraction</li>
                    </ul>
                    
                    <h3>Reading:</h3>
                    <p><a href="https://2012books.lardbucket.org/books/geographic-information-system-basics/s06-map-anatomy.html" target="_blank">Chapter 2: Map Anatomy</a></p>""",
                    course_id=gis_course.id
                ),
                Module(
                    order=3,
                    title="GIS Data Models",
                    content="""<h2>GIS Data Models</h2>
                    <p><strong>Objective:</strong> Understand the different data models used in GIS, including raster and vector models, and the role of satellite imagery.</p>
                    
                    <h3>Topics:</h3>
                    <ul>
                        <li>Raster Data Models</li>
                        <li>Vector Data Models</li>
                        <li>Satellite Imagery and Aerial Photography</li>
                    </ul>
                    
                    <h3>Reading:</h3>
                    <p><a href="https://2012books.lardbucket.org/books/geographic-information-system-basics/s08-data-models-for-gis.html" target="_blank">Chapter 3: Data Models for GIS</a></p>""",
                    course_id=gis_course.id
                ),
                Module(
                    order=4,
                    title="Geospatial Data Management",
                    content="""<h2>Geospatial Data Management</h2>
                    <p><strong>Objective:</strong> Learn about acquiring geographic data, managing geospatial databases, understanding file formats, and ensuring data quality.</p>
                    
                    <h3>Topics:</h3>
                    <ul>
                        <li>Geographic Data Acquisition</li>
                        <li>Geospatial Database Management</li>
                        <li>File Formats</li>
                        <li>Data Quality</li>
                    </ul>
                    
                    <h3>Reading:</h3>
                    <p><a href="https://2012books.lardbucket.org/books/geographic-information-system-basics/s09-geospatial-data-management.html" target="_blank">Chapter 4: Geospatial Data Management</a></p>""",
                    course_id=gis_course.id
                ),
                Module(
                    order=5,
                    title="GIS Knowledge Check",
                    content="""<h2>GIS Knowledge Check</h2>
                    <p>Test your knowledge of GIS fundamentals with this comprehensive quiz. Each question has multiple choice answers. Select the best answer for each question.</p>""",
                    course_id=gis_course.id
                )
            ]
            
            for module in modules:
                db.session.add(module)
            db.session.commit()
            print("Created all modules for GIS Fundamentals course")
            
            # Create quiz questions for the final module
            quiz_module = Module.query.filter_by(course_id=gis_course.id, order=5).first()
            quiz_questions = [
                QuizQuestion(
                    question_text="Which of the following is not a core component of a GIS?",
                    option_a="Hardware",
                    option_b="Software",
                    option_c="People",
                    option_d="Word processor",
                    correct_answer="d",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="What type of map projection best represents the poles?",
                    option_a="Cylindrical",
                    option_b="Conic",
                    option_c="Planar",
                    option_d="Spherical",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which of the following is a key feature of raster data models?",
                    option_a="Represent data with points and lines",
                    option_b="Use grid cells to model spatial phenomena",
                    option_c="Are ideal for representing roads and parcels",
                    option_d="Store data in shapefiles",
                    correct_answer="b",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which format is commonly used for storing vector GIS data?",
                    option_a="JPEG",
                    option_b="TIFF",
                    option_c="Shapefile (.shp)",
                    option_d="PNG",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which method is most suitable for acquiring land cover data over large areas?",
                    option_a="Field surveying",
                    option_b="Manual sketching",
                    option_c="Remote sensing",
                    option_d="Map annotation",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which factor best describes accuracy in GIS data quality?",
                    option_a="The number of formats supported",
                    option_b="The size of the dataset",
                    option_c="How close data is to the true value",
                    option_d="How many layers are stored",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which coordinate system is based on degrees of latitude and longitude?",
                    option_a="UTM",
                    option_b="Cartesian",
                    option_c="Geographic Coordinate System (GCS)",
                    option_d="Polar",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which of the following is a common application of GIS?",
                    option_a="Text editing",
                    option_b="Spreadsheet analysis",
                    option_c="Urban planning",
                    option_d="Social media networking",
                    correct_answer="c",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which file format is used to store GIS map documents in ArcGIS?",
                    option_a="DOCX",
                    option_b="MXD",
                    option_c="CSV",
                    option_d="JPG",
                    correct_answer="b",
                    module_id=quiz_module.id
                ),
                QuizQuestion(
                    question_text="Which of the following is a major benefit of using GIS?",
                    option_a="Requires no data",
                    option_b="Improves decision-making",
                    option_c="Increases paperwork",
                    option_d="Reduces computing needs",
                    correct_answer="b",
                    module_id=quiz_module.id
                )
            ]
            
            for question in quiz_questions:
                db.session.add(question)
            db.session.commit()
            print("Created quiz questions for GIS Fundamentals course")
            
        except Exception as e:
            print(f"Error creating GIS course: {str(e)}")
            db.session.rollback()

# Add the GIS course
add_gis_course()

def add_web_dev_and_civil3d_courses():
    with app.app_context():
        try:
            # Check if courses already exist
            if Course.query.filter_by(title="Web Development Crash Course").first():
                print("Web Development course already exists")
            else:
                # Create Web Development course
                web_dev_course = Course(
                    title="Web Development Crash Course",
                    description="Build and deploy a complete dynamic web application using core technologies. Learn HTML, CSS, JavaScript, PHP, and MySQL in this comprehensive crash course.",
                    duration="4 weeks",
                    mode="Online & Physical (Hybrid)",
                    fee="KES 15,000",
                    is_active=True
                )
                db.session.add(web_dev_course)
                db.session.commit()
                print("Created Web Development Crash Course")

                # Create modules for Web Development course
                web_dev_modules = [
                    Module(
                        order=1,
                        title="Frontend Foundations",
                        content="""<h2>Frontend Foundations – HTML, CSS, and JavaScript Basics</h2>
                        <p><strong>Week 1 Theme:</strong> Learn how the web works and build your first static website.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Introduction to Web Development (How the web works, Frontend vs Backend)</li>
                            <li>HTML Essentials: Tags, forms, tables, media, links</li>
                            <li>CSS Basics: Selectors, box model, backgrounds, typography</li>
                            <li>JavaScript Basics: Variables, data types, operators, events, functions</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Create a personal homepage (HTML)</li>
                            <li>Add styling with CSS (fonts, layout, colors)</li>
                            <li>Add a button with JavaScript interaction</li>
                        </ul>
                        
                        <h3>Recommended Resources:</h3>
                        <ul>
                            <li>HTML Basics – MDN</li>
                            <li>CSS Fundamentals – MDN</li>
                            <li>JavaScript Introduction – MDN</li>
                        </ul>""",
                        course_id=web_dev_course.id
                    ),
                    Module(
                        order=2,
                        title="Responsive Design & JavaScript Interactivity",
                        content="""<h2>Responsive Design & JavaScript Interactivity</h2>
                        <p><strong>Week 2 Theme:</strong> Make your site dynamic and adaptable.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Advanced CSS: Flexbox, Grid, Media Queries</li>
                            <li>JavaScript DOM Manipulation</li>
                            <li>Event listeners, form inputs, conditionals, loops</li>
                            <li>Debugging JavaScript with browser DevTools</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Build a responsive navigation bar using Flexbox</li>
                            <li>Interactive To-Do List with Add/Delete using JS DOM</li>
                            <li>Mini quiz app with multiple questions and scoring</li>
                        </ul>
                        
                        <h3>Recommended Resources:</h3>
                        <ul>
                            <li>CSS Flexbox – CSS-Tricks</li>
                            <li>Grid Layout – MDN</li>
                            <li>DOM Manipulation Guide – JavaScript.info</li>
                        </ul>""",
                        course_id=web_dev_course.id
                    ),
                    Module(
                        order=3,
                        title="Backend Development with PHP & MySQL",
                        content="""<h2>Backend Development with PHP & MySQL</h2>
                        <p><strong>Week 3 Theme:</strong> Learn how the backend works and handle user data dynamically.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>PHP Syntax, Variables, Conditionals, $_GET & $_POST</li>
                            <li>Connecting PHP with MySQL using mysqli or PDO</li>
                            <li>SQL Basics: SELECT, INSERT, UPDATE, DELETE</li>
                            <li>Building CRUD operations</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Contact form storing entries in MySQL</li>
                            <li>Display form entries in a styled HTML table</li>
                            <li>Optional: Add a simple login form with PHP sessions</li>
                        </ul>
                        
                        <h3>Recommended Resources:</h3>
                        <ul>
                            <li>PHP Basics – W3Schools</li>
                            <li>PHP & MySQL Tutorial – TutorialRepublic</li>
                            <li>SQL Tutorial – W3Schools</li>
                        </ul>""",
                        course_id=web_dev_course.id
                    ),
                    Module(
                        order=4,
                        title="Full-Stack Web Project Development & Deployment",
                        content="""<h2>Full-Stack Web Project Development & Deployment</h2>
                        <p><strong>Week 4 Theme:</strong> Build, secure, and present a dynamic, real-world app.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Project planning and file organization</li>
                            <li>Connecting frontend and backend</li>
                            <li>Input validation and security tips</li>
                            <li>Testing and deploying</li>
                        </ul>
                        
                        <h3>Final Project Options:</h3>
                        <ul>
                            <li>Task Manager App</li>
                            <li>Student Portal</li>
                            <li>Simple Blog or Guestbook</li>
                        </ul>
                        
                        <h3>Recommended Resources:</h3>
                        <ul>
                            <li>PHP Form Validation – PHP.net</li>
                            <li>Deploying PHP App with XAMPP – Bitnami Guide</li>
                            <li>Security Checklist – OWASP Top 10</li>
                        </ul>""",
                        course_id=web_dev_course.id
                    ),
                    Module(
                        order=5,
                        title="Final Quiz",
                        content="""<h2>Web Development Crash Course Quiz</h2>
                        <p>Test your knowledge of web development fundamentals with this comprehensive quiz. Each question has multiple choice answers. Select the best answer for each question.</p>""",
                        course_id=web_dev_course.id
                    )
                ]
                
                for module in web_dev_modules:
                    db.session.add(module)
                db.session.commit()
                print("Created all modules for Web Development course")
                
                # Create quiz questions for Web Development course
                web_dev_quiz_module = Module.query.filter_by(course_id=web_dev_course.id, order=5).first()
                web_dev_quiz_questions = [
                    QuizQuestion(
                        question_text="Which HTML tag is used to insert an image?",
                        option_a="<pic>",
                        option_b="<media>",
                        option_c="<img>",
                        option_d="<src>",
                        correct_answer="c",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which property in CSS controls the layout spacing outside an element?",
                        option_a="padding",
                        option_b="margin",
                        option_c="border",
                        option_d="position",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What JavaScript keyword is used to declare a variable?",
                        option_a="varname",
                        option_b="data",
                        option_c="let",
                        option_d="constance",
                        correct_answer="c",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which layout method provides a grid-like structure in CSS?",
                        option_a="Flexbox",
                        option_b="Float",
                        option_c="CSS Grid",
                        option_d="Inline-block",
                        correct_answer="c",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="How do you select an element by ID using JavaScript?",
                        option_a="getElementsByClass()",
                        option_b="querySelectorAll('#id')",
                        option_c="document.getElementById('id')",
                        option_d="document.id('id')",
                        correct_answer="c",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which PHP global is used to access form data submitted with POST method?",
                        option_a="$POST",
                        option_b="$_POST",
                        option_c="$FormData",
                        option_d="$_DATA",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What SQL statement is used to retrieve data?",
                        option_a="INSERT",
                        option_b="SELECT",
                        option_c="UPDATE",
                        option_d="DELETE",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which language runs in the browser and controls page interaction?",
                        option_a="PHP",
                        option_b="JavaScript",
                        option_c="Python",
                        option_d="SQL",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What does XAMPP provide?",
                        option_a="A version of Git",
                        option_b="A local server for PHP & MySQL",
                        option_c="A text editor",
                        option_d="Hosting on GitHub",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which is a best practice for user input security?",
                        option_a="Disable JavaScript",
                        option_b="Validate and sanitize all inputs",
                        option_c="Use inline scripts",
                        option_d="Minify CSS files",
                        correct_answer="b",
                        module_id=web_dev_quiz_module.id
                    )
                ]
                
                for question in web_dev_quiz_questions:
                    db.session.add(question)
                db.session.commit()
                print("Created quiz questions for Web Development course")

            # Check if Civil 3D course exists
            if Course.query.filter_by(title="AutoCAD Civil 3D Crash Course").first():
                print("AutoCAD Civil 3D course already exists")
            else:
                # Create Civil 3D course
                civil3d_course = Course(
                    title="AutoCAD Civil 3D Crash Course",
                    description="Master AutoCAD Civil 3D for geospatial, land surveying, and engineering surveying. Learn surface modeling, parceling, road alignment, and volume calculations.",
                    duration="4 weeks",
                    mode="Online & Physical (Hybrid)",
                    fee="KES 20,000",
                    is_active=True
                )
                db.session.add(civil3d_course)
                db.session.commit()
                print("Created AutoCAD Civil 3D Crash Course")

                # Create modules for Civil 3D course
                civil3d_modules = [
                    Module(
                        order=1,
                        title="Introduction to Civil 3D for Surveying & Geospatial Mapping",
                        content="""<h2>Introduction to Civil 3D for Surveying & Geospatial Mapping</h2>
                        <p><strong>Theme:</strong> Get familiar with the Civil 3D environment and start managing survey data.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Overview of AutoCAD vs Civil 3D</li>
                            <li>Understanding the Civil 3D workspace, toolspace, and templates</li>
                            <li>Setting coordinate systems (NAD83, WGS84, UTM, Local Grid)</li>
                            <li>Importing survey points from CSV or data collectors</li>
                            <li>Working with description keys and point groups</li>
                            <li>Creating and labeling surfaces from points</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Import and manage raw point data</li>
                            <li>Create a Digital Terrain Model (DTM) surface</li>
                            <li>Apply contour labeling and display styles</li>
                        </ul>
                        
                        <h3>Resources:</h3>
                        <ul>
                            <li>Autodesk Civil 3D Introduction Video</li>
                            <li>Survey Data in Civil 3D – Autodesk Help</li>
                        </ul>""",
                        course_id=civil3d_course.id
                    ),
                    Module(
                        order=2,
                        title="Surface Modeling, Profiles, and Terrain Analysis",
                        content="""<h2>Surface Modeling, Profiles, and Terrain Analysis</h2>
                        <p><strong>Theme:</strong> Build surfaces, generate profiles, and analyze terrain features.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Creating TIN surfaces from survey data and breaklines</li>
                            <li>Adding boundaries and contours</li>
                            <li>Creating surface profiles along alignments</li>
                            <li>Extracting spot elevations and slope analysis</li>
                            <li>Labeling surface data dynamically</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Draw an alignment and generate a surface profile</li>
                            <li>Analyze cut-and-fill using two surfaces</li>
                            <li>Create slope maps and contour maps for export</li>
                        </ul>
                        
                        <h3>Resources:</h3>
                        <ul>
                            <li>Civil 3D Surface Modeling Basics – Autodesk</li>
                            <li>Profile Creation – YouTube Civil 3D Tutorial</li>
                        </ul>""",
                        course_id=civil3d_course.id
                    ),
                    Module(
                        order=3,
                        title="Parcels, Alignments, and Site Design Tools",
                        content="""<h2>Parcels, Alignments, and Site Design Tools</h2>
                        <p><strong>Theme:</strong> Create parcels, alignments, and prepare site layout for engineering use.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Parcel creation from layout tools and polylines</li>
                            <li>Using alignments for roads, boundaries, or canals</li>
                            <li>Creating and editing feature lines</li>
                            <li>Corridor modeling basics</li>
                            <li>Site grading and earthwork setup</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Subdivide a site using parcel tools and add labels</li>
                            <li>Create a basic road alignment with offset and station labels</li>
                            <li>Grade a site with slopes, benches, and create volume surfaces</li>
                        </ul>
                        
                        <h3>Resources:</h3>
                        <ul>
                            <li>Parcels in Civil 3D – Official Guide</li>
                            <li>Corridor Basics – Autodesk YouTube</li>
                        </ul>""",
                        course_id=civil3d_course.id
                    ),
                    Module(
                        order=4,
                        title="Quantity Takeoff, Data Sharing, and Final Plot Production",
                        content="""<h2>Quantity Takeoff, Data Sharing, and Final Plot Production</h2>
                        <p><strong>Theme:</strong> Extract quantities, prepare final deliverables, and share Civil 3D data effectively.</p>
                        
                        <h3>Key Topics:</h3>
                        <ul>
                            <li>Cut & fill volume calculations between surfaces</li>
                            <li>Earthwork quantity reporting</li>
                            <li>Creating cross-sections</li>
                            <li>Data shortcut management</li>
                            <li>Producing annotated plan & profile sheets</li>
                            <li>Exporting to GIS, PDF, DWG, and LandXML formats</li>
                        </ul>
                        
                        <h3>Activities:</h3>
                        <ul>
                            <li>Generate cross-sections and quantity reports</li>
                            <li>Create a layout sheet with plan/profile view</li>
                            <li>Export surface to GIS shapefile and LandXML</li>
                        </ul>
                        
                        <h3>Resources:</h3>
                        <ul>
                            <li>Civil 3D Earthwork Quantities – Tutorial</li>
                            <li>Civil 3D to GIS Export – Autodesk Knowledge</li>
                        </ul>""",
                        course_id=civil3d_course.id
                    ),
                    Module(
                        order=5,
                        title="Final Quiz",
                        content="""<h2>AutoCAD Civil 3D Fundamentals Quiz</h2>
                        <p>Test your knowledge of Civil 3D fundamentals with this comprehensive quiz. Each question has multiple choice answers. Select the best answer for each question.</p>""",
                        course_id=civil3d_course.id
                    )
                ]
                
                for module in civil3d_modules:
                    db.session.add(module)
                db.session.commit()
                print("Created all modules for Civil 3D course")
                
                # Create quiz questions for Civil 3D course
                civil3d_quiz_module = Module.query.filter_by(course_id=civil3d_course.id, order=5).first()
                civil3d_quiz_questions = [
                    QuizQuestion(
                        question_text="What does a TIN surface in Civil 3D represent?",
                        option_a="A type of 2D surface used for drafting",
                        option_b="A flat map with elevation symbols",
                        option_c="A triangulated network of 3D points representing terrain",
                        option_d="A data table of elevations",
                        correct_answer="c",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which Civil 3D object is used to define the horizontal path of a road or pipeline?",
                        option_a="Feature Line",
                        option_b="Alignment",
                        option_c="Profile",
                        option_d="Parcel Line",
                        correct_answer="b",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="In Civil 3D, what is the purpose of a description key?",
                        option_a="To filter alignments",
                        option_b="To automatically assign styles and layers to points",
                        option_c="To label surfaces",
                        option_d="To generate volumes",
                        correct_answer="b",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What does the 'Point Group' in Civil 3D help you manage?",
                        option_a="Volume computations",
                        option_b="Road design templates",
                        option_c="Sets of survey points with shared characteristics",
                        option_d="File import formats",
                        correct_answer="c",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which tool is used to calculate cut and fill between two surfaces?",
                        option_a="Grading Tool",
                        option_b="Surface Slope Analysis",
                        option_c="Earthwork Volume Report",
                        option_d="Corridor Surfaces",
                        correct_answer="c",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is the first step when creating a parcel in Civil 3D from a closed polyline?",
                        option_a="Export the polyline as a shapefile",
                        option_b="Assign a feature line",
                        option_c="Convert it to a parcel using the 'Create Parcel from Object' tool",
                        option_d="Assign a coordinate system",
                        correct_answer="c",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which command allows you to create contour lines from a surface?",
                        option_a="Create Profile View",
                        option_b="Add Labels",
                        option_c="Extract Contours",
                        option_d="Surface Properties > Contours",
                        correct_answer="d",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="How do you define elevations along an alignment for road design?",
                        option_a="By creating a feature line",
                        option_b="By assigning a parcel boundary",
                        option_c="By creating a surface",
                        option_d="By creating a profile view",
                        correct_answer="d",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="Which export format is best for sharing terrain data with GIS software?",
                        option_a="DWG",
                        option_b="DXF",
                        option_c="LandXML",
                        option_d="PDF",
                        correct_answer="c",
                        module_id=civil3d_quiz_module.id
                    ),
                    QuizQuestion(
                        question_text="What is a Corridor in Civil 3D primarily used for?",
                        option_a="Mapping flood zones",
                        option_b="Modeling roads, channels, or railways based on assemblies",
                        option_c="Managing coordinate systems",
                        option_d="Creating boundary layouts",
                        correct_answer="b",
                        module_id=civil3d_quiz_module.id
                    )
                ]
                
                for question in civil3d_quiz_questions:
                    db.session.add(question)
                db.session.commit()
                print("Created quiz questions for Civil 3D course")
                
        except Exception as e:
            print(f"Error creating courses: {str(e)}")
            db.session.rollback()

# Add the new courses
add_web_dev_and_civil3d_courses()

def add_additional_courses():
    with app.app_context():
        try:
            # List of new courses to add
            new_courses = [
                {
                    "title": "ArcGIS for Geospatial and Survey Applications",
                    "description": "Master ArcGIS for geospatial applications. Learn data creation, analysis, visualization, and map publishing using ArcGIS Online.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 25,000",
                    "modules": [
                        {
                            "title": "Getting Started with ArcGIS",
                            "content": """<h2>Getting Started with ArcGIS</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>ArcGIS Desktop vs Pro overview</li>
                                <li>Shapefiles, layers, and projections</li>
                                <li>Add and symbolize data, explore attribute tables</li>
                            </ul>"""
                        },
                        {
                            "title": "Data Editing and Geoprocessing",
                            "content": """<h2>Data Editing and Geoprocessing</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Digitizing, snapping, and topology</li>
                                <li>Buffer, clip, intersect, merge, dissolve</li>
                                <li>Join and relate tables</li>
                            </ul>"""
                        },
                        {
                            "title": "Spatial Analysis and Mapping",
                            "content": """<h2>Spatial Analysis and Mapping</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Thematic mapping and classification</li>
                                <li>Spatial query and selection tools</li>
                                <li>Geocoding and spatial joins</li>
                            </ul>"""
                        },
                        {
                            "title": "ArcGIS Online and Sharing Maps",
                            "content": """<h2>ArcGIS Online and Sharing Maps</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Intro to ArcGIS Online & Web Maps</li>
                                <li>Publishing map services</li>
                                <li>Sharing and embedding maps</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "ArchiCAD for Building and Infrastructure Designers",
                    "description": "Learn ArchiCAD for architectural design. Master 3D modeling, documentation, and BIM collaboration.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 30,000",
                    "modules": [
                        {
                            "title": "ArchiCAD Interface & Modeling Basics",
                            "content": """<h2>ArchiCAD Interface & Modeling Basics</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Workspace orientation</li>
                                <li>Story settings, walls, slabs, roofs</li>
                            </ul>"""
                        },
                        {
                            "title": "Advanced Object Placement",
                            "content": """<h2>Advanced Object Placement</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Windows, doors, stairs, columns</li>
                                <li>Object libraries and parametric editing</li>
                            </ul>"""
                        },
                        {
                            "title": "Documentation and Annotation",
                            "content": """<h2>Documentation and Annotation</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Dimensions, labels, sections, elevations</li>
                                <li>Layout book, publishing drawings</li>
                            </ul>"""
                        },
                        {
                            "title": "Rendering and BIM Collaboration",
                            "content": """<h2>Rendering and BIM Collaboration</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>3D views and rendering tools</li>
                                <li>IFC export and BIMcloud collaboration</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "Global Mapper Essentials",
                    "description": "Master Global Mapper for GIS and terrain analysis. Learn raster handling, vector editing, and data conversion.",
                    "duration": "3 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 20,000",
                    "modules": [
                        {
                            "title": "Introduction to Interface and Raster Handling",
                            "content": """<h2>Introduction to Interface and Raster Handling</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Exploring UI, loading raster data</li>
                                <li>Coordinate systems</li>
                            </ul>"""
                        },
                        {
                            "title": "Vector Data Editing and Terrain Analysis",
                            "content": """<h2>Vector Data Editing and Terrain Analysis</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Creating shapefiles, digitizing tools</li>
                                <li>Contours, slope maps</li>
                            </ul>"""
                        },
                        {
                            "title": "Data Conversion and Export",
                            "content": """<h2>Data Conversion and Export</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Format conversion, GPS data integration</li>
                                <li>Exporting tiles</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "Graphic Design Mastery with Canva & Adobe Suite",
                    "description": "Master graphic design using Canva and Adobe Creative Suite. Learn design principles, image editing, and vector design.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 25,000",
                    "modules": [
                        {
                            "title": "Design Principles and Canva Basics",
                            "content": """<h2>Design Principles and Canva Basics</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Typography, alignment, hierarchy</li>
                                <li>Color theory, designing with templates</li>
                            </ul>"""
                        },
                        {
                            "title": "Adobe Photoshop for Image Editing",
                            "content": """<h2>Adobe Photoshop for Image Editing</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Layer management, masks</li>
                                <li>Adjustment layers, background removal</li>
                            </ul>"""
                        },
                        {
                            "title": "Adobe Illustrator for Vector Design",
                            "content": """<h2>Adobe Illustrator for Vector Design</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Pen tool, shapes, paths</li>
                                <li>Logo design, custom illustrations</li>
                            </ul>"""
                        },
                        {
                            "title": "Branding and Portfolio Creation",
                            "content": """<h2>Branding and Portfolio Creation</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Creating a brand kit, mockups</li>
                                <li>Exporting assets, portfolio presentation</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "Carlson 3D for Land Surveying and Engineering",
                    "description": "Master Carlson 3D for surveying and engineering. Learn data import, surface modeling, and road design.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 28,000",
                    "modules": [
                        {
                            "title": "Survey Data Import and Field-to-Finish",
                            "content": """<h2>Survey Data Import and Field-to-Finish</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Importing RAW/JOB files</li>
                                <li>Codes and linework, COGO</li>
                            </ul>"""
                        },
                        {
                            "title": "Surface and Contour Modeling",
                            "content": """<h2>Surface and Contour Modeling</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Creating TINs, breaklines</li>
                                <li>Contours, profiles</li>
                            </ul>"""
                        },
                        {
                            "title": "Road Design and Sections",
                            "content": """<h2>Road Design and Sections</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Alignments, cross sections</li>
                                <li>Templates, volume reports</li>
                            </ul>"""
                        },
                        {
                            "title": "Plotting, Annotation, and Output",
                            "content": """<h2>Plotting, Annotation, and Output</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Sheet setup, scale, plotting</li>
                                <li>Labeling points and features</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "Adobe Creative Cloud Essentials",
                    "description": "Master Adobe Creative Cloud tools. Learn Photoshop, Illustrator, and InDesign for professional design work.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 30,000",
                    "modules": [
                        {
                            "title": "Adobe Photoshop",
                            "content": """<h2>Adobe Photoshop</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Image adjustments, retouching</li>
                                <li>Masking, compositing</li>
                            </ul>"""
                        },
                        {
                            "title": "Adobe Illustrator",
                            "content": """<h2>Adobe Illustrator</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Vector art, logo design</li>
                                <li>Tracing, type effects</li>
                            </ul>"""
                        },
                        {
                            "title": "Adobe InDesign",
                            "content": """<h2>Adobe InDesign</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Document layout, master pages</li>
                                <li>Typography</li>
                            </ul>"""
                        },
                        {
                            "title": "Cross-App Workflows & Exports",
                            "content": """<h2>Cross-App Workflows & Exports</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Moving files across apps</li>
                                <li>Preparing for print/web</li>
                            </ul>"""
                        }
                    ]
                },
                {
                    "title": "Advanced Python for Databases and Automation",
                    "description": "Master Python for database management and automation. Learn ORM, web development, and data processing.",
                    "duration": "4 weeks",
                    "mode": "Online & Physical (Hybrid)",
                    "fee": "KES 25,000",
                    "modules": [
                        {
                            "title": "Python and Relational Databases",
                            "content": """<h2>Python and Relational Databases</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>SQLite, PostgreSQL, MySQL</li>
                                <li>Database connections and queries</li>
                            </ul>"""
                        },
                        {
                            "title": "ORM with SQLAlchemy & Data Models",
                            "content": """<h2>ORM with SQLAlchemy & Data Models</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Tables, relationships</li>
                                <li>Queries, migrations</li>
                            </ul>"""
                        },
                        {
                            "title": "Building Data Dashboards or APIs",
                            "content": """<h2>Building Data Dashboards or APIs</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Flask/FastAPI for web apps</li>
                                <li>Frontend integration</li>
                            </ul>"""
                        },
                        {
                            "title": "Automation and Integration",
                            "content": """<h2>Automation and Integration</h2>
                            <p><strong>Key Topics:</strong></p>
                            <ul>
                                <li>Automating reports, ETL</li>
                                <li>REST APIs, data sync</li>
                            </ul>"""
                        }
                    ]
                }
            ]

            # Add each course
            for course_data in new_courses:
                # Check if course already exists
                if Course.query.filter_by(title=course_data["title"]).first():
                    print(f"Course '{course_data['title']}' already exists")
                    continue

                # Create course
                course = Course(
                    title=course_data["title"],
                    description=course_data["description"],
                    duration=course_data["duration"],
                    mode=course_data["mode"],
                    fee=course_data["fee"],
                    is_active=True
                )
                db.session.add(course)
                db.session.commit()
                print(f"Created course: {course_data['title']}")

                # Create modules
                for i, module_data in enumerate(course_data["modules"], 1):
                    module = Module(
                        order=i,
                        title=module_data["title"],
                        content=module_data["content"],
                        course_id=course.id
                    )
                    db.session.add(module)
                db.session.commit()
                print(f"Created modules for {course_data['title']}")

                # Create quiz module
                quiz_module = Module(
                    order=len(course_data["modules"]) + 1,
                    title="Final Project",
                    content=f"""<h2>{course_data['title']} Final Project</h2>
                    <p>This module contains your final project requirements and submission guidelines. Your project will be evaluated based on the following criteria:</p>
                    
                    <h3>Project Deliverables:</h3>
                    <ul>
                        <li>Complete project files and documentation</li>
                        <li>Project report explaining your approach and methodology</li>
                        <li>Presentation of your work and results</li>
                    </ul>
                    
                    <h3>Evaluation Criteria:</h3>
                    <ul>
                        <li>Technical accuracy and completeness</li>
                        <li>Quality of implementation</li>
                        <li>Documentation and presentation</li>
                        <li>Problem-solving approach</li>
                    </ul>
                    
                    <h3>Submission Guidelines:</h3>
                    <ul>
                        <li>Submit all project files in a single ZIP archive</li>
                        <li>Include a detailed project report in PDF format</li>
                        <li>Prepare a 10-minute presentation of your work</li>
                        <li>Deadline: End of Week {course_data['duration'].split()[0]}</li>
                    </ul>""",
                    course_id=course.id
                )
                db.session.add(quiz_module)
                db.session.commit()
                print(f"Created final project module for {course_data['title']}")

        except Exception as e:
            print(f"Error creating courses: {str(e)}")
            db.session.rollback()

# Add the additional courses
add_additional_courses()

# Import fallback routes
try:
    import dashboard_fallback
    print("Imported dashboard fallback routes")
except Exception as e:
    print(f"Error importing dashboard fallback: {str(e)}")

try:
    import certificate_fallback
    print("Imported certificate fallback routes")
except Exception as e:
    print(f"Error importing certificate fallback: {str(e)}")

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal Server Error: {str(error)}")
    return render_template('error.html', 
                         message="Internal Server Error",
                         error="The server encountered an error. Please try again later or contact support.",
                         user=current_user if current_user.is_authenticated else None), 500

@app.route('/test-image/<filename>')
def test_image(filename):
    return send_file(f'static/{filename}', mimetype='image/jpeg')

@app.route('/brochure')
def brochure():
    return render_template('brochure.html')

if __name__ == '__main__':
    app.run(debug=True)
