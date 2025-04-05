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
                    content="""<h3>Final Assessment Questions</h3>
                    <p>Test your knowledge with these 10 multiple-choice questions. You need to score 80% or higher to pass.</p>
                    
                    <div class="quiz-questions">
                        <div class="question mb-4">
                            <h5>1. Which AI technique is most commonly used for satellite image classification in Web GIS?</h5>
                            <ul>
                                <li>A) Convolutional Neural Networks (CNN)</li>
                                <li>B) Recurrent Neural Networks (RNN)</li>
                                <li>C) Linear Regression</li>
                                <li>D) Decision Trees</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>2. What is the primary advantage of using machine learning for spatial analysis in Web GIS?</h5>
                            <ul>
                                <li>A) Reduced server costs</li>
                                <li>B) Automated pattern recognition in spatial data</li>
                                <li>C) Faster map loading times</li>
                                <li>D) Better user interface</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>3. Which deep learning architecture is best suited for temporal spatial data analysis?</h5>
                            <ul>
                                <li>A) Feedforward Neural Networks</li>
                                <li>B) Support Vector Machines</li>
                                <li>C) Long Short-Term Memory (LSTM)</li>
                                <li>D) Random Forests</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>4. What is the role of AI in automated map generalization?</h5>
                            <ul>
                                <li>A) To increase map file size</li>
                                <li>B) To simplify map features while preserving essential characteristics</li>
                                <li>C) To add more details to maps</li>
                                <li>D) To change map projections</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>5. Which of the following is NOT a common application of AI in Web GIS?</h5>
                            <ul>
                                <li>A) Traffic prediction</li>
                                <li>B) Land use classification</li>
                                <li>C) Manual data entry</li>
                                <li>D) Change detection</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>6. What type of neural network is most effective for object detection in aerial imagery?</h5>
                            <ul>
                                <li>A) YOLO (You Only Look Once)</li>
                                <li>B) Simple Perceptron</li>
                                <li>C) Hopfield Network</li>
                                <li>D) Boltzmann Machine</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>7. Which technology is essential for real-time spatial AI analysis in web applications?</h5>
                            <ul>
                                <li>A) WebGL</li>
                                <li>B) Flash</li>
                                <li>C) Java Applets</li>
                                <li>D) Silverlight</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>8. What is the primary purpose of using AI for feature extraction in GIS?</h5>
                            <ul>
                                <li>A) To slow down processing</li>
                                <li>B) To automatically identify and classify map elements</li>
                                <li>C) To increase data storage requirements</li>
                                <li>D) To manually verify data</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>9. Which of the following is a key benefit of implementing AI-powered predictive analytics in Web GIS?</h5>
                            <ul>
                                <li>A) Increased data entry requirements</li>
                                <li>B) Manual processing of spatial patterns</li>
                                <li>C) Proactive decision-making based on spatial trends</li>
                                <li>D) Reduced accuracy in spatial analysis</li>
                            </ul>
                        </div>

                        <div class="question mb-4">
                            <h5>10. What role does machine learning play in web-based spatial clustering?</h5>
                            <ul>
                                <li>A) It requires manual intervention</li>
                                <li>B) It automatically identifies spatial patterns and groups</li>
                                <li>C) It slows down the clustering process</li>
                                <li>D) It increases data redundancy</li>
                            </ul>
                        </div>
                    </div>

                    <div class="alert alert-info mt-4">
                        <p><strong>Note:</strong> To take the quiz and get your certificate, click the "Take Quiz" button below.</p>
                    </div>""",
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