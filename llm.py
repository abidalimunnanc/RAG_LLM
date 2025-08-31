import os
import logging
import time
import requests
from config import config
from rag import generate_answer_extractive
import logging
import ollama
from utils.ollama_monitor import record_ollama_request

# # Try to import OpenAI
# try:
#     import openai
#     openai.api_key = os.getenv("OPENAI_API_KEY")
#     OPENAI_AVAILABLE = True
# except ImportError:
#     OPENAI_AVAILABLE = False

# # Try to import Transformers for local model
# try:
#     from transformers import pipeline
#     llm_pipeline = pipeline(
#         "text-generation",
#         model=config.LLM_MODEL,
#         tokenizer=config.LLM_MODEL,
#         max_length=config.MAX_TOKENS,
#         temperature=config.TEMPERATURE,
#         pad_token_id=50256
#     )
#     TRANSFORMERS_AVAILABLE = True
# except ImportError:
#     llm_pipeline = None
#     TRANSFORMERS_AVAILABLE = False




def generate_answer(query: str, context_docs: list[str], model: str = "gemma3:1b") -> tuple[str, str]:
    """Generate an answer using Ollama, fallback to extractive"""
    start_time = time.time()
    max_retries = 2  # Prevent infinite loops
    
    for attempt in range(max_retries):
        try:
            # Check if model is available
            if not _is_model_available(model):
                logging.warning(f"Model {model} not available, trying to pull...")
                _pull_model_if_needed(model)
            
            context = "\n\n".join(context_docs[:3])  # Use up to 3 documents for better context
            prompt = f"""Context:
{context}

Question: {query}

Instructions: Please provide a comprehensive and detailed answer based on the context provided. Your response should:
1. Be thorough and well-explained
2. Include relevant details and examples from the context
3. Be at least 100 words long
4. Address all aspects of the question
5. Use clear and professional language

Answer:"""

            response = ollama.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": config.TEMPERATURE, 
                    "num_predict": config.MAX_RESPONSE_TOKENS,
                    "stop": ["Question:", "Context:", "Human:", "Assistant:"]
                }
            )

            answer = response["response"].strip()
            
            # Check minimum response length (but don't recurse infinitely)
            word_count = len(answer.split())
            if word_count < config.MIN_RESPONSE_TOKENS and attempt < max_retries - 1:
                logging.info(f"Response too short ({word_count} words), attempt {attempt + 1}/{max_retries}")
                continue  # Try again instead of recursing
            
            # Ensure the answer ends properly
            answer = ensure_proper_ending(answer)
            
            # Record the request for monitoring
            response_time = time.time() - start_time
            record_ollama_request(model, response_time, success=True)
            
            return answer, f"ollama-{model}"
            
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"⚠️ Ollama generation failed (attempt {attempt + 1}): {e}")
                continue
            else:
                # Record the failed request for monitoring
                response_time = time.time() - start_time
                record_ollama_request(model, response_time, success=False)
                
                logging.error(f"⚠️ Ollama generation failed after {max_retries} attempts: {e}")
                return generate_answer_extractive(query, context_docs)
    
    # Fallback if all attempts fail
    return generate_answer_extractive(query, context_docs)

