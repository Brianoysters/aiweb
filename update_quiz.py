from app import app, db, Module
from datetime import datetime

def update_quiz_content():
    try:
        with app.app_context():
            # Get the quiz module (module 5)
            quiz_module = Module.query.filter_by(order=5).first()
            if not quiz_module:
                print("Quiz module not found")
                return
            
            # Update the quiz content
            quiz_module.content = """<div class="container">
                <h3 class="mb-4">Final Assessment</h3>
                <p class="mb-4">Test your knowledge with these 10 multiple-choice questions. You need to score 80% or higher to pass.</p>
                
                <form action="/submit_quiz" method="post">
                    <div class="quiz-questions">
                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question1">
                            <h5 id="question1">1. Which AI technique is most commonly used for satellite image classification in Web GIS?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q1" id="q1a" value="a" required>
                                <label class="form-check-label" for="q1a">Convolutional Neural Networks (CNN)</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q1" id="q1b" value="b">
                                <label class="form-check-label" for="q1b">Recurrent Neural Networks (RNN)</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q1" id="q1c" value="c">
                                <label class="form-check-label" for="q1c">Linear Regression</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q1" id="q1d" value="d">
                                <label class="form-check-label" for="q1d">Decision Trees</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question2">
                            <h5 id="question2">2. What is the primary advantage of using machine learning for spatial analysis in Web GIS?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q2" id="q2a" value="a" required>
                                <label class="form-check-label" for="q2a">Reduced server costs</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q2" id="q2b" value="b">
                                <label class="form-check-label" for="q2b">Automated pattern recognition in spatial data</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q2" id="q2c" value="c">
                                <label class="form-check-label" for="q2c">Faster map loading times</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q2" id="q2d" value="d">
                                <label class="form-check-label" for="q2d">Better user interface</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question3">
                            <h5 id="question3">3. Which deep learning architecture is best suited for temporal spatial data analysis?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q3" id="q3a" value="a" required>
                                <label class="form-check-label" for="q3a">Feedforward Neural Networks</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q3" id="q3b" value="b">
                                <label class="form-check-label" for="q3b">Support Vector Machines</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q3" id="q3c" value="c">
                                <label class="form-check-label" for="q3c">Long Short-Term Memory (LSTM)</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q3" id="q3d" value="d">
                                <label class="form-check-label" for="q3d">Random Forests</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question4">
                            <h5 id="question4">4. What is the role of AI in automated map generalization?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q4" id="q4a" value="a" required>
                                <label class="form-check-label" for="q4a">To increase map file size</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q4" id="q4b" value="b">
                                <label class="form-check-label" for="q4b">To simplify map features while preserving essential characteristics</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q4" id="q4c" value="c">
                                <label class="form-check-label" for="q4c">To add more details to maps</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q4" id="q4d" value="d">
                                <label class="form-check-label" for="q4d">To change map projections</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question5">
                            <h5 id="question5">5. Which of the following is NOT a common application of AI in Web GIS?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q5" id="q5a" value="a" required>
                                <label class="form-check-label" for="q5a">Traffic prediction</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q5" id="q5b" value="b">
                                <label class="form-check-label" for="q5b">Land use classification</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q5" id="q5c" value="c">
                                <label class="form-check-label" for="q5c">Manual data entry</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q5" id="q5d" value="d">
                                <label class="form-check-label" for="q5d">Change detection</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question6">
                            <h5 id="question6">6. What type of neural network is most effective for object detection in aerial imagery?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q6" id="q6a" value="a" required>
                                <label class="form-check-label" for="q6a">YOLO (You Only Look Once)</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q6" id="q6b" value="b">
                                <label class="form-check-label" for="q6b">Simple Perceptron</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q6" id="q6c" value="c">
                                <label class="form-check-label" for="q6c">Hopfield Network</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q6" id="q6d" value="d">
                                <label class="form-check-label" for="q6d">Boltzmann Machine</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question7">
                            <h5 id="question7">7. Which technology is essential for real-time spatial AI analysis in web applications?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q7" id="q7a" value="a" required>
                                <label class="form-check-label" for="q7a">WebGL</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q7" id="q7b" value="b">
                                <label class="form-check-label" for="q7b">Flash</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q7" id="q7c" value="c">
                                <label class="form-check-label" for="q7c">Java Applets</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q7" id="q7d" value="d">
                                <label class="form-check-label" for="q7d">Silverlight</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question8">
                            <h5 id="question8">8. What is the primary purpose of using AI for feature extraction in GIS?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q8" id="q8a" value="a" required>
                                <label class="form-check-label" for="q8a">To slow down processing</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q8" id="q8b" value="b">
                                <label class="form-check-label" for="q8b">To automatically identify and classify map elements</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q8" id="q8c" value="c">
                                <label class="form-check-label" for="q8c">To increase data storage requirements</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q8" id="q8d" value="d">
                                <label class="form-check-label" for="q8d">To manually verify data</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question9">
                            <h5 id="question9">9. Which of the following is a key benefit of implementing AI-powered predictive analytics in Web GIS?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q9" id="q9a" value="a" required>
                                <label class="form-check-label" for="q9a">Increased data entry requirements</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q9" id="q9b" value="b">
                                <label class="form-check-label" for="q9b">Manual processing of spatial patterns</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q9" id="q9c" value="c">
                                <label class="form-check-label" for="q9c">Proactive decision-making based on spatial trends</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q9" id="q9d" value="d">
                                <label class="form-check-label" for="q9d">Reduced accuracy in spatial analysis</label>
                            </div>
                        </div>

                        <div class="question mb-4 p-3 border rounded bg-light" role="group" aria-labelledby="question10">
                            <h5 id="question10">10. What role does machine learning play in web-based spatial clustering?</h5>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q10" id="q10a" value="a" required>
                                <label class="form-check-label" for="q10a">It requires manual intervention</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q10" id="q10b" value="b">
                                <label class="form-check-label" for="q10b">It automatically identifies spatial patterns and groups</label>
                            </div>
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" name="q10" id="q10c" value="c">
                                <label class="form-check-label" for="q10c">It slows down the clustering process</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q10" id="q10d" value="d">
                                <label class="form-check-label" for="q10d">It increases data redundancy</label>
                            </div>
                        </div>
                    </div>
                    <div class="text-center mt-4">
                        <button type="submit" class="btn btn-primary">Submit Quiz</button>
                    </div>
                </form>
            </div>"""
            
            db.session.commit()
            print("Quiz content updated successfully")
            
    except Exception as e:
        print(f"Error updating quiz content: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    update_quiz_content()
