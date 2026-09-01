"""
Text sanitization utilities
Cleans and processes text responses from Ollama before sending to client
"""
from typing import Optional
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def create_prompt_translation(target_language: str, text: Optional[str] = None,  type: Optional[str] = None, title: Optional[str] = None, body: Optional[str] = None, section: Optional[str] = None) -> str:
    """
    Create a structured prompt for translation
    
    Args:
        type: Type of translation (e.g., "raw" for raw translation)
        text: Text to translate
        target_language: Target language for translation
        title: Optional title for the translation
        body: Optional body for the translation
        section: Optional section for the translation
        
    Returns:
        Formatted prompt string
    """
    print(f"DOING CREATE PROMPT DEBUG: Creating translation prompt with type: {type}, target_language: {target_language}")

    prompt = f"""
        ## ROLE
            You are Senior flight operations and technical documentation expert and specialized in translating to {target_language}.
            Your task is strictly to translate the provided text into {target_language} by following the next list of rules:
        
        ## CRITICAL DIRECTIVES AND CONSTRAINTS
            1. **Zero Chat:** Return ONLY the translated text. No markdown code blocks (```), no introductions, no explanations, no chatty filler text, no "Aquí te dejo la traducción:", no "Here is the translation:" .

        Text to Translate:
        {text}

        Output format:
        Return ONLY the translated "text" values.
    """
    return prompt
