import os
import uuid
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import CHROMA_PERSIST_DIRECTORY

# Load a SentenceTransformer model for embedding generation.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Ensure the persistence directory exists.
os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)

# Initialize a Chroma client (using duckdb+parquet for persistence).
client = chromadb.Client(
    Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_PERSIST_DIRECTORY)
)

def get_or_create_collection(name: str):
    collections = client.list_collections()
    logger.info(f"Existing collections: {[col.name for col in collections]}")
    for col in collections:
        if col.name == name:
            logger.info(f"Loading existing collection: {name}")
            return client.get_collection(name=name)
    logger.info(f"Creating new collection: {name}")
    return client.create_collection(name=name)


collection = get_or_create_collection("peacy_memories")

def get_embedding(text: str) -> list:
    return embedding_model.encode(text, convert_to_tensor=False, show_progress_bar=False)

def add_memory(text: str, metadata: dict = None):
    embedding = get_embedding(text)
    doc_id = metadata.get("id", str(uuid.uuid4()))
    collection.add(
        documents=[text],
        metadatas=[metadata or {}],
        embeddings=[embedding],
        ids=[doc_id]
    )

def retrieve_memory(query: str, n_results: int = 3) -> str:
    query_embedding = get_embedding(query)
    try:
        count = collection.count()
    except Exception:
        count = 0
    if count == 0:
        return ""
    # Request no more than available documents.
    k = min(n_results, count)
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        if not results["documents"] or not results["documents"][0]:
            return ""
        return "\n".join(results["documents"][0])
    except Exception as e:
        print("Error during memory retrieval:", e)
        return ""

def seed_memory():
    seed_prompt = (
        "Peacy is a compassionate AI mediator built for group chats. "
        "It fosters peaceful communication and helps build genuine relationships through Nonviolent Communication (NVC) principles. "
        "Peacy listens, remembers past interactions, and evolves over time by learning from conversations. "
        "Its mission is to ensure every chat is supportive, empathetic, and conflict‐free."
    )
    try:
        count = collection.count()
    except Exception:
        count = 0
    if count == 0:
        add_memory(seed_prompt, metadata={"type": "seed"})
        print("Seed memory added (collection was empty).")
    else:
        try:
            existing = collection.query(
                query_embeddings=[get_embedding("compassionate AI mediator")],
                n_results=1
            )
        except Exception:
            add_memory(seed_prompt, metadata={"type": "seed"})
            print("Seed memory added (query failed: no index present).")
        else:
            if not existing["documents"][0]:
                add_memory(seed_prompt, metadata={"type": "seed"})
                print("Seed memory added (seed not found in collection).")
            else:
                print("Seed memory already exists.")

if __name__ == "__main__":
    seed_memory()
