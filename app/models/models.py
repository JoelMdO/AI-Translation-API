from pydantic import BaseModel
from typing import Optional, List


class TranslationRequest(BaseModel):
    title: str
    body: str
    section: str
    target_language: Optional[str] = "Spanish"
    model: Optional[str] = "llama3.2"


class TranslationResponse(BaseModel):
    translated_text: str
    original_prompt: str
    model_used: str
    success: bool


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
