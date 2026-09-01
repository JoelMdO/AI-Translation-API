# ============================================================================== 
# Author: Joel Montes de Oca Lopez
# Creation Date: 25/07/2025
# Last Modified: 1/09/2026
# Contact: https://joelmontesdeoca.dev
# 
# Description:
# This script contains the API routes for api translation with Ollama LLM, using 
# the models Llama 3.2 and Yag, the api gets called from CMS app for translation.
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
from services import translation_service
from utils.auth import verify_user_access
from schemas.testUser import GoogleUser
import logging
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

# ===========================================================================
# Route: /user/add
# Description:  Create a new user
# ===========================================================================
@router.post(
    "/translate",
    response_model=TranslationResponse,
    response_model_exclude_none=True,
)
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
    print(f"DEBUG: Received request at /api/translate")
    try:
        # Process translation through service layer
        response = await translation_service.TranslationService().translate(request)
        print(
            "/// Translation response: "
            f"{response.model_dump(mode='json', exclude_none=True)}"
        )
        print(f"/// Translation response status: {response.status}")
        if response.status == 200:
            print(f"TRANSLATE ROUTER: Translation successful for user: {current_user.email}")
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Translation failed."
            )
    except Exception as e:
        print(f"Translation failed for user: {current_user.email}, error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation failed."
        )
