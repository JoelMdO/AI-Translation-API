"""
Text sanitization utilities
Cleans and processes text responses from Ollama before sending to client
"""
import re


def sanitize_text(text: str) -> str:
    """
    Sanitize text response from Ollama
    
    Args:
        text: Raw text from Ollama
        
    Returns:
        Cleaned and sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove any potential injection attempts (basic sanitization)
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text
