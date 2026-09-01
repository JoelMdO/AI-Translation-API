from dotenv import load_dotenv
import os
import ast

load_dotenv()

_raw_origins = os.getenv("ALLOWED_ORIGINS", '["*"]')
try:
    ALLOWED_ORIGINS = ast.literal_eval(_raw_origins)
    if not isinstance(ALLOWED_ORIGINS, list):
        ALLOWED_ORIGINS = [str(ALLOWED_ORIGINS)]
except (ValueError, SyntaxError):
    ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
CORS_METHODS = ast.literal_eval(os.getenv("CORS_METHODS", '["POST","GET","OPTIONS"]'))
CORS_ALLOW_HEADERS = ast.literal_eval(os.getenv("CORS_ALLOW_HEADERS", '["Content-Type","Authorization"]'))
URL_AUTH = os.getenv("URL_AUTH")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL")
OLLAMA_BACKUP_MODEL = os.getenv("OLLAMA_BACKUP_MODEL")
OLLAMA_REQUEST_TIMEOUT = float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "900"))
TESTING_MODE = os.getenv("TESTING_MODE", "false").lower() == "true"
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# RAG / ChromaDB settings
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
RAG_N_RESULTS = int(os.getenv("RAG_N_RESULTS", "3"))
CMS_RAG_URL = os.getenv("CMS_RAG_URL", "")
CMS_RAG_TOKEN = os.getenv("CMS_RAG_TOKEN", "")
