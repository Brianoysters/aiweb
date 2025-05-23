-- Fix course table
ALTER TABLE course 
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN duration VARCHAR(50) NOT NULL DEFAULT '8 weeks',
ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'Online',
ADD COLUMN fee VARCHAR(50) NOT NULL DEFAULT 'KES 15,000',
ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Fix user table
ALTER TABLE user
ADD COLUMN is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN is_paid BOOLEAN DEFAULT FALSE,
ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Fix module table
ALTER TABLE module
ADD COLUMN date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN doc_link VARCHAR(500) NULL,
ADD COLUMN `order` INT NOT NULL DEFAULT 1;

-- Fix progress table
ALTER TABLE progress
ADD COLUMN completion_date DATETIME NULL;

-- Fix quiz_result table
ALTER TABLE quiz_result
ADD COLUMN completion_date DATETIME NULL,
ADD COLUMN next_attempt_available DATETIME NULL,
ADD COLUMN attempt_number INT NOT NULL DEFAULT 1;

-- Make first user admin and paid
UPDATE user SET is_admin = TRUE, is_paid = TRUE WHERE id = 1; 