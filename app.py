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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
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

def initialize_db():
    if not wait_for_db():
        return
        
    try:
        # Check if columns already exist
        columns = db.session.execute(text("""
            SHOW COLUMNS FROM user
        """)).fetchall()
        
        column_names = [col[0] for col in columns]
        
        if 'is_admin' not in column_names:
            print("Adding is_admin column...")
            db.session.execute(text("""
                ALTER TABLE user 
                ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
            """))
        
        if 'is_paid' not in column_names:
            print("Adding is_paid column...")
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
        print(f"Error during initialization: {str(e)}")
        db.session.rollback()

# Run initialization when the app starts
with app.app_context():
    initialize_db()

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

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    completion_date = db.Column(db.DateTime, nullable=True)
    next_attempt_available = db.Column(db.DateTime, nullable=True)

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
    return render_template('index.html', courses=courses)

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

@app.route('/download_certificate')
@login_required
def download_certificate():
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
    
    try:
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
        app.logger.error(f"Certificate generation error: {str(e)}")
        flash('Error generating certificate. Please try again later.', 'error')
        return redirect(url_for('dashboard'))

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
            
if __name__ == '__main__':
    app.run(debug=True)
