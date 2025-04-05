from app import app, db, User, Course, Module
from werkzeug.security import generate_password_hash

def restore_data():
    with app.app_context():
        try:
            # Delete existing data in correct order
            Module.query.delete()
            Course.query.delete()
            User.query.delete()
            db.session.commit()
            print("Cleared existing data")

            # Create admin user with pbkdf2:sha256 hashing
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True,
                is_paid=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Successfully created admin user")

            # Create AI course
            ai_course = Course(
                title="Introduction to Artificial Intelligence",
                description="Master the fundamentals of AI through our comprehensive course covering key concepts, applications, and hands-on projects.",
                is_active=True
            )
            db.session.add(ai_course)
            db.session.commit()
            print("Successfully created AI course")

            # Create modules
            modules = [
                Module(
                    order=1,
                    title="Introduction to AI and ML in GIS",
                    content="""<h3>Overview of AI and ML in GIS</h3>
                    <p>This module covers:</p>
                    <ul>
                        <li>AI and ML concepts in GIS context</li>
                        <li>Role of AI and ML in GIS applications</li>
                        <li>Data types and sources in GIS (Raster, Vector, Remote Sensing)</li>
                        <li>Geospatial data processing fundamentals</li>
                        <li>Ethical considerations and challenges</li>
                    </ul>""",
                    course_id=ai_course.id,
                    doc_link="https://docs.google.com/document/d/1"
                ),
                Module(
                    order=2,
                    title="Machine Learning for Spatial Analysis",
                    content="""<h3>Key Topics</h3>
                    <ul>
                        <li>Supervised vs. Unsupervised Learning in GIS</li>
                        <li>Feature Engineering for Spatial Data</li>
                        <li>Spatial Clustering and Classification Techniques</li>
                        <li>Regression Models for Geospatial Prediction</li>
                    </ul>""",
                    course_id=ai_course.id,
                    doc_link="https://docs.google.com/document/d/2"
                ),
                Module(
                    order=3,
                    title="AI and Deep Learning for GIS Applications",
                    content="""<h3>Core Concepts</h3>
                    <ul>
                        <li>Neural Networks for Geospatial Data</li>
                        <li>Object Detection in Remote Sensing</li>
                        <li>Semantic Segmentation for Land Cover Classification</li>
                        <li>Deep Learning Models (CNNs, RNNs) for GIS</li>
                    </ul>""",
                    course_id=ai_course.id,
                    doc_link="https://docs.google.com/document/d/3"
                ),
                Module(
                    order=4,
                    title="Practical Applications of AI and ML in GIS",
                    content="""<h3>Applications</h3>
                    <ul>
                        <li>AI for Water Body Detection in Satellite Images</li>
                        <li>Route Optimization Using AI and GIS</li>
                        <li>Real-time Geospatial Data Processing</li>
                        <li>AI-Powered Urban Planning</li>
                    </ul>""",
                    course_id=ai_course.id,
                    doc_link="https://docs.google.com/document/d/4"
                ),
                Module(
                    order=5,
                    title="Final Assessment",
                    content="""<h3>Final Assessment Instructions</h3>
                    <p>You have completed all the modules! Now it's time to test your knowledge:</p>
                    <ul>
                        <li>The quiz consists of 10 multiple-choice questions</li>
                        <li>You need to score 80% or higher to pass</li>
                        <li>Upon passing, you can download your certificate</li>
                    </ul>""",
                    course_id=ai_course.id,
                    doc_link="https://docs.google.com/document/d/5"
                )
            ]
            
            for module in modules:
                db.session.add(module)
            
            db.session.commit()
            print("Successfully created all modules")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    restore_data() 