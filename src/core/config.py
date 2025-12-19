# Model selection
# Default: gemini-2.5-flash (working model)
# Alternatives if needed:
#   - "gemini-1.5-flash" 
#   - "gemini-pro"
#   - "gemini-1.5-pro" (may require billing)
LLM_MODEL_NAME = "gemini-2.5-flash"

# RAG / Embedding
COLLECTION_NAME = "srs_collection"
EMBEDDING_MODEL_NAME = "distiluse-base-multilingual-cased-v1"

DEFAULT_CHUNK_SIZE = 1000       # characters
DEFAULT_CHUNK_OVERLAP = 100     # characters

DEFAULT_TOP_K = 5