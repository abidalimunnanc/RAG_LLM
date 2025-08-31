from fastapi import APIRouter, HTTPException
from models import Document, DocumentResponse
from database import get_collection, get_ollama_embedding
from datetime import datetime




router = APIRouter()


@router.post("/", response_model=dict)
async def add_document(document: Document):
    if not document.title.strip() or not document.content.strip():
        raise HTTPException(status_code=400, detail="Title and content required")

    embedding = get_ollama_embedding(document.content)
    
    # Check if embedding generation failed
    if not embedding or len(embedding) == 0:
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate embedding for the document. Please check if Ollama is running and the embedding model is available."
        )
    
    doc_id = f"doc_{datetime.now().timestamp()}"

    metadata = {
        **document.metadata,
        "title": document.title,
        "created_at": datetime.now().isoformat(),
        "document_type": "user_added"
    }
    collection = get_collection()  # ✅ called here, after startup

    try:
        collection.add(
            embeddings=[embedding],
            documents=[document.content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return {"message": "Document added successfully", "id": doc_id, "title": document.title}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to add document to database: {str(e)}"
        )

@router.get("/", response_model=list[DocumentResponse])
async def get_documents():
    collection = get_collection()
    result = collection.get(include=["metadatas", "documents"])
    documents = []
    for i, doc_id in enumerate(result["ids"]):
        metadata = result["metadatas"][i]
        documents.append(DocumentResponse(
            id=doc_id,
            title=metadata.get("title", "Untitled"),
            content=result["documents"][i],
            metadata=metadata,
            created_at=metadata.get("created_at", "")
        ))
    return documents

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    collection = get_collection()
    existing = collection.get(ids=[document_id])
    if not existing["ids"]:
        raise HTTPException(status_code=404, detail="Document not found")

    collection.delete(ids=[document_id])
    return {"message": "Document deleted successfully", "id": document_id}
