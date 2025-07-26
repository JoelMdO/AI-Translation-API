"""
Translation service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
from app.utils.generate_translation import ollama_service
from app.utils.sanitize_text import sanitize_text
from app.utils.create_prompt_translation import create_prompt_translation
from app.schemas.translation import TranslationRequest, TranslationResponse


class TranslationService:
    """Service class for handling translation business logic"""
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Process translation request
        
        Args:
            request: Translation request data
            
        Returns:
            Translation response with sanitized text
            
        Raises:
            Exception: If translation fails
        """
        #Sanitization and validation can be added here if needed
        # Sanitize input text
        sanitized_title = sanitize_text(request.title)
        sanitized_body = sanitize_text(request.body)
        sanitized_section = sanitize_text(request.section)
        sanitized_target_language = sanitize_text(request.target_language)

        # Create structured prompt
        prompt = create_prompt_translation(
            title=sanitized_title,
            body=sanitized_body,
            section=sanitized_section,
            target_language=sanitized_target_language
        )
        
        # Get translation from Ollama
        raw_translation = await ollama_service.generate_translation(
            prompt=prompt,
            model=request.model
        )
        
        # Sanitize the response
        clean_translation = sanitize_text(raw_translation)
        
        return TranslationResponse(
            translated_text=clean_translation,
            success=True,
            model_used=request.model
        )


# Global service instance
translation_service = TranslationService()
