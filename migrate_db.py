import mysql.connector
from datetime import datetime
import json
import os

# Source database configuration
SOURCE_DB = {
    'host': 'yamanote.proxy.rlwy.net',
    'port': 17657,
    'user': 'root',
    'password': 'RlnjaHZoFYoaoxssxFHKtLFQlvwqninP',
    'database': 'railway'
}

# Target database configuration (your new Railway instance)
TARGET_DB = {
    'host': 'yamanote.proxy.rlwy.net',
    'port': 17657,
    'user': 'root',
    'password': 'RlnjaHZoFYoaoxssxFHKtLFQlvwqninP',
    'database': 'railway'
}

def get_connection(config):
    return mysql.connector.connect(**config)

def create_tables(conn):
    cursor = conn.cursor()
    
    # Create user table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(128),
        is_admin BOOLEAN DEFAULT FALSE,
        is_paid BOOLEAN DEFAULT FALSE
    )
    """)
    
    # Create course table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS course (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create module table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS module (
        id INT AUTO_INCREMENT PRIMARY KEY,
        course_id INT,
        title VARCHAR(100) NOT NULL,
        content TEXT,
        doc_link VARCHAR(255),
        FOREIGN KEY (course_id) REFERENCES course(id)
    )
    """)
    
    # Create quiz_question table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_question (
        id INT AUTO_INCREMENT PRIMARY KEY,
        module_id INT,
        question TEXT NOT NULL,
        option1 VARCHAR(255) NOT NULL,
        option2 VARCHAR(255) NOT NULL,
        option3 VARCHAR(255) NOT NULL,
        correct_option INT NOT NULL,
        FOREIGN KEY (module_id) REFERENCES module(id)
    )
    """)
    
    # Create quiz_result table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_result (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        module_id INT,
        score INT NOT NULL,
        passed BOOLEAN DEFAULT FALSE,
        attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (module_id) REFERENCES module(id)
    )
    """)
    
    # Create progress table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        module_id INT,
        completed BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (module_id) REFERENCES module(id)
    )
    """)
    
    # Create certificate table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificate (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        course_id INT,
        issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        certificate_path VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (course_id) REFERENCES course(id)
    )
    """)
    
    # Create enrollment table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        course_id INT,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (course_id) REFERENCES course(id)
    )
    """)
    
    conn.commit()
    cursor.close()

def backup_table(conn, table_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    cursor.close()
    return rows

def restore_table(conn, table_name, data):
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = [column[0] for column in cursor.fetchall()]
    
    # Prepare insert statement
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    # Insert data
    for row in data:
        values = [row.get(col) for col in columns]
        cursor.execute(insert_query, values)
    
    conn.commit()
    cursor.close()

def migrate_database():
    try:
        # Create backup directory if it doesn't exist
        backup_dir = 'database_backup'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
        
        # Connect to source database
        print("Connecting to source database...")
        source_conn = get_connection(SOURCE_DB)
        
        # Connect to target database
        print("Connecting to target database...")
        target_conn = get_connection(TARGET_DB)
        
        # Create tables in target database
        print("Creating tables in target database...")
        create_tables(target_conn)
        
        # List of tables to migrate (in correct order to maintain foreign key constraints)
        tables = [
            'user',
            'course',
            'module',
            'quiz_question',
            'quiz_result',
            'progress',
            'certificate',
            'enrollment'
        ]
        
        # Backup data from source database
        print("Backing up data from source database...")
        backup_data = {}
        for table in tables:
            try:
                print(f"Backing up {table} table...")
                backup_data[table] = backup_table(source_conn, table)
            except mysql.connector.errors.ProgrammingError as e:
                if "doesn't exist" in str(e):
                    print(f"Table {table} doesn't exist in source database, skipping...")
                    backup_data[table] = []
                else:
                    raise
        
        # Save backup to file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, default=str)
        
        # Restore data to target database
        print("Restoring data to target database...")
        for table in tables:
            if backup_data[table]:  # Only restore if there's data
                print(f"Restoring {table} table...")
                restore_table(target_conn, table, backup_data[table])
            else:
                print(f"Skipping {table} table (no data to restore)")
        
        print("Migration completed successfully!")
        print(f"Backup saved to: {backup_file}")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()

if __name__ == '__main__':
    migrate_database() 