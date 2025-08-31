import logging
from database import collection
from config import config

def generate_answer_extractive(query: str, context_docs: list[str]) -> tuple[str, str]:
    """Fallback extractive answer (when LLM fails)"""
    if not context_docs:
        return "No relevant docs found.", "extractive"

    query_words = set(query.lower().split())
    best_sentences = []

    for doc in context_docs:
        sentences = doc.split('. ')
        for s in sentences:
            overlap = len(query_words.intersection(set(s.lower().split())))
            if overlap > 0:
                best_sentences.append((s, overlap))

    # Sort sentences by overlap count
    best_sentences.sort(key=lambda x: x[1], reverse=True)
    top_sentences = [s[0] for s in best_sentences[:3]]

    return ". ".join(top_sentences) or "No good match.", "extractive"
