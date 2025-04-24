-- Direct fix for the progress.completion_date column
-- Execute this in a MySQL client if other automated methods fail

ALTER TABLE progress ADD COLUMN completion_date DATETIME NULL;

-- Check if the column was added successfully
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'railway' 
AND TABLE_NAME = 'progress' 
AND COLUMN_NAME = 'completion_date'; 