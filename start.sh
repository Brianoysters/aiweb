#!/bin/bash

# Set environment variable to run in production mode
export FLASK_ENV=production

# Run the database migration script first
echo "Running database migrations..."
python run_migration.py

# Start the gunicorn server
echo "Starting gunicorn server..."
gunicorn app:app 