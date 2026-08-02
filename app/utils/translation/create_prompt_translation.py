"""
Text sanitization utilities
Cleans and processes text responses from Ollama before sending to client
"""
from typing import Optional
import logging
from utils.load_vocabulary import get_style_rules
# from utils.rag_service.build_context import build_context_block
logger = logging.getLogger(__name__)
async def create_prompt_translation(type: str, text: str, target_language: str, title: Optional[str] = None, body: Optional[str] = None, section: Optional[str] = None) -> str:
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
    logger.info("DEBUG: Creating translation prompt with type: %s, target_language: %s", type, target_language)
    # Build RAG context block (gracefully empty when ChromaDB unavailable)
    # context_block = await build_context_block(text, target_language)
    # if context_block:
    #     logger.info("DEBUG: RAG context block injected into translation prompt: %s", context_block[:500])  # Log first 500 chars of context for debugging
    # else:
    #     logger.info("DEBUG: No RAG context available, proceeding without enrichment")
            
    # style_prefix = f"{context_block}\n\n" if context_block else ""
    # logger.info("DEBUG: Getting style rules for target language: %s", target_language)
    # Get the styles from vocabulary.json
    style_rules = get_style_rules(target_language)
    logger.info("DEBUG: Retrieved %d style rules for language: %s", len(style_rules), target_language)
    if style_rules:
        rules_block = "\n".join(f"- {r}" for r in style_rules)
        style_rules = f"## Style Rules\n{rules_block}"

#TODO working on semantic filtering to reduce the number of rules injected into the prompt, for now we are injecting all the rules for the target language, but in the future we could filter them based on the content of the text to translate and the target language
#     prompt = f"""You are an AI specialized in translating to {target_language}, accordingly translate the below text by following the next list of rules:
#                     Rules:{style_rules}
# -Technical Context (RAG): Always prioritize the terms and acronyms found in the provided {style_prefix}. 
# -Use the specific technical context provided in {style_prefix} instead of a generic or literal translation.
# -Translate the following text segments to {target_language}. 
# - Use only one translation, no alternatives or explanations.
# - In case the text is a list, translate ONLY the text content after each number, once done keep the same numbering if any (1., 2., 3., etc.)
# - Preserve the HTML structure and tags exactly as they are.
# - Translate literally the visible text between the tags.
# - Return only the translated. Do not wrap it in extra markdown, do not explain, do not say "Here is your translation".
# - Use style suitable for an educational or explanatory talk. Avoid slang or regional idioms.
# - Do not return any context array numbers.
# {"- Return the translation in this exact format: # Título: [translated title] # Cuerpo: [translated body] # Sección: [translated section] Title: {title} Body: {body} Sección: {section}" if type == "raw" else ""}
# """
    style_rules = style_rules or ""

    prompt = f"""You are an AI specialized in translating to {target_language}, accordingly translate the below text by following the next list of rules:
                    Rules:{style_rules}
-Translate the following text segments to {target_language}. 
- Use only one translation, no alternatives or explanations.
- In case the text is a list, translate ONLY the text content after each number, once done keep the same numbering if any (1., 2., 3., etc.)
- Preserve the HTML structure and tags exactly as they are.
- Translate literally the visible text between the tags.
- Return only the translated. Do not wrap it in extra markdown, do not explain, do not say "Here is your translation".
- Use style suitable for an educational or explanatory talk. Avoid slang or regional idioms.
- Do not return any context array numbers.
{"- Return the translation in this exact format: # Título: [translated title] # Cuerpo: [translated body] # Sección: [translated section] Title: {title} Body: {body} Sección: {section}" if type == "raw" else ""}
IMPORTANT: The text below contains segments separated by '---SEGMENT---'. You MUST preserve every '---SEGMENT---' separator exactly in your translated output. The number of '---SEGMENT---' separators in the output MUST match the number in the input. Translate each segment independently.
The text to translate is:{text}
"""

    return prompt #type: ignore
