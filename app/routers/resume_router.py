# ============================================================================== 
# Author: Joel Montes de Oca Lopez
# Creation Date: 20/10/2025
# Last Modified: 22/03/2026
# Contact: https://joelmontesdeoca.dev
# 
# Description:
# This script contains the API routes for articles content summary with Ollama LLM, the api
# gets called from CMS app to create a proper description of the article.
#
# Contained Routes:
#
# 1. Route: /summary
#    Description: Creates a summary for the article using the Ollama service. This endpoint accepts
#    a summary request containing the article content, the target length for the summary,
#    and the model to use. It processes the request, interacts with the Ollama service
#    for summarization, and returns the summarized text along with metadata about the
#    summarization process.
#
# Usage:
# These routes are designed for use in a FastAPI environment, enabling seamless 
# management of user accounts and their associated data.
# ==============================================================================

from fastapi import APIRouter, HTTPException, status, Depends
# from app.schemas.translation import ResumeRequest, ResumeResponse
# from app.services.resume import resume_service
# from app.utils.auth import verify_user_access
# from app.schemas.testUser import GoogleUser
from schemas.translation import ResumeRequest, ResumeResponse
from services.summary import summary_service
from utils.auth import verify_user_access
from schemas.testUser import GoogleUser

router = APIRouter()

# ===========================================================================
# Route: /summary
# Description:  Create a summary for the article
# ===========================================================================
@router.post("/summary", response_model=ResumeResponse)
async def summarize_text(
    request: ResumeRequest,
    current_user: GoogleUser = Depends(verify_user_access)
):
    """
    Summary endpoint with Google Authentication
    1. Validates Google ID token from NextJS app
    2. Checks user permissions
    3. Sends text to Ollama for summarization
    4. Sanitizes response
    5. Returns summarized text
    
    Authentication:
    - Requires valid Google ID token in Authorization header
    - Token format: "Bearer <google_id_token>"
    - User must have verified email
    """
    try:
        # Process summarization through service layer
        print(f"DEBUG: Summary request: {request}")
        response = await summary_service.summarize(request)
        print(f"DEBUG: Summary successful: {response}")
        return response
        
    except Exception as e:
        print(f"DEBUG: Summary failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary failed: {str(e)}"
        )