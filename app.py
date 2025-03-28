from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from flask_migrate import Migrate
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Database Configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Handle Render's postgres:// URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
else:
    # Local development database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:4832@localhost/AIDB'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with explicit engine configuration
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], 
                      **app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}))
db = SQLAlchemy(app, engine=engine)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Increased length to 255
    progress = db.relationship('Progress', backref='user', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
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
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
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
    modules = Module.query.order_by(Module.order).all()
    progress = Progress.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', modules=modules, progress=progress)

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
    
    return render_template('module.html', module=module, progress=progress)

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
    # Check if all previous modules are completed
    modules_count = Module.query.count()
    completed_count = Progress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()
    
    if completed_count < modules_count - 1:  # Excluding quiz module
        flash('Please complete all modules before taking the quiz')
        return redirect(url_for('dashboard'))
    
    # Get latest quiz attempt
    latest_attempt = QuizResult.query.filter_by(
        user_id=current_user.id
    ).order_by(QuizResult.completion_date.desc()).first()
    
    # Check attempt limits
    if latest_attempt:
        if latest_attempt.passed:
            flash('You have already passed the quiz!')
            return redirect(url_for('certificate'))
            
        current_time = datetime.utcnow()
        if latest_attempt.next_attempt_available and current_time < latest_attempt.next_attempt_available:
            wait_time = latest_attempt.next_attempt_available - current_time
            hours = int(wait_time.total_seconds() / 3600)
            minutes = int((wait_time.total_seconds() % 3600) / 60)
            flash(f'Please wait {hours} hours and {minutes} minutes before your next attempt')
            return redirect(url_for('dashboard'))
            
        attempts_today = QuizResult.query.filter(
            QuizResult.user_id == current_user.id,
            QuizResult.completion_date >= current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        if attempts_today >= 2:
            next_attempt = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            flash(f'You have reached the maximum attempts for today. Try again tomorrow.')
            return redirect(url_for('dashboard'))
            
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
    quiz_result = QuizResult.query.filter_by(
        user_id=current_user.id,
        passed=True
    ).first()
    
    if not quiz_result:
        return redirect(url_for('dashboard'))
        
    return render_template('certificate.html')

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Check if modules exist, if not create sample modules
        if not Module.query.first():
            modules = [
                Module(order=1, title="Introduction to AI in Web GIS", 
                      content="""<h3>Introduction to AI in Web GIS</h3>
                      <p>This module covers the fundamentals of integrating AI with Web GIS systems:</p>
                      <ul>
                          <li>Understanding AI and Machine Learning basics</li>
                          <li>Overview of Web GIS architecture</li>
                          <li>Integration points between AI and GIS</li>
                          <li>Basic tools and frameworks</li>
                      </ul>"""),
                Module(order=2, title="Machine Learning for Spatial Analysis", 
                      content="""<h3>Machine Learning in Spatial Analysis</h3>
                      <p>Learn how machine learning algorithms can be applied to spatial data:</p>
                      <ul>
                          <li>Spatial pattern recognition</li>
                          <li>Predictive modeling for geographic data</li>
                          <li>Classification of spatial features</li>
                          <li>Clustering algorithms for geographic data</li>
                      </ul>"""),
                Module(order=3, title="Deep Learning in GIS", 
                      content="""<h3>Deep Learning Applications in GIS</h3>
                      <p>Explore how deep learning enhances GIS capabilities:</p>
                      <ul>
                          <li>Neural networks for spatial analysis</li>
                          <li>Image recognition in satellite data</li>
                          <li>Feature extraction from maps</li>
                          <li>Time series analysis of spatial data</li>
                      </ul>"""),
                Module(order=4, title="Project Implementation", 
                      content="""<h3>Practical Implementation</h3>
                      <p>Apply your knowledge in real-world GIS projects:</p>
                      <ul>
                          <li>Setting up an AI-powered Web GIS</li>
                          <li>Implementing spatial analysis algorithms</li>
                          <li>Creating interactive map features</li>
                          <li>Deploying AI models in web environment</li>
                      </ul>"""),
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
