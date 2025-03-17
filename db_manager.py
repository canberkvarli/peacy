import psycopg2
from config import PG_CONNECTION_STRING

def init_db():
    """
    Initialize the database by creating tables for messages, users, and conversation summaries.
    """
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    # Table for storing individual messages.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id TEXT,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Table for storing user profiles.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            profile_info TEXT
        )
    """)
    # Table for storing conversation summaries for each chat.
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
    """
    Insert an individual message into the messages table.
    """
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
    """
    Insert or update a user's profile in the users table.
    """
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, profile_info)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET username = EXCLUDED.username, profile_info = EXCLUDED.profile_info
    """, (str(user_id), username, profile_info))
    conn.commit()
    cur.close()
    conn.close()

def get_user_profile(user_id):
    """
    Retrieve a user's profile (username and profile_info).
    """
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("SELECT username, profile_info FROM users WHERE user_id = %s", (str(user_id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_conversation_summary(chat_id):
    """
    Retrieve the current conversation summary for a given chat.
    Returns an empty string if no summary exists.
    """
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("SELECT summary FROM conversation_summaries WHERE chat_id = %s", (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else ""

def update_conversation_summary_in_db(chat_id, new_summary):
    """
    Update the conversation summary for a given chat.
    If no summary exists, insert a new row.
    """
    conn = psycopg2.connect(PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversation_summaries (chat_id, summary)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE
        SET summary = EXCLUDED.summary
    """, (chat_id, new_summary))
    conn.commit()
    cur.close()
    conn.close()
