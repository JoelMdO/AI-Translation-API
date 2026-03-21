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
#     prompt = f"""Translate the following text to {target_language}:

# Title: {title}
# Body: {body}
# Section: {section}

    prompt = f"""Translate the following text segments to {target_language}. 
- Use only one translation, no alternatives or explanations.
- Preserve the HTML structure and tags exactly as they are.
- Translate literally the visible text between the tags.
- Use a neutral, formal, and clear Spanish style — suitable for an educational or explanatory talk. Avoid slang or regional idioms.
- Return only the translated. Do not wrap it in extra markdown, do not explain, do not say "Here is your translation".
- Do not return any context array numbers.
- Return the translation in this exact format:
# Título: [translated title]
# Cuerpo: [translated body]
# Sección: [translated section]
Title: {title}
Body: {body}
Sección: {section}
"""
# - Return the translation in this exact format:
# Título: [translated title]
# Cuerpo: [translated body]
# Sección: [translated section]
# # Title: {title}
# # Body: {body}
# # Section: {section}
# """    
    
    return prompt
