# ============================================================================== 
# Author: Joel Montes de Oca Lopez
# Creation Date: 30/08/2025
# Last Modified: 30/08/2025
# Contact: https://joelmontesdeoca.dev
# 
# Description:
# This script contains the API routes for articles content resume with Ollama LLM, the api
# gets called from CMS app to create a proper description of the article.
#
# Contained Routes:
#
# 1. Route: /resume
#    Description: Creates a summary for the article using the Ollama service. This endpoint accepts
#    a resume request containing the article content, the target length for the summary,
#    and the model to use. It processes the request, interacts with the Ollama service
#    for summarization, and returns the summarized text along with metadata about the
#    summarization process.
#
# Usage:
# These routes are designed for use in a FastAPI environment, enabling seamless 
# management of user accounts and their associated data.
# ==============================================================================

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.translation import ResumeRequest, ResumeResponse
from app.services.resume import resume_service
from app.utils.auth import verify_user_access
from app.schemas.testUser import GoogleUser

router = APIRouter()

# ===========================================================================
# Route: /user/add
# Description:  Create a new user
# ===========================================================================
@router.post("/resume", response_model=ResumeResponse)
async def resume_text(
    request: ResumeRequest,
    current_user: GoogleUser = Depends(verify_user_access)
):
    """
    Resume endpoint with Google Authentication
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
        response = await resume_service.summarize(request)
        print(f"DEBUG: Resume successful: {response}")
        return response
        
    except Exception as e:
        print(f"DEBUG: Resume failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume failed: {str(e)}"
        )