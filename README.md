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

## Module Details

Each module contains comprehensive learning materials and practical exercises. For detailed information about each module, please refer to the following documentation:

- [Module 1: Introduction to AI in Web GIS](https://docs.google.com/document/d/1qajlv9m0qQ6mLHen5IqfnS-KY75TIc8x9NbKLwAzO0s/edit?usp=sharing)
- [Module 2: Advanced AI Applications in GIS](https://docs.google.com/document/d/1XKCEm18sHRooGkCC90IhcQvdWGCNGdKK2px4iOHCn9Q/edit?usp=sharing)
- [Module 3: Machine Learning for Spatial Analysis](https://docs.google.com/document/d/1u3mq0dvNmsIhZOKk4yLJWpvlbLT2n6L4VkoweE1rWWQ/edit?usp=sharing)
- [Module 4: Deep Learning in Geospatial Applications](https://docs.google.com/document/d/1qUcU2GUbgxqI7QCGhgX6xKCL36cBqLSreUoaySGm0Qc/edit?usp=sharing)

# SUBOMAP AFRICA ACADEMY

Learning Management System for SUBOMAP AFRICA ACADEMY.

## Deployment Instructions

### Railway MySQL Database

1. Create a MySQL database on Railway.
2. Note the database connection string.
3. Use the connection string in your `.env` file or directly in the config.

### Render Web Service

1. Create a new Web Service on Render.
2. Connect to your GitHub repository.
3. Use the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`
4. Add the environment variables from the `.env.example` file.
5. Add the Railway MySQL database URL to the environment variables.

## Database Migration

The `start.sh` script will automatically run the database migration script before starting the application. The migration script:

1. Checks for existing tables
2. Adds missing columns to tables
3. Sets default values for required columns
4. Makes the first user an admin

## Local Development

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install requirements: `pip install -r requirements.txt`
5. Create a `.env` file based on `.env.example`.
6. Run the migration script: `python run_migration.py`
7. Start the application: `flask run`
