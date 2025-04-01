import psycopg2
from config import config

def init_db():
    """
    Initialize the database by creating tables for messages, users, and conversation summaries.
    Also, ensure that any new columns (like 'emotional_state') are added if they don't exist.
    """
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    
    # Create messages table.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id TEXT,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create users table if it does not exist.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            location TEXT,
            profile_info TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if the 'emotional_state' column exists; if not, add it.
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'emotional_state'
    """)
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE users ADD COLUMN emotional_state TEXT")
    
    # Create conversation summaries table.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            chat_id BIGINT PRIMARY KEY,
            summary TEXT
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def log_message(chat_id, user_id, message_text):
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (chat_id, user_id, message_text) VALUES (%s, %s, %s)",
        (chat_id, user_id, message_text)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_profile(user_id, username=None, display_name=None, location=None, profile_info=None, emotional_state=None):
    user_id = str(user_id)
    fields = []
    values = []
    if username is not None:
        fields.append("username = %s")
        values.append(username)
    if display_name is not None:
        fields.append("display_name = %s")
        values.append(display_name)
    if location is not None:
        fields.append("location = %s")
        values.append(location)
    if profile_info is not None:
        fields.append("profile_info = %s")
        values.append(profile_info)
    if emotional_state is not None:
        fields.append("emotional_state = %s")
        values.append(emotional_state)
    if not fields:
        return
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(user_id)
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = %s"
    cur.execute(query, tuple(values))
    conn.commit()
    cur.close()
    conn.close()

def get_user_profile(user_id):
    """
    Returns (username, profile_info)
    """
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("SELECT username, profile_info FROM users WHERE user_id = %s", (str(user_id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_user(user_id):
    """
    Retrieve a user's profile (username, display_name, location, profile_info, emotional_state).
    """
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute(
        "SELECT username, display_name, location, profile_info, emotional_state FROM users WHERE user_id = %s",
        (str(user_id),)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def update_conversation_summary_in_db(chat_id, new_summary):
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversation_summaries (chat_id, summary)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET summary = EXCLUDED.summary
    """, (chat_id, new_summary))
    conn.commit()
    cur.close()
    conn.close()

def get_conversation_summary(chat_id):
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("SELECT summary FROM conversation_summaries WHERE chat_id = %s", (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else ""

def create_user(user_id, username, display_name="", location="", profile_info=""):
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, display_name, location, profile_info)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, username, display_name, location, profile_info))
    conn.commit()
    cur.close()
    conn.close()

def delete_user(user_id):
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s", (str(user_id),))
    conn.commit()
    cur.close()
    conn.close()
