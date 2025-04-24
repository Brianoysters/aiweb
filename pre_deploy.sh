#!/bin/bash

# Set environment variable to run in production mode
export FLASK_ENV=production

# Run the database migration script
echo "Running pre-deployment database migrations..."
python run_migration.py

echo "Pre-deployment tasks completed successfully" 