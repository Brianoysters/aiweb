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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    progress = db.relationship('Progress', backref='user', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    modules = db.relationship('Module', backref='course', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    doc_link = db.Column(db.String(500), nullable=True)
    progress = db.relationship('Progress', backref='module', lazy=True)

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
    # Get all modules for the courses section
    modules = Module.query.all()
    
    # Get all admin users for the admin section
    admins = User.query.filter_by(is_admin=True).all()
    
    # Get user's progress
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()
    completed_modules = [p.module_id for p in user_progress if p.completed]
    
    return render_template('dashboard.html', 
                         modules=modules,
                         admins=admins,
                         completed_modules=completed_modules)

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
    module = Module.query.get_or_404(module_id)
    progress = Progress.query.filter_by(user_id=current_user.id, module_id=module_id).first()
    
    # Check if previous module is completed
    if module.order > 1:
        prev_module = Module.query.filter_by(order=module.order-1).first()
        prev_progress = Progress.query.filter_by(
            user_id=current_user.id, 
            module_id=prev_module.id
        ).first()
        
        if not prev_progress or not prev_progress.completed:
            flash('Please complete the previous module first')
            return redirect(url_for('dashboard'))
    
    return render_template('module.html', module=module, progress=progress, doc_link=module.doc_link)

@app.route('/complete_module/<int:module_id>')
@login_required
def complete_module(module_id):
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
    return redirect(url_for('dashboard'))

@app.route('/quiz')
@login_required
def quiz():
    if not current_user.is_paid:
        flash('Please complete your payment to access the quiz.', 'warning')
        return redirect(url_for('dashboard'))
    
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
                    return render_template('quiz.html', next_attempt_available=next_attempt_time)
        
        # Check if cooldown period has passed
        if last_attempt.next_attempt_available and datetime.utcnow() < last_attempt.next_attempt_available:
            return render_template('quiz.html', next_attempt_available=last_attempt.next_attempt_available)
    
    return render_template('quiz.html')

@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    score = float(request.form['score'])
    passed = score >= 80
    current_time = datetime.utcnow()
    
    # Get attempt number
    attempt_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    
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
    
    if passed:
        flash('Congratulations! You have passed the quiz!')
        return redirect(url_for('certificate'))
    else:
        flash(f'You scored {score}%. You need 80% to pass. Try again after the cooldown period.')
        return redirect(url_for('dashboard'))

@app.route('/certificate')
@login_required
def certificate():
    if not current_user.is_paid:
        flash('Please complete your payment to access the certificate.', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        # Create certificate
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 700, "Certificate of Completion")
        
        c.setFont("Helvetica", 16)
        c.drawString(100, 650, f"This is to certify that {current_user.username}")
        c.drawString(100, 620, "has successfully completed the AI Course")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, 550, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        # Save the PDF
        c.save()
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=AI_Course_Certificate_{current_user.username}.pdf'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Certificate generation error: {str(e)}")
        flash('Error generating certificate. Please try again later.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/download_certificate')
@login_required
def download_certificate():
    # Create a unique temporary file for the certificate
    temp_file = os.path.join(os.environ.get('TEMP', 'temp'), f'certificate_{current_user.id}_{int(datetime.now().timestamp())}.pdf')
    
    try:
        # Create the PDF with letter size
        c = canvas.Canvas(temp_file, pagesize=letter)
        width, height = letter
        
        # Add company name at the top
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 150, "SUBOMAP AFRICA GEOSYSTEMS")
        
        # Add certificate title
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width/2, height - 200, "Certificate of Completion")
        
        # Add decorative border
        c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray color
        c.setLineWidth(15)
        c.rect(50, 50, width-100, height-100)
        
        # Add watermark (smaller and contained within certificate)
        c.saveState()
        c.setFillColorRGB(0.9, 0.9, 0.9)  # Very light gray
        c.setFont("Helvetica-Bold", 40)  # Reduced font size
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "SUBOMAP AFRICA GEOSYSTEMS")
        c.restoreState()
        
        # Add certificate text
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height - 250, "This is to certify that")
        
        # Add user name
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 300, current_user.username)
        
        # Add completion text
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height - 350, "has successfully completed the")
        c.drawCentredString(width/2, height - 380, "AI in Web GIS Course")
        
        # Add date
        c.setFont("Helvetica", 14)
        date_str = datetime.now().strftime("%B %d, %Y")
        c.drawCentredString(width/2, height - 450, f"Completed on {date_str}")
        
        # Add signature lines
        y_position = 150  # Position from bottom
        line_width = 200  # Width of signature line
        
        # Course Director signature
        c.setLineWidth(1)
        c.setStrokeColorRGB(0, 0, 0)
        c.line(width/4 - line_width/2, y_position, width/4 + line_width/2, y_position)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/4, y_position - 20, "Course Director")
        
        # CEO signature
        c.line(3*width/4 - line_width/2, y_position, 3*width/4 + line_width/2, y_position)
        c.drawCentredString(3*width/4, y_position - 20, "Chief Executive Officer")
        
        c.save()
        
        # Send the file
        return_data = send_file(
            temp_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'AI_WebGIS_Certificate_{current_user.username}.pdf'
        )
        
        return return_data
        
    finally:
        # Clean up the temporary file in a finally block to ensure it's always deleted
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except Exception as e:
            app.logger.error(f"Error cleaning up temporary file: {e}")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Update existing modules with documentation links
        module_links = {
            1: "https://docs.google.com/document/d/1qajlv9m0qQ6mLHen5IqfnS-KY75TIc8x9NbKLwAzO0s/edit?usp=sharing",
            2: "https://docs.google.com/document/d/1XKCEm18sHRooGkCC90IhcQvdWGCNGdKK2px4iOHCn9Q/edit?usp=sharing",
            3: "https://docs.google.com/document/d/1u3mq0dvNmsIhZOKk4yLJWpvlbLT2n6L4VkoweE1rWWQ/edit?usp=sharing",
            4: "https://docs.google.com/document/d/1qUcU2GUbgxqI7QCGhgX6xKCL36cBqLSreUoaySGm0Qc/edit?usp=sharing"
        }
        
        for order, link in module_links.items():
            module = Module.query.filter_by(order=order).first()
            if module:
                module.doc_link = link
                db.session.commit()
        
        # Check if modules exist, if not create sample modules
        if not Module.query.first():
            modules = [
                Module(order=1, title="Introduction to AI and ML in GIS", 
                      content="""<h3>Overview of AI and ML in GIS</h3>
                      <p>This module covers:</p>
                      <ul>
                        <li>AI and ML concepts in GIS context</li>
                        <li>Role of AI and ML in GIS applications</li>
                        <li>Data types and sources in GIS (Raster, Vector, Remote Sensing)</li>
                        <li>Geospatial data processing fundamentals</li>
                        <li>Ethical considerations and challenges</li>
                      </ul>
                      <h3>Practical Components</h3>
                      <ul>
                        <li>Basic Python scripting for GIS</li>
                        <li>Introduction to geospatial libraries (GDAL, Rasterio, GeoPandas)</li>
                      </ul>
                      """,
                      doc_link="https://docs.google.com/document/d/1qajlv9m0qQ6mLHen5IqfnS-KY75TIc8x9NbKLwAzO0s/edit?usp=sharing"),
                Module(order=2, title="Machine Learning for Spatial Analysis", 
                      content="""<h3>Key Topics</h3>
                      <ul>
                        <li>Supervised vs. Unsupervised Learning in GIS</li>
                        <li>Feature Engineering for Spatial Data</li>
                        <li>Spatial Clustering and Classification Techniques</li>
                        <li>Regression Models for Geospatial Prediction</li>
                        <li>Time-Series Analysis in GIS</li>
                        <li>Deep Learning-Based Models</li>
                      </ul>
                      <h3>Practical Components</h3>
                      <ul>
                        <li>Implementing K-Means and DBSCAN for spatial clustering</li>
                        <li>Training Random Forest models for land-use classification</li>
                        <li>Using CNNs for feature extraction in remote sensing</li>
                      </ul>
                      """,
                      doc_link="https://docs.google.com/document/d/1XKCEm18sHRooGkCC90IhcQvdWGCNGdKK2px4iOHCn9Q/edit?usp=sharing"),
                Module(order=3, title="AI and Deep Learning for GIS Applications", 
                      content="""<h3>Core Concepts</h3>
                      <ul>
                        <li>Neural Networks for Geospatial Data</li>
                        <li>Object Detection in Remote Sensing</li>
                        <li>Semantic Segmentation for Land Cover Classification</li>
                        <li>Deep Learning Models (CNNs, RNNs) for GIS</li>
                        <li>AI in Geospatial Automation and Decision Support</li>
                      </ul>
                      <h3>Practical Components</h3>
                      <ul>
                        <li>Training CNNs for land cover classification</li>
                        <li>Using TensorFlow/Keras for geospatial image analysis</li>
                      </ul>
                      """,
                      doc_link="https://docs.google.com/document/d/1u3mq0dvNmsIhZOKk4yLJWpvlbLT2n6L4VkoweE1rWWQ/edit?usp=sharing"),
                Module(order=4, title="Practical Applications of AI and ML in GIS", 
                      content="""<h3>Applications</h3>
                      <ul>
                        <li>AI for Water Body Detection in Satellite Images</li>
                        <li>Route Optimization Using AI and GIS</li>
                        <li>Real-time Geospatial Data Processing</li>
                        <li>AI-Powered Urban Planning and Environmental Monitoring</li>
                      </ul>
                      <h3>Practical Components</h3>
                      <ul>
                        <li>Water Body Detection Using AI</li>
                        <li>Implementing AI for detecting water bodies in remote sensing imagery</li>
                        <li>Shortest Route Optimization Using GIS and AI</li>
                        <li>Using Folium for mapping and visualization</li>
                      </ul>
                      """,
                      doc_link="https://docs.google.com/document/d/1qUcU2GUbgxqI7QCGhgX6xKCL36cBqLSreUoaySGm0Qc/edit?usp=sharing"),
                Module(order=5, title="Final Assessment", 
                      content="""<h3>Final Assessment Instructions</h3>
                      <p>You have completed all the modules! Now it's time to test your knowledge:</p>
                      <ul>
                          <li>The quiz consists of 10 multiple-choice questions</li>
                          <li>You need to score 80% or higher to pass (8 or more correct answers)</li>
                          <li>Each question tests your understanding of AI in Web GIS</li>
                          <li>You'll receive immediate feedback on your answers</li>
                          <li>Upon passing, you can download your certificate</li>
                      </ul>
                      <div class="text-center mt-4">
                          <a href="/quiz" class="btn btn-primary btn-lg">Start Quiz</a>
                      </div>""")
            ]
            for module in modules:
                db.session.add(module)
            db.session.commit()
            
    app.run(debug=True)
