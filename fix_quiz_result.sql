-- SQL script to fix the quiz_result table
-- Execute this directly on your deployed database

-- Check if the quiz_result table exists
-- If it doesn't, this will show an error but won't stop execution

-- Add completion_date column if it doesn't exist
ALTER TABLE quiz_result ADD COLUMN IF NOT EXISTS completion_date DATETIME NULL;

-- Add next_attempt_available column if it doesn't exist
ALTER TABLE quiz_result ADD COLUMN IF NOT EXISTS next_attempt_available DATETIME NULL;

-- Add attempt_number column if it doesn't exist
ALTER TABLE quiz_result ADD COLUMN IF NOT EXISTS attempt_number INT NOT NULL DEFAULT 1;

-- Verify the columns were added successfully
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'railway' 
AND TABLE_NAME = 'quiz_result'; 