"""
This file provides a simpler alternative dashboard route that doesn't rely on progress data.
It can be used as a fallback if the database isn't fully migrated.
"""

from flask import render_template
from app import app, Course, current_user, login_required, User

@app.route('/dashboard_simple')
@login_required
def dashboard_simple():
    try:
        # Get all available courses
        courses = Course.query.filter_by(is_active=True).all()
        
        # Get all admin users for the admin section
        admins = User.query.filter_by(is_admin=True).all()
        
        # We don't use progress data in this simplified version
        enrolled_courses = []
        if hasattr(current_user, 'enrolled_courses'):
            try:
                enrolled_courses = [c.id for c in current_user.enrolled_courses]
            except Exception:
                pass
        
        return render_template('dashboard.html', 
                            courses=courses,
                            admins=admins,
                            enrolled_courses=enrolled_courses,
                            simple_mode=True)
        
    except Exception as e:
        # Provide a very basic view in case of database issues
        error_message = str(e)
        return render_template('error.html', 
                            message="Dashboard error",
                            error=error_message,
                            user=current_user) 