import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ENV = os.environ.get("ENV", "development")
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")
    PG_CONNECTION_STRING = os.environ.get("PG_CONNECTION_STRING")
    CHROMA_PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

config = Config()