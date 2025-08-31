from fastapi import APIRouter, HTTPException
from models import Query, SearchResult
from database import get_ollama_embedding, get_collection  # use ollama embedding

router = APIRouter()

@router.post("/", response_model=list[SearchResult])
async def search_documents(query: Query):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Use Ollama embedding instead of SentenceTransformer
    query_embedding = get_ollama_embedding(query.question)

    collection = get_collection()  # ✅ call the function to get collection

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(query.top_k, 20),
        include=["metadatas", "documents", "distances"]
    )

    search_results = []
    for i, doc_id in enumerate(results["ids"][0]):
        similarity = max(0, 1 - results["distances"][0][i])  # cosine similarity
        if similarity >= query.threshold:
            metadata = results["metadatas"][0][i]
            search_results.append(SearchResult(
                id=doc_id,
                title=metadata.get("title", "Untitled"),
                content=results["documents"][0][i],
                similarity=round(similarity, 4),
                metadata=metadata
            ))

    return search_results
