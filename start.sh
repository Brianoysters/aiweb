#!/bin/bash

# Set environment variable to run in production mode
export FLASK_ENV=production

# Run the database migration scripts first
echo "Running database migrations..."
python run_migration.py
python fix_progress_table.py

# Start the gunicorn server
echo "Starting gunicorn server..."
gunicorn app:app 