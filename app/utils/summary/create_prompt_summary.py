"""
Text sanitization utilities
Cleans and processes text responses from Ollama before sending to client
"""
from typing import Optional
from utils.load_vocabulary import get_summary_rules
from utils.rag_service.build_context import build_context_block
async def create_prompt_summary(type: str, text: str, target_language: str, title: Optional[str] = None, body: Optional[str] = None, section: Optional[str] = None) -> str:
    """
    Create a structured prompt for summary
    
    Args:
        type: Type of summary (e.g., "raw" for raw summary)
        text: Text to summarize
        target_language: Target language for summary
        title: Optional title for the summary
        body: Optional body for the summary
        section: Optional section for the summary
        
    Returns:
        Formatted prompt string
    """

    # Build RAG context block (gracefully empty when ChromaDB unavailable)
    context_block = await build_context_block(text, target_language)
    if context_block:
        print("DEBUG: RAG context block injected into translation prompt")
    else:
        print("DEBUG: No RAG context available, proceeding without enrichment")
            
    # Get the styles from vocabulary.json
    summary_rules = get_summary_rules(target_language)
    if summary_rules:
        rules_block = "\n".join(f"- {r}" for r in summary_rules)
        summary_rules = f"## Summary Rules\n{rules_block}"

    prompt = f"""You are an AI specialized in creating article descriptions. Given the below blog title and slice of article body, generate a description that provides a clear idea of its content while encouraging readers to explore further. 
    the language shall be {target_language}, accordingly create the description by following the next list of rules:
                    Rules:{summary_rules}
- Return only the article description. Do not wrap it in extra markdown, do not explain, do not say "Here is your article description".
- Do not return any context array numbers.
{"if {target_language} == 'en': Title: " + title if title else "", " Article: " + body if body else ""} else {"Titulo: " + title if title else "", " Artículo: " + body if body else ""}"""
    
    return prompt
