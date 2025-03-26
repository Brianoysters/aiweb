# AI in Web GIS Learning Management System

A comprehensive learning platform for AI in Web GIS and mapping with project examples. The platform features user authentication, progressive module unlocking, quiz assessment, and certificate generation.

## Features

- User authentication (signup/login)
- Progressive module unlocking
- Interactive course content
- Final assessment quiz with 80% pass mark
- Automatic PDF certificate generation
- Modern, responsive UI

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css      # Custom CSS styles
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── index.html    # Landing page
│   ├── signup.html   # User registration
│   ├── login.html    # User login
│   ├── dashboard.html # User dashboard
│   ├── module.html   # Module view
│   ├── quiz.html     # Final assessment
│   └── certificate.html # Certificate view
└── certificates/     # Generated PDF certificates
```

## Database

The application uses SQLite with SQLAlchemy ORM. The database includes the following models:
- User
- Module
- Progress
- QuizResult

## Security

- Passwords are hashed using Werkzeug's security functions
- Flask-Login handles user session management
- CSRF protection with Flask-WTF
