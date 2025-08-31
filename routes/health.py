from fastapi import APIRouter
from models import HealthResponse
from database import get_collection, get_ollama_embedding
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    try:
        collection = get_collection()
        doc_count = collection.count() if collection else 0
        
        # Test Ollama embedding
        test_embedding = get_ollama_embedding("test")
        ollama_working = len(test_embedding) > 0
        
        return HealthResponse(
            status="healthy" if ollama_working else "degraded",
            timestamp=datetime.now().isoformat(),
            models_loaded={
                "ollama_embeddings": ollama_working,
                "chromadb": collection is not None
            },
            document_count=doc_count
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            models_loaded={
                "ollama_embeddings": False,
                "chromadb": False
            },
            document_count=0
        )
