#!/bin/bash

# Set environment variable to run in production mode
export FLASK_ENV=production

# Run the database migration script
echo "Running pre-deployment database migrations..."
python run_migration.py

# Run the progress table fix script
echo "Fixing progress table..."
python fix_progress_table.py

# Run the quiz result table fix script
echo "Fixing quiz_result table..."
python fix_quiz_result_table.py

echo "Pre-deployment tasks completed successfully" 