import os
import uuid
import logging
import asyncio
import nest_asyncio

import pytz
import psycopg2
import spacy

from rich.console import Console
from rich.theme import Theme
from rich.logging import RichHandler

from config import config

# LangChain & Chroma Imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

# Import DB helper functions from db_manager (instead of duplicating them here)
from db_manager import init_db, log_message, update_user_profile, get_user_profile, get_conversation_summary, update_conversation_summary_in_db
# Import start_scheduler from background_tasks for standalone execution
from background_tasks import start_scheduler

# ------------------------
# Global Objects and Setup
# ------------------------
# Define a custom theme for colorful logs.
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "debug": "blue",
    "critical": "bold red"
})

console = Console(theme=custom_theme)
handler = RichHandler(rich_tracebacks=True, markup=True, show_time=True, show_level=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Load spaCy model.
nlp = spacy.load("en_core_web_sm")

# Initialize the embedding model.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Ensure the persistence directory exists.
os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

# Initialize the Chroma vector store.
vectorstore = Chroma(
    collection_name="peacy_memories",
    embedding_function=embeddings,
    persist_directory=config.CHROMA_PERSIST_DIRECTORY,
)

# ------------------------
# Memory Management Functions
# ------------------------
def add_memory(text: str, metadata: dict = None):
    """Add a memory by storing a Document in the vector store and persisting the change."""
    doc = Document(page_content=text, metadata=metadata or {})
    vectorstore.add_documents([doc])
    logger.info("[bold blue]Memory added and persisted.[/bold blue]")

def retrieve_memory(query: str, n_results: int = 3) -> str:
    """Retrieve memories by performing a similarity search."""
    results = vectorstore.similarity_search(query, k=n_results)
    if not results:
        return ""
    return "\n".join([doc.page_content for doc in results])

def seed_memory_dynamic():
    """Seed the memory with a base prompt if none exists."""
    current_seed = retrieve_memory("system prompt", n_results=1)
    if not current_seed:
        dynamic_seed = (
            "Peacy is a friendly AI that learns continuously from every conversation, "
            "building personal connections and evolving with each interaction. "
            "Every message helps me understand you better, and I'm always growing from our shared experiences."
        )
        add_memory(dynamic_seed, metadata={"type": "seed"})
        print("[bold yellow]Dynamic seed memory added (collection was empty).[/bold yellow]")
    else:
        print("[bold green]Seed memory already exists.[/bold green]")

# ------------------------
# Main Routine (for standalone execution)
# ------------------------
if __name__ == '__main__':
    nest_asyncio.apply()

    async def main():
        await asyncio.to_thread(init_db)
        # Local import of start_scheduler to avoid circular dependency
        start_scheduler()
        # ... rest of your standalone logic

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown gracefully via KeyboardInterrupt.")
