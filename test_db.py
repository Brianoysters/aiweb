import mysql.connector

try:
    connection = mysql.connector.connect(
        host="sql8.freesqldatabase.com",
        user="sql8769838",
        password="WHUW9lqTPD",
        database="sql8769838"
    )
    print("Successfully connected to the database!")
    connection.close()
except Exception as e:
    print(f"Error connecting to database: {e}")
