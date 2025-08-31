from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import Query, RAGResponse
from datetime import datetime
from routes.search import search_documents
from llm import generate_answer, generate_answer_streaming
import json


router = APIRouter()

@router.post("/", response_model=RAGResponse)
async def perform_rag(query: Query):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Set better defaults for RAG
    query.top_k = query.top_k or 20  # Use all documents
    query.threshold = query.threshold or 0.55  # 55% similarity threshold

    search_results = await search_documents(query)

    # Only use docs above threshold
    if search_results:
        context_docs = [result.content for result in search_results if result.similarity >= query.threshold]
        if context_docs:
            generated_answer, model_used = generate_answer(query.question, context_docs)
        else:
            generated_answer, model_used = "No relevant documents found."
    else:
        generated_answer,model_used = "No relevant documents found."

    return RAGResponse(
        query=query.question,
        # retrieved_documents=search_results,
        generated_answer=generated_answer,
        timestamp=datetime.now().isoformat(),
        model_used=model_used
    )

@router.post("/stream")
async def perform_rag_streaming(query: Query):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Set better defaults for RAG streaming
    query.top_k = query.top_k or 20  # Use all documents
    query.threshold = query.threshold or 0.55  # 55% similarity threshold

    async def generate_stream():
        try:
            # Get search results
            search_results = await search_documents(query)
            
            # Send search results info
            yield f"data: {json.dumps({'type': 'search_results', 'count': len(search_results)})}\n\n"
            
            if search_results:
                context_docs = [result.content for result in search_results if result.similarity >= query.threshold]
                if context_docs:
                    yield f"data: {json.dumps({'type': 'context_found', 'documents': len(context_docs)})}\n\n"
                    
                    # Stream the answer
                    async for chunk in generate_answer_streaming(query.question, context_docs):
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant documents found.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant documents found.'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/plain")
