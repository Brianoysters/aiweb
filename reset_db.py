from app import app, db, User, Course, Module
from werkzeug.security import generate_password_hash

def reset_database():
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("Dropped all tables")

            # Create all tables with new schema
            db.create_all()
            print("Created all tables with new schema")

            # Create admin user
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

            # Create initial course
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
            print("Created initial course")

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
                    course_id=course.id
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
                    course_id=course.id
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
                    course_id=course.id
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
                    course_id=course.id
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
                    course_id=course.id
                )
            ]
            
            for module in modules:
                db.session.add(module)
            db.session.commit()
            print("Created all modules")

            print("Database reset and initialization completed successfully")

        except Exception as e:
            print(f"Error during database reset: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database()
