"""
Text sanitization utilities
Cleans and processes text responses from Ollama before sending to client
"""

def create_prompt_translation(title: str, body: str, section: str, target_language: str) -> str:
    """
    Create a structured prompt for translation
    
    Args:
        title: Title text to translate
        body: Body text to translate
        section: Section text to translate
        target_language: Target language for translation
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Translate the following text to {target_language}:

Title: {title}
Body: {body}
Section: {section}

Please provide only the translation without any additional commentary."""
    
    return prompt
