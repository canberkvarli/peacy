import psycopg2
from config import PG_CONNECTION_STRING

def init_db():
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    # Create table for conversation messages.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id TEXT,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Create table for user profiles.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            profile_info TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def log_message(chat_id, user_id, message_text):
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (chat_id, user_id, message_text) VALUES (%s, %s, %s)",
        (chat_id, user_id, message_text)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_profile(user_id, username, profile_info=""):
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, profile_info)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET username = EXCLUDED.username, profile_info = EXCLUDED.profile_info
    """, (user_id, username, profile_info))
    conn.commit()
    cur.close()
    conn.close()

def get_user_profile(user_id):
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("SELECT username, profile_info FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result
