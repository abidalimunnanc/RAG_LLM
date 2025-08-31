class Config:
    CHROMADB_PATH = "./chromadb_storage"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "microsoft/DialoGPT-medium"
    MAX_TOKENS = 2000  # Optimized for efficiency
    TEMPERATURE = 0.7
    MIN_RESPONSE_TOKENS = 50  # Reduced for faster responses
    MAX_RESPONSE_TOKENS = 1500  # Optimized for efficiency

config = Config()
