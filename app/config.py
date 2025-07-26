from dotenv import load_dotenv
import os
import ast

load_dotenv()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")
CORS_METHODS = ast.literal_eval(os.getenv("CORS_METHODS", '["POST","GET","OPTIONS"]'))
CORS_ALLOW_HEADERS = ast.literal_eval(os.getenv("CORS_ALLOW_HEADERS", '["Content-Type","Authorization"]'))
URL_AUTH = os.getenv("URL_AUTH")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL")
TESTING_MODE = os.getenv("TESTING_MODE", "false").lower() == "true"