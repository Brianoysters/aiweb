import pymysql
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_local_db():
    try:
        logger.info("Attempting to connect to local database...")
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="4832",
            database="aidb",
            connect_timeout=30
        )
        logger.info("Connected to local database successfully!")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to local database: {str(e)}")
        return None

def connect_to_railway_db():
    try:
        logger.info("Attempting to connect to Railway database...")
        # Get the DATABASE_URL from environment
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        logger.info(f"Using DATABASE_URL: {db_url}")
        
        # Extract connection details from the URL
        # Format: mysql+pymysql://root:password@gondola.proxy.rlwy.net:41520/railway
        if 'mysql+pymysql://' in db_url:
            db_url = db_url.replace('mysql+pymysql://', '')
        
        # Split into user:pass@host:port/dbname
        auth, connection = db_url.split('@')
        user, password = auth.split(':')
        host_port, database = connection.split('/')
        
        # Use the exact host, port, and credentials from the URL
        host = 'gondola.proxy.rlwy.net'
        port = '41520'
        user = 'root'
        password = 'hHqxqLIMvuNqKHjzAPNwVpgqJitEJhrM'  # Use the exact password
        database = 'railway'
        
        logger.info(f"Attempting to connect to: {host}:{port} as {user}")
        
        # Create connection with SSL disabled
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            connect_timeout=30,
            ssl={'ssl': {}}  # Disable SSL verification
        )
        logger.info("Connected to Railway database successfully!")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to Railway database: {str(e)}")
        logger.error(f"Connection details: host={host}, port={port}, user={user}, database={database}")
        return None

def migrate_modules(old_conn, new_conn):
    try:
        with old_conn.cursor() as old_cursor:
            old_cursor.execute("SELECT * FROM module")
            modules = old_cursor.fetchall()
            logger.info(f"Found {len(modules)} modules to migrate")
            
        with new_conn.cursor() as new_cursor:
            for module in modules:
                new_cursor.execute(
                    "INSERT INTO module (id, title, content, `order`, doc_link) VALUES (%s, %s, %s, %s, %s)",
                    (module[0], module[1], module[2], module[3], module[4])
                )
                logger.debug(f"Migrated module: {module[1]}")
        
        new_conn.commit()
        logger.info(f"Successfully migrated {len(modules)} modules")
        return True
    except Exception as e:
        logger.error(f"Error migrating modules: {str(e)}")
        return False

def migrate_users(old_conn, new_conn):
    try:
        with old_conn.cursor() as old_cursor:
            old_cursor.execute("SELECT * FROM user")
            users = old_cursor.fetchall()
            logger.info(f"Found {len(users)} users to migrate")
            
        with new_conn.cursor() as new_cursor:
            for user in users:
                new_cursor.execute(
                    "INSERT INTO user (id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
                    (user[0], user[1], user[2], user[3])
                )
                logger.debug(f"Migrated user: {user[1]}")
        
        new_conn.commit()
        logger.info(f"Successfully migrated {len(users)} users")
        return True
    except Exception as e:
        logger.error(f"Error migrating users: {str(e)}")
        return False

def migrate_progress(old_conn, new_conn):
    try:
        with old_conn.cursor() as old_cursor:
            old_cursor.execute("SELECT * FROM progress")
            progress_records = old_cursor.fetchall()
            logger.info(f"Found {len(progress_records)} progress records to migrate")
            
        with new_conn.cursor() as new_cursor:
            for progress in progress_records:
                new_cursor.execute(
                    "INSERT INTO progress (id, user_id, module_id, completed, completion_date) VALUES (%s, %s, %s, %s, %s)",
                    (progress[0], progress[1], progress[2], progress[3], progress[4])
                )
                logger.debug(f"Migrated progress record for user {progress[1]}, module {progress[2]}")
        
        new_conn.commit()
        logger.info(f"Successfully migrated {len(progress_records)} progress records")
        return True
    except Exception as e:
        logger.error(f"Error migrating progress records: {str(e)}")
        return False

def migrate_quiz_results(old_conn, new_conn):
    try:
        with old_conn.cursor() as old_cursor:
            old_cursor.execute("SELECT * FROM quiz_result")
            quiz_results = old_cursor.fetchall()
            logger.info(f"Found {len(quiz_results)} quiz results to migrate")
            
        with new_conn.cursor() as new_cursor:
            for result in quiz_results:
                new_cursor.execute(
                    "INSERT INTO quiz_result (id, user_id, score, passed, attempt_number, completion_date, next_attempt_available) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (result[0], result[1], result[2], result[3], result[4], result[5], result[6])
                )
                logger.debug(f"Migrated quiz result for user {result[1]}")
        
        new_conn.commit()
        logger.info(f"Successfully migrated {len(quiz_results)} quiz results")
        return True
    except Exception as e:
        logger.error(f"Error migrating quiz results: {str(e)}")
        return False

def main():
    logger.info("Starting data migration...")
    
    # Load environment variables
    load_dotenv()
    
    # Connect to both databases
    old_conn = connect_to_local_db()
    new_conn = connect_to_railway_db()
    
    if not old_conn or not new_conn:
        logger.error("Failed to connect to one or both databases")
        return
    
    try:
        # Migrate data in the correct order
        if not migrate_modules(old_conn, new_conn):
            return
        if not migrate_users(old_conn, new_conn):
            return
        if not migrate_progress(old_conn, new_conn):
            return
        if not migrate_quiz_results(old_conn, new_conn):
            return
        
        logger.info("Data migration completed successfully!")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
    finally:
        if old_conn:
            old_conn.close()
        if new_conn:
            new_conn.close()

if __name__ == "__main__":
    main() 