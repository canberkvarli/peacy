import os
import shutil
import psycopg2
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_chroma():
    # Remove the Chroma persistence directory if it exists.
    if os.path.exists(config.CHROMA_PERSIST_DIRECTORY):
        shutil.rmtree(config.CHROMA_PERSIST_DIRECTORY)
        logger.info(f"Deleted Chroma persistence directory: {config.CHROMA_PERSIST_DIRECTORY}")
    else:
        logger.info("Chroma persistence directory not found; nothing to delete.")

def reset_postgres():
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    
    # Option 1: Drop tables (they will be re-created on next init)
    tables = ["messages", "users", "conversation_summaries"]
    for table in tables:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            logger.info(f"Dropped table: {table}")
        except Exception as e:
            logger.exception(f"Error dropping table {table}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    logger.info("Resetting storage...")
    reset_chroma()
    reset_postgres()
    logger.info("Storage reset complete.")
