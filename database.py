import logging
import ollama
import chromadb
from pathlib import Path
from config import config

chroma_client = None
collection = None


def get_collection():
    global collection
    if collection is None:
        raise RuntimeError("ChromaDB collection is not initialized yet")
    return collection


def get_ollama_embedding(text: str, model: str = "nomic-embed-text:v1.5") -> list[float]:
    """Get embeddings from Ollama model"""
    try:
        if not text.strip():
            logging.error("❌ Empty text provided for embedding")
            return []
            
        response = ollama.embeddings(model=model, prompt=text)
        if response and "embedding" in response:
            embedding = response["embedding"]
            if embedding and len(embedding) > 0:
                logging.info(f"✅ Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logging.error("❌ Ollama returned empty embedding")
                return []
        else:
            logging.error("❌ Invalid response from Ollama embeddings API")
            return []
    except Exception as e:
        logging.error(f"❌ Ollama embedding failed: {e}")
        return []

async def startup_event():
    """Initialize ChromaDB on app startup"""
    global chroma_client, collection
    logging.info("🚀 Starting RAG Application with Ollama...")

    try:
        Path(config.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=config.CHROMADB_PATH)

        try:
            collection = chroma_client.get_collection("rag_documents")
            logging.info("✅ Loaded existing ChromaDB collection")
        except Exception:
            collection = chroma_client.create_collection(
                name="rag_documents", metadata={"hnsw:space": "cosine"}
            )
            logging.info("✅ Created new ChromaDB collection")

        if collection:
            logging.info(f"📂 Collection '{collection.name}' is ready")
        else:
            logging.error("❌ Collection initialization returned None!")

    except Exception as e:
        logging.error(f"❌ Failed to initialize ChromaDB: {e}")
        collection = None
