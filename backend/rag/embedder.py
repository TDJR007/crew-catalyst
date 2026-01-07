from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
import os

load_dotenv()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-xs")

def get_embedding_function():
    print(f"🧠 Using {EMBEDDING_MODEL} for embeddings...")
    return SentenceTransformerEmbeddingFunction(EMBEDDING_MODEL)
