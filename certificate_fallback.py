"""
This file provides simpler alternative certificate routes that don't rely on quiz_result data.
It can be used as a fallback if the database isn't fully migrated.
"""

from flask import render_template, redirect, url_for, flash
from app import app, current_user, login_required
from datetime import datetime

@app.route('/certificate_simple')
@login_required
def certificate_simple():
    try:
        if not current_user.is_paid:
            flash('Please complete your payment to access the certificate.', 'warning')
            return redirect(url_for('dashboard'))
            
        # Using hardcoded values instead of relying on quiz_result data
        return render_template('certificate_simple.html', 
                            user=current_user,
                            completion_date=datetime.utcnow())
    except Exception as e:
        # Provide a very basic view in case of database issues
        error_message = str(e)
        return render_template('error.html', 
                            message="Certificate error",
                            error=error_message,
                            user=current_user) 