import psycopg2
from config import PG_CONNECTION_STRING

def init_db():
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    # Create a table for messages.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id TEXT,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Optionally, create a users table to track user profiles.
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
