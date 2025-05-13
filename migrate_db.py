import mysql.connector
from datetime import datetime
import json
import os

# Source database configuration (old Railway instance)
SOURCE_DB = {
    'host': 'gondola.proxy.rlwy.net',
    'port': 41520,
    'user': 'root',
    'password': 'hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM',
    'database': 'railway'
}

# Target database configuration (new Railway instance)
TARGET_DB = {
    'host': 'yamanote.proxy.rlwy.net',
    'port': 17657,
    'user': 'root',
    'password': 'RlnjaHZoFYoaoxssxFHKtLFQlvwqninP',
    'database': 'railway'
}

def get_connection(config):
    return mysql.connector.connect(**config)

def inspect_table(source_conn, table_name):
    cursor = source_conn.cursor(dictionary=True)
    try:
        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        structure = cursor.fetchall()
        print(f"\nStructure of {table_name} table:")
        for col in structure:
            print(f"Column: {col['Field']}, Type: {col['Type']}, Null: {col['Null']}, Default: {col['Default']}")
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample_data = cursor.fetchall()
        print(f"\nSample data from {table_name} table:")
        for row in sample_data:
            print(row)
            
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cursor.fetchone()['count']
        print(f"\nTotal rows in {table_name}: {count}")
        
        return structure, sample_data, count
    finally:
        cursor.close()

def get_table_structure(source_conn, table_name):
    cursor = source_conn.cursor(dictionary=True)
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        return columns
    finally:
        cursor.close()

def create_table_from_structure(target_conn, table_name, columns):
    cursor = target_conn.cursor()
    try:
        # Special handling for quiz_question table
        if table_name == 'quiz_question':
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS quiz_question (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    correct_answer VARCHAR(255) NOT NULL,
                    module_id INT,
                    FOREIGN KEY (module_id) REFERENCES module(id)
                )
            """
        else:
            # Build CREATE TABLE statement for other tables
            column_defs = []
            for col in columns:
                col_def = f"`{col['Field']}` {col['Type']}"
                if col['Null'] == 'NO':
                    col_def += " NOT NULL"
                if col['Key'] == 'PRI':
                    col_def += " PRIMARY KEY"
                if col['Extra'] == 'auto_increment':
                    col_def += " AUTO_INCREMENT"
                if col['Default'] is not None:
                    col_def += f" DEFAULT {col['Default']}"
                column_defs.append(col_def)
            
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        
        cursor.execute(create_table_sql)
        target_conn.commit()
        print(f"Created table {table_name} with matching structure")
    except Exception as e:
        print(f"Error creating table {table_name}: {str(e)}")
        raise
    finally:
        cursor.close()

def get_target_columns(target_conn, table_name):
    cursor = target_conn.cursor(dictionary=True)
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        return {col['Field']: col for col in columns}
    finally:
        cursor.close()

def get_default_value(col_type, col_name):
    col_type = col_type.lower()
    if 'varchar' in col_type or 'text' in col_type or 'char' in col_type:
        return f"Default {col_name}"
    elif 'int' in col_type:
        return 0
    elif 'float' in col_type or 'double' in col_type or 'decimal' in col_type:
        return 0.0
    elif 'datetime' in col_type or 'timestamp' in col_type:
        return datetime.now()
    elif 'date' in col_type:
        return datetime.now().date()
    elif 'time' in col_type:
        return datetime.now().time()
    elif 'boolean' in col_type or 'tinyint(1)' in col_type:
        return False
    else:
        return None

def is_row_valid(row, target_columns, common_columns):
    for col in common_columns:
        if target_columns[col]['Null'] == 'NO' and row[col] is None:
            return False
    return True

def migrate_table(source_conn, target_conn, table_name):
    source_cursor = source_conn.cursor(dictionary=True)
    target_cursor = target_conn.cursor()
    
    try:
        # For quiz_question table, first inspect its content
        if table_name == 'quiz_question':
            print("\nInspecting quiz_question table...")
            structure, sample_data, count = inspect_table(source_conn, table_name)
            
        # Get data from source table
        source_cursor.execute(f"SELECT * FROM {table_name}")
        rows = source_cursor.fetchall()
        
        if not rows:
            print(f"No data in {table_name} table")
            return
        
        # Special handling for quiz_question table
        if table_name == 'quiz_question':
            # Map source columns to target columns
            column_mapping = {
                'id': 'id',
                'question_text': 'question',
                'correct_answer': 'correct_answer',
                'module_id': 'module_id'
            }
            # Use mapped columns
            common_columns = [col for col in source_columns if col in column_mapping]
            target_column_names = [column_mapping[col] for col in common_columns]
        else:
            # For other tables, use direct mapping
            source_columns = list(rows[0].keys())
            target_columns = get_target_columns(target_conn, table_name)
            common_columns = [col for col in source_columns if col in target_columns]
            target_column_names = common_columns
        
        if not common_columns:
            print(f"No common columns found between source and target for {table_name}")
            return
        
        # Prepare column strings with backticks
        columns_str = ', '.join([f"`{col}`" for col in target_column_names])
        placeholders = ', '.join(['%s'] * len(common_columns))
        
        # Disable foreign key checks
        target_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear target table
        target_cursor.execute(f"TRUNCATE TABLE {table_name}")
        
        # Insert data into target table
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        valid_rows = 0
        skipped_rows = 0
        
        for row in rows:
            values = []
            for col in common_columns:
                value = row[col]
                values.append(value)
            
            try:
                target_cursor.execute(insert_query, values)
                valid_rows += 1
            except Exception as e:
                print(f"Error inserting row: {str(e)}")
                print(f"Problematic row data: {row}")
                skipped_rows += 1
        
        # Re-enable foreign key checks
        target_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        target_conn.commit()
        print(f"Successfully migrated {valid_rows} rows from {table_name} table")
        if skipped_rows > 0:
            print(f"Skipped {skipped_rows} rows due to errors")
        print(f"Migrated columns: {', '.join(target_column_names)}")
        
    except Exception as e:
        print(f"Error migrating {table_name} table: {str(e)}")
        # Ensure foreign key checks are re-enabled even if there's an error
        target_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        target_conn.commit()
        raise
    finally:
        source_cursor.close()
        target_cursor.close()

def migrate_database():
    try:
        # Connect to databases
        print("Connecting to source database...")
        source_conn = get_connection(SOURCE_DB)
        
        print("Connecting to target database...")
        target_conn = get_connection(TARGET_DB)
        
        # List of tables to migrate
        tables = [
            'alembic_version',
            'user',
            'course',
            'module',
            'quiz_question',
            'quiz_result',
            'progress',
            'enrollment',
            'user_completed_modules'
        ]
        
        # First get structure and create tables
        for table in tables:
            print(f"\nGetting structure for {table} table...")
            columns = get_table_structure(source_conn, table)
            create_table_from_structure(target_conn, table, columns)
        
        # Then migrate data
        for table in tables:
            print(f"\nMigrating {table} table...")
            migrate_table(source_conn, target_conn, table)
        
        print("\nMigration completed successfully!")
        
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