from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Document(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: str

class Query(BaseModel):
    question: str
    top_k: Optional[int] = 3
    threshold: Optional[float] = 0.3
    use_llm: Optional[bool] = True

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    metadata: Dict[str, Any]

class RAGResponse(BaseModel):
    query: str
    # retrieved_documents: List[SearchResult]
    generated_answer: str
    timestamp: str
    model_used: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    models_loaded: Dict[str, bool]
    document_count: int