async def generate_answer_streaming(query: str, context_docs: list[str], model: str = "gemma3:1b"):
    """Generate an answer using Ollama streaming with optimized performance"""
    start_time = time.time()
    try:
        # Check if model is available
        if not _is_model_available(model):
            logging.warning(f"Model {model} not available, trying to pull...")
            _pull_model_if_needed(model)
        
        context = "\n\n".join(context_docs[:3])  # Use up to 3 documents for better context
        prompt = f"""Context:
{context}

Question: {query}

Instructions: Please provide a comprehensive and detailed answer based on the context provided. Your response should:
1. Be thorough and well-explained
2. Include relevant details and examples from the context
3. Be at least 100 words long
4. Address all aspects of the question
5. Use clear and professional language

Answer:"""

        stream = ollama.generate(
            model=model,
            prompt=prompt,
            options={
                "temperature": config.TEMPERATURE, 
                "num_predict": config.MAX_RESPONSE_TOKENS,
                "stop": ["Question:", "Context:", "Human:", "Assistant:"]
            },
            stream=True
        )

        accumulated_text = ""
        buffer = ""
        chunk_count = 0
        max_chunks = config.MAX_RESPONSE_TOKENS // 10  # Approximate chunk limit
        
        for chunk in stream:
            if chunk.get("response"):
                buffer += chunk["response"]
                chunk_count += 1
                
                # Check if we're approaching chunk limit
                if chunk_count >= max_chunks:
                    # Yield remaining buffer and stop
                    if buffer:
                        accumulated_text += buffer
                        yield buffer
                    break
                
                # Process buffer to yield natural chunks (without artificial delays)
                while len(buffer) > 0:
                    # Look for natural break points
                    break_points = [' ', '.', ',', '!', '?', ':', ';', '\n']
                    break_found = False
                    
                    for i, char in enumerate(buffer):
                        if char in break_points:
                            # Yield the chunk up to this break point
                            chunk_to_yield = buffer[:i+1]
                            accumulated_text += chunk_to_yield
                            buffer = buffer[i+1:]
                            break_found = True
                            
                            # Yield immediately without artificial delays
                            yield chunk_to_yield
                            
                            # Check for natural ending
                            if detect_natural_ending(accumulated_text):
                                # Add a final pause for natural ending
                                await asyncio.sleep(random.uniform(0.2, 0.4))
                                break
                            
                            break
                    
                    # If no break point found and buffer is getting long, yield anyway
                    if not break_found and len(buffer) > 10:
                        chunk_to_yield = buffer
                        accumulated_text += chunk_to_yield
                        buffer = ""
                        
                        import asyncio
                        import random
                        await asyncio.sleep(random.uniform(0.02, 0.05))  # Variable delay
                        
                        yield chunk_to_yield
                        break
                    
                    # If no break found and buffer is short, wait for more content
                    if not break_found:
                        break
        
        # Yield any remaining buffer content
        if buffer:
            yield buffer
        
        # Ensure proper ending
        final_answer = ensure_proper_ending(accumulated_text)
        if final_answer != accumulated_text:
            # If ending was modified, yield the final part
            remaining = final_answer[len(accumulated_text):]
            if remaining:
                yield remaining
        
        # Record the successful streaming request
        response_time = time.time() - start_time
        record_ollama_request(model, response_time, success=True)
                
    except Exception as e:
        # Record the failed streaming request
        response_time = time.time() - start_time
        record_ollama_request(model, response_time, success=False)
        
        logging.warning(f"⚠️ Ollama streaming generation failed: {e}")
        # Fallback to non-streaming with simulated streaming
        answer, _ = generate_answer(query, context_docs, model)
        
        # Simulate streaming by breaking the answer into chunks
        words = answer.split()
        for i, word in enumerate(words):
            yield word + (' ' if i < len(words) - 1 else '')
            import asyncio
            import random
            await asyncio.sleep(random.uniform(0.05, 0.15))  # Variable delay between words

def ensure_proper_ending(text: str) -> str:
    """Ensure the text ends properly with natural sentence completion"""
    if not text:
        return text
    
    text = text.strip()
    
    # Check if text ends with proper punctuation
    if text.endswith(('.', '!', '?')):
        return text
    
    # Check if text ends with incomplete sentence
    last_sentence = text.split('.')[-1].strip()
    if len(last_sentence) < 5:  # Reduced threshold for incomplete sentence
        # Remove the incomplete sentence
        sentences = text.split('.')
        if len(sentences) > 1:
            text = '.'.join(sentences[:-1]) + '.'
        else:
            # If only one sentence and it's incomplete, add a period
            text = text.rstrip() + '.'
    
    # Ensure proper capitalization
    if text and not text[0].isupper():
        text = text[0].upper() + text[1:]
    
    return text

def _is_model_available(model: str) -> bool:
    """Check if a model is available in Ollama"""
    try:
        response = requests.get(f"http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [m['name'] for m in data.get('models', [])]
            return model in available_models
    except Exception as e:
        logging.debug(f"Error checking model availability: {e}")
    return False

def _pull_model_if_needed(model: str):
    """Pull a model if it's not available"""
    try:
        logging.info(f"Pulling model {model}...")
        response = requests.post(f"http://localhost:11434/api/pull", 
                               json={"name": model}, timeout=300)
        if response.status_code == 200:
            logging.info(f"Successfully pulled model {model}")
        else:
            logging.error(f"Failed to pull model {model}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error pulling model {model}: {e}")

def detect_natural_ending(text: str) -> bool:
    """Detect if the text has reached a natural ending point"""
    if not text:
        return False
    
    # Check for natural ending patterns
    ending_patterns = [
        r'\.$',  # Ends with period
        r'!$',   # Ends with exclamation
        r'\?$',  # Ends with question mark
        r'\.\s*$',  # Ends with period and whitespace
        r'\.\s*\n*$',  # Ends with period and newlines
        r'Thank you\.?$',  # Polite ending
        r'That\'s all\.?$',  # Conclusion
        r'In conclusion\.?$',  # Formal conclusion
        r'Hope this helps\.?$',  # Helpful ending
    ]
    
    import re
    for pattern in ending_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check for incomplete sentences at the end
    sentences = text.split('.')
    if len(sentences) > 1:
        last_sentence = sentences[-1].strip()
        if len(last_sentence) < 5:  # Very short incomplete sentence
            return True
    
    return False


    # # Try local Transformers model
    # if TRANSFORMERS_AVAILABLE and llm_pipeline:
    #     try:
    #         context = "\n".join(context_docs[:2])
    #         prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
    #         result = llm_pipeline(prompt, num_return_sequences=1)[0]["generated_text"]
    #         answer = result[len(prompt):].strip()
    #         return answer, "local-llm"
    #     except Exception as e:
    #         logging.warning(f"Local LLM failed: {e}")

    # # Fallback to extractive
    # return generate_answer_extractive(query, context_docs)
