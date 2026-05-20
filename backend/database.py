import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configure MySQL Connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Ravi1234",
    "database": "CodeSphereDB"
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn, conn.cursor(dictionary=True)

# 1. Creating a user on db
def create_user(full_name, username, email, password):
    """Creates a new user with a hashed password"""
    conn, cursor = get_db_connection()
    
    try:
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return {"message": "Username already taken!"}, 400

        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"message": "Email already registered!"}, 400

        # Insert new user
        hashed_password = generate_password_hash(password)
        query = "INSERT INTO users (full_name, username, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (full_name, username, email, hashed_password))
        conn.commit()

        # Log activity
        log_user_activity(username, "Account Created")
        return {"message": "Signup successful!"}, 201

    finally:
        cursor.close()
        conn.close()

# 2. Getting user info from db
def get_user(username):
    """Fetches a user by username"""
    conn, cursor = get_db_connection()
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone() # Returns a dict or None
    finally:
        cursor.close()
        conn.close()

# 3. Password verification
def verify_password(stored_password, provided_password):
    """Checks if the provided password matches the stored hashed password"""
    return check_password_hash(stored_password, provided_password)

# 4. Storing activities (Max 10 records)
def log_user_activity(username, action):
    """Logs user activity with a maximum of 10 records per user"""
    conn, cursor = get_db_connection()
    try:
        # Insert activity
        query = "INSERT INTO user_activities (username, action, timestamp) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, action, datetime.utcnow()))
        conn.commit()

        # Count total activities
        cursor.execute("SELECT COUNT(*) as total FROM user_activities WHERE username = %s", (username,))
        total_activities = cursor.fetchone()['total']

        # If exceeds 10, delete the oldest
        if total_activities > 10:
            # Find oldest ID
            cursor.execute("SELECT id FROM user_activities WHERE username = %s ORDER BY timestamp ASC LIMIT 1", (username,))
            oldest_id = cursor.fetchone()['id']
            
            # Delete oldest
            cursor.execute("DELETE FROM user_activities WHERE id = %s", (oldest_id,))
            conn.commit()
    finally:
        cursor.close()
        conn.close()

# 5. Get recent activities
def get_recent_activities(username, limit=5):
    """Fetch the latest user activities (default: last 5)"""
    conn, cursor = get_db_connection()
    try:
        query = "SELECT * FROM user_activities WHERE username = %s ORDER BY timestamp DESC LIMIT %s"
        cursor.execute(query, (username, limit))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

# 6. Save code on db history (Max 10 records)
def save_code(username, code, language):
    """Saves user code with a maximum limit of 10 records per user"""
    print(f"Saving {language} code for {username}")  
    conn, cursor = get_db_connection()
    
    try:
        # Count total codes
        cursor.execute("SELECT COUNT(*) as total FROM codes WHERE username = %s", (username,))
        total_codes = cursor.fetchone()['total']

        # If 10 or more, delete the oldest one
        if total_codes >= 10:
            cursor.execute("SELECT id FROM codes WHERE username = %s ORDER BY timestamp ASC LIMIT 1", (username,))
            oldest_code = cursor.fetchone()
            if oldest_code:
                print(f"Deleting oldest {language} code") 
                cursor.execute("DELETE FROM codes WHERE id = %s", (oldest_code['id'],))
                conn.commit()

        # Insert new code
        query = "INSERT INTO codes (username, code, language, timestamp) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (username, code, language, datetime.utcnow()))
        conn.commit()
        
        print(f"{language} code saved successfully with MySQL Row ID: {cursor.lastrowid}")  
    finally:
        cursor.close()
        conn.close()

# 7. Get recent codes 
def get_recent_codes(username, limit=10):
    """Fetch the latest 10 codes from the user"""
    conn, cursor = get_db_connection()
    try:
        query = "SELECT * FROM codes WHERE username = %s ORDER BY timestamp DESC LIMIT %s"
        cursor.execute(query, (username, limit))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
print("all set")