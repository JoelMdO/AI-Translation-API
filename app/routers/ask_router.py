# ============================================================================== 
# Author: Joel Montes de Oca Lopez
# Creation Date: 25/07/2025
# Last Modified: 25/07/2025
# Contact: https://joelmontesdeoca.dev
# 
# Description:
# This script contains the API routes for api translation with Ollama LLM, the api
# gets called from CMS app for translation.
#
# Contained Routes:
#
# 1. Route: /translate
#    Description: Translates text using the Ollama service. This endpoint accepts
#    a translation request containing the text to be translated, the target language,
#    and the model to use. It processes the request, interacts with the Ollama service
#    for translation, and returns the translated text along with metadata about the
#    translation process.
#
# Usage:
# These routes are designed for use in a FastAPI environment, enabling seamless 
# management of user accounts and their associated data.
# ==============================================================================

from fastapi import APIRouter, HTTPException, status, Depends
# import uvicorn
# import os
from schemas.translation import TranslationRequest, TranslationResponse
from services.translation import translation_service
from utils.auth import verify_user_access
from schemas.testUser import GoogleUser

router = APIRouter()

# ===========================================================================
# Route: /user/add
# Description:  Create a new user
# ===========================================================================
@router.post("/ask", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user: GoogleUser = Depends(verify_user_access)
):
    """
    Translation endpoint with Google Authentication
    1. Validates Google ID token from NextJS app
    2. Checks user permissions
    3. Sends text to Ollama for translation
    4. Sanitizes response
    5. Returns translated text
    
    Authentication:
    - Requires valid Google ID token in Authorization header
    - Token format: "Bearer <google_id_token>"
    - User must have verified email
    """
    try:
        # Process translation through service layer
        response = await translation_service.translate(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )